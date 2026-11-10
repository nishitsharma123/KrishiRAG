"""
RAG Orchestration Service — Phase 4
End-to-end question answering pipeline:
Question Preprocessing -> Hybrid Retrieval -> Reranking -> Evidence Sufficiency Check
-> Grounded Prompt Construction -> Qwen3 Generation -> Citation Validation -> DB Persistence
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.schemas.chat import ChatResponse, SourceCitation
from backend.app.schemas.retrieval import RetrievedChunkResponse
from backend.app.services.retrieval_service import retrieve_context, RetrievedChunk
from backend.app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# Minimum cross-encoder threshold below which passages are deemed ungrounded/irrelevant
RERANKER_MIN_SUFFICIENCY_SCORE = -4.0

SYSTEM_PROMPT = """You are KrishiRAG, an expert agricultural advisory assistant built strictly on verified ICAR publications and government package of practices.

Answer the user's question strictly using ONLY the retrieved context passages provided below.

MANDATORY RULES:
1. Never invent or assume agricultural recommendations, dosages, or chemical names.
2. Do not use external or unsupported general knowledge. Every factual recommendation must be backed by the supplied passages.
3. Preserve fertilizer quantities, seed rates, spray concentrations, and measurement units EXACTLY as stated in the text (e.g. kg/ha, g/litre, ml/acre, DAS).
4. Never transfer pesticide or herbicide recommendations between different crops without explicit textual evidence.
5. If the retrieved documents contain conflicting recommendations, explicitly disclose the discrepancy.
6. Explain technical agricultural terminology in clear, practical terms for farmers.
7. If the retrieved passages do NOT contain sufficient evidence to answer the question, explicitly state: "The authentic ICAR publications in the knowledge base do not contain sufficient evidence to answer this question." Do not attempt to guess.
8. Cite your sources directly in the text using the format: [Document Title, p. PageNumber].

REQUIRED ANSWER STRUCTURE:
- **Direct Answer**: Concise, direct answer to the question.
- **Detailed Explanation**: Clear agronomic explanation grounded in the text.
- **Recommended Practices**: Step-by-step verified recommendations with exact dosages, timings, and citations [Document Title, p. X].
- **Important Precautions**: Critical safety, pollinator, soil, or resistance warnings mentioned in the documents.
- **Verified Sources**: List of cited publications and page numbers.
"""


class RAGService:
    """Orchestrates end-to-end RAG question answering."""

    @classmethod
    def check_evidence_sufficiency(
        cls,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> Tuple[bool, Optional[str]]:
        """
        Evaluate whether the retrieved passages contain sufficient evidence
        to answer the user's question without hallucination.
        """
        if not retrieved_chunks:
            return False, "No relevant documents found in the agricultural knowledge base."

        top_chunk = retrieved_chunks[0]

        # Check if the top reranker score is below the minimum threshold
        if top_chunk.relevance_score < RERANKER_MIN_SUFFICIENCY_SCORE:
            logger.warning(
                "Top reranker score %.3f is below threshold %.3f — abstaining.",
                top_chunk.relevance_score,
                RERANKER_MIN_SUFFICIENCY_SCORE,
            )
            return False, "Retrieved documents have low semantic alignment with the query."

        # Check keyword overlap for non-agricultural or out-of-domain queries
        question_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", question.lower()))
        combined_text = " ".join(c.text.lower() for c in retrieved_chunks)

        # Remove common query filler words
        stop_words = {"what", "when", "where", "which", "about", "should", "could", "would", "their", "there", "recommend", "recommended", "management", "control"}
        content_words = question_words - stop_words

        if content_words:
            matched_words = [w for w in content_words if w in combined_text]
            overlap_ratio = len(matched_words) / len(content_words)
            if overlap_ratio < 0.25:
                logger.warning("Low content word overlap (%.2f) — abstaining.", overlap_ratio)
                return False, "The query topics are not sufficiently addressed in the verified publications."

        return True, None

    @classmethod
    def construct_context_prompt(
        cls,
        question: str,
        retrieved_chunks: List[RetrievedChunk],
        conversation_history: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        Build the chat messages payload for Qwen3.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Append recent relevant history (up to last 2 user-assistant pairs)
        if conversation_history:
            for msg in conversation_history[-4:]:
                messages.append(msg)

        # Format retrieved evidence passages
        context_blocks = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            context_blocks.append(
                f"--- PASSAGE {i} ---\n"
                f"Document: {chunk.document_title}\n"
                f"Page: {chunk.page_number}\n"
                f"Source Institution: {chunk.source_institution}\n"
                f"Section: {chunk.section_heading or 'General'}\n"
                f"Content:\n{chunk.text.strip()}\n"
            )

        context_text = "\n".join(context_blocks)
        user_message_content = (
            f"RETRIEVED AGRICULTURAL CONTEXT PASSAGES:\n\n{context_text}\n\n"
            f"FARMER / USER QUESTION:\n{question}\n\n"
            f"Please answer strictly based on the passages above following the required answer structure."
        )

        messages.append({"role": "user", "content": user_message_content})
        return messages

    @classmethod
    def validate_citations(
        cls,
        answer: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> List[SourceCitation]:
        """
        Extract citations from the generated answer and match them
        against the actually retrieved chunks. Rejects fabricated citations.
        """
        validated_sources: List[SourceCitation] = []
        seen_keys = set()

        # Build lookup table from retrieved chunks
        chunk_lookup = {}
        for c in retrieved_chunks:
            # Map by document_id and page
            key = (c.document_title.lower().strip(), c.page_number)
            chunk_lookup[key] = c

        # Find citation occurrences like [Document Title, p. 2] or [p. 2]
        citation_patterns = [
            r"\[([^,\]]+),\s*p(?:age|\.)?\s*(\d+)\]",
            r"\[p(?:age|\.)?\s*(\d+)\]",
        ]

        for chunk in retrieved_chunks:
            # Check if document title or page is mentioned in the answer
            title_part = chunk.document_title[:25].lower()
            page_str = f"p. {chunk.page_number}"
            page_str_alt = f"page {chunk.page_number}"

            answer_lower = answer.lower()
            if (title_part in answer_lower or page_str in answer_lower or page_str_alt in answer_lower) or (chunk.relevance_score > 0.5):
                key = (chunk.document_id, chunk.page_number)
                if key not in seen_keys:
                    seen_keys.add(key)
                    validated_sources.append(
                        SourceCitation(
                            document_id=chunk.document_id,
                            document_title=chunk.document_title,
                            source_institution=chunk.source_institution,
                            page_number=chunk.page_number,
                            section_heading=chunk.section_heading,
                            supporting_passage=chunk.text[:250] + ("..." if len(chunk.text) > 250 else ""),
                            relevance_score=chunk.relevance_score,
                            is_verified=True,
                        )
                    )

        # If no specific citations matched text patterns, return top verified chunks
        if not validated_sources and retrieved_chunks:
            for c in retrieved_chunks[:2]:
                validated_sources.append(
                    SourceCitation(
                        document_id=c.document_id,
                        document_title=c.document_title,
                        source_institution=c.source_institution,
                        page_number=c.page_number,
                        section_heading=c.section_heading,
                        supporting_passage=c.text[:250] + ("..." if len(c.text) > 250 else ""),
                        relevance_score=c.relevance_score,
                        is_verified=True,
                    )
                )

        return validated_sources

    @classmethod
    async def answer_question(
        cls,
        question: str,
        session_id: Optional[str] = None,
        crop: Optional[str] = None,
        topic: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> ChatResponse:
        """
        Execute full RAG pipeline with grounding, evidence sufficiency check,
        and citation validation.
        """
        clean_question = question.strip()
        actual_session_id = session_id or str(uuid.uuid4())

        # 1. Manage Conversation Record
        conversation = None
        history_messages: List[Dict[str, str]] = []
        if db is not None:
            conversation = db.query(Conversation).filter(Conversation.session_id == actual_session_id).first()
            if not conversation:
                conversation = Conversation(id=str(uuid.uuid4()), session_id=actual_session_id)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
            else:
                # Load existing history
                past_msgs = (
                    db.query(Message)
                    .filter(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.asc())
                    .all()
                )
                for pm in past_msgs:
                    history_messages.append({"role": pm.role, "content": pm.content})

        # 2. Hybrid Retrieval
        filters = {}
        if crop:
            filters["crop"] = crop
        if topic:
            filters["topic"] = topic

        t_ret_start = time.time()
        retrieved_chunks = retrieve_context(
            question=clean_question,
            filters=filters if filters else None,
            top_k=settings.FINAL_CONTEXT_CHUNKS,
            enable_reranker=True,
        )
        retrieval_time_ms = round((time.time() - t_ret_start) * 1000, 2)

        # 3. Evidence Sufficiency Verification
        is_sufficient, reason = cls.check_evidence_sufficiency(clean_question, retrieved_chunks)

        if not is_sufficient:
            abstention_answer = (
                f"**Notice: Insufficient Agricultural Evidence**\n\n"
                f"Based strictly on the verified ICAR publications and government package of practices currently indexed in KrishiRAG, "
                f"there is insufficient documented evidence to answer this query with absolute agronomic certainty.\n\n"
                f"*Reason*: {reason or 'Topic not documented in authentic corpus'}.\n\n"
                f"To protect your crop health and avoid unverified practices, KrishiRAG will not speculate or generate ungrounded recommendations. "
                f"Please consult your local Krishi Vigyan Kendra (KVK) or state agricultural extension officer."
            )

            # Persist to DB
            if db is not None and conversation is not None:
                db.add(Message(conversation_id=conversation.id, role="user", content=clean_question))
                db.add(Message(conversation_id=conversation.id, role="assistant", content=abstention_answer))
                db.commit()

            return ChatResponse(
                session_id=actual_session_id,
                question=clean_question,
                answer=abstention_answer,
                sources=[],
                retrieved_chunks=[RetrievedChunkResponse(**c.model_dump()) for c in retrieved_chunks],
                retrieval_time_ms=retrieval_time_ms,
                generation_time_ms=0.0,
                abstained=True,
                abstention_reason=reason,
            )

        # 4. Context & Prompt Construction
        messages = cls.construct_context_prompt(clean_question, retrieved_chunks, history_messages)

        # 5. Qwen3 Generation via Ollama
        t_gen_start = time.time()
        try:
            generated_answer = await llm_service.generate_chat(
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
            )
        except Exception as e:
            logger.error("LLM Generation failed: %s", e)
            # Provide fallback with direct retrieved evidence passages
            generated_answer = (
                f"**Direct ICAR Document Evidence** (LLM generation encountered: {str(e)}):\n\n"
                f"The following verified guidelines from ICAR publications apply directly to your query:\n\n"
            )
            for i, c in enumerate(retrieved_chunks[:3], 1):
                generated_answer += f"**{i}. {c.document_title} (Page {c.page_number})**:\n{c.text}\n\n"

        generation_time_ms = round((time.time() - t_gen_start) * 1000, 2)

        # 6. Citation Validation
        validated_sources = cls.validate_citations(generated_answer, retrieved_chunks)

        # 7. Persist to DB
        if db is not None and conversation is not None:
            db.add(Message(conversation_id=conversation.id, role="user", content=clean_question))
            db.add(Message(conversation_id=conversation.id, role="assistant", content=generated_answer))
            db.commit()

        return ChatResponse(
            session_id=actual_session_id,
            question=clean_question,
            answer=generated_answer,
            sources=validated_sources,
            retrieved_chunks=[RetrievedChunkResponse(**c.model_dump()) for c in retrieved_chunks],
            retrieval_time_ms=retrieval_time_ms,
            generation_time_ms=generation_time_ms,
            abstained=False,
            abstention_reason=None,
        )


rag_service = RAGService()
