import re
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.schemas.document import ChunkMetadata
from backend.app.services.extractor import ExtractedPage
from backend.app.services.cleaner import AgronomicTextCleaner
from backend.app.services.tagger import AgronomicTagger

class HeadingAwareChunker:
    """
    Splits agricultural publications into semantically cohesive, heading-aware chunks.
    Preserves original page numbers, chemical dosages, and table structures.
    """

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Token estimator: approximately 1.33 tokens per whitespace-separated word for agronomic text.
        """
        words = len(text.split())
        return max(1, int(words * 1.33))

    @classmethod
    def chunk_document(
        cls,
        document_id: str,
        document_title: str,
        source_institution: str,
        source_url: Optional[str],
        pages: List[ExtractedPage],
        target_min_tokens: int = None,
        target_max_tokens: int = None,
        overlap_tokens: int = None
    ) -> List[ChunkMetadata]:
        min_tokens = target_min_tokens or settings.CHUNK_MIN_TOKENS
        max_tokens = target_max_tokens or settings.CHUNK_MAX_TOKENS
        overlap = overlap_tokens or settings.CHUNK_OVERLAP_TOKENS

        chunks: List[ChunkMetadata] = []
        chunk_counter = 0

        current_heading = None

        for page in pages:
            if page.section_heading:
                current_heading = page.section_heading

            cleaned_text = AgronomicTextCleaner.clean_text(page.text, document_title=document_title)
            if not cleaned_text:
                continue

            # Split by double newlines into discrete paragraphs / table blocks
            paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]
            
            current_chunk_paras: List[str] = []
            current_tokens = 0

            for para in paragraphs:
                para_tokens = cls.estimate_tokens(para)

                # If single paragraph exceeds max_tokens, split into sentences
                if para_tokens > max_tokens:
                    # Flush any accumulated paragraphs first
                    if current_chunk_paras:
                        chunk_text = "\n\n".join(current_chunk_paras)
                        chunk_meta = cls._create_chunk(
                            document_id=document_id,
                            document_title=document_title,
                            source_institution=source_institution,
                            source_url=source_url,
                            page_number=page.page_number,
                            section_heading=current_heading,
                            text=chunk_text,
                            chunk_index=chunk_counter
                        )
                        chunks.append(chunk_meta)
                        chunk_counter += 1
                        current_chunk_paras = []
                        current_tokens = 0

                    # Split large paragraph by sentence boundaries
                    sentence_chunks = cls._split_large_paragraph(para, max_tokens, overlap)
                    for s_text in sentence_chunks:
                        chunk_meta = cls._create_chunk(
                            document_id=document_id,
                            document_title=document_title,
                            source_institution=source_institution,
                            source_url=source_url,
                            page_number=page.page_number,
                            section_heading=current_heading,
                            text=s_text,
                            chunk_index=chunk_counter
                        )
                        chunks.append(chunk_meta)
                        chunk_counter += 1
                    continue

                # Normal paragraph accumulation
                if current_tokens + para_tokens > max_tokens:
                    # Flush current chunk
                    chunk_text = "\n\n".join(current_chunk_paras)
                    chunk_meta = cls._create_chunk(
                        document_id=document_id,
                        document_title=document_title,
                        source_institution=source_institution,
                        source_url=source_url,
                        page_number=page.page_number,
                        section_heading=current_heading,
                        text=chunk_text,
                        chunk_index=chunk_counter
                    )
                    chunks.append(chunk_meta)
                    chunk_counter += 1

                    # Handle overlap by retaining trailing paragraphs
                    overlap_paras: List[str] = []
                    overlap_token_sum = 0
                    for p_rev in reversed(current_chunk_paras):
                        p_t = cls.estimate_tokens(p_rev)
                        if overlap_token_sum + p_t <= overlap:
                            overlap_paras.insert(0, p_rev)
                            overlap_token_sum += p_t
                        else:
                            break

                    current_chunk_paras = overlap_paras + [para]
                    current_tokens = overlap_token_sum + para_tokens
                else:
                    current_chunk_paras.append(para)
                    current_tokens += para_tokens

            # Flush any remaining paragraphs on the page
            if current_chunk_paras:
                chunk_text = "\n\n".join(current_chunk_paras)
                chunk_meta = cls._create_chunk(
                    document_id=document_id,
                    document_title=document_title,
                    source_institution=source_institution,
                    source_url=source_url,
                    page_number=page.page_number,
                    section_heading=current_heading,
                    text=chunk_text,
                    chunk_index=chunk_counter
                )
                chunks.append(chunk_meta)
                chunk_counter += 1

        return chunks

    @classmethod
    def _split_large_paragraph(cls, paragraph: str, max_tokens: int, overlap_tokens: int) -> List[str]:
        # Split paragraph on sentence delimiters: periods, question marks, exclamation marks
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        sub_chunks: List[str] = []
        current: List[str] = []
        tokens = 0

        for sentence in sentences:
            s_tokens = cls.estimate_tokens(sentence)
            if tokens + s_tokens > max_tokens and current:
                sub_chunks.append(" ".join(current))
                # Keep last sentence as overlap if feasible
                last = current[-1]
                if cls.estimate_tokens(last) <= overlap_tokens:
                    current = [last, sentence]
                    tokens = cls.estimate_tokens(last) + s_tokens
                else:
                    current = [sentence]
                    tokens = s_tokens
            else:
                current.append(sentence)
                tokens += s_tokens

        if current:
            sub_chunks.append(" ".join(current))
        return sub_chunks

    @classmethod
    def _create_chunk(
        cls,
        document_id: str,
        document_title: str,
        source_institution: str,
        source_url: Optional[str],
        page_number: int,
        section_heading: Optional[str],
        text: str,
        chunk_index: int
    ) -> ChunkMetadata:
        chunk_id = f"doc_{document_id}_p{page_number}_c{chunk_index}"
        token_count = cls.estimate_tokens(text)
        crop_tags, topic_tags, language = AgronomicTagger.extract_tags(text)

        # Context inheritance: If chunk text doesn't explicitly name the crop/topic,
        # inherit from document title or section heading to ensure retrieval recall
        if not crop_tags:
            doc_crops, _, _ = AgronomicTagger.extract_tags(document_title)
            crop_tags = doc_crops

        if section_heading:
            _, sec_topics, _ = AgronomicTagger.extract_tags(section_heading)
            for st in sec_topics:
                if st not in topic_tags:
                    topic_tags.append(st)

        return ChunkMetadata(
            chunk_id=chunk_id,
            document_id=document_id,
            document_title=document_title,
            source_institution=source_institution,
            source_url=source_url,
            page_number=page_number,
            section_heading=section_heading,
            text=text,
            token_count=token_count,
            crop_tags=crop_tags,
            topic_tags=topic_tags,
            language=language
        )
