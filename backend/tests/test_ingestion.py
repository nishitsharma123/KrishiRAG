import os
import pytest
from backend.app.database.session import init_db, SessionLocal
from backend.app.models.document import Document
from backend.app.services.extractor import DocumentExtractor
from backend.app.services.cleaner import AgronomicTextCleaner
from backend.app.services.tagger import AgronomicTagger
from backend.app.services.chunker import HeadingAwareChunker
from backend.app.services.ingestion import DocumentIngestionService
from backend.app.utils.chunk_inspector import ChunkInspector

@pytest.fixture(scope="module")
def setup_database():
    init_db()
    # Safe fixture: Do not delete existing user documents from krishirag.db
    yield

def test_agronomic_text_cleaner():
    raw_text = (
        "ICAR Wheat Manual 2024\n"
        "Page 14\n"
        "Wheat (Triticum aestivum) crop requires timely insec-\n"
        "ticide application. Spray 2,4-D Ethyl Ester @ 1250 ml/ha.\n"
        "Yellow Rust (Puccinia striiformis) should be managed with Propiconazole 25% EC @ 0.1% (500 ml/ha).\n"
        "------------------------------------\n"
    )
    cleaned = AgronomicTextCleaner.clean_text(raw_text, document_title="ICAR Wheat Manual 2024")
    
    # 1. Verify de-hyphenation rejoining
    assert "insecticide" in cleaned
    # 2. Verify chemical names with hyphens are preserved
    assert "2,4-D" in cleaned
    # 3. Verify exact dosage and scientific names are preserved
    assert "Propiconazole 25% EC @ 0.1%" in cleaned
    assert "Puccinia striiformis" in cleaned
    # 4. Verify running header and dashes removed
    assert "ICAR Wheat Manual 2024" not in cleaned
    assert "------------------------------------" not in cleaned

def test_agronomic_tagger():
    wheat_text = "Yellow Rust (Puccinia striiformis) in wheat crop managed by Propiconazole @ 500 ml/ha at CRI stage."
    crops, topics, lang = AgronomicTagger.extract_tags(wheat_text)
    
    assert "Wheat" in crops
    assert "Disease Management" in topics
    assert lang == "en"

    mustard_text = "Mustard aphid Lipaphis erysimi controlled by Dimethoate 30 EC @ 1 ml/l after 3:30 PM."
    crops, topics, lang = AgronomicTagger.extract_tags(mustard_text)
    assert "Mustard / Rapeseed" in crops
    assert "Pest Management" in topics

def test_pdf_extraction_page_fidelity():
    pdf_path = "./data/raw/icar_wheat_package_of_practices_2024.pdf"
    assert os.path.exists(pdf_path)
    
    pages = DocumentExtractor.extract_document(pdf_path, "ICAR Package of Practices for Wheat 2024")
    assert len(pages) == 4
    
    # Verify exact 1-indexed page numbering
    for idx, page in enumerate(pages, 1):
        assert page.page_number == idx
        assert len(page.text) > 100
        assert page.document_title == "ICAR Package of Practices for Wheat 2024"

    # Verify content extraction fidelity
    assert "HD 2967" in pages[1].text  # Page 2
    assert "150:60:40 kg/ha" in pages[2].text  # Page 3
    assert "Propiconazole 25% EC" in pages[3].text  # Page 4

def test_scanned_page_detection_and_ocr_fallback():
    pdf_path = "./data/raw/icar_scanned_specimen_page.pdf"
    assert os.path.exists(pdf_path)

    pages = DocumentExtractor.extract_document(pdf_path, "ICAR Scanned Specimen")
    assert len(pages) == 1
    # Check that scanned page detection was triggered and OCR status/error recorded
    assert pages[0].ocr_error is not None or pages[0].is_ocr is True

def test_heading_aware_chunking():
    pdf_path = "./data/raw/icar_wheat_package_of_practices_2024.pdf"
    pages = DocumentExtractor.extract_document(pdf_path, "ICAR Package of Practices for Wheat 2024")
    
    chunks = HeadingAwareChunker.chunk_document(
        document_id="test_wheat_doc",
        document_title="ICAR Package of Practices for Wheat 2024",
        source_institution="ICAR",
        source_url="https://iiwbr.icar.gov.in",
        pages=pages
    )
    
    assert len(chunks) >= 4
    for chunk in chunks:
        assert chunk.document_id == "test_wheat_doc"
        assert chunk.page_number in [1, 2, 3, 4]
        assert chunk.token_count > 0
        assert chunk.chunk_id.startswith("doc_test_wheat_doc_p")
        assert "Wheat" in chunk.crop_tags

def test_end_to_end_ingestion_and_duplicate_detection(setup_database):
    db = SessionLocal()
    try:
        # Ingest PDF 1: Wheat
        wheat_path = "./data/raw/icar_wheat_package_of_practices_2024.pdf"
        with open(wheat_path, "rb") as f:
            wheat_bytes = f.read()

        result1 = DocumentIngestionService.ingest_file(
            file_bytes=wheat_bytes,
            original_filename="icar_wheat_package_of_practices_2024.pdf",
            title="ICAR Package of Practices for Wheat 2024",
            source_institution="ICAR-IIWBR",
            source_url="https://iiwbr.icar.gov.in",
            publication_date="2024",
            db=db
        )
        assert result1.status == "COMPLETED"
        assert result1.page_count == 4
        assert result1.chunk_count >= 4
        assert result1.is_duplicate is False

        # Ingest PDF 2: Paddy
        paddy_path = "./data/raw/icar_paddy_direct_seeded_rice_manual.pdf"
        with open(paddy_path, "rb") as f:
            paddy_bytes = f.read()

        result2 = DocumentIngestionService.ingest_file(
            file_bytes=paddy_bytes,
            original_filename="icar_paddy_direct_seeded_rice_manual.pdf",
            title="ICAR-NRRI Guidelines for Direct Seeded Rice (DSR)",
            source_institution="ICAR-NRRI",
            source_url="https://nrri.icar.gov.in",
            publication_date="2024",
            db=db
        )
        assert result2.status == "COMPLETED"
        assert result2.page_count == 3
        assert result2.chunk_count >= 3

        # Ingest PDF 3: Mustard
        mustard_path = "./data/raw/icar_mustard_integrated_pest_management.pdf"
        with open(mustard_path, "rb") as f:
            mustard_bytes = f.read()

        result3 = DocumentIngestionService.ingest_file(
            file_bytes=mustard_bytes,
            original_filename="icar_mustard_integrated_pest_management.pdf",
            title="ICAR-DRMR IPM in Rapeseed-Mustard",
            source_institution="ICAR-DRMR",
            source_url="https://drmr.icar.gov.in",
            publication_date="2024",
            db=db
        )
        assert result3.status == "COMPLETED"
        assert result3.page_count == 3
        assert result3.chunk_count >= 3

        # Test DUPLICATE DETECTION with identical Wheat PDF bytes
        result_dup = DocumentIngestionService.ingest_file(
            file_bytes=wheat_bytes,
            original_filename="icar_wheat_package_of_practices_2024.pdf",
            title="ICAR Package of Practices for Wheat 2024",
            source_institution="ICAR-IIWBR",
            source_url="https://iiwbr.icar.gov.in",
            publication_date="2024",
            db=db
        )
        assert result_dup.is_duplicate is True
        assert result_dup.document_id == result1.document_id
        assert result_dup.chunk_count == result1.chunk_count

        # Verify Chunk Inspector on ingested wheat doc
        inspection = ChunkInspector.inspect(result1.document_id)
        assert inspection["total_pages"] == 4
        assert inspection["token_stats"]["avg_tokens"] > 50

    finally:
        db.close()
