# Requirements Traceability Matrix (RTM)

**Project:** AI Map QA & Validation Agent  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** Approved Initial Baseline  

---

## 1. Overview & Legend

This matrix links every core business, functional, non-functional, safety, and operational requirement to its architectural component, codebase implementation module, test suite verification, and current implementation status.

**Status Codes:**
- `NOT_STARTED`: Requirement specified, design complete, implementation pending.
- `IN_PROGRESS`: Implementation actively under development.
- `IMPLEMENTED`: Code complete; awaiting integration/gold-set validation.
- `VALIDATED`: Verified by automated tests and locked dataset validation.
- `BLOCKED`: Blocked by missing business confirmation or external dependency.

---

## 2. Traceability Matrix Table

| Req ID | Requirement Summary | Source Document | Architecture Component | Implementation Target | Test Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-ING-001** | Root folder recursive discovery & inventory | Requirements §6.1, Plan §7 | `FileInventoryService` | `src/ingestion/inventory.py` | `tests/unit/test_inventory.py` | NOT_STARTED |
| **REQ-ING-002** | SHA-256 cryptographic hashing of all discovered files | Requirements §6.3, Arch §8 | `FileInventoryService` | `src/ingestion/hasher.py` | `tests/unit/test_inventory.py` | NOT_STARTED |
| **REQ-ING-003** | Deterministic file classification (INDEX, MAP, LEGEND, UPSTREAM, REFERENCE, OTHER, UNKNOWN) | Requirements §8, Arch §8 | `FileClassifier` | `src/ingestion/classifier.py` | `tests/unit/test_classifier.py` | NOT_STARTED |
| **REQ-ING-004** | Manifest generation & audit recording of all discovered files | Requirements §6.3, Plan §7 | `JobManager` | `src/ingestion/manifest.py` | `tests/unit/test_inventory.py` | NOT_STARTED |
| **REQ-IDX-001** | Production Excel immutability (strict read-only, no modifications, no column alterations) | Requirements §7.1, Arch §9 | `IndexProcessor` | `src/index/parser.py` | `tests/unit/test_index_parser.py` | NOT_STARTED |
| **REQ-IDX-002** | Internal canonical `IndexRecord` normalization | Requirements §7.2, Arch §9 | `IndexProcessor` | `src/domain/index_record.py` | `tests/unit/test_index_parser.py` | NOT_STARTED |
| **REQ-IDX-003** | Accounting for every index row (no silent skipping: PROCESSED, BLOCKED, EXPLICITLY_EXCLUDED) | Requirements §7.3, Plan §8 | `IndexProcessor` / `JobManager` | `src/index/reconciler.py` | `tests/unit/test_index_reconciler.py` | NOT_STARTED |
| **REQ-IDX-004** | Index validation (missing files, duplicate records, invalid providers/types, empty required values) | Requirements §7.4, Plan §8 | `IndexValidator` | `src/index/validator.py` | `tests/unit/test_index_validator.py` | NOT_STARTED |
| **REQ-DOC-001** | Deterministic document mapping from IndexRecord to candidate map file | Requirements §9, Arch §10 | `DocumentResolver` | `src/documents/resolver.py` | `tests/unit/test_document_resolver.py` | NOT_STARTED |
| **REQ-DOC-002** | Fail-closed handling for ambiguous mappings (AMBIGUOUS_MAPPING -> HUMAN_REVIEW / BLOCKED) | Requirements §9.1, Plan §9 | `DocumentResolver` | `src/documents/resolver.py` | `tests/unit/test_document_resolver.py` | NOT_STARTED |
| **REQ-DOC-003** | Missing document handling (MISSING_MAP -> BLOCKED with audit log) | Requirements §9.2, Plan §9 | `DocumentResolver` | `src/documents/resolver.py` | `tests/unit/test_document_resolver.py` | NOT_STARTED |
| **REQ-PDF-001** | Local PyMuPDF PDF inspection & integrity verification (corrupt, encrypted, dimensions, page count) | Requirements §10.1, Plan §10 | `PDFInspector` | `src/pdf/inspector.py` | `tests/unit/test_pdf_inspector.py` | NOT_STARTED |
| **REQ-PDF-002** | PDF modality classification (VECTOR, RASTER, HYBRID, UNKNOWN) | Requirements §10.2, Arch §11 | `PDFInspector` | `src/pdf/classifier.py` | `tests/unit/test_pdf_classifier.py` | NOT_STARTED |
| **REQ-PDF-003** | Native PDF extraction priority (text, words, vector paths, strokes, fills, widths, dash patterns, metadata) | Requirements §10.3, Arch §18 | `VectorExtractor` | `src/vector/extractor.py` | `tests/unit/test_vector_extractor.py` | NOT_STARTED |
| **REQ-PDF-004** | High-resolution rasterization fallback only when required for CV/OCR/evidence | Requirements §10.4, Plan §10 | `PDFRenderer` | `src/pdf/renderer.py` | `tests/unit/test_pdf_renderer.py` | NOT_STARTED |
| **REQ-PRV-001** | Modular provider plugin architecture & registry (dependency injection, no giant if/elif) | Requirements §44, Arch §50 | `ProviderRegistry` | `src/providers/registry.py` | `tests/unit/test_provider_registry.py` | NOT_STARTED |
| **REQ-PRV-002** | Evidence-backed provider identification from title block, text, index, metadata | Requirements §12, Arch §12 | `ProviderResolver` | `src/providers/resolver.py` | `tests/unit/test_provider_resolver.py` | NOT_STARTED |
| **REQ-PRV-003** | Initial pilot provider implementations (SGN, UKPN, Clean Water) followed by expansion set | Requirements §46, Plan §41 | Provider Plugins | `src/providers/sgn/`, `ukpn/`, `water/` | `tests/integration/test_providers.py` | NOT_STARTED |
| **REQ-WRN-001** | Versioned master Warning Catalogue as business truth | Requirements §11, Arch §13 | `WarningCatalogueService` | `src/warnings/catalogue.py` | `tests/unit/test_warning_catalogue.py` | NOT_STARTED |
| **REQ-WRN-002** | Preservation of original business warning text, canonical code, severity, geometry type, AOI req | Requirements §11.1-11.2 | `WarningCatalogueService` | `src/domain/warning.py` | `tests/unit/test_warning_catalogue.py` | NOT_STARTED |
| **REQ-WRN-003** | Strict prohibition on inventing warning definitions or severity in code/AI | Requirements §11.3, Rule 4, 5 | `WarningCatalogueService` | `src/warnings/validator.py` | `tests/unit/test_warning_catalogue.py` | NOT_STARTED |
| **REQ-LGD-001** | Versioned Legend Registry & profile schema (colors, stroke widths, dash patterns, symbols, labels) | Requirements §12.2, Arch §14 | `LegendRegistry` | `src/legends/registry.py` | `tests/unit/test_legend_registry.py` | NOT_STARTED |
| **REQ-LGD-002** | Multi-source legend resolution hierarchy (embedded -> approved external -> symbol guide) | Requirements §12.1, Arch §15 | `LegendResolver` | `src/legends/resolver.py` | `tests/unit/test_legend_resolver.py` | NOT_STARTED |
| **REQ-LGD-003** | Missing legend safety gate (LEGEND_UNAVAILABLE -> NO AUTO_CLEAR, fail closed) | Requirements §12.3, Rule 3 | `LegendResolver` / `PolicyEngine` | `src/legends/resolver.py` | `tests/unit/test_legend_resolver.py` | NOT_STARTED |
| **REQ-AOI-001** | AOI as first-class domain object (circle, polygon, buffered line, vector boundary) | Requirements §13.1, Arch §16 | `AOIService` | `src/aoi/service.py` | `tests/unit/test_aoi_service.py` | NOT_STARTED |
| **REQ-AOI-002** | AOI detection priority (native vector -> explicit geometry -> approved external -> CV) | Requirements §13.2, Plan §12 | `AOIDetector` | `src/aoi/detector.py` | `tests/unit/test_aoi_detector.py` | NOT_STARTED |
| **REQ-AOI-003** | Missing/ambiguous mandatory AOI gate (AOI_MISSING / AOI_AMBIGUOUS -> NO AUTO_CLEAR) | Requirements §13.5, Rule 10 | `AOIService` / `PolicyEngine` | `src/aoi/service.py` | `tests/unit/test_aoi_service.py` | NOT_STARTED |
| **REQ-SPT-001** | Spatial validation engine using Shapely/PostGIS (INTERSECTS, WITHIN, CONTAINS, DISTANCE, etc.) | Requirements §17, Arch §22 | `SpatialEngine` | `src/spatial/engine.py` | `tests/unit/test_spatial_engine.py` | NOT_STARTED |
| **REQ-SPT-002** | Coordinate transformation & provenance preservation (PDF coords <-> pixel coords <-> map coords) | Requirements §18, Arch §22 | `CoordinateTransformer` | `src/spatial/coordinates.py` | `tests/unit/test_coordinates.py` | NOT_STARTED |
| **REQ-SPT-003** | Scale-aware, provider-specific boundary tolerance (no universal arbitrary tolerance) | Requirements §13.4, Plan §12 | `SpatialEngine` | `src/spatial/engine.py` | `tests/unit/test_spatial_engine.py` | NOT_STARTED |
| **REQ-DET-001** | Layered independent warning discovery (Vector -> Classical CV -> OCR -> ML) | Requirements §15, §16 | `IndependentQAEngine` | `src/cv/`, `vector/`, `ocr/` | `tests/integration/test_detection.py` | NOT_STARTED |
| **REQ-DET-002** | Mandatory independent search execution regardless of upstream status ("no upstream warning" != clean) | Requirements §14.2, Rule 2 | `IndependentQAEngine` | `src/orchestration/pipeline.py` | `tests/integration/test_pipeline.py` | NOT_STARTED |
| **REQ-DET-003** | Classical CV operations (RGB/HSV/LAB, tolerance thresholding, contours, morphology, dash analysis) | Requirements §16.2, Arch §19 | `CVService` | `src/cv/pipeline.py` | `tests/unit/test_cv_pipeline.py` | NOT_STARTED |
| **REQ-DET-004** | OCR engine integration (map labels, legends, annotations, bboxes, confidence) | Requirements §16.3, Arch §20 | `OCRService` | `src/ocr/service.py` | `tests/unit/test_ocr_service.py` | NOT_STARTED |
| **REQ-DET-005** | Candidate detection persistence (candidate_id, doc_id, page, warning_code, geometry, bbox, confidence, evidence_ids) | Requirements §27, Arch §17 | `DetectionService` | `src/domain/detection.py` | `tests/unit/test_detection_service.py` | NOT_STARTED |
| **REQ-REC-001** | Upstream vs independent reconciliation (MATCH, MISSED_WARNING, POSSIBLE_FALSE_POSITIVE, TYPE_MISMATCH, etc.) | Requirements §20, Arch §26 | `ReconciliationEngine` | `src/reconciliation/engine.py` | `tests/unit/test_reconciliation.py` | NOT_STARTED |
| **REQ-EVD-001** | Immutable Evidence Engine with unique stable IDs (E-000001) | Requirements §21, Arch §27 | `EvidenceEngine` | `src/evidence/engine.py` | `tests/unit/test_evidence_engine.py` | NOT_STARTED |
| **REQ-EVD-002** | Multi-modal evidence types (crops, vectors, OCR text, spatial relationships, source hashes, versions) | Requirements §21.1, Plan §16 | `EvidenceEngine` | `src/evidence/builder.py` | `tests/unit/test_evidence_engine.py` | NOT_STARTED |
| **REQ-EVD-003** | Evidence completeness verification (distinguish evidence exists from evidence sufficient for release) | Requirements §22, Arch §28 | `EvidenceCompletenessChecker` | `src/evidence/completeness.py` | `tests/unit/test_completeness.py` | NOT_STARTED |
| **REQ-POL-001** | Deterministic Policy Engine as authoritative release gate (no LLM in release authority) | Requirements §24, Rule 11 | `PolicyEngine` | `src/policy/engine.py` | `tests/unit/test_policy_engine.py` | NOT_STARTED |
| **REQ-POL-002** | Strict 17-gate AUTO_CLEAR evaluation (all mandatory gates must PASS) | Requirements §24.1, Plan §18 | `PolicyEngine` | `src/policy/gates.py` | `tests/unit/test_policy_gates.py` | NOT_STARTED |
| **REQ-POL-003** | HUMAN_REVIEW routing (missed warnings, high-risk, contradictions, detector disagreement, poor quality) | Requirements §24.2, Plan §19 | `PolicyEngine` | `src/policy/routing.py` | `tests/unit/test_policy_routing.py` | NOT_STARTED |
| **REQ-POL-004** | BLOCKED routing (corrupt file, missing map, unsupported provider, missing mandatory legend/AOI) | Requirements §24.3, Plan §20 | `PolicyEngine` | `src/policy/routing.py` | `tests/unit/test_policy_routing.py` | NOT_STARTED |
| **REQ-POL-005** | Prohibition on high-confidence alone authorizing AUTO_CLEAR | Requirements §23, Rule 1 | `PolicyEngine` | `src/policy/gates.py` | `tests/unit/test_policy_gates.py` | NOT_STARTED |
| **REQ-POL-006** | Safe fail-closed mode / Development SAFE_MODE (disable production auto-clear until gold-set locked) | Requirements Rule 14, 18, §86 | `PolicyEngine` | `src/policy/safe_mode.py` | `tests/unit/test_safe_mode.py` | NOT_STARTED |
| **REQ-ORC-001** | LangGraph orchestration of services with durable state checkpointing | Requirements §34, Plan §21 | `MapQAOrchestrator` | `src/orchestration/graph.py` | `tests/integration/test_workflow.py` | NOT_STARTED |
| **REQ-ORC-002** | Lightweight state references (large PDFs, images, vectors remain in object storage) | Requirements §36, Plan §22 | `MapQAState` | `src/orchestration/state.py` | `tests/unit/test_workflow_state.py` | NOT_STARTED |
| **REQ-ORC-003** | HITL workflow interruption on HUMAN_REVIEW and resume upon human disposition | Requirements §26, Plan §23 | `HITLController` | `src/orchestration/hitl.py` | `tests/integration/test_hitl.py` | NOT_STARTED |
| **REQ-ORC-004** | Mandatory policy recheck after human review before final decision | Requirements §37, Plan §23 | `HITLController` | `src/orchestration/hitl.py` | `tests/integration/test_hitl.py` | NOT_STARTED |
| **REQ-QA-001** | Human QA task creation, prioritization, reviewer skill matching, and SLA tracking | Requirements §26, §27 | `QATaskManager` | `src/qa/task_manager.py` | `tests/unit/test_qa_task_manager.py` | NOT_STARTED |
| **REQ-QA-002** | Human disposition actions (CONFIRM, REJECT, ADD, REMOVE, BLOCK, SECOND_REVIEW) + comments | Requirements §26.2, Plan §24 | `QAReviewService` | `src/qa/review_service.py` | `tests/unit/test_qa_review.py` | NOT_STARTED |
| **REQ-LLM-001** | Optional LLM QA Agent bounded to structured evidence summarization & explanation | Requirements §25, Arch §34 | `QAAgentService` | `src/agent/service.py` | `tests/unit/test_qa_agent.py` | NOT_STARTED |
| **REQ-LLM-002** | Strict prohibition on LLM inventing evidence/legends/warnings or overriding policy | Requirements §25.2, Rule 11 | `QAAgentService` | `src/agent/guardrails.py` | `tests/unit/test_agent_guardrails.py` | NOT_STARTED |
| **REQ-LLM-003** | System continuity: Core deterministic QA must continue if LLM is unavailable | Requirements §25, Arch §44 | `QAAgentService` | `src/agent/fallback.py` | `tests/unit/test_agent_fallback.py` | NOT_STARTED |
| **REQ-UI-001** | Production UI implementation following design specification (Enterprise SaaS, 3-panel workspace) | Design §1-97, Plan §26 | Frontend UI | `src/ui/` / web workspace | `tests/e2e/test_ui_flows.py` | NOT_STARTED |
| **REQ-UI-002** | High-performance Map Viewer (pan, zoom, fit AOI/warning, annotation layers, compare mode) | Design §25-28, §82-84 | Map Viewer Component | `src/ui/components/map_viewer/` | `tests/unit/test_ui_components.py` | NOT_STARTED |
| **REQ-UI-003** | Interactive Evidence Viewer linked to source map crop & spatial highlight | Design §31, §59 | Evidence Viewer Component | `src/ui/components/evidence/` | `tests/unit/test_ui_components.py` | NOT_STARTED |
| **REQ-UI-004** | Contextual QA Agent side panel with evidence references | Design §36, §66 | QA Agent Panel | `src/ui/components/qa_agent/` | `tests/unit/test_ui_components.py` | NOT_STARTED |
| **REQ-SCL-001** | Batch processing scalability (1,000+ folders via async queue and worker pool) | Requirements §38, Plan §27 | `BatchWorkerPool` | `src/orchestration/worker.py` | `tests/integration/test_batch.py` | NOT_STARTED |
| **REQ-SCL-002** | Idempotent execution using file SHA-256 + config + rule + legend versions | Requirements §35, Arch §49 | `IdempotencyManager` | `src/orchestration/idempotency.py` | `tests/unit/test_idempotency.py` | NOT_STARTED |
| **REQ-AUD-001** | Complete decision audit trail persisting all 25+ parameters & versions | Requirements §28, Arch §46 | `AuditService` | `src/audit/service.py` | `tests/unit/test_audit_service.py` | NOT_STARTED |
| **REQ-AUD-002** | Historical decision reproducibility verification | Requirements §29, Arch §47 | `ReproducibilityEngine` | `src/audit/reproducibility.py` | `tests/unit/test_reproducibility.py` | NOT_STARTED |
| **REQ-SEC-001** | Enterprise security controls (RBAC, encryption in transit/rest, path traversal defense) | Requirements §37, Arch §43 | `SecurityService` | `src/api/security.py` | `tests/unit/test_security.py` | NOT_STARTED |
| **REQ-OBS-001** | Structured logging, metrics, tracing, and operational health monitoring | Requirements §53, Arch §45 | `ObservabilityService` | `src/observability/` | `tests/unit/test_observability.py` | NOT_STARTED |
| **REQ-EVL-001** | Versioned locked gold-standard evaluation dataset | Requirements §40, Plan §33 | Gold Dataset Manager | `datasets/gold/` | `tests/regression/test_gold_dataset.py` | NOT_STARTED |
| **REQ-EVL-002** | Primary KPI tracking: Auto-clear escape rate (zero escaped critical warnings target) | Requirements §42, Plan §34 | Evaluation Engine | `src/reporting/evaluation.py` | `tests/regression/test_metrics.py` | NOT_STARTED |
| **REQ-OUT-001** | Standard output generation (`job_report.json`, `document_results.json`, evidence/, annotated_maps/) | Requirements §48, Arch §75 | `ReportGenerator` | `src/reporting/generator.py` | `tests/unit/test_reporting.py` | NOT_STARTED |

---
