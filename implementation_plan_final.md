# AI Map QA & Validation Agent
## Final Production Implementation Plan

**Status:** Final implementation blueprint  
**Architecture:** Deterministic Map QA + Computer Vision + Native PDF Analysis + Spatial Validation + Human-in-the-Loop + Optional QA Agent/LLM

---

# 1. Executive Summary

The AI Map QA & Validation Agent is a production QA platform that receives a **root folder location** containing an Excel index, utility/engineering map PDFs, legend/reference documents, and, where available, upstream warning results.

The system must:

1. Discover and validate all input files.
2. Read the existing Excel index without modifying it.
3. Resolve every index record to the correct map/document.
4. Inspect PDFs using native PDF analysis first.
5. Resolve provider-specific warning definitions.
6. Resolve the authoritative legend.
7. Resolve and validate the Area of Interest (AOI).
8. Independently inspect maps for expected warnings.
9. Validate warnings reported by the upstream system.
10. Detect warnings missed by the upstream system.
11. Perform spatial validation.
12. Build evidence for every important conclusion.
13. Apply deterministic release policy.
14. Automatically clear only cases satisfying all mandatory release conditions.
15. Route uncertain/discrepant cases to Human QA.
16. Block cases where mandatory validation cannot safely be completed.
17. Optionally use an LLM-powered QA Agent to summarize and reason over structured evidence.
18. Maintain complete auditability and reproducibility.
19. Support batch processing of 1,000+ folders.
20. Continuously evaluate changes against a locked gold-standard dataset.

> **Core safety principle: The LLM is optional assistance. Deterministic validation, evidence, and policy gates remain authoritative.**

---

# 2. Final Architecture

```text
ROOT FOLDER
    ↓
CREATE JOB
    ↓
FILE INVENTORY
    ↓
READ EXCEL (READ ONLY)
    ↓
VALIDATE INDEX
    ↓
DOCUMENT RESOLUTION
    ↓
PDF INSPECTION
    ↓
PROVIDER RESOLUTION
    ↓
WARNING CATALOGUE + LEGEND
    ↓
AOI RESOLUTION
    ↓
INDEPENDENT WARNING DETECTION
    ↓
SPATIAL VALIDATION
    ↓
UPSTREAM vs INDEPENDENT RECONCILIATION
    ↓
EVIDENCE ENGINE
    ↓
DETERMINISTIC POLICY ENGINE
    │
    ├── AUTO_CLEAR
    │
    ├── HUMAN_REVIEW
    │       ↓
    │   HUMAN QA / OPTIONAL QA AGENT
    │       ↓
    │   POLICY RECHECK
    │
    └── BLOCKED
    ↓
FINAL DECISION
    ↓
OUTPUT / CLIENT DISPATCH
    ↓
AUDIT + METRICS + FEEDBACK
```

---

# 3. Architecture Responsibilities

## LangGraph

LangGraph is the **workflow orchestration and state-management layer**.

It handles:

- workflow sequencing;
- conditional routing;
- retries;
- checkpointing;
- long-running execution;
- human-review interruption;
- resume;
- workflow state.

It should **not contain all business logic**.

Instead:

```text
LangGraph
 ├── IngestionService
 ├── IndexService
 ├── DocumentResolver
 ├── PDFAnalysisService
 ├── LegendService
 ├── WarningService
 ├── AOIService
 ├── DetectionService
 ├── SpatialService
 ├── ReconciliationService
 ├── EvidenceService
 └── PolicyEngine
```

## LLM / QA Agent

The LLM can:

- summarize structured evidence;
- explain contradictions;
- suggest what a reviewer should inspect;
- generate reviewer-friendly explanations;
- assist with case prioritization.

It cannot:

- invent evidence;
- invent warning classes;
- invent coordinates;
- override policy;
- turn uncertainty into AUTO_CLEAR;
- claim tools ran when they did not.

The deterministic pipeline must work if the LLM is unavailable.

---

# 4. Implementation Phases

```text
Phase 0  Requirements & Data Discovery
Phase 1  Project Foundation
Phase 2  Input/Ingestion
Phase 3  Document Resolution
Phase 4  PDF Analysis
Phase 5  Provider/Warning/Legend Configuration
Phase 6  AOI & Spatial Engine
Phase 7  Independent Warning Detection
Phase 8  Reconciliation & Evidence
Phase 9  Deterministic Policy Engine
Phase 10 LangGraph Orchestration
Phase 11 Human QA / HITL
Phase 12 QA Agent / LLM
Phase 13 Production UI
Phase 14 Batch Scaling
Phase 15 Testing & Gold Dataset
Phase 16 Production Hardening
Phase 17 Pilot
Phase 18 Provider Expansion
```

---

# 5. Phase 0 — Requirements & Data Discovery

Before production coding, inspect the actual project data.

## Required investigation

### Root folder

Determine:

- folder hierarchy;
- Excel filename;
- map naming conventions;
- provider folders;
- legend documents;
- upstream outputs;
- reference files.

### Excel

Confirm:

- sheet names;
- exact columns;
- required/optional fields;
- provider fields;
- warning fields;
- map path fields;
- row uniqueness;
- invalid/blank rows.

### PDFs

Sample:

- vector PDFs;
- raster PDFs;
- hybrid PDFs;
- multi-page maps;
- large drawings;
- low-quality scans;
- maps with embedded legends.

### Warning catalogue

Confirm:

- warning codes;
- names;
- providers;
- utility types;
- severity;
- geometry;
- AOI requirement;
- detection semantics.

### Legends

Confirm:

- authoritative source;
- provider;
- version;
- effective date;
- colors;
- line styles;
- dash patterns;
- symbols;
- warning mappings.

### Upstream results

Confirm:

- schema;
- warning IDs;
- geometry;
- confidence;
- document IDs;
- model version;
- timestamp.

## Deliverables

```text
docs/
├── data_inventory.md
├── input_contract.md
├── warning_catalogue_spec.md
├── legend_spec.md
└── upstream_contract.md
```

---

# 6. Phase 1 — Project Foundation

Recommended repository:

```text
ai-map-qa/
├── README.md
├── requirements.md
├── architecture.md
├── design.md
├── implementation_plan.md
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── src/
│   ├── api/
│   ├── config/
│   ├── domain/
│   ├── orchestration/
│   ├── ingestion/
│   ├── index/
│   ├── documents/
│   ├── pdf/
│   ├── vector/
│   ├── cv/
│   ├── ocr/
│   ├── providers/
│   ├── warnings/
│   ├── legends/
│   ├── aoi/
│   ├── spatial/
│   ├── reconciliation/
│   ├── evidence/
│   ├── policy/
│   ├── qa/
│   ├── agent/
│   ├── audit/
│   ├── reporting/
│   └── observability/
│
├── configs/
├── tests/
├── datasets/
├── migrations/
├── scripts/
└── docs/
```

Foundation work:

- dependency pinning;
- formatting;
- linting;
- type checking;
- logging;
- configuration;
- database migrations;
- Docker;
- CI.

---

# 7. Phase 2 — Input & Ingestion

Flow:

```text
Root Folder
 ↓
Create Job
 ↓
Recursive File Scan
 ↓
SHA-256 Hash
 ↓
File Classification
 ↓
Index Discovery
 ↓
Input Validation
 ↓
Job Manifest
```

File classes:

```text
INDEX
MAP
LEGEND
UPSTREAM_OUTPUT
REFERENCE
OTHER
UNKNOWN
```

Unknown files must be logged.

No input row may silently disappear.

---

# 8. Excel Processing

The production Excel is **read-only**.

The system must never:

- rename columns;
- add columns;
- delete columns;
- overwrite values;
- reorder source rows;
- modify formatting.

Instead:

```text
Excel
 ↓
Read-only parser
 ↓
Canonical internal representation
```

Each index row receives a status such as:

```text
VALID
MISSING_MAP
AMBIGUOUS_MAP
INVALID_PROVIDER
INVALID_WARNING
BLOCKED
```

---

# 9. Phase 3 — Document Resolver

Resolve each Excel row to the correct map using deterministic signals:

- explicit path;
- filename;
- provider;
- utility;
- project/reference ID;
- configured naming patterns;
- directory context.

If ambiguity remains:

```text
AMBIGUOUS_MAPPING
→ HUMAN_REVIEW / BLOCKED
```

Never guess.

Each document gets:

```text
document_id
source_path
sha256
filename
provider
index_record_id
job_id
```

---

# 10. Phase 4 — PDF Analysis

Use **PyMuPDF first**.

The PDF is processed by your own application worker. PyMuPDF is a local/server-side library, not a required cloud document-processing service.

Flow:

```text
PDF
 ↓
PyMuPDF
 ↓
VECTOR / RASTER / HYBRID / UNREADABLE
 ↓
Text / Vectors / Images / Metadata
 ↓
Analysis Artifacts
```

Extract where available:

- text and coordinates;
- vector paths;
- strokes;
- fills;
- colors;
- widths;
- dash patterns;
- embedded images;
- page dimensions;
- metadata.

Rasterize only when required for CV/OCR.

---

# 11. Phase 5 — Provider / Warning / Legend Configuration

## Warning Catalogue

The warning catalogue is the business definition of what must be detected.

Conceptual schema:

```text
WarningDefinition
├── warning_code
├── provider
├── utility_type
├── warning_name
├── severity
├── geometry_type
├── aoi_required
├── detection_profile
├── active
└── version
```

## Provider Registry

Each provider can define:

```text
identity rules
warning definitions
legend profiles
AOI rules
detection rules
spatial rules
policy context
```

Avoid a huge hard-coded provider `if/elif` system.

## Legend Registry

Store:

```text
provider
legend_id
version
source
source_hash
effective_date
symbols
colors
line_styles
dash_patterns
warning_mappings
status
```

Every decision must reference the legend version used.

If a required authoritative legend cannot be resolved:

```text
LEGEND_UNAVAILABLE
→ NO AUTO_CLEAR
```

---

# 12. Phase 6 — AOI & Spatial Engine

Resolve the Area of Interest using approved methods:

1. native vector geometry;
2. explicit map geometry;
3. approved external AOI;
4. CV detection;
5. other approved methods.

AOI record:

```text
aoi_id
document_id
page
geometry
method
confidence
coordinate_system
tolerance
validity
```

Spatial operations:

```text
INTERSECTS
WITHIN
CONTAINS
TOUCHES
OVERLAPS
CROSSES
DISTANCE
```

Do not silently mix PDF coordinates, pixel coordinates, and real-world coordinates.

---

# 13. Phase 7 — Independent Warning Detection

This is the core QA capability.

The system must independently inspect the map even when upstream says:

```text
NO WARNING
```

Flow:

```text
Provider
+
Warning Catalogue
+
Legend
+
Map
+
AOI
 ↓
Independent Detector
 ↓
Candidate Warnings
```

Detection layers:

## Level 1 — Native PDF

- vector geometry;
- colors;
- stroke styles;
- text;
- symbols.

## Level 2 — Deterministic CV

- thresholding;
- morphology;
- connected components;
- line detection;
- symbol/template matching.

## Level 3 — OCR

- map labels;
- legend text;
- annotations.

## Level 4 — ML/CV models

Use only when simpler methods cannot reliably resolve the feature.

---

# 14. Detection Output

Each candidate should contain:

```text
candidate_id
document_id
page
warning_code
geometry
bbox
detection_method
confidence
evidence_ids
```

Confidence is supporting information, not release authority.

---

# 15. Phase 8 — Upstream Reconciliation

Compare:

```text
UPSTREAM
vs
INDEPENDENT QA
```

Possible outcomes:

```text
MATCH
MISSED_WARNING
POSSIBLE_FALSE_POSITIVE
TYPE_MISMATCH
LOCATION_MISMATCH
DUPLICATE
UNCERTAIN
```

Examples:

```text
Upstream: HP Gas
Independent: HP Gas
→ MATCH
```

```text
Upstream: No warning
Independent: HP Gas
→ MISSED_WARNING
```

```text
Upstream: HP Gas
Independent: No supporting evidence
→ POSSIBLE_FALSE_POSITIVE
```

---

# 16. Phase 8 — Evidence Engine

Every important conclusion needs evidence.

Evidence types:

```text
SOURCE_FILE
PAGE
MAP_CROP
LEGEND_CROP
VECTOR
OCR
CV
GEOMETRY
AOI
UPSTREAM_RESULT
INDEPENDENT_RESULT
RULE_RESULT
```

Example:

```text
Warning W-001
 ├── E-001 Map crop
 ├── E-002 Legend crop
 ├── E-003 Vector path
 ├── E-004 AOI geometry
 ├── E-005 Spatial intersection
 ├── E-006 Upstream result
 └── E-007 Independent result
```

Mandatory evidence must be explicitly defined per warning/policy type.

---

# 17. Phase 9 — Deterministic Policy Engine

The Policy Engine is the **release authority**.

It must not depend on an LLM.

It evaluates:

```text
Index validity
Document mapping
PDF usability
Provider
Warning catalogue
Legend
AOI
Independent QA completion
Upstream reconciliation
Critical warnings
Detector conflicts
Evidence completeness
Spatial validation
Provider rules
Audit persistence
System integrity
```

Output:

```text
AUTO_CLEAR
HUMAN_REVIEW
BLOCKED
```

Do not use:

```text
"100% confidence"
```

as a release condition.

Instead use:

```text
All mandatory gates pass
+
Required evidence complete
+
No unresolved critical issue
+
No unresolved contradiction
+
Policy permits AUTO_CLEAR
```

---

# 18. AUTO_CLEAR

Conceptual conditions:

```text
Index valid
AND
Document mapping valid
AND
Map readable
AND
Provider resolved
AND
Warning catalogue resolved
AND
Required legend resolved
AND
Required AOI resolved
AND
Independent QA completed
AND
Reconciliation completed
AND
No unresolved critical warning
AND
No unresolved detector conflict
AND
Evidence complete
AND
Required spatial checks passed
AND
Policy passed
AND
Audit persisted
AND
System integrity checks passed
```

The exact approved business gates, including the project's 17 mandatory gates, must be configured from the authoritative requirements rather than invented in code.

---

# 19. HUMAN_REVIEW

Escalate for:

- missed warnings;
- possible false positives;
- high-risk warnings;
- detector disagreement;
- legend ambiguity;
- AOI ambiguity;
- OCR uncertainty;
- poor-quality maps;
- conflicting evidence;
- policy-required review.

---

# 20. BLOCKED

Block when safe validation cannot be completed, for example:

- missing required map;
- corrupt PDF;
- unsupported document;
- unresolved provider;
- unavailable required legend;
- unavailable required AOI;
- mandatory validation failure;
- infrastructure failure preventing safe validation.

---

# 21. Phase 10 — LangGraph Orchestration

Only after the deterministic services work should they be wrapped in LangGraph.

Workflow:

```text
START
 ↓
Create Job Context
 ↓
Ingest Folder
 ↓
Validate Index
 ↓
Resolve Documents
 ↓
Inspect PDFs
 ↓
Resolve Provider
 ↓
Resolve Warning Catalogue
 ↓
Resolve Legend
 ↓
Resolve AOI
 ↓
Independent QA
 ↓
Spatial Validation
 ↓
Reconcile Upstream
 ↓
Build Evidence
 ↓
Evaluate Policy
 │
 ├── AUTO_CLEAR → Finalize Release
 ├── BLOCKED → Finalize Block
 └── HUMAN_REVIEW → Interrupt
                         ↓
                      Human QA
                         ↓
                    Human Decision
                         ↓
                    Policy Recheck
                         ↓
                    Final Decision
```

---

# 22. LangGraph State

Do not store large PDFs, images, or complete vector datasets directly in workflow state.

Use artifact references:

```python
class MapQAState(TypedDict):
    job_id: str
    workflow_run_id: str

    input_manifest_id: str
    index_record_ids: list[str]
    document_ids: list[str]

    provider_context: dict
    warning_catalogue_version: str
    legend_context: dict
    aoi_context: dict

    upstream_result_ids: list[str]
    detection_ids: list[str]
    reconciliation_ids: list[str]
    evidence_ids: list[str]

    policy_result: dict
    decision: str

    human_review_id: str | None
    error_state: dict | None
    component_versions: dict
```

Large artifacts remain in object storage.

Use a unique `workflow_run_id`, not the folder name.

---

# 23. HITL Architecture

When review is required:

```text
Policy Engine
 ↓
HUMAN_REVIEW
 ↓
Create QA Task
 ↓
LangGraph Interrupt
 ↓
Reviewer UI
 ↓
Human Decision
 ↓
Resume Workflow
 ↓
Policy Recheck
 ↓
Final Decision
```

Never implement:

```text
HUMAN_REVIEW
 ↓
AUTO_CLEAR directly
```

The Policy Engine remains authoritative after human input.

---

# 24. Phase 11 — Human QA

Reviewer workspace should show:

```text
Map
AOI
Upstream Warning
Independent Finding
Legend
Evidence
Reason for Escalation
Policy Result
QA Agent Summary
Decision Controls
Audit
```

Possible actions:

```text
CONFIRM_WARNING
REJECT_WARNING
ADD_WARNING
REMOVE_WARNING
BLOCK
REQUEST_SECOND_REVIEW
```

Every decision should capture reviewer, time, reason/comment, and relevant evidence.

---

# 25. Phase 12 — QA Agent / LLM

Add only after the deterministic workflow works.

Input:

```text
Structured Case
+
Evidence Metadata
+
Selected Evidence
```

Output:

```text
Summary
Potential Conflict
Recommended Inspection
Explanation
```

If the LLM fails:

```text
LLM unavailable
 ↓
Structured evidence remains available
 ↓
Human reviewer continues
```

---

# 26. Phase 13 — Production UI

## P0

```text
1. Job Submission
2. Job Progress
3. Map Inventory
4. QA Queue
5. Map QA Workspace
6. Evidence Viewer
```

## P1

```text
7. Warning Catalogue
8. Providers
9. Legends
10. Rules
11. Reports
12. Audit
```

## P2

```text
13. Evaluation
14. System Health
15. Advanced analytics
16. Advanced QA Agent
```

The **Map QA Workspace** is the highest-priority screen.

---

# 27. Phase 14 — Batch Processing

Target:

> 1,000+ folders.

Architecture:

```text
Batch Input
 ↓
Job Creation
 ↓
Queue
 ↓
Worker Pool
 ↓
Independent Job Executions
```

Do not process all folders in one in-memory workflow.

Concurrency should be configurable, for example:

```text
MAX_CONCURRENT_JOBS=20
```

The actual value must be determined by load testing.

---

# 28. Queue Requirements

Workers must support:

- retries;
- timeouts;
- idempotency;
- dead-letter handling;
- backpressure;
- cancellation;
- graceful shutdown.

Human-review cases must pause independently without blocking unrelated jobs.

---

# 29. Phase 15 — Persistence

Use PostgreSQL/PostGIS for structured data.

Core entities:

```text
jobs
index_records
files
documents
document_mappings
pages
providers
warning_definitions
legend_profiles
aois
detections
warnings
validation_results
reconciliations
evidence
decisions
qa_tasks
qa_reviews
audit_events
model_versions
rule_versions
feedback_records
```

Use object storage for:

```text
Original PDFs
Rendered pages
Vector artifacts
OCR artifacts
Evidence crops
Annotated maps
Reports
```

Database stores references to these artifacts.

---

# 30. Phase 16 — Audit & Versioning

Record:

```text
Who
What
When
Why
Document
Evidence
Rule
Legend
Model
Configuration
Decision
```

Version:

```text
Warning Catalogue
Legend
Provider Configuration
Detection Rules
AOI Method
CV Model
OCR Version
PDF Parser Version
Policy Rules
QA Agent
Application
```

A decision must reference all decision-relevant versions.

---

# 31. Phase 17 — Testing Strategy

Testing must be continuous.

## Unit tests

- file classification;
- Excel parsing;
- document resolution;
- provider resolution;
- warning matching;
- legend matching;
- AOI;
- geometry;
- spatial rules;
- reconciliation;
- evidence completeness;
- policy gates.

## PDF fixtures

Include:

```text
Vector
Raster
Hybrid
Multi-page
Corrupt
Missing text
Faded scan
Complex drawing
Embedded legend
No legend
```

## CV tests

Include:

- line detection;
- color tolerance;
- symbol detection;
- dash patterns;
- overlapping utilities;
- low-resolution scans;
- noisy scans.

## Spatial tests

Test:

```text
INSIDE
OUTSIDE
BOUNDARY
TOUCHING
INTERSECTING
OVERLAPPING
CROSSING
```

---

# 32. End-to-End Tests

Minimum scenarios:

### Clean map

```text
→ AUTO_CLEAR
```

### Missed warning

```text
→ HUMAN_REVIEW
```

### Corrupt PDF

```text
→ BLOCKED
```

### Missing legend

```text
→ HUMAN_REVIEW / BLOCKED
```

### Ambiguous mapping

```text
→ HUMAN_REVIEW / BLOCKED
```

### Human decision

```text
Human Decision
→ Policy Recheck
→ Final Decision
```

---

# 33. Gold-Standard Dataset

Create a domain-reviewed dataset containing:

```text
True clean maps
True warning maps
Missed upstream warnings
False upstream warnings
Ambiguous cases
Raster maps
Vector maps
Hybrid maps
Poor-quality maps
AOI boundary cases
Legend variations
```

Lock the evaluation dataset.

---

# 34. Quality Metrics

Primary safety metric:

> **Escaped warning rate among AUTO_CLEAR results.**

Definition:

```text
Real warning exists
+
System AUTO_CLEAR
=
ESCAPED WARNING
```

Also measure:

```text
Warning Recall
Warning Precision
False Negative Rate
False Positive Rate
AUTO_CLEAR Rate
HUMAN_REVIEW Rate
BLOCKED Rate
Human Override Rate
Processing Latency
```

Do not invent production thresholds before evaluating representative data.

---

# 35. Phase 18 — Production Hardening

## Security

Implement:

- authentication;
- RBAC;
- least privilege;
- encrypted transport;
- encrypted storage;
- secrets management;
- audit;
- secure file handling;
- environment isolation;
- retention policy.

## File security

Before processing:

```text
Validate type
Validate size
Validate path
Prevent traversal
Hash
Quarantine if required
Apply resource limits
```

## Observability

Track:

```text
jobs_total
jobs_completed
jobs_failed
jobs_blocked
jobs_human_review

warnings_detected
missed_warnings
false_positives
auto_clear
human_review
escaped_warnings

processing_time
pdf_time
cv_time
ocr_time
spatial_time
evidence_time
policy_time
```

---

# 36. Failure Handling

Classify failures:

```text
INPUT_ERROR
DOCUMENT_ERROR
PDF_ERROR
LEGEND_ERROR
AOI_ERROR
DETECTION_ERROR
SPATIAL_ERROR
POLICY_ERROR
INFRASTRUCTURE_ERROR
LLM_ERROR
```

Each error should contain:

```text
code
message
stage
recoverable
retry_count
impact
```

Retry only recoverable failures.

Examples:

```text
Temporary storage error → retry
Temporary queue error → retry
Corrupt PDF → BLOCKED
Missing legend → HUMAN_REVIEW/BLOCKED
```

---

# 37. Fail-Closed Principle

Critical rule:

```text
Validation incomplete
 ↓
NOT clean
```

Never:

```text
Processing failed
 ↓
AUTO_CLEAR
```

If mandatory validation cannot complete:

```text
HUMAN_REVIEW or BLOCKED
```

---

# 38. Performance Strategy

Optimize after correctness.

Priority:

1. Native PDF extraction.
2. Avoid unnecessary rendering.
3. Cache immutable artifacts.
4. Parallelize independent documents.
5. Batch database operations.
6. Optimize geometry queries.
7. Bound CV/GPU concurrency.
8. Stream large files.
9. Lazy-load UI evidence.
10. Measure before optimizing.

---

# 39. Caching

Cache keys should include decision-relevant versions:

```text
SHA256
+
PDF Parser Version
+
Provider Version
+
Legend Version
+
Warning Catalogue Version
+
Detection Version
```

Do not reuse stale results after a relevant configuration change.

---

# 40. Client Dispatch

Client dispatch happens only after final validation.

```text
Policy
 ↓
Final Decision
 ↓
Output Validation
 ↓
Report Generation
 ↓
Artifact Integrity Check
 ↓
Client Dispatch
```

Never dispatch directly from an intermediate model result.

---

# 41. Pilot Strategy

Start with the approved initial provider set, recommended in the project planning as:

```text
SGN
UKPN
Clean Water
```

The pilot should include:

- real production-like folders;
- known clean cases;
- known warning cases;
- known upstream misses;
- human review;
- performance testing;
- audit;
- reporting.

---

# 42. Pilot Acceptance

Before expansion:

```text
✓ Escape rate within approved threshold
✓ Required recall achieved
✓ No critical unexplained failures
✓ Evidence complete
✓ Human QA usable
✓ Audit reproducible
✓ Batch processing stable
✓ Recovery tested
✓ Security reviewed
✓ Operational runbook complete
```

---

# 43. Provider Expansion

For each new provider:

```text
Provider Configuration
 ↓
Warning Catalogue
 ↓
Legend
 ↓
Detection Rules
 ↓
AOI Rules
 ↓
Spatial Tests
 ↓
Gold Dataset
 ↓
Regression
 ↓
Staging
 ↓
Pilot
 ↓
Production
```

Never add a provider directly to production without provider-specific validation.

---

# 44. Recommended Coding Order

```text
01. Repository
02. Configuration
03. Database
04. File inventory
05. Excel parser
06. Document resolver
07. PyMuPDF PDF inspector
08. PDF fixtures
09. Provider registry
10. Warning catalogue
11. Legend registry
12. AOI service
13. Vector analysis
14. CV pipeline
15. OCR
16. Spatial engine
17. Independent warning discovery
18. Upstream reconciliation
19. Evidence engine
20. Policy engine
21. Deterministic end-to-end pipeline
22. Tests + gold dataset
23. LangGraph orchestration
24. Checkpointing
25. HITL
26. Reviewer UI
27. QA Agent
28. Batch queue
29. Observability
30. Security hardening
31. Performance testing
32. Pilot
33. Production
```

---

# 45. First Working Milestone

Do **not** begin with LangGraph or the LLM.

First make one real folder work:

```text
ONE REAL FOLDER
 ↓
Excel
 ↓
Map Resolver
 ↓
PyMuPDF
 ↓
Provider
 ↓
Warning Catalogue
 ↓
Legend
 ↓
AOI
 ↓
Independent Detection
 ↓
Spatial Validation
 ↓
Evidence
 ↓
Policy
 ↓
Result
```

This deterministic core must work reliably first.

---

# 46. Second Milestone

Run approximately 10–50 representative folders.

Measure:

- accuracy;
- failure modes;
- performance;
- evidence quality;
- policy behavior.

Fix underlying QA logic before scaling.

---

# 47. Third Milestone

Add:

```text
LangGraph
+
PostgreSQL checkpointing
+
HITL
+
Reviewer UI
```

Now long-running workflows and human pauses become production-capable.

---

# 48. Fourth Milestone

Load-test:

```text
100 folders
500 folders
1,000+ folders
```

Measure:

- CPU;
- RAM;
- GPU;
- queue depth;
- worker throughput;
- database load;
- storage throughput;
- recovery;
- latency.

---

# 49. Fifth Milestone

Add the QA Agent/LLM.

Measure whether it actually improves:

- reviewer time;
- evidence understanding;
- case prioritization;
- explanation quality.

If it does not materially improve the workflow, keep it outside the critical path.

---

# 50. Production Non-Negotiables

1. Do not modify the source Excel.
2. Do not silently drop an index row.
3. Do not guess document mappings.
4. Do not guess provider identity.
5. Do not invent warning definitions.
6. Do not invent legend semantics.
7. Do not treat upstream “no warning” as proof of cleanliness.
8. Independent warning discovery is mandatory.
9. Spatial validation must be evidence-backed.
10. Every release decision needs evidence.
11. Confidence is not release authority.
12. The Policy Engine controls AUTO_CLEAR.
13. The LLM cannot override the Policy Engine.
14. Human decisions require policy re-evaluation.
15. Incomplete validation cannot produce AUTO_CLEAR.
16. Infrastructure failure cannot be interpreted as a clean map.
17. Large artifacts stay outside LangGraph state.
18. Workflow executions use unique IDs, not folder names.
19. Decision-relevant versions are recorded.
20. Provider logic is configurable and versioned.
21. Legend logic is versioned.
22. Warning catalogue is versioned.
23. Production changes require regression testing.
24. Gold-standard evaluation precedes production auto-clear.
25. Human QA feedback is auditable.
26. The primary optimization target is low escaped-warning risk.

---

# 51. Definition of Done

```text
✓ Real root folders can be processed
✓ Excel is safely read without modification
✓ Every row is accounted for
✓ Documents are resolved deterministically
✓ PDFs are reliably inspected
✓ Provider semantics are resolved
✓ Warning catalogue is authoritative
✓ Legends are versioned and resolved
✓ AOI is reliably established
✓ Independent warning detection works
✓ Upstream discrepancies are detected
✓ Spatial relationships are validated
✓ Evidence is generated
✓ Policy is deterministic
✓ AUTO_CLEAR is fail-closed
✓ HUMAN_REVIEW works
✓ BLOCKED works
✓ LangGraph checkpoint/resume works
✓ QA UI works
✓ QA Agent is safely bounded
✓ Audit is complete
✓ Batch processing is tested
✓ 1,000+ folder scalability is demonstrated
✓ Gold-standard evaluation passes
✓ Regression suite passes
✓ Security controls pass
✓ Observability is operational
✓ Recovery procedures are tested
✓ Pilot acceptance criteria are met
```

---

# 52. Final Recommendation

The implementation order should be:

> **Build the deterministic QA core → prove it on real data → wrap it with LangGraph → add HITL → add production UI → add optional LLM assistance → scale to 1,000+ folders → validate against a locked gold dataset → pilot → production.**

The project should ultimately be:

```text
DETERMINISTIC QA CORE
        +
COMPUTER VISION
        +
PDF ANALYSIS
        +
SPATIAL QA
        +
EVIDENCE
        +
POLICY ENGINE
        +
LANGGRAPH
        +
HITL
        +
OPTIONAL LLM
        +
PRODUCTION PLATFORM
```

**Primary production objective:**

> Minimize escaped real warnings while reducing unnecessary human QA effort.
