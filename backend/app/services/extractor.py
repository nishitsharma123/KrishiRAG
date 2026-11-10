import os
import re
from typing import List, Dict, Any, Optional
import pymupdf  # PyMuPDF
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import DocumentProcessingError

class ExtractedPage:
    def __init__(
        self,
        page_number: int,
        text: str,
        document_title: str,
        section_heading: Optional[str] = None,
        is_ocr: bool = False,
        ocr_error: Optional[str] = None
    ):
        self.page_number = page_number
        self.text = text
        self.document_title = document_title
        self.section_heading = section_heading
        self.is_ocr = is_ocr
        self.ocr_error = ocr_error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "document_title": self.document_title,
            "section_heading": self.section_heading,
            "is_ocr": self.is_ocr,
            "ocr_error": self.ocr_error
        }

class DocumentExtractor:
    """
    Extracts structured page-by-page text from agricultural publications.
    """

    @classmethod
    def extract_document(cls, file_path: str, document_title: str) -> List[ExtractedPage]:
        if not os.path.exists(file_path):
            raise DocumentProcessingError(f"File not found on disk: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls._extract_pdf(file_path, document_title)
        elif ext == ".txt":
            return cls._extract_txt(file_path, document_title)
        elif ext == ".docx":
            return cls._extract_docx(file_path, document_title)
        else:
            raise DocumentProcessingError(f"Unsupported file format '{ext}'. Supported: .pdf, .txt, .docx")

    @classmethod
    def _extract_pdf(cls, file_path: str, document_title: str) -> List[ExtractedPage]:
        extracted_pages: List[ExtractedPage] = []
        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            raise DocumentProcessingError(f"PyMuPDF failed to open PDF {file_path}: {str(e)}")

        current_heading = None

        for page_idx in range(len(doc)):
            page_num = page_idx + 1  # 1-indexed page
            page = doc[page_idx]

            # 1. Extract text and blocks to detect headings
            page_text = page.get_text("text").strip()
            
            # Detect section heading candidates from text blocks or font sizes
            heading_detected = cls._detect_heading_from_page(page)
            if heading_detected:
                current_heading = heading_detected

            # 2. Check for scanned / image-only page
            images = page.get_images(full=True)
            char_count = len(page_text)
            
            is_ocr_applied = False
            ocr_error_msg = None

            if char_count < settings.SCAN_TEXT_THRESHOLD and len(images) > 0:
                logger.info(f"Page {page_num} in '{document_title}' appears scanned ({char_count} chars, {len(images)} images). Attempting OCR fallback...")
                ocr_text, ocr_error_msg = cls._run_ocr_fallback(page, page_num)
                if ocr_text:
                    page_text = ocr_text
                    is_ocr_applied = True
                elif ocr_error_msg:
                    logger.warning(f"OCR fallback recorded issue on page {page_num}: {ocr_error_msg}")

            extracted_pages.append(
                ExtractedPage(
                    page_number=page_num,
                    text=page_text,
                    document_title=document_title,
                    section_heading=current_heading,
                    is_ocr=is_ocr_applied,
                    ocr_error=ocr_error_msg
                )
            )

        doc.close()
        return extracted_pages

    @classmethod
    def _detect_heading_from_page(cls, page) -> Optional[str]:
        """
        Scans text blocks for likely headings (short, capitalised, or isolated introductory lines).
        """
        try:
            blocks = page.get_text("blocks")
            for block in blocks:
                # block: (x0, y0, x1, y1, text, block_no, block_type)
                if len(block) >= 5 and block[6] == 0:  # Text block
                    text = block[4].strip()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if lines:
                        first_line = lines[0]
                        # Heuristic for section heading: length between 4 and 80 chars, not ending in period
                        if 4 <= len(first_line) <= 80 and not first_line.endswith("."):
                            if (
                                first_line.isupper() or 
                                re.match(r"^(?:Section|Chapter|\d+\.|\b[IVXLCDM]+\b|Package of Practices|Management of)\s+", first_line, re.IGNORECASE)
                            ):
                                return first_line
        except Exception:
            pass
        return None

    @classmethod
    def _run_ocr_fallback(cls, page, page_num: int) -> tuple[Optional[str], Optional[str]]:
        """
        Optional PaddleOCR fallback for scanned pages.
        Records errors explicitly if PaddleOCR is missing or fails.
        """
        try:
            # Check if PaddleOCR is installed
            from paddleocr import PaddleOCR
            import numpy as np
            from PIL import Image
            import io

            # Render page to pixmap image
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            img_np = np.array(img)

            ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            result = ocr.ocr(img_np, cls=True)

            text_lines = []
            if result and len(result) > 0:
                for line in result[0]:
                    text_lines.append(line[1][0])

            ocr_extracted = "\n".join(text_lines).strip()
            return (ocr_extracted if ocr_extracted else None, None)

        except ImportError:
            return (None, "PaddleOCR is not installed in the environment. Page left with native extractable text.")
        except Exception as e:
            return (None, f"PaddleOCR processing error on page {page_num}: {str(e)}")

    @classmethod
    def _extract_txt(cls, file_path: str, document_title: str) -> List[ExtractedPage]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read text file: {e}")

        # Check for explicit form feed page dividers (\f)
        raw_pages = content.split("\x0c") if "\x0c" in content else [content]
        pages: List[ExtractedPage] = []
        for idx, page_text in enumerate(raw_pages):
            pages.append(
                ExtractedPage(
                    page_number=idx + 1,
                    text=page_text.strip(),
                    document_title=document_title,
                    section_heading=None
                )
            )
        return pages

    @classmethod
    def _extract_docx(cls, file_path: str, document_title: str) -> List[ExtractedPage]:
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs: List[str] = []
            current_heading = None

            for p in doc.paragraphs:
                p_text = p.text.strip()
                if not p_text:
                    continue
                if p.style and ("Heading" in p.style.name or "Title" in p.style.name):
                    current_heading = p_text
                paragraphs.append(p_text)

            # Also extract tables
            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_lines.append(" | ".join(row_cells))
                if table_lines:
                    paragraphs.append("\n".join(table_lines))

            full_text = "\n\n".join(paragraphs)
            return [
                ExtractedPage(
                    page_number=1,
                    text=full_text,
                    document_title=document_title,
                    section_heading=current_heading
                )
            ]
        except Exception as e:
            raise DocumentProcessingError(f"Failed to extract DOCX file: {e}")
