import os
import json
import hashlib
import uuid
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import DocumentProcessingError
from backend.app.models.document import Document
from backend.app.schemas.document import DocumentIngestionResult
from backend.app.services.extractor import DocumentExtractor
from backend.app.services.chunker import HeadingAwareChunker

class DocumentIngestionService:
    """
    Coordinates end-to-end ingestion:
    File Validation -> Duplicate Check -> Extraction -> OCR Fallback -> Cleaning -> Chunking -> Storage.
    """

    @classmethod
    def calculate_sha256(cls, file_bytes: bytes) -> str:
        sha256 = hashlib.sha256()
        sha256.update(file_bytes)
        return sha256.hexdigest()

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        # Keep alphanumeric, underscores, hyphens, and single dots
        clean = re.sub(r"[^\w\.-]", "_", filename)
        return clean.strip("._") or "document.pdf"

    @classmethod
    def ingest_file(
        cls,
        file_bytes: bytes,
        original_filename: str,
        title: Optional[str],
        source_institution: str,
        source_url: Optional[str],
        publication_date: Optional[str],
        db: Session
    ) -> DocumentIngestionResult:
        # 1. Validate File Size
        file_size = len(file_bytes)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise DocumentProcessingError(
                f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB (received {file_size / (1024*1024):.2f}MB)"
            )

        # 2. Validate Extension
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise DocumentProcessingError(
                f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 3. Duplicate Detection via SHA-256
        file_hash = cls.calculate_sha256(file_bytes)
        existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()

        if existing_doc and existing_doc.status == "COMPLETED":
            logger.info(f"Duplicate document detected (Hash: {file_hash}). Returning existing document record: {existing_doc.id}")
            return DocumentIngestionResult(
                document_id=existing_doc.id,
                title=existing_doc.title,
                filename=existing_doc.filename,
                page_count=existing_doc.page_count,
                chunk_count=existing_doc.chunk_count,
                status=existing_doc.status,
                is_duplicate=True,
                ocr_pages=[],
                ocr_errors=[],
                message="Duplicate document detected via SHA-256. Document already processed and indexed."
            )

        # Derive title if not explicitly provided
        doc_title = title.strip() if title and title.strip() else os.path.splitext(original_filename)[0].replace("_", " ").title()

        # 4. Secure File Storage
        doc_id = str(uuid.uuid4())
        safe_name = cls.sanitize_filename(original_filename)
        saved_filename = f"{doc_id}_{safe_name}"
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        saved_file_path = os.path.join(settings.STORAGE_PATH, saved_filename)

        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        # 5. Register in Database with Status 'PROCESSING'
        doc_record = existing_doc if existing_doc else Document(id=doc_id)
        doc_record.id = doc_id
        doc_record.title = doc_title
        doc_record.filename = original_filename
        doc_record.file_hash = file_hash
        doc_record.file_size = file_size
        doc_record.mime_type = "application/pdf" if ext == ".pdf" else "text/plain" if ext == ".txt" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        doc_record.source_institution = source_institution or "ICAR"
        doc_record.source_url = source_url
        doc_record.publication_date = publication_date
        doc_record.file_path = saved_file_path
        doc_record.status = "PROCESSING"
        doc_record.error_message = None

        if not existing_doc:
            db.add(doc_record)
        db.commit()

        # 6. Execute Pipeline
        ocr_pages_list: List[int] = []
        ocr_errors_list: List[Dict[str, Any]] = []

        try:
            logger.info(f"Starting extraction for document '{doc_title}' ({saved_file_path})...")
            extracted_pages = DocumentExtractor.extract_document(saved_file_path, doc_title)
            page_count = len(extracted_pages)

            # Record any OCR occurrences or errors
            for page in extracted_pages:
                if page.is_ocr:
                    ocr_pages_list.append(page.page_number)
                if page.ocr_error:
                    ocr_errors_list.append({
                        "page_number": page.page_number,
                        "error": page.ocr_error
                    })

            # 7. Intelligent Chunking
            logger.info(f"Chunking {page_count} pages for document '{doc_title}'...")
            chunks = HeadingAwareChunker.chunk_document(
                document_id=doc_id,
                document_title=doc_title,
                source_institution=doc_record.source_institution,
                source_url=source_url,
                pages=extracted_pages
            )
            chunk_count = len(chunks)

            # 8. Persist Processed Chunks to JSON
            os.makedirs(settings.PROCESSED_DATA_PATH, exist_ok=True)
            processed_json_path = os.path.join(settings.PROCESSED_DATA_PATH, f"{doc_id}.json")

            chunks_data = [c.model_dump() for c in chunks]
            with open(processed_json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "document_id": doc_id,
                        "title": doc_title,
                        "filename": original_filename,
                        "file_hash": file_hash,
                        "source_institution": doc_record.source_institution,
                        "source_url": source_url,
                        "page_count": page_count,
                        "chunk_count": chunk_count,
                        "chunks": chunks_data
                    },
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            # 9. Update Database Record as 'COMPLETED'
            doc_record.page_count = page_count
            doc_record.chunk_count = chunk_count
            doc_record.status = "COMPLETED"
            db.commit()
            logger.info(f"Successfully processed document '{doc_title}' ({page_count} pages, {chunk_count} chunks).")

            return DocumentIngestionResult(
                document_id=doc_id,
                title=doc_title,
                filename=original_filename,
                page_count=page_count,
                chunk_count=chunk_count,
                status="COMPLETED",
                is_duplicate=False,
                ocr_pages=ocr_pages_list,
                ocr_errors=ocr_errors_list,
                message=f"Document successfully ingested into {chunk_count} verified agricultural chunks across {page_count} pages."
            )

        except Exception as exc:
            db.rollback()
            doc_record.status = "FAILED"
            doc_record.error_message = str(exc)
            db.commit()
            logger.exception(f"Document ingestion failed for '{doc_title}': {exc}")
            raise DocumentProcessingError(f"Failed to ingest document '{doc_title}': {str(exc)}")
