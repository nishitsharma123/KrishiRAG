# KrishiRAG: Agricultural Document Ingestion Report (Phase 2)

**Execution Date**: 2026-11-10  
**Target Architecture**: PyMuPDF + Selective PaddleOCR Fallback + Heading-Aware Chunking + SQLite / JSON Persistence  
**Hardware Profile**: AMD Ryzen 5 5500U, 8 GB RAM (CPU-only, in-process processing)

---

## 1. Ingestion Pipeline Architecture

```
Uploaded Document (.pdf, .txt, .docx)
   │
   ▼
[SHA-256 Hash Computation] ────────► (Match Found?) ──YES──► Return Existing Record (Deduplication)
   │ (NO)
   ▼
[Secure Disk Storage] (./storage/{uuid}_{sanitized_name})
   │
   ▼
[Database Registration] (Status: PROCESSING in SQLite)
   │
   ▼
[PyMuPDF Page-by-Page Extractor]
   │
   ├──► Scanned Page Detected? (<50 chars + images)
   │       └──► YES: Trigger PaddleOCR Fallback (Record page-level errors if uninstalled)
   │       └──► NO:  Native Text Layer Extracted with Page Index (1-indexed)
   ▼
[Agronomic Text Cleaner]
   ├── Unicode NFKC Normalization
   ├── De-hyphenation rejoining (e.g. "insec-ticide" -> "insecticide")
   ├── Running header & footer removal
   └── Strict preservation of chemicals (2,4-D, Propiconazole), dosages (@ 1.5 ml/l), & scientific names
   ▼
[Heading-Aware Chunker]
   ├── Target Window: 500–700 tokens (80-token overlap)
   ├── Preserves paragraph and sentence integrity
   ├── Keeps dosage recommendations tethered to agronomic conditions
   └── Generates unique deterministic chunk ID: doc_{id}_p{page}_c{index}
   ▼
[Agricultural Knowledge Tagger]
   ├── Crop Extraction (Wheat, Rice/Paddy, Mustard, Chickpea, Cotton, etc.)
   ├── Topic Extraction (Pest Management, Diseases, Nutrients, Weeds, Seed Rate, Irrigation)
   └── Language Detection (English, Hindi)
   ▼
[Dual Persistence]
   ├── Relational: SQLite (Document metadata, chunk count, file hash, status: COMPLETED)
   └── Processed Storage: ./data/processed/{doc_id}.json
```

---

## 2. Ingested Agricultural Publications Summary

| Document Title | Source Institution | File Name | Pages | Chunks | Avg. Tokens | SHA-256 Hash | Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **ICAR Package of Practices for Wheat Cultivation (NWPZ)** | ICAR-IIWBR | `icar_wheat_package_of_practices_2024.pdf` | 4 | 4 | 215.0 | `2b443d5f...301d` | **COMPLETED** |
| **ICAR-NRRI Guidelines for Direct Seeded Rice (DSR)** | ICAR-NRRI | `icar_paddy_direct_seeded_rice_manual.pdf` | 3 | 3 | 198.3 | `8918cd23...82c2` | **COMPLETED** |
| **ICAR-DRMR IPM in Rapeseed-Mustard** | ICAR-DRMR | `icar_mustard_integrated_pest_management.pdf` | 3 | 3 | 204.7 | `cc107700...7710` | **COMPLETED** |
| **ICAR Scanned Specimen Plate (OCR Test)** | ICAR Test | `icar_scanned_specimen_page.pdf` | 1 | 1 | 42.0 | `20d54a24...9b6e` | **COMPLETED** |

---

## 3. Verification & Quality Assessment

### 3.1 Page Number & Provenance Fidelity
- Every extracted chunk contains explicit `page_number` metadata matching the physical PDF page (1-indexed).
- **Test Evidence**:
  - Wheat Page 1: Agro-climatic zones & zero-till land preparation $\rightarrow$ `page_number: 1`
  - Wheat Page 2: Varietal recommendations (HD 2967, DBW 187, DBW 303) and seed rate (100 kg/ha) $\rightarrow$ `page_number: 2`
  - Wheat Page 3: Balanced NPK fertilizer dosage (150:60:40 kg/ha) and CRI irrigation timing $\rightarrow$ `page_number: 3`
  - Wheat Page 4: Yellow Rust (*Puccinia striiformis*) management with Propiconazole 25% EC @ 0.1% $\rightarrow$ `page_number: 4`

### 3.2 Duplicate Detection (SHA-256)
- Submitting an identical document verifies duplicate detection without re-indexing.
- Result: Returns `is_duplicate = True` and links to the existing database record and processed JSON storage in `< 5 ms`.

### 3.3 Text Cleaning & Information Preservation
- **De-hyphenation**: Words split across line breaks (e.g., `insec-\nticide`) were cleanly rejoined as `insecticide`.
- **Chemical Name Preservation**: Hyphenated chemical names (`2,4-D`, `alpha-cypermethrin`) and complex formulations (`Propiconazole 25% EC`, `Pendimethalin 30% EC`, `Thiamethoxam 25% WG`) remained unaltered.
- **Dosage Preservation**: Rates (`@ 1.0 ml/litre`, `150:60:40 kg/ha`, `20-25 kg/ha`) and operational constraints (*"strictly conducts sprays in late afternoon after 3:30 PM to protect honeybee pollinators"*) were preserved intact.

### 3.4 Scanned Document Detection & OCR Fallback
- Tested on `icar_scanned_specimen_page.pdf` (character count $< 50$ with embedded raster chart).
- Detection logic successfully identified scanned characteristics.
- When PaddleOCR is uninstalled, the pipeline records the issue without crashing (`"PaddleOCR is not installed in the environment. Page left with native extractable text."`), meeting the requirement that OCR must never fail silently.

### 3.5 Chunk Inspector CLI Utility
- The inspection utility was verified via command line:
  ```powershell
  python -m backend.app.utils.chunk_inspector --latest
  ```
- Sample output demonstrates token statistics, heading tracking, and automated tagging:
  - Heading: *Section 2: Sowing Technique & Herbicide Weed Protocol*
  - Crop Tags: `["Rice / Paddy"]`
  - Topic Tags: `["Weed Management", "Seed Rate & Sowing", "Fertilizer & Nutrition"]`
  - Page: `2`
