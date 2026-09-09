# Upstream Warning Integration Contract

**Document:** `docs/upstream_contract.md`  
**Version:** 1.0.0  
**Status:** Approved Master Specification  

---

## 1. Upstream Data Contract

The upstream system provides warning status via:
1. The `Warning` and `Comments` columns in `index.xlsx`.
2. Optional structured JSON output where available.

### Canonical Upstream Warning Model
```json
{
  "upstream_id": "UP-00124",
  "document_id": "DOC-42332089_NGED",
  "claimed_warning_code": "NGED_11KV_LINE",
  "claimed_warning_text": "There is a 11kV High Voltage Electricity Line in this Area |",
  "upstream_confidence": 1.0,
  "has_warning": true,
  "model_version": "upstream-v2.4"
}
```

---

## 2. Reconciliation Matrix

| Upstream Status | Independent QA Status | Reconciliation Outcome | Policy Action |
| :--- | :--- | :--- | :--- |
| Warning Claimed | Warning Verified & Confirmed | `VALID_WARNING` | Route by Severity Policy |
| Warning Claimed | No Warning Found in Map | `POSSIBLE_FALSE_POSITIVE` | `HUMAN_REVIEW` |
| No Warning | Warning Discovered Independently | `MISSED_WARNING` | **MANDATORY HUMAN_REVIEW** |
| No Warning | No Warning Found | `CONFIRMED_CLEAN` | Eligible for `AUTO_CLEAR` (if all 17 gates pass) |
| Warning Claimed (Type A) | Warning Found (Type B) | `WARNING_TYPE_MISMATCH` | `HUMAN_REVIEW` |

---
