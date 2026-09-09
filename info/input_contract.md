# Input & Data Contract Specification

**Document:** `docs/input_contract.md`  
**Version:** 1.0.0  
**Status:** Approved Phase 0 Specification  

---

## 1. Root Folder Ingestion Contract

The system accepts a root folder directory path. The directory must contain:
1. One primary index spreadsheet (`index.xlsx` or `*.xlsx`).
2. Map PDF documents corresponding to index rows where `Status == 'Yes'`.
3. Supporting reference documents, safety booklets, or provider letters.

### File Discovered Inventory Model
```json
{
  "file_id": "FIL-9a3b8c2d",
  "relative_path": "42332089_NGED - Wales.pdf",
  "filename": "42332089_NGED - Wales.pdf",
  "extension": ".pdf",
  "mime_type": "application/pdf",
  "size_bytes": 260286,
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "classification": "MAP",
  "processing_status": "DISCOVERED"
}
```

---

## 2. Production Excel Contract (Read-Only)

### Invariants:
- The production Excel file is strictly immutable.
- No columns added, removed, renamed, or reordered.
- No cell values or formats overwritten.

### Canonical IndexRecord Model
```json
{
  "index_record_id": "IDX-00124",
  "job_id": "JOB-244414_201678",
  "row_index": 4,
  "file_name": "42332089_NGED - Wales.pdf",
  "utility_name": "National Grid Electricity Distribution",
  "utility_type": "Electricity",
  "raw_status": "Yes",
  "is_asset_present": true,
  "raw_warning": "There is a 11kV High Voltage Electricity Line in this Area |",
  "raw_comments": "100.0",
  "canonical_status": "PROCESSED"
}
```

---

## 3. Document Resolution Contract

Every `IndexRecord` with `raw_status == 'Yes'` must resolve to a unique file:
- `UNIQUE`: Exactly one candidate file matches deterministic rules.
- `AMBIGUOUS`: Multiple matching candidate files -> escalated to `HUMAN_REVIEW` or `BLOCKED`.
- `MISSING`: Claimed file does not exist in folder -> `BLOCKED`.
- `EXCLUDED`: `raw_status == 'No'` with no file attached -> `EXPLICITLY_EXCLUDED`.

---
