# Architecture Assumptions & Engineering Decisions (ADR)

**Document:** `docs/assumptions_and_decisions.md`  
**Version:** 1.0.0  
**Date:** 2026-09-01  

---

## ADR-001: Separation of Critical Validation Core from Optional LLM
- **Decision:** The safety-critical validation pipeline (PDF vector analysis, CV, OCR, spatial predicates, policy gates) is implemented entirely in deterministic Python code without LLM dependency.
- **Rationale:** LLMs are non-deterministic, can hallucinate, and cannot be safety authorities for critical infrastructure clearance. The LLM QA Agent is strictly bounded to structured evidence summarization and reviewer assistance.

## ADR-002: Immutability of Production Excel Workbooks
- **Decision:** Production Excel workbooks (`index.xlsx`) are treated as strictly read-only. No columns are added or modified. Derived results are exported to separate reports (`job_report.json`, derived Excel exports).
- **Rationale:** Production compliance and audit integrity prevent modifying client input artifacts.

## ADR-003: Native PDF Vector Extraction Priority
- **Decision:** Native vector paths, strokes, fills, and text extracted via PyMuPDF are processed first. Rasterization is only performed on demand when vector data is absent or for visual crop generation.
- **Rationale:** Native vectors provide mathematical precision (sub-point accuracy) without raster distortion or heavy GPU overhead.

## ADR-004: 17-Gate Deterministic Release Policy
- **Decision:** `AUTO_CLEAR` requires 100% of the 17 mandatory policy gates to PASS. No confidence score threshold can override a failed gate.
- **Rationale:** The primary KPI is minimizing the auto-clear escape rate (zero escaped critical warnings).

## ADR-005: Fail-Closed Uncertainty Abstention
- **Decision:** Whenever a file, legend, AOI, or coordinate transform is ambiguous or missing, the system abstains from auto-clearing and routes to `HUMAN_REVIEW` or `BLOCKED`.
- **Rationale:** Prevents infrastructure damage from ambiguous utility interpretations.

## ADR-006: Warning Catalogue Column Mapping
- **Decision:** The 4th column of `warnings_list 2 1 (1).xlsx`, labeled `Status`, is formally mapped to canonical `Severity` (`High`, `Medium`, `Low`).
- **Rationale:** Real-data profiling proved that this column contains severity strings rather than processing status.

---
