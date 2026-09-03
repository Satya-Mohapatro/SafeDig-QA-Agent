# AI Map QA & Validation Agent

## Production-Grade Project Requirements Document

**Document Type:** Software / AI-CV / Document Intelligence / QA
Platform Requirements\
**Project:** AI Map QA & Validation Agent\
**Target:** Production-grade enterprise system\
**Primary Goal:** Independently validate utility/engineering map
warnings, detect missed warnings, reduce repetitive human QA, and
prevent unsafe auto-clear decisions.

------------------------------------------------------------------------

## 1. Executive Summary

The AI Map QA & Validation Agent is a downstream, independent QA
platform for utility and engineering map documents.

The existing upstream system already produces maps and/or warning
information using AI/image processing. This project does **not** replace
that upstream system. Instead, it independently examines the source map,
determines what warning conditions are actually present, validates the
upstream warnings, discovers warnings that may have been missed, and
produces an evidence-backed release decision.

The system must be production-grade, auditable, reproducible, secure,
testable, scalable, and fail-safe.

### Core principle

> **Do not build an LLM that simply looks at a map and says PASS/FAIL.
> Build a layered validation platform in which PDF/vector analysis,
> computer vision, OCR, spatial analysis, provider-specific rules,
> warning definitions, evidence aggregation, and deterministic policy
> gates produce the final decision.**

An LLM may be used inside the **QA Agent** for reasoning, summarization,
contradiction analysis, explanation, and reviewer assistance. However:

-   the critical validation path must not depend on an LLM;
-   the LLM must not invent evidence;
-   the LLM must not invent legends or warning rules;
-   the LLM must not override mandatory policy gates;
-   the LLM must never be the sole basis for `AUTO_CLEAR`.

This follows the supplied project requirements, which explicitly require
an independent QA layer, deterministic release gates, evidence, human
escalation, and low escaped-warning risk.

------------------------------------------------------------------------

# 2. Business Objective

## 2.1 Primary objective

Reduce manual map QA effort while maintaining or improving release
safety.

The system must:

1.  Read the existing Excel index.
2.  Discover and classify the supplied root-folder contents.
3.  Resolve every expected map/document.
4.  Validate map readability and integrity.
5.  Resolve the correct provider/utility.
6.  Resolve the authoritative legend/symbol definition.
7.  Resolve and validate the relevant AOI/digsite where required.
8.  Independently detect warning conditions.
9.  Validate upstream warnings.
10. Detect warnings missed by the upstream system.
11. Compare upstream and independent findings.
12. Produce evidence for every decision.
13. Apply deterministic business/release rules.
14. Auto-clear only evidence-complete, policy-approved cases.
15. Escalate uncertain/high-risk cases to human QA.
16. Block unsafe or incomplete cases.
17. Preserve a complete audit trail.
18. Capture human QA feedback for controlled improvement.

------------------------------------------------------------------------

# 3. Scope

## 3.1 In scope

### Input processing

-   Root-folder ingestion
-   File discovery
-   File classification
-   Excel/index parsing
-   Map/document resolution
-   PDF inspection
-   Raster/vector/hybrid classification
-   Native PDF extraction
-   Legend resolution
-   AOI/digsite resolution
-   Upstream warning ingestion
-   Independent warning discovery
-   Computer vision
-   OCR
-   Spatial validation
-   Warning classification
-   Warning reconciliation
-   Evidence generation
-   Decision/policy engine
-   Human QA routing
-   QA Agent assistance
-   Audit logging
-   Reporting
-   Feedback/evaluation
-   Monitoring
-   Regression testing

## 3.2 Out of scope unless explicitly approved

-   Replacing the upstream AI/image-processing system
-   Automatically changing the production Excel structure
-   Uncontrolled model retraining
-   Uncontrolled LLM-based client release
-   Inventing provider warning definitions
-   Inventing missing legends
-   Releasing unsupported providers automatically
-   Treating arbitrary confidence thresholds as release policy

------------------------------------------------------------------------

# 4. Source of Truth and Authority

The project has several different sources of truth, and they must not be
conflated.

  -----------------------------------------------------------------------
  Information                         Authority
  ----------------------------------- -----------------------------------
  Existing production index structure Existing production Excel

  Warning definitions                 Approved warning catalogue supplied
                                      by business

  Warning severity                    Approved warning catalogue

  Provider semantics                  Approved provider/legend registry

  Map visual meaning                  Authoritative provider
                                      legend/symbol guide

  Actual map evidence                 Source map/PDF/image

  Upstream result                     Existing upstream system

  Final release decision              Deterministic policy engine

  Human disposition                   Authorized QA reviewer
  -----------------------------------------------------------------------

### Important

The user has supplied a warning catalogue workbook. It is intended to
define which warning categories should be detected and how they are
categorized/severitized. Before production adoption, its exact role as
the authoritative master catalogue must be formally confirmed.

------------------------------------------------------------------------

# 5. Fundamental Design Principles

## 5.1 No LLM dependency for critical validation

The system must be able to perform the core validation without an LLM.

Critical path:

``` text
PDF
→ Vector/Text/Image Extraction
→ Legend
→ AOI
→ Warning Detection
→ Spatial Validation
→ Evidence
→ Policy
→ Decision
```

The LLM is optional and supplementary.

## 5.2 Deterministic safety gates

No:

``` text
confidence > 0.95
→ AUTO_CLEAR
```

Instead:

``` text
all mandatory gates PASS
+
evidence complete
+
no unresolved risk
+
policy allows release
→ AUTO_CLEAR
```

## 5.3 Fail closed

When the system cannot safely establish correctness:

``` text
UNCERTAIN → HUMAN_REVIEW
```

or:

``` text
BLOCKED
```

Never:

``` text
UNCERTAIN → PASS
```

## 5.4 Independent validation

The system must independently search for warnings even when the upstream
system reports no warning.

## 5.5 Provider-specific behavior

Different utilities/providers can use different:

-   colors
-   line styles
-   symbols
-   legends
-   annotations
-   AOI styles
-   map formats
-   semantics

There must be no unsafe universal color detector.

## 5.6 Evidence-first

Every final decision must reference machine-readable evidence.

## 5.7 Reproducibility

Historical decisions must be reproducible using:

-   input file hashes
-   parser versions
-   legend versions
-   rule versions
-   model versions
-   configuration versions
-   evidence references
-   timestamps

------------------------------------------------------------------------

# 6. Input Requirements

## 6.1 Root folder

The primary input is a root folder path.

Example:

``` text
root_folder/
├── index.xlsx
├── utility_maps/
├── legends/
├── upstream_outputs/
└── supporting_documents/
```

The actual folder structure may vary.

The system must discover contents rather than depend on hard-coded
filenames.

## 6.2 Supported input categories

At minimum:

-   Excel workbooks
-   PDF documents
-   image documents where required
-   provider legend/symbol documents
-   upstream warning output
-   supporting/reference documents

## 6.3 File metadata

For each discovered file, capture:

-   absolute/relative path
-   filename
-   extension
-   MIME/content type
-   size
-   creation/modification metadata where available
-   SHA-256 or approved cryptographic hash
-   classification
-   processing status

------------------------------------------------------------------------

# 7. Excel Requirements

## 7.1 Production Excel is immutable

The system must never:

-   add columns
-   delete columns
-   rename columns
-   reorder columns
-   overwrite values
-   change business formatting
-   modify the source workbook

The workbook is read-only input.

## 7.2 Internal canonical representation

The application may normalize the workbook internally.

Recommended internal object:

``` json
{
  "document_id": "DOC-...",
  "utility_name": "...",
  "utility_type": "...",
  "source_file": "...",
  "source_file_hash": "...",
  "index_status": "...",
  "claimed_warning_code": "...",
  "claimed_warning_text": "...",
  "warning_severity": "...",
  "aoi_reference": "...",
  "legend_reference": "...",
  "upstream_model_version": "...",
  "upstream_confidence": null
}
```

## 7.3 Every row must be accounted for

Every index row must end in one of:

-   `PROCESSED`
-   `BLOCKED`
-   `EXPLICITLY_EXCLUDED`

No silent skipping.

## 7.4 Excel validation

Validate:

-   required columns
-   data types
-   empty required values
-   duplicate records
-   unsupported utility types
-   inconsistent status values
-   invalid warning values
-   missing references

------------------------------------------------------------------------

# 8. File Classification Requirements

Every file should receive a classification such as:

``` text
INDEX
MAP
LEGEND
UPSTREAM_OUTPUT
REFERENCE
SERVICE_MAP
SAFETY_REFERENCE
OTHER
UNKNOWN
```

Unknown files must be logged.

Reference files must not accidentally enter the map-validation pipeline
as maps.

------------------------------------------------------------------------

# 9. Document Resolution Requirements

For every index record:

``` text
Index Record
→ Candidate Files
→ Deterministic Matching
→ Unique Document
```

Matching may use:

-   provider
-   utility type
-   job reference
-   scheme/reference
-   filename patterns
-   directory structure
-   configured provider patterns
-   document metadata

## 9.1 Ambiguity

If multiple documents are possible:

``` text
AMBIGUOUS_MAPPING
→ HUMAN_REVIEW or BLOCKED
```

The system must not guess.

## 9.2 Missing document

If no expected document exists:

``` text
MISSING_MAP
→ BLOCKED
```

and the event must be logged.

------------------------------------------------------------------------

# 10. PDF and Document Inspection

Every selected document must be inspected before semantic validation.

## 10.1 Integrity

Check:

-   file readability
-   corruption
-   page count
-   blank pages
-   content type
-   page dimensions
-   orientation
-   permissions where relevant
-   duplicate documents

## 10.2 Modality

Classify document as:

``` text
VECTOR
RASTER
HYBRID
UNKNOWN
```

## 10.3 Native extraction first

Where available, extract:

-   native text
-   words
-   blocks
-   vector paths
-   colors
-   line widths
-   dash patterns
-   images
-   coordinates
-   page geometry
-   metadata

Do not render every page to an image unnecessarily.

## 10.4 Rendering

Render high-resolution images only when required for:

-   CV
-   OCR
-   visual evidence
-   annotation
-   rasterized maps

------------------------------------------------------------------------

# 11. Warning Catalogue Requirements

The supplied warning catalogue is a critical business input.

It should become a versioned registry.

Conceptually:

``` text
Warning Catalogue
├── Provider
├── Utility Type
├── Warning Code
├── Business Warning Text
├── Severity
├── Geometry Type
├── AOI Requirement
├── Detection Methods
├── Legend Profile
└── Active/Inactive
```

## 11.1 Warning definition

Example:

``` json
{
  "warning_code": "SGN_HIGH_PRESSURE_GAS_LINE",
  "provider": "SGN",
  "utility_type": "Gas",
  "severity": "HIGH",
  "geometry_type": "LINE",
  "aoi_required": true
}
```

## 11.2 Preserve original wording

Store both:

``` text
claimed_warning_text
```

and:

``` text
canonical_warning_code
```

Do not silently rewrite business wording.

## 11.3 Severity

Severity must come from the approved business catalogue.

The CV/AI system must not invent severity.

------------------------------------------------------------------------

# 12. Legend Resolution

Legend interpretation is mandatory before treating a visual feature as a
warning.

## 12.1 Legend sources

Priority should be configurable, for example:

1.  Embedded authoritative provider legend
2.  Approved external provider legend
3.  Approved symbol guide
4.  Other explicitly approved reference

## 12.2 Legend profile

A legend profile should contain:

``` text
Provider
Map Type
Version
Source
Source Hash
Effective Date
Color Signature
Line Signature
Dash Signature
Width Signature
Symbol Signature
Text Labels
Detection Rules
```

## 12.3 Missing legend

If a required legend cannot be resolved:

``` text
LEGEND_UNAVAILABLE
→ no AUTO_CLEAR
→ HUMAN_REVIEW or BLOCKED
```

## 12.4 No invented semantics

The system must never say:

``` text
red = gas
```

unless supported by the authoritative legend/rule profile.

------------------------------------------------------------------------

# 13. AOI / Digsite Requirements

The AOI is a first-class object.

## 13.1 AOI representations

Support, where applicable:

-   circle
-   polygon
-   buffered line
-   selected region
-   vector boundary
-   rasterized boundary

## 13.2 Detection priority

Prefer:

1.  native vector geometry
2.  explicit map geometry
3.  approved external AOI source
4.  CV/segmentation
5.  other approved methods

## 13.3 AOI record

Recommended:

``` json
{
  "aoi_id": "AOI-123",
  "document_id": "DOC-123",
  "page": 1,
  "geometry": "...",
  "method": "native_vector",
  "confidence": 0.99,
  "valid": true
}
```

## 13.4 Boundary tolerance

Boundary tolerance must be explicit and provider/map-scale aware.

It must not be an arbitrary universal value.

## 13.5 Missing/ambiguous AOI

If AOI is mandatory:

``` text
AOI_MISSING / AOI_AMBIGUOUS
→ no AUTO_CLEAR
```

------------------------------------------------------------------------

# 14. Upstream Warning Integration

The system is downstream from the upstream AI/image-processing system.

## 14.1 Required upstream data

The integration should support, where available:

-   document/map ID
-   warning code/type
-   warning text
-   severity if provided
-   location
-   bounding box
-   polygon/mask
-   confidence
-   model version
-   timestamp
-   source output reference

## 14.2 No-warning case

An upstream result of:

``` text
NO WARNING
```

must not be treated as proof that the map is clean.

It must trigger independent validation.

------------------------------------------------------------------------

# 15. Independent Warning Discovery

This is the core safety mechanism.

For each supported provider and relevant warning class:

``` text
Map
→ Provider Rules
→ Warning Catalogue
→ Legend
→ AOI
→ Independent Detection
```

The system should search for:

-   expected warnings
-   unexpected/mismatched warning candidates
-   missed warnings
-   duplicate warnings
-   conflicting warnings

## 15.1 Candidate retention

Low-confidence candidates should not simply disappear.

They should be retained as evidence and may trigger human review.

------------------------------------------------------------------------

# 16. Computer Vision Requirements

Use a layered strategy.

## 16.1 Level 1 --- Native PDF/vector

Use when reliable.

Detect:

-   line geometry
-   color
-   width
-   dash pattern
-   vector symbols
-   text
-   coordinates

## 16.2 Level 2 --- Classical CV

Use:

-   RGB/HSV/LAB
-   color tolerance
-   thresholding
-   connected components
-   contours
-   morphology
-   line/segment detection
-   line width analysis
-   dash analysis
-   symbol/template detection

Never rely on exact RGB equality alone.

## 16.3 Level 3 --- OCR

Use for:

-   rasterized legends
-   map labels
-   annotations
-   warning text

Retain:

-   text
-   bounding box
-   confidence
-   page

Low-confidence OCR must not be sole release evidence.

## 16.4 Level 4 --- ML/Deep Learning

Use only where simpler methods are insufficient.

Possible uses:

-   segmentation
-   object detection
-   symbol recognition
-   difficult raster map interpretation

The model must be provider/domain appropriate.

------------------------------------------------------------------------

# 17. Spatial Validation Requirements

Detected features should be converted into geometry whenever possible.

Required operations may include:

``` text
INTERSECTS
CONTAINS
WITHIN
DISTANCE
TOUCHES
OVERLAPS
CROSSES
```

Provider-specific topology may include:

-   connectivity
-   network relationships
-   impossible geometry
-   conflicting asset relationships

All spatial results must retain:

-   geometry
-   coordinate reference
-   tolerance
-   method
-   source evidence

------------------------------------------------------------------------

# 18. Coordinate System Requirements

The system should preserve transformations between:

``` text
PDF Coordinates
→ Rendered Pixel Coordinates
→ Map Coordinates
```

Where applicable, preserve:

-   PDF page coordinate system
-   image coordinate system
-   map/grid coordinate system
-   transformation matrix
-   scale
-   units
-   CRS if known

Do not discard coordinate information.

------------------------------------------------------------------------

# 19. Warning Validation

Every upstream warning should be independently evaluated.

Possible per-warning states:

``` text
VALID
INVALID
UNCERTAIN
NOT_FOUND
```

Recommended extended internal classifications:

``` text
VALID_WARNING
FALSE_POSITIVE
MISSED_WARNING
WARNING_TYPE_MISMATCH
DUPLICATE_WARNING
UNCERTAIN_WARNING
OUTSIDE_AOI
```

The final business-facing state can be mapped to the approved output
contract.

------------------------------------------------------------------------

# 20. Warning Reconciliation

Example:

``` text
Upstream:
HV Cable

Independent:
HV Cable
```

Result:

``` text
VALID_WARNING
```

Example:

``` text
Upstream:
No warning

Independent:
HV Cable
```

Result:

``` text
MISSED_WARNING
→ HUMAN_REVIEW
```

Example:

``` text
Upstream:
HV Cable

Independent:
No supporting evidence
```

Result:

``` text
POSSIBLE_FALSE_POSITIVE
```

The exact release consequence is determined by policy.

------------------------------------------------------------------------

# 21. Evidence Engine

Every decision must have evidence.

## 21.1 Evidence types

Possible evidence:

-   source file
-   file hash
-   page
-   AOI geometry
-   legend reference
-   legend version
-   claimed warning
-   detected warning
-   vector evidence
-   color/style evidence
-   OCR evidence
-   CV evidence
-   spatial evidence
-   rule result
-   model version
-   configuration version
-   confidence/calibration
-   decision reason

## 21.2 Evidence ID

Every evidence object should have a stable identifier.

Example:

``` text
E-000123
```

## 21.3 Evidence package

Recommended structure:

``` text
evidence/
├── E-000123.json
├── E-000124.json
├── E-000125.png
├── E-000126.png
└── ...
```

------------------------------------------------------------------------

# 22. Evidence Fusion

The system should combine independent evidence.

Example:

``` text
Legend match          PASS
Vector style          PASS
Color match            PASS
AOI intersection       PASS
Spatial validation     PASS
OCR/context            PASS
Independent detector   PASS
Upstream warning       PRESENT
```

This supports:

``` text
VALID_WARNING
```

Negative/no-warning decisions require stronger completeness because a
missed warning can escape to the client.

The system must record which independent searches were actually
performed and their results.

------------------------------------------------------------------------

# 23. Confidence Model

Do not use one generic confidence value.

Use separate concepts:

### Detection confidence

How likely the detected feature is actually present.

### Semantic confidence

How likely the feature corresponds to the intended warning class.

### Evidence completeness

Whether all mandatory validation procedures were completed.

### Release eligibility

A deterministic policy result, not a probability.

Example:

``` text
Detection confidence:     0.97
Semantic confidence:      0.94
Evidence completeness:    0.72

Final:
HUMAN_REVIEW
```

------------------------------------------------------------------------

# 24. Deterministic Policy Engine

The policy engine is authoritative for release.

## 24.1 AUTO_CLEAR

Only when all mandatory gates pass.

Minimum gates:

1.  Index record valid
2.  Expected map exists
3.  Map opens
4.  Mapping is correct
5.  Provider identified
6.  Required legend resolved
7.  Required AOI resolved
8.  AOI validation completed
9.  Independent warning scan completed
10. Upstream reconciliation completed
11. No unresolved critical warning
12. No unresolved detector/model disagreement
13. No critical image-quality issue
14. Provider rules pass
15. Evidence package generated
16. Audit record persisted
17. Release policy permits auto-clear

## 24.2 HUMAN_REVIEW

Examples:

-   confirmed warning
-   possible missed warning
-   contradictory evidence
-   detector disagreement
-   ambiguous legend
-   poor image quality
-   high-risk case
-   AOI ambiguity
-   insufficient evidence
-   policy-required human review

## 24.3 BLOCKED

Examples:

-   missing map
-   corrupt PDF
-   unsupported format
-   unsupported provider
-   required legend unavailable
-   required AOI unavailable
-   infrastructure failure
-   unrecoverable processing failure

------------------------------------------------------------------------

# 25. QA Agent / LLM Requirements

The LLM is an optional reasoning layer.

## 25.1 Allowed responsibilities

The QA Agent may:

-   summarize structured evidence
-   explain contradictions
-   interpret structured evidence
-   recommend which validation tool to run next
-   recommend escalation
-   generate human-readable case explanations
-   summarize a complex QA case
-   assist reviewer investigation
-   classify the reason for escalation
-   suggest likely interpretation for ambiguous evidence

## 25.2 Prohibited responsibilities

The LLM must not:

-   invent map evidence
-   invent a legend
-   invent warning definitions
-   invent severity
-   invent coordinates
-   claim a detector ran when it did not
-   override policy gates
-   automatically clear a critical case
-   convert uncertainty into PASS
-   be the sole basis for release

## 25.3 LLM input contract

The QA Agent should primarily receive structured evidence:

``` json
{
  "document": {...},
  "provider": "...",
  "legend": {...},
  "aoi": {...},
  "warnings": [...],
  "detections": [...],
  "spatial_results": [...],
  "policy_results": [...],
  "evidence_ids": [...]
}
```

It should not be allowed to freely invent missing information.

------------------------------------------------------------------------

# 26. Human QA Workflow

Human QA is a deliberate safety layer.

Flow:

``` text
Validation
→ QA Case
→ Priority
→ Skill Matching
→ Severity/SLA
→ Availability
→ Workload
→ Reviewer
→ Review
→ Decision
→ Audit
```

## 26.1 Reviewer should receive

-   original map
-   page
-   AOI
-   claimed warning
-   detected warning
-   legend
-   evidence crops
-   spatial result
-   reason for escalation
-   upstream result
-   independent result

## 26.2 Human decisions

Subject to business confirmation, support:

-   approve
-   reject
-   confirm warning
-   remove false warning
-   add missed warning
-   correct warning type
-   correct severity
-   add comment
-   request further review

------------------------------------------------------------------------

# 27. QA Assignment Requirements

Assignment should be deterministic and auditable.

Inputs:

``` text
Utility/domain
+
Warning type
+
Severity
+
SLA
+
Required skill
+
Reviewer availability
+
Current workload
+
Case complexity
```

Output:

``` text
Qualified QA Reviewer
```

An LLM may help classify the case, but assignment policy must remain
deterministic.

------------------------------------------------------------------------

# 28. Audit Requirements

Every decision must create an immutable/auditable record.

Record at minimum:

``` text
JobID
DocumentID
IndexRecordID
SourceFileHash
Provider
UtilityType
WarningCode
WarningSeverity
LegendVersion
AOIVersion/Method
ParserVersion
CVVersion
OCRVersion
ModelVersion
RuleVersion
AgentVersion
UpstreamResult
IndependentResult
EvidenceIDs
Decision
DecisionReason
Timestamp
Reviewer
HumanDisposition
```

------------------------------------------------------------------------

# 29. Reproducibility Requirements

Given:

``` text
same source file
+
same configuration versions
+
same rule versions
+
same provider profile
```

the system must be able to reproduce or explain the historical decision.

Historical decisions must not depend on mutable external state without
recording the relevant version.

------------------------------------------------------------------------

# 30. Persistence Requirements

Recommended entities:

``` text
Job
Document
DocumentPage
IndexRecord
DocumentMapping
Provider
WarningDefinition
LegendProfile
AOI
Detection
Warning
Evidence
ValidationResult
Decision
QATask
AuditEvent
FeedbackRecord
ModelVersion
RuleVersion
DatasetVersion
```

------------------------------------------------------------------------

# 31. Recommended Database

Recommended:

``` text
PostgreSQL
+
PostGIS
```

PostGIS should hold:

-   geometries
-   AOIs
-   detected infrastructure
-   spatial relationships
-   spatial evidence

Object storage should hold:

-   original PDFs
-   rendered pages
-   crops
-   annotated maps
-   OCR artifacts
-   evidence images

------------------------------------------------------------------------

# 32. Recommended Technology Stack

  Area                       Recommended Technology
  -------------------------- ----------------------------------------------
  Language                   Python
  API                        FastAPI
  Validation models          Pydantic
  PDF processing             PyMuPDF
  CV                         OpenCV
  Numerical processing       NumPy
  OCR                        Approved OCR engine such as PaddleOCR
  Geometry                   Shapely
  Spatial DB                 PostgreSQL + PostGIS
  Database ORM               SQLAlchemy
  Queue                      RabbitMQ or approved equivalent
  Cache                      Redis
  Object storage             S3-compatible storage
  Workflow                   Durable workflow/orchestration layer
  LLM/QA Agent               Approved enterprise LLM only where permitted
  Containers                 Docker
  Production orchestration   Kubernetes where justified
  Monitoring                 Prometheus/Grafana
  Tracing                    OpenTelemetry
  Logging                    Centralized structured logging
  CI/CD                      Enterprise-approved pipeline

The final choice must follow company infrastructure/security
constraints.

------------------------------------------------------------------------

# 33. Recommended System Components

``` text
1. API Gateway
2. Job Manager
3. Ingestion Service
4. File Inventory Service
5. Index Processor
6. Document Resolver
7. PDF Inspector
8. Legend Registry
9. Legend Resolver
10. AOI Service
11. Warning Catalogue Service
12. Vector Analysis Service
13. CV Service
14. OCR Service
15. Spatial Validation Service
16. Warning Validator
17. Evidence Engine
18. Reconciliation Engine
19. Policy Engine
20. Decision Engine
21. QA Assignment Service
22. QA Agent
23. Human QA UI
24. Audit Service
25. Feedback/Evaluation Service
26. Reporting Service
27. Monitoring/Observability
```

------------------------------------------------------------------------

# 34. Orchestration Architecture

The orchestrator manages workflow state.

Example:

``` text
JOB_CREATED
→ INGESTING
→ INDEX_VALIDATED
→ DOCUMENTS_RESOLVED
→ DOCUMENTS_INSPECTED
→ LEGENDS_RESOLVED
→ AOI_RESOLVED
→ UPSTREAM_LOADED
→ INDEPENDENT_SCAN
→ RECONCILIATION
→ EVIDENCE_COMPLETE
→ POLICY_EVALUATION
→ DECISION
```

The orchestrator must support:

-   state persistence
-   retries
-   resumability
-   idempotency
-   parallel document processing
-   dependency management
-   human pause/resume
-   error handling

------------------------------------------------------------------------

# 35. Idempotency

Reprocessing the same unchanged document should not create uncontrolled
duplicate work.

Use:

``` text
File Hash
+
Configuration Version
+
Provider Rule Version
```

to identify equivalent processing.

If input is unchanged, the system should be able to reuse approved
artifacts where policy allows.

------------------------------------------------------------------------

# 36. Error Handling

Each failure must have a structured error code.

Examples:

``` text
ERR_ROOT_NOT_FOUND
ERR_INDEX_MISSING
ERR_INDEX_INVALID
ERR_DOCUMENT_MISSING
ERR_DOCUMENT_AMBIGUOUS
ERR_PDF_CORRUPT
ERR_UNSUPPORTED_FORMAT
ERR_PROVIDER_UNKNOWN
ERR_LEGEND_MISSING
ERR_AOI_MISSING
ERR_AOI_AMBIGUOUS
ERR_CV_FAILED
ERR_OCR_FAILED
ERR_SPATIAL_FAILED
ERR_EVIDENCE_INCOMPLETE
ERR_POLICY_BLOCKED
ERR_INFRASTRUCTURE_FAILURE
```

Errors must be logged and surfaced appropriately.

------------------------------------------------------------------------

# 37. Security Requirements

Because utility/engineering maps can represent sensitive infrastructure,
security must be treated as a first-class requirement.

Minimum requirements:

-   authentication
-   authorization
-   RBAC
-   least privilege
-   encryption in transit
-   encryption at rest
-   secure object storage
-   audit logging
-   secure secrets management
-   secure file handling
-   malware/file scanning where required
-   access logging
-   retention policy
-   deletion policy
-   environment isolation

## 37.1 LLM security

If an external LLM is used:

-   company approval is required;
-   data classification must permit it;
-   sensitive map data must not be sent externally without approval;
-   provider/model/version must be recorded;
-   prompts/responses must follow company retention policy.

The core validation system must remain functional without the LLM.

------------------------------------------------------------------------

# 38. Performance Requirements

The system must support asynchronous processing.

A job may contain multiple maps:

``` text
Job
├── SGN
├── ESP
├── GTC
├── UKPN
├── TFL
├── Water
├── BT
└── VM
```

Independent documents should be processed concurrently subject to
controlled resource limits.

Performance targets must be defined after production volume is
confirmed.

Metrics should include:

-   average map processing time
-   P95 processing time
-   P99 processing time
-   queue latency
-   CV latency
-   OCR latency
-   PDF extraction latency
-   database latency

------------------------------------------------------------------------

# 39. Testing Strategy

Testing must be treated as a software engineering discipline, not only
an AI experiment.

## 39.1 Unit tests

Test:

-   Excel parsing
-   normalization
-   file classification
-   document matching
-   hash generation
-   PDF extraction
-   legend matching
-   AOI geometry
-   CV functions
-   OCR normalization
-   spatial predicates
-   warning mapping
-   policy rules
-   QA assignment

## 39.2 Integration tests

Test:

``` text
Root Folder
→ Index
→ Resolver
→ PDF
→ Legend
→ AOI
→ Detection
→ Spatial
→ Evidence
→ Policy
→ Decision
```

## 39.3 End-to-end tests

Run complete representative jobs from real sample folders.

## 39.4 Failure tests

Simulate:

-   missing index
-   missing map
-   duplicate map
-   corrupted PDF
-   missing legend
-   ambiguous legend
-   missing AOI
-   ambiguous AOI
-   OCR failure
-   CV failure
-   database failure
-   queue failure
-   object storage failure
-   worker crash
-   retry
-   timeout

------------------------------------------------------------------------

# 40. Golden Dataset

Before enabling production AUTO_CLEAR, create a locked gold-standard
dataset reviewed by experienced domain QA engineers.

Include:

-   warning-present maps
-   genuinely clean maps
-   upstream false positives
-   upstream missed warnings
-   faded colors
-   broken lines
-   clutter
-   overlapping infrastructure
-   ambiguous symbols
-   missing legends
-   changed legends
-   raster maps
-   vector maps
-   hybrid maps
-   multi-page maps
-   AOI edge cases
-   boundary cases
-   difficult legacy drawings

Dataset splits must avoid leakage across the same source/document
family.

------------------------------------------------------------------------

# 41. Regression Testing

Every change to:

-   provider rules
-   legend profiles
-   CV algorithms
-   OCR
-   spatial logic
-   warning catalogue
-   policy
-   models
-   agent prompts/logic

must run the regression suite.

A critical regression must block release.

------------------------------------------------------------------------

# 42. Evaluation Metrics

Primary safety metric:

## Auto-clear escape rate

Definition:

> A real warning exists, but the system incorrectly produces AUTO_CLEAR.

This is more important than generic accuracy.

Other metrics:

-   warning recall
-   warning precision
-   false-negative rate
-   false-positive rate
-   auto-clear rate
-   human-review rate
-   blocked rate
-   AOI detection accuracy
-   legend resolution accuracy
-   OCR accuracy
-   processing latency
-   system failure rate
-   human override rate
-   decision reproducibility
-   QA time saved

------------------------------------------------------------------------

# 43. Production Acceptance Criteria

The system is not production-ready until all of the following are true:

-   Every index row maps to a document or is explicitly blocked.
-   Every processed map receives a deterministic status.
-   Every warning decision has evidence.
-   Every AUTO_CLEAR satisfies all mandatory release gates.
-   No unresolved critical warning can pass AUTO_CLEAR.
-   Human QA receives exact evidence and escalation reason.
-   Human corrections are recorded.
-   Model/rule/legend versions are recorded.
-   Historical decisions are reproducible.
-   Gold-standard performance meets company-approved risk targets.
-   Security approval is complete.
-   Data-retention approval is complete.
-   Monitoring is operational.
-   Incident response is operational.
-   Regression tests are passing.
-   Failure/recovery tests are passing.

------------------------------------------------------------------------

# 44. Provider Architecture

Provider-specific logic must be modular.

Recommended interface:

``` python
class ProviderValidator:
    def identify(self, document): ...
    def resolve_legend(self, document): ...
    def detect_aoi(self, document): ...
    def get_warning_definitions(self): ...
    def detect_candidates(self, document, aoi): ...
    def validate_warning(self, warning, evidence): ...
    def get_policy_context(self): ...
```

Providers can then implement:

``` text
SGN
ESP Utilities Group
GTC
UKPN
TFL
Clean Water
Waste Water
BT
VM
...
```

Do not create one giant conditional implementation.

------------------------------------------------------------------------

# 45. Provider Validation Pipeline

For each provider:

``` text
Provider
↓
Provider Configuration
↓
Warning Catalogue
↓
Legend Profile
↓
AOI Strategy
↓
Detection Strategy
↓
Spatial Rules
↓
Evidence Requirements
↓
Release Policy
```

------------------------------------------------------------------------

# 46. Initial Provider Strategy

The supplied specification recommends beginning with a representative
subset.

Recommended pilot:

1.  SGN
2.  UKPN
3.  Clean Water

Then:

4.  ESP
5.  GTC
6.  TFL
7.  Waste Water
8.  BT
9.  VM
10. Additional providers

This sequence exercises different combinations of vector/raster content,
legends, external references, line styles, symbols, and warning
semantics.

------------------------------------------------------------------------

# 47. Development Phases

## Phase 0 --- Requirements Freeze

Finalize:

-   production Excel semantics
-   warning catalogue
-   provider list
-   severity
-   critical warnings
-   AOI source
-   legend authority
-   upstream interface
-   release policy
-   human QA rules
-   security
-   deployment
-   scale
-   acceptance thresholds

## Phase 1 --- Deterministic Foundation

Build:

-   repository
-   configuration
-   root-folder inventory
-   Excel reader
-   canonical schema
-   document resolver
-   PDF inspector
-   structured logging

Output:

``` text
qa_output/
├── job_report.json
├── document_results.json
├── evidence/
├── annotated_maps/
└── logs/
```

## Phase 2 --- PDF/Legend/AOI

Build:

-   native extraction
-   vector extraction
-   raster classification
-   legend registry
-   legend resolver
-   AOI detector
-   geometry normalization

## Phase 3 --- First Provider

Implement SGN end-to-end.

## Phase 4 --- Independent Warning Discovery

Implement:

-   vector detection
-   CV
-   OCR
-   spatial validation
-   warning reconciliation

## Phase 5 --- Evidence + Policy

Implement:

-   evidence engine
-   deterministic decision engine
-   AUTO_CLEAR/HUMAN_REVIEW/BLOCKED
-   audit

## Phase 6 --- Human QA

Implement:

-   QA task
-   evidence viewer
-   reviewer assignment
-   human disposition
-   feedback capture

## Phase 7 --- QA Agent / LLM

Add optional LLM functionality for:

-   case summarization
-   contradiction explanation
-   evidence interpretation
-   escalation reasoning
-   reviewer assistance

## Phase 8 --- Evaluation

Build:

-   gold dataset
-   regression framework
-   metrics
-   calibration
-   failure analysis

## Phase 9 --- Pilot

Run a controlled production-like pilot.

## Phase 10 --- Scale

Add additional providers only after the common framework is stable.

------------------------------------------------------------------------

# 48. First Development Deliverable

The first working deliverable should be a deterministic pipeline.

Input:

``` text
root_folder/
```

Output:

``` text
qa_output/
├── job_report.json
├── document_results.json
├── evidence/
├── annotated_maps/
└── logs/
```

For every Excel record:

``` text
Locate map
→ Validate mapping
→ Validate document
→ Inspect PDF
→ Resolve legend
→ Resolve AOI
→ Run warning checks
→ Produce result
```

This should work without an LLM.

------------------------------------------------------------------------

# 49. Recommended Internal Decision Model

Example:

``` json
{
  "document_id": "DOC-123",
  "status": "HUMAN_REVIEW",
  "warnings": [
    {
      "code": "HV_CABLE_PRESENT",
      "upstream": false,
      "discovered": true,
      "validation": "CONFIRMED",
      "severity": "HIGH",
      "page": 1,
      "aoi_intersection": true,
      "evidence_ids": [
        "E-001",
        "E-002"
      ]
    }
  ],
  "gates": {
    "index_valid": true,
    "map_exists": true,
    "mapping_valid": true,
    "legend_resolved": true,
    "aoi_resolved": true,
    "independent_scan_completed": true,
    "reconciliation_completed": true,
    "evidence_complete": true,
    "critical_issue": false,
    "auto_clear_allowed": false
  },
  "reason": "Independent QA detected a warning not present in the upstream result."
}
```

------------------------------------------------------------------------

# 50. Output Requirements

## 50.1 Per-map status

Required:

``` text
AUTO_CLEAR
HUMAN_REVIEW
BLOCKED
```

## 50.2 Per-warning result

Required:

``` text
VALID
INVALID
UNCERTAIN
NOT_FOUND
```

with internal extended reason codes as necessary.

## 50.3 Human-readable report

Include:

-   job summary
-   map summary
-   warning summary
-   decision
-   reason
-   evidence
-   QA disposition

## 50.4 Machine-readable output

JSON should contain:

-   IDs
-   statuses
-   warning codes
-   severity
-   evidence IDs
-   geometry references
-   rule results
-   versions
-   decision reason

------------------------------------------------------------------------

# 51. Example End-to-End Scenario

``` text
Root Folder
↓
Discover 30 PDFs + Excel + references
↓
Read Excel
↓
Identify SGN record
↓
Resolve 42336412_SGN.pdf
↓
PDF is valid/vector-rich
↓
Resolve SGN legend
↓
Detect AOI
↓
Load upstream result:
No warning
↓
Independent vector scan
↓
Detect SGN line
↓
Legend confirms line type
↓
Spatial intersection with AOI = TRUE
↓
Warning catalogue confirms warning class
↓
Evidence package created
↓
Upstream vs independent:
NO WARNING vs WARNING
↓
MISSED_WARNING
↓
Policy:
No AUTO_CLEAR
↓
HUMAN_REVIEW
↓
QA reviewer confirms
↓
Final disposition
↓
Audit record
↓
Feedback dataset
```

------------------------------------------------------------------------

# 52. Critical Safety Rules

These rules must be implemented as hard constraints.

### Rule 1

Never auto-clear solely because the model confidence is high.

### Rule 2

Never treat "no upstream warning" as "no warning."

### Rule 3

Never invent missing legends.

### Rule 4

Never invent warning definitions.

### Rule 5

Never assume one provider's visual conventions apply to another.

### Rule 6

Never silently skip an index row.

### Rule 7

Never guess ambiguous document mappings.

### Rule 8

Never allow unresolved critical warnings to AUTO_CLEAR.

### Rule 9

Never allow unresolved mandatory AOI/legend issues to AUTO_CLEAR.

### Rule 10

Never allow an LLM to override mandatory policy gates.

### Rule 11

Never automatically retrain production models from a single human
correction.

### Rule 12

Never release production AUTO_CLEAR functionality before locked
evaluation.

------------------------------------------------------------------------

# 53. Observability Requirements

Track:

### System metrics

-   jobs received
-   jobs completed
-   jobs failed
-   queue depth
-   worker health
-   CPU
-   memory
-   GPU
-   storage
-   database health

### QA metrics

-   maps processed
-   AUTO_CLEAR %
-   HUMAN_REVIEW %
-   BLOCKED %
-   warning recall
-   warning precision
-   false-negative rate
-   false-positive rate
-   escape rate
-   human override %
-   AOI accuracy
-   legend accuracy

### Performance

-   average latency
-   P95 latency
-   P99 latency
-   provider-specific latency

### Reliability

-   retry rate
-   timeout rate
-   tool failure rate
-   infrastructure failure rate

------------------------------------------------------------------------

# 54. Data Retention

The production design must define retention for:

-   source documents
-   evidence
-   audit events
-   QA decisions
-   model outputs
-   feedback data
-   logs

Retention periods must be configurable according to company policy.

------------------------------------------------------------------------

# 55. Configuration Management

Do not hard-code business rules.

Configuration should include:

``` text
providers
warning catalogue
severity
legend profiles
AOI rules
spatial tolerance
detection profiles
release policy
QA skills
SLA
feature flags
```

Every production decision must reference the configuration version.

------------------------------------------------------------------------

# 56. Change Management

Changes to any of the following require controlled release:

-   warning catalogue
-   severity
-   legend
-   provider rules
-   spatial tolerance
-   CV algorithm
-   OCR configuration
-   ML model
-   QA Agent logic
-   release policy

Required process:

``` text
Change
→ Unit Tests
→ Integration Tests
→ Gold Dataset
→ Regression
→ Risk Review
→ Approval
→ Version
→ Deploy
→ Monitor
```

------------------------------------------------------------------------

# 57. Incident Management

The system must support operational investigation.

For every production issue, operators should be able to identify:

``` text
Job
→ Document
→ File Hash
→ Processing Version
→ Evidence
→ Rules
→ Decision
→ Reviewer
```

Critical incidents should be traceable end-to-end.

------------------------------------------------------------------------

# 58. Requirements Still Requiring Business Confirmation

The following are intentionally not guessed:

1.  Exact production Excel columns and semantics.
2.  Exact meaning of `Status`.
3.  Exact meaning of blank `Warning`.
4.  Exact upstream warning interface.
5.  Whether upstream provides coordinates/masks.
6.  Authoritative AOI source.
7.  AOI boundary tolerance.
8.  Exact warning catalogue authority.
9.  Critical warning definitions.
10. Exact AUTO_CLEAR eligibility by severity/provider.
11. Mandatory HUMAN_REVIEW conditions.
12. Mandatory evidence for no-warning decisions.
13. Legend authority and version lifecycle.
14. Native vector trust policy.
15. Production map volume.
16. Maximum processing latency.
17. Deployment environment.
18. LLM/data-security restrictions.
19. Data retention requirements.
20. QA team/skill matrix.
21. QA assignment policy.
22. Approved escaped-warning rate.

These should be resolved before full production build.

------------------------------------------------------------------------

# 59. Recommended Final Architecture

``` text
                         ROOT FOLDER
                              |
                              v
                   INGESTION & INVENTORY
                              |
                              v
                       INDEX PROCESSOR
                              |
                              v
                     DOCUMENT RESOLVER
                              |
                              v
                       PDF INSPECTOR
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          WARNING CATALOGUE          LEGEND REGISTRY
          Business Truth             Map Semantics
                 |                         |
                 +------------+------------+
                              |
                              v
                         AOI SERVICE
                              |
                              v
                  INDEPENDENT MAP QA
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
          VECTOR             CV               OCR
             |                |                |
             +----------------+----------------+
                              |
                              v
                    SPATIAL VALIDATION
                              |
                              v
                    WARNING DISCOVERY
                              |
               +--------------+--------------+
               |                             |
               v                             v
       UPSTREAM WARNINGS             INDEPENDENT FINDINGS
               |                             |
               +--------------+--------------+
                              |
                              v
                      RECONCILIATION
                              |
                              v
                       EVIDENCE ENGINE
                              |
                              v
                       POLICY ENGINE
                              |
               +--------------+--------------+
               |              |              |
               v              v              v
          AUTO_CLEAR      HUMAN_REVIEW     BLOCKED
                              |
                              v
                         QA AGENT
                       (Optional LLM)
                              |
                              v
                         HUMAN QA
                              |
                              v
                     FINAL DISPOSITION
                              |
                              v
                    OUTPUT + AUDIT TRAIL
                              |
                              v
                  FEEDBACK / EVALUATION
```

------------------------------------------------------------------------

# 60. Final Definition of the Product

The finished system should be understood as:

> **A production-grade, evidence-based, independent QA platform for
> utility/engineering maps. It receives a root folder, validates the
> existing index and documents, resolves provider-specific legends and
> AOIs, independently discovers predefined warning conditions using
> PDF/vector analysis, CV, OCR and spatial reasoning, reconciles those
> findings with upstream warnings, aggregates auditable evidence,
> applies deterministic safety policy, and produces AUTO_CLEAR,
> HUMAN_REVIEW or BLOCKED outcomes. An optional LLM-powered QA Agent
> assists with reasoning and human-review workflows but cannot override
> safety-critical deterministic gates.**

------------------------------------------------------------------------

# 61. Golden Engineering Principle

The safest architecture is not one giant AI model.

It is:

``` text
SOURCE
  ↓
INDEX VALIDATION
  ↓
FILE VALIDATION
  ↓
PDF/VECTOR EXTRACTION
  ↓
WARNING CATALOGUE
  ↓
LEGEND RESOLUTION
  ↓
AOI VALIDATION
  ↓
INDEPENDENT WARNING DISCOVERY
  ↓
CLAIMED WARNING VALIDATION
  ↓
SPATIAL/RULE VALIDATION
  ↓
EVIDENCE FUSION
  ↓
RISK/POLICY GATE
  ↓
AUTO_CLEAR / HUMAN_REVIEW / BLOCKED
  ↓
AUDIT
  ↓
FEEDBACK
```

The QA Agent sits above these capabilities as an orchestration and
reasoning layer.

**Deterministic release gates remain authoritative.**

------------------------------------------------------------------------

# 62. Definition of Done

The project is considered complete only when:

-   production requirements are frozen;
-   warning catalogue is approved;
-   provider rules are approved;
-   AOI policy is approved;
-   legend registry is approved;
-   upstream integration is stable;
-   deterministic validation works;
-   independent warning discovery works;
-   evidence is generated for every decision;
-   human QA workflow works;
-   QA Agent assistance is bounded and auditable;
-   AUTO_CLEAR gates are deterministic;
-   gold-standard evaluation passes;
-   critical false-negative/escape targets pass;
-   security approval is complete;
-   observability is operational;
-   incident response is operational;
-   historical decisions are reproducible;
-   controlled deployment is complete;
-   pilot results meet business acceptance criteria.

**Production readiness must be demonstrated through measurable
evaluation, not through a successful demo.**
