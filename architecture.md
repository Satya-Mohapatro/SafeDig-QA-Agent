# AI Map QA & Validation Agent

## Production Architecture Document

**Document:** `architecture.md`\
**Architecture Type:** Production-grade enterprise
AI/CV/document-intelligence QA platform\
**Primary architectural objective:** Independently validate
utility/engineering map warnings while minimizing escaped real warnings
and preserving deterministic release safety.

------------------------------------------------------------------------

# 1. Architecture Summary

The **AI Map QA & Validation Agent** is a downstream, independent QA
platform.

An existing upstream AI/image-processing system generates maps and/or
warning information. This platform does **not** replace that upstream
system. It independently inspects the source maps, validates claimed
warnings, searches for missed warnings, resolves provider-specific
legends and AOIs, builds evidence, and applies deterministic release
policy.

The architecture is deliberately **not LLM-centric**.

The safety-critical path is based on:

-   native PDF analysis;
-   vector extraction;
-   computer vision;
-   OCR;
-   geometry/spatial analysis;
-   provider-specific warning definitions;
-   authoritative legends;
-   deterministic rules;
-   evidence aggregation;
-   deterministic release gates.

An optional **QA Agent / LLM** sits above these capabilities and assists
with:

-   orchestration;
-   evidence summarization;
-   contradiction analysis;
-   explanation;
-   reviewer assistance;
-   recommended next actions.

The LLM cannot override mandatory validation or release gates.

------------------------------------------------------------------------

# 2. Golden Architecture Principle

> **The safest production system is a layered verification system, not
> one large AI model. Different mechanisms independently check different
> failure modes.**

``` text
ROOT FOLDER
     |
     v
INDEX + FILE VALIDATION
     |
     v
DOCUMENT RESOLUTION
     |
     v
PDF / IMAGE INSPECTION
     |
     +-------------------------------+
     |                               |
     v                               v
WARNING CATALOGUE               LEGEND REGISTRY
(Business Truth)                (Map Semantics)
     |                               |
     +---------------+---------------+
                     |
                     v
                AOI SERVICE
                     |
                     v
          INDEPENDENT MAP ANALYSIS
                     |
          +----------+----------+
          |          |          |
          v          v          v
       VECTOR       CV         OCR
          |          |          |
          +----------+----------+
                     |
                     v
             SPATIAL VALIDATION
                     |
                     v
             WARNING DISCOVERY
                     |
          +----------+----------+
          |                     |
          v                     v
   UPSTREAM WARNINGS      INDEPENDENT FINDINGS
          |                     |
          +----------+----------+
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
          +----------+----------+
          |          |          |
          v          v          v
     AUTO_CLEAR  HUMAN_REVIEW BLOCKED
                     |
                     v
              QA AGENT / LLM
                     |
                     v
                 HUMAN QA
                     |
                     v
             FINAL DISPOSITION
                     |
                     v
             OUTPUT + AUDIT
                     |
                     v
          FEEDBACK / EVALUATION
```

The architecture follows the supplied project specification's
requirement for independent validation, missed-warning discovery,
provider-specific semantics, evidence, risk/policy gates, human
escalation, auditability, and controlled feedback.

------------------------------------------------------------------------

# 3. High-Level System Context

``` text
                         +----------------------+
                         |      INPUT WORLD     |
                         |                      |
                         | Root Folder          |
                         | Excel Index          |
                         | Map PDFs              |
                         | Legends              |
                         | References            |
                         | Upstream Results      |
                         +----------+-----------+
                                    |
                                    v
                 +----------------------------------------+
                 |       AI MAP QA PLATFORM                |
                 |                                        |
                 |  Ingestion / Processing / Validation   |
                 |  Evidence / Policy / QA                |
                 +----------------+-----------------------+
                                  |
                +-----------------+------------------+
                |                 |                  |
                v                 v                  v
          AUTO_CLEAR        HUMAN QA            BLOCKED
                |                 |                  |
                v                 v                  v
             Release          Review             Operations
                |
                v
             Client

Additional supporting systems:

Configuration / Warning Catalogue / Legend Registry
Database / Object Storage
Queue / Workers
Observability
Audit
Feedback / Evaluation
```

------------------------------------------------------------------------

# 4. Architectural Layers

The platform is divided into the following logical layers.

## Layer 1 --- Input & Ingestion

Responsible for:

-   root-folder discovery;
-   file inventory;
-   file classification;
-   source metadata;
-   hashing;
-   job creation.

## Layer 2 --- Document Understanding

Responsible for:

-   Excel parsing;
-   document resolution;
-   PDF inspection;
-   vector/text/image extraction;
-   raster/vector/hybrid classification.

## Layer 3 --- Domain Semantics

Responsible for:

-   provider identification;
-   warning catalogue;
-   warning ontology;
-   severity;
-   legend registry;
-   AOI definition.

## Layer 4 --- Independent Validation

Responsible for:

-   vector analysis;
-   CV;
-   OCR;
-   symbol detection;
-   warning candidate discovery;
-   geometry generation;
-   spatial validation.

## Layer 5 --- Reconciliation & Evidence

Responsible for:

-   upstream vs independent comparison;
-   evidence aggregation;
-   evidence completeness;
-   traceability.

## Layer 6 --- Decision & Safety

Responsible for:

-   deterministic rules;
-   policy gates;
-   AUTO_CLEAR;
-   HUMAN_REVIEW;
-   BLOCKED.

## Layer 7 --- Human QA & QA Agent

Responsible for:

-   QA case creation;
-   assignment;
-   evidence presentation;
-   LLM-assisted reasoning;
-   human final disposition.

## Layer 8 --- Output & Governance

Responsible for:

-   reports;
-   annotations;
-   audit;
-   metrics;
-   feedback;
-   evaluation;
-   controlled improvement.

------------------------------------------------------------------------

# 5. End-to-End Runtime Architecture

``` text
+----------------+
| Root Folder    |
+-------+--------+
        |
        v
+----------------------+
| Job Manager          |
| Create JobID         |
+----------+-----------+
           |
           v
+----------------------+
| File Inventory       |
| Discover + classify  |
+----------+-----------+
           |
           v
+----------------------+
| Index Processor      |
| Read-only Excel      |
+----------+-----------+
           |
           v
+----------------------+
| Document Resolver    |
+----------+-----------+
           |
           v
+----------------------+
| PDF Inspector        |
+----------+-----------+
           |
      +----+----+
      |         |
      v         v
   Vector     Raster
      |         |
      +----+----+
           |
           v
+----------------------+
| Provider Resolver    |
+----------+-----------+
           |
     +-----+------+
     |            |
     v            v
 Warning       Legend
 Catalogue     Registry
     |            |
     +-----+------+
           |
           v
+----------------------+
| AOI Service          |
+----------+-----------+
           |
           v
+----------------------+
| Independent QA       |
|                      |
| Vector / CV / OCR    |
+----------+-----------+
           |
           v
+----------------------+
| Spatial Validator    |
+----------+-----------+
           |
           v
+----------------------+
| Reconciliation       |
| Upstream vs QA       |
+----------+-----------+
           |
           v
+----------------------+
| Evidence Engine      |
+----------+-----------+
           |
           v
+----------------------+
| Policy Engine        |
+----------+-----------+
           |
     +-----+-----+------+
     |           |      |
     v           v      v
 AUTO_CLEAR  HUMAN_QA  BLOCKED
                 |
                 v
          +--------------+
          | QA Agent     |
          | Optional LLM |
          +------+-------+
                 |
                 v
          Human Reviewer
                 |
                 v
          Final Decision
                 |
                 v
          Output + Audit
```

------------------------------------------------------------------------

# 6. Core Component Architecture

## 6.1 API Gateway

Responsibilities:

-   accept job requests;
-   accept root folder reference;
-   expose job status;
-   expose results;
-   expose QA operations;
-   enforce authentication/authorization.

Example endpoints:

``` text
POST /jobs
GET  /jobs/{job_id}
GET  /jobs/{job_id}/documents
GET  /jobs/{job_id}/results
GET  /jobs/{job_id}/evidence
GET  /qa/tasks
POST /qa/tasks/{task_id}/decision
```

Exact API contracts are to be finalized during implementation.

------------------------------------------------------------------------

# 7. Job Manager

The Job Manager owns the lifecycle of a processing job.

Responsibilities:

-   create stable JobID;
-   validate root-folder reference;
-   create initial job state;
-   track job status;
-   coordinate workers;
-   support retries;
-   support resume;
-   enforce idempotency.

Example states:

``` text
CREATED
INGESTING
INDEX_VALIDATING
RESOLVING_DOCUMENTS
INSPECTING_DOCUMENTS
RESOLVING_LEGENDS
RESOLVING_AOI
RUNNING_INDEPENDENT_QA
RECONCILING
BUILDING_EVIDENCE
EVALUATING_POLICY
DECIDED
HUMAN_REVIEW
COMPLETED
BLOCKED
FAILED
```

------------------------------------------------------------------------

# 8. File Inventory Service

The File Inventory Service recursively scans the root folder.

It records:

``` text
FileID
Path
Filename
Extension
MIME Type
Size
Hash
Classification
Status
```

Classification:

``` text
INDEX
MAP
LEGEND
UPSTREAM_OUTPUT
REFERENCE
OTHER
UNKNOWN
```

Unknown files must be logged.

No file should silently disappear from the inventory.

------------------------------------------------------------------------

# 9. Index Processor

The Index Processor reads the existing Excel.

## Important constraint

``` text
PRODUCTION EXCEL = READ ONLY
```

The system must not:

-   rename columns;
-   add columns;
-   delete columns;
-   reorder columns;
-   overwrite values;
-   alter business formatting.

The processor creates an internal canonical representation.

Every index row receives a processing status.

------------------------------------------------------------------------

# 10. Document Resolver

The resolver maps:

``` text
Index Record
       |
       v
Candidate Documents
       |
       v
Deterministic Matching
       |
       v
Unique Document
```

Matching signals can include:

-   provider;
-   utility type;
-   job/reference;
-   filename patterns;
-   configured directory patterns;
-   document metadata.

If mapping is ambiguous:

``` text
AMBIGUOUS_MAPPING
→ HUMAN_REVIEW / BLOCKED
```

Never guess.

------------------------------------------------------------------------

# 11. PDF Inspector

The PDF Inspector determines:

``` text
VECTOR
RASTER
HYBRID
UNKNOWN
```

It extracts, where available:

-   pages;
-   dimensions;
-   text;
-   word coordinates;
-   vector paths;
-   colors;
-   line widths;
-   dash patterns;
-   images;
-   metadata;
-   geometry.

Native PDF evidence should be preferred before rasterization or deep
learning.

------------------------------------------------------------------------

# 12. Provider Resolver

The Provider Resolver determines which provider/utility configuration
applies.

Example:

``` text
SGN
UKPN
GTC
TFL
ESP
Clean Water
Waste Water
BT
VM
...
```

Provider identification should be evidence-backed.

Possible signals:

-   index record;
-   filename;
-   map text;
-   title block;
-   legend;
-   known provider metadata.

Ambiguity must be escalated.

------------------------------------------------------------------------

# 13. Warning Catalogue Service

The Warning Catalogue is the **business definition of what warnings the
system is expected to detect**.

It should be versioned.

Conceptual model:

``` text
Warning Definition
├── Provider
├── Utility Type
├── Warning Code
├── Business Warning Text
├── Severity
├── Geometry Type
├── AOI Requirement
├── Detection Profile
├── Legend Profile
├── Active
└── Version
```

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

The supplied warning workbook should be converted into this governed
registry after its business authority and exact column semantics are
confirmed.

------------------------------------------------------------------------

# 14. Legend Registry

The Legend Registry stores provider-specific semantic definitions.

A profile can contain:

``` text
Provider
Map Type
Legend Version
Source
Source Hash
Effective Date
Colors
Line Styles
Dash Patterns
Widths
Symbols
Text Labels
Detection Rules
```

The registry must support versioning.

Example:

``` text
SGN Legend v1.2
UKPN Legend v2.0
```

A production decision must reference the legend version used.

------------------------------------------------------------------------

# 15. Legend Resolver

The Legend Resolver determines the authoritative legend for the
document.

Priority can be configured:

``` text
Embedded Authoritative Legend
        ↓
Approved External Legend
        ↓
Approved Symbol Guide
```

If the required legend cannot be resolved:

``` text
LEGEND_UNAVAILABLE
→ NO AUTO_CLEAR
```

The system must never invent a symbol interpretation.

------------------------------------------------------------------------

# 16. AOI Service

The AOI Service resolves the relevant Area of Interest/digsite.

Potential sources:

1.  native vector geometry;
2.  explicit map geometry;
3.  approved external AOI;
4.  CV/segmentation;
5.  other approved methods.

AOI object:

``` text
AOI_ID
Document_ID
Page
Geometry
Method
Confidence
Validity
Coordinate System
Tolerance
```

AOI is used for spatial validation.

------------------------------------------------------------------------

# 17. Independent QA Engine

This is the central technical validation layer.

It must independently inspect the map even when upstream reports:

``` text
NO WARNING
```

The engine receives:

``` text
Document
Provider
Warning Catalogue
Legend
AOI
```

and produces:

``` text
Detected Candidates
Warning Class
Geometry
Evidence
Confidence
Detection Method
```

------------------------------------------------------------------------

# 18. Vector Analysis Service

Preferred when the PDF contains reliable native vectors.

Analyze:

-   line geometry;
-   fill geometry;
-   stroke color;
-   stroke width;
-   dash pattern;
-   symbol shapes;
-   text;
-   spatial relationships.

Vector evidence is generally more precise than pixel-only analysis.

------------------------------------------------------------------------

# 19. Computer Vision Service

Used primarily for raster or difficult visual cases.

Potential operations:

``` text
Color-space conversion
Thresholding
Connected components
Contours
Morphology
Line detection
Segment detection
Width estimation
Dash-pattern analysis
Symbol/template detection
Segmentation
Object detection
```

Do not depend on exact RGB values alone.

Use provider-specific tolerances.

------------------------------------------------------------------------

# 20. OCR Service

OCR is used for:

-   map labels;
-   legends;
-   annotations;
-   rasterized text;
-   warning text.

Output:

``` text
Text
Bounding Box
Page
Confidence
```

Low-confidence OCR must not be treated as sole release evidence.

------------------------------------------------------------------------

# 21. Symbol Detection

Symbol detection may use:

### Deterministic methods

-   template matching;
-   geometry;
-   line/symbol characteristics;
-   legend matching.

### ML methods

Only where deterministic methods are insufficient.

Detected symbols must map to approved provider warning definitions.

------------------------------------------------------------------------

# 22. Spatial Validation Service

The Spatial Validation Service converts findings into geometry and
performs:

``` text
INTERSECTS
WITHIN
CONTAINS
DISTANCE
TOUCHES
OVERLAPS
CROSSES
```

It should also support provider-specific topology where required.

Example:

``` text
Detected Utility Line
        |
        v
Does line intersect AOI?
        |
    +---+---+
    |       |
   YES      NO
    |       |
Relevant  Outside
```

Scale-aware tolerance must be configurable.

------------------------------------------------------------------------

# 23. Warning Discovery Engine

The discovery engine uses the warning catalogue to determine which
warning conditions are relevant.

Example:

``` text
Provider = SGN
      |
      v
Warning Catalogue
      |
      +----------------------+
      |                      |
      v                      v
High Pressure           Medium Pressure
Gas Line                 Gas Line
      |                      |
      +-----------+----------+
                  |
                  v
          Map Analysis
                  |
                  v
       Candidate Warnings
```

This prevents the system from relying on generic, uncontrolled "anything
suspicious" classification.

------------------------------------------------------------------------

# 24. Warning Validation Engine

For every claimed or discovered warning:

``` text
Warning
  |
  +--> Legend Match
  |
  +--> Geometry
  |
  +--> AOI Relationship
  |
  +--> Visual Evidence
  |
  +--> Spatial Evidence
  |
  +--> Provider Rule
  |
  v
Validation Result
```

Possible result:

``` text
VALID
INVALID
UNCERTAIN
NOT_FOUND
```

Extended internal reason codes can include:

``` text
MISSED_WARNING
FALSE_POSITIVE
WARNING_TYPE_MISMATCH
OUTSIDE_AOI
DUPLICATE
AMBIGUOUS
```

------------------------------------------------------------------------

# 25. Upstream Integration

The platform consumes upstream warning output.

The upstream contract should ideally contain:

``` text
Document ID
Warning Code/Type
Warning Text
Severity
Location
Bounding Box
Polygon/Mask
Confidence
Model Version
Timestamp
Output Reference
```

The exact interface is a project decision that must be finalized.

------------------------------------------------------------------------

# 26. Reconciliation Engine

The Reconciliation Engine compares:

``` text
UPSTREAM
vs
INDEPENDENT QA
```

Example:

``` text
Upstream:
HV Cable

Independent:
HV Cable

→ VALID_WARNING
```

Example:

``` text
Upstream:
NO WARNING

Independent:
HV Cable

→ MISSED_WARNING
```

Example:

``` text
Upstream:
HV Cable

Independent:
No supporting evidence

→ POSSIBLE_FALSE_POSITIVE
```

The reconciliation result feeds the evidence and policy engines.

------------------------------------------------------------------------

# 27. Evidence Engine

The Evidence Engine creates the authoritative evidence package.

Possible evidence:

``` text
Source File
File Hash
Page
Map Crop
AOI
Legend
Legend Version
Detected Geometry
Vector Evidence
CV Evidence
OCR Evidence
Spatial Evidence
Upstream Warning
Independent Result
Rule Result
Model Version
Configuration Version
```

Each evidence item receives an EvidenceID.

Example:

``` text
E-001
E-002
E-003
```

------------------------------------------------------------------------

# 28. Evidence Completeness

The system must distinguish:

``` text
Evidence Exists
```

from:

``` text
Evidence Is Sufficient for Release
```

For example:

``` text
Detection confidence = 0.97
Evidence completeness = FALSE

→ HUMAN_REVIEW
```

A high score cannot compensate for missing mandatory evidence.

------------------------------------------------------------------------

# 29. Evidence Fusion

Evidence is combined from independent mechanisms.

Example:

``` text
Legend Match             PASS
Vector Style             PASS
Color/Style               PASS
AOI Intersection          PASS
Spatial Validation        PASS
OCR Context               PASS
Independent Detector      PASS
Upstream Warning          PRESENT
```

This creates a stronger basis for the validation result.

------------------------------------------------------------------------

# 30. Policy Engine

The Policy Engine is the authoritative release gate.

It consumes:

``` text
Validation Results
Evidence
Provider Rules
Warning Severity
AOI Status
Legend Status
System Health
```

and produces:

``` text
AUTO_CLEAR
HUMAN_REVIEW
BLOCKED
```

------------------------------------------------------------------------

# 31. AUTO_CLEAR Gate

AUTO_CLEAR is not a model prediction.

It is a deterministic policy result.

Minimum conceptual gates:

``` text
Index valid
AND
Map exists
AND
Mapping valid
AND
PDF usable
AND
Provider resolved
AND
Required legend resolved
AND
Required AOI resolved
AND
Independent scan completed
AND
Upstream reconciliation completed
AND
No unresolved critical warning
AND
No unresolved detector disagreement
AND
No critical quality issue
AND
Provider rules pass
AND
Evidence complete
AND
Audit persisted
AND
Release policy allows AUTO_CLEAR
```

Only then:

``` text
AUTO_CLEAR
```

------------------------------------------------------------------------

# 32. HUMAN_REVIEW Gate

Human QA should be triggered for:

-   confirmed warnings where policy requires review;
-   missed warnings;
-   uncertain results;
-   contradictory evidence;
-   ambiguous AOI;
-   ambiguous legend;
-   detector disagreement;
-   poor image quality;
-   high-risk cases;
-   insufficient evidence;
-   policy-required review.

------------------------------------------------------------------------

# 33. BLOCKED Gate

Blocking conditions may include:

-   missing map;
-   corrupt PDF;
-   unsupported document;
-   unsupported provider;
-   required legend unavailable;
-   required AOI unavailable;
-   unrecoverable processing failure;
-   critical infrastructure failure;
-   mandatory validation not completed.

The exact business mapping of individual conditions must be
configurable.

------------------------------------------------------------------------

# 34. QA Agent Architecture

The QA Agent is an **optional reasoning/orchestration layer**, not the
final judge.

``` text
                Structured Evidence
                       |
                       v
              +------------------+
              |     QA Agent     |
              |   Optional LLM   |
              +--------+---------+
                       |
          +------------+------------+
          |            |            |
          v            v            v
       Summary     Conflict      Recommended
                   Analysis       Action
          |            |            |
          +------------+------------+
                       |
                       v
                 Human Reviewer
```

## Allowed

The QA Agent can:

-   summarize evidence;
-   explain contradictions;
-   identify why a case was escalated;
-   recommend additional investigation;
-   assist with case prioritization;
-   generate reviewer-friendly explanations;
-   interpret structured evidence.

## Not allowed

The QA Agent cannot:

-   invent evidence;
-   invent legends;
-   invent warning classes;
-   invent severity;
-   invent coordinates;
-   claim tools ran when they did not;
-   override deterministic policy;
-   turn uncertainty into AUTO_CLEAR;
-   independently authorize client release.

------------------------------------------------------------------------

# 35. Human QA Architecture

``` text
HUMAN_REVIEW
     |
     v
QA Case Created
     |
     v
Priority / Severity
     |
     v
Skill Matching
     |
     v
SLA / Availability
     |
     v
Workload
     |
     v
Reviewer Assigned
     |
     v
Evidence Viewer
     |
     v
Human Decision
     |
     v
Audit Record
```

The reviewer should receive the exact evidence used to generate the
escalation.

------------------------------------------------------------------------

# 36. QA Evidence Viewer

The UI should present:

``` text
+--------------------------------------------------+
| Map                                               |
|                                                  |
|      AOI                                         |
|       +------------------+                       |
|       |  Warning line    |                       |
|       +------------------+                       |
|                                                  |
+--------------------------------------------------+

Warning:
High Pressure Gas Line

Upstream:
Not Detected

Independent QA:
Detected

Legend:
Matched

Spatial:
Intersects AOI

Reason:
Potential missed warning

Evidence:
[E001] [E002] [E003]
```

The exact UI design is implementation-specific, but the reviewer must be
able to inspect the same evidence that supports the decision.

------------------------------------------------------------------------

# 37. Data Architecture

Recommended persistence:

``` text
                    PostgreSQL
                         |
       +-----------------+----------------+
       |                 |                |
       v                 v                v
   Metadata          Decisions         Config
       |                 |                |
       v                 v                v
    PostGIS          Audit Events    Warning Catalogue
       |
       v
   Geometries
```

Object storage:

``` text
Object Storage
├── Original PDFs
├── Rendered Pages
├── Evidence Crops
├── Annotated Maps
├── OCR Artifacts
└── Generated Reports
```

------------------------------------------------------------------------

# 38. Core Data Model

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
ValidationResult
Evidence
Decision
QATask
AuditEvent
FeedbackRecord
ModelVersion
RuleVersion
LegendVersion
DatasetVersion
```

------------------------------------------------------------------------

# 39. Suggested Relationships

``` text
Job
 |
 +--- IndexRecord
 |       |
 |       +--- DocumentMapping
 |
 +--- Document
 |       |
 |       +--- DocumentPage
 |       +--- AOI
 |       +--- Detection
 |       +--- Warning
 |               |
 |               +--- ValidationResult
 |                       |
 |                       +--- Evidence
 |
 +--- Decision
 |
 +--- QATask
 |
 +--- AuditEvent
```

------------------------------------------------------------------------

# 40. Object Storage Architecture

Use object storage for large immutable artifacts.

``` text
/jobs/{job_id}/
    source/
    rendered/
    evidence/
    annotations/
    reports/
```

Example:

``` text
/jobs/JOB-001/source/map.pdf
/jobs/JOB-001/rendered/page-001.png
/jobs/JOB-001/evidence/E-001.json
/jobs/JOB-001/evidence/E-001.png
/jobs/JOB-001/annotations/page-001.png
/jobs/JOB-001/reports/job_report.json
```

------------------------------------------------------------------------

# 41. Queue and Worker Architecture

Processing should be asynchronous.

``` text
                 Job API
                    |
                    v
               Job Queue
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
   PDF Worker   CV Worker   OCR Worker
        |           |           |
        +-----------+-----------+
                    |
                    v
              Spatial Worker
                    |
                    v
              Evidence Worker
                    |
                    v
              Policy Worker
```

Workers must support:

-   retries;
-   timeouts;
-   idempotency;
-   dead-letter handling;
-   resource limits.

------------------------------------------------------------------------

# 42. Deployment Architecture

A production deployment can be structured as:

``` text
                    Load Balancer
                         |
                         v
                    API Service
                         |
               +---------+---------+
               |                   |
               v                   v
          Job/Workflow         QA API
             Service              |
               |                  |
               +---------+--------+
                         |
                    Message Queue
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
  Document Workers   CV Workers      OCR Workers
        |                |                |
        +----------------+----------------+
                         |
                         v
                 Evidence/Policy
                         |
               +---------+---------+
               |                   |
               v                   v
          PostgreSQL/PostGIS   Object Storage
               |
               v
          Audit/Reporting
```

Containerization should be used.

Kubernetes may be used if the production environment and scale justify
it.

------------------------------------------------------------------------

# 43. Security Architecture

``` text
User / Upstream
      |
      v
Authentication
      |
      v
Authorization / RBAC
      |
      v
API
      |
      v
Services
      |
      +----> Encrypted Database
      |
      +----> Encrypted Object Storage
      |
      +----> Audit
```

Required controls include:

-   authentication;
-   RBAC;
-   least privilege;
-   encryption in transit;
-   encryption at rest;
-   secure secrets;
-   audit logging;
-   data retention;
-   file security;
-   environment isolation.

------------------------------------------------------------------------

# 44. LLM Security Boundary

The LLM should sit behind a controlled boundary.

``` text
Sensitive Map Data
       |
       X
       |  DO NOT SEND BY DEFAULT
       |
       v

Structured Evidence
       |
       v
PII/Sensitive Data Policy
       |
       v
Approved LLM Endpoint
       |
       v
QA Agent
```

The core pipeline must remain operational if the LLM is unavailable.

------------------------------------------------------------------------

# 45. Observability Architecture

Use structured logs, metrics, and traces.

``` text
Services
   |
   +---- Logs ----> Central Logging
   |
   +---- Metrics --> Metrics Platform
   |
   +---- Traces ---> Distributed Tracing
```

Track:

### System

-   job throughput;
-   queue depth;
-   worker health;
-   CPU;
-   memory;
-   GPU;
-   storage;
-   database health.

### QA

-   warning recall;
-   warning precision;
-   escaped-warning rate;
-   auto-clear percentage;
-   human-review percentage;
-   blocked percentage;
-   human override rate.

### Performance

-   average latency;
-   P95 latency;
-   P99 latency;
-   provider-specific latency.

------------------------------------------------------------------------

# 46. Versioning Architecture

Version all decision-relevant components.

``` text
Document
   |
   +--- Parser Version
   +--- Provider Version
   +--- Legend Version
   +--- Warning Catalogue Version
   +--- AOI Method Version
   +--- CV Version
   +--- OCR Version
   +--- Model Version
   +--- Rule Version
   +--- Policy Version
   +--- QA Agent Version
```

A decision record must reference the versions used.

------------------------------------------------------------------------

# 47. Reproducibility Architecture

Historical decision:

``` text
Decision
 |
 +-- Source File Hash
 +-- Document ID
 +-- Legend Version
 +-- Warning Catalogue Version
 +-- Rule Version
 +-- Model Version
 +-- Configuration Version
 +-- Evidence IDs
 +-- Timestamp
```

This makes it possible to explain how a decision was produced.

------------------------------------------------------------------------

# 48. Reliability Architecture

The system must be resilient to:

-   worker crashes;
-   queue failures;
-   database failures;
-   object storage failures;
-   OCR failures;
-   CV failures;
-   PDF parser failures;
-   timeouts;
-   network failures.

Critical processing must fail safely.

``` text
Failure
   |
   v
Retry if recoverable
   |
   +---- YES → Retry
   |
   +---- NO
          |
          v
     HUMAN_REVIEW
          OR
        BLOCKED
```

Infrastructure failure must not be silently interpreted as "map is
clean."

------------------------------------------------------------------------

# 49. Idempotency Architecture

Processing identity should consider:

``` text
File Hash
+
Configuration Version
+
Warning Catalogue Version
+
Legend Version
+
Rule Version
```

This supports safe reprocessing and controlled caching.

------------------------------------------------------------------------

# 50. Provider Plugin Architecture

Provider-specific logic should be modular.

Example conceptual interface:

``` python
class ProviderValidator:

    def identify(self, document):
        ...

    def resolve_legend(self, document):
        ...

    def detect_aoi(self, document):
        ...

    def get_warning_definitions(self):
        ...

    def detect_candidates(self, document, aoi):
        ...

    def validate_warning(self, warning, evidence):
        ...

    def get_policy_context(self):
        ...
```

This prevents a single giant provider-specific conditional codebase.

------------------------------------------------------------------------

# 51. Provider Configuration

Recommended structure:

``` text
providers/
├── sgn/
│   ├── provider.yaml
│   ├── warnings.yaml
│   ├── legend.yaml
│   ├── detection.yaml
│   └── policy.yaml
│
├── ukpn/
│   ├── provider.yaml
│   ├── warnings.yaml
│   ├── legend.yaml
│   ├── detection.yaml
│   └── policy.yaml
│
└── clean_water/
    └── ...
```

Exact configuration format may be YAML, database-backed, or another
governed configuration mechanism.

------------------------------------------------------------------------

# 52. Configuration-Driven Design

Do not hard-code:

``` python
if provider == "SGN":
    ...
elif provider == "UKPN":
    ...
```

Business configuration should define:

-   providers;
-   warning definitions;
-   severity;
-   legend semantics;
-   detection profiles;
-   AOI rules;
-   spatial tolerance;
-   release policy;
-   QA routing.

------------------------------------------------------------------------

# 53. Decision State Machine

``` text
                    +----------------+
                    |    PROCESSING  |
                    +-------+--------+
                            |
                 +----------+----------+
                 |                     |
                 v                     v
              VALID                  ERROR
                 |                     |
                 v                     v
             EVALUATE              BLOCKED
                 |
       +---------+---------+
       |         |         |
       v         v         v
   AUTO_CLEAR HUMAN_QA   BLOCKED
                 |
                 v
             QA REVIEW
                 |
                 v
          FINAL DISPOSITION
```

------------------------------------------------------------------------

# 54. Evidence-Based Decision Example

``` text
Document:
SGN.pdf

Legend:
SGN Legend v1.2 → MATCH

AOI:
Valid → PASS

Independent Detection:
High Pressure Gas Line → DETECTED

Spatial:
Intersects AOI → TRUE

Upstream:
No Warning

Reconciliation:
MISSED_WARNING

Evidence:
Complete

Policy:
High-risk warning → HUMAN_REVIEW

Final:
HUMAN_REVIEW
```

The LLM may summarize this case, but the policy engine produces the
release state.

------------------------------------------------------------------------

# 55. Performance Architecture

The system should parallelize independent documents.

``` text
JOB
 |
 +--- Document A → Worker
 |
 +--- Document B → Worker
 |
 +--- Document C → Worker
 |
 +--- Document D → Worker
 |
 +--- Document E → Worker
```

Shared services should have controlled concurrency.

GPU workloads should use bounded queues.

CPU-heavy PDF/vector operations should not block interactive API
requests.

------------------------------------------------------------------------

# 56. Caching

Safe cache candidates include:

-   file hashes;
-   PDF extraction artifacts;
-   rendered pages;
-   OCR artifacts;
-   legend resolution;
-   immutable configuration;
-   approved intermediate results.

Caching must respect versioning.

------------------------------------------------------------------------

# 57. Testing Architecture

Testing must exist at multiple levels.

``` text
                Test Pyramid
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
      Unit     Integration    E2E
        |           |           |
        +-----------+-----------+
                    |
                    v
             Gold Dataset
                    |
                    v
             Regression Suite
                    |
                    v
            Production Pilot
```

------------------------------------------------------------------------

# 58. Gold-Standard Evaluation

Create a domain-reviewed dataset containing:

-   warning-present maps;
-   genuinely clean maps;
-   upstream missed warnings;
-   upstream false positives;
-   ambiguous legends;
-   missing legends;
-   raster maps;
-   vector maps;
-   hybrid maps;
-   difficult scans;
-   faded colors;
-   overlapping lines;
-   boundary cases;
-   AOI edge cases.

The dataset must be versioned and locked for evaluation.

------------------------------------------------------------------------

# 59. Primary Production KPI

The most important safety metric is:

> **Auto-clear escape rate.**

Definition:

``` text
Real warning exists
+
System outputs AUTO_CLEAR
=
ESCAPED WARNING
```

The system should optimize primarily to minimize this failure mode.

Other KPIs:

-   warning recall;
-   warning precision;
-   false-negative rate;
-   false-positive rate;
-   auto-clear percentage;
-   human-review percentage;
-   human QA time saved;
-   AOI accuracy;
-   legend accuracy;
-   processing time;
-   availability.

------------------------------------------------------------------------

# 60. Feedback Architecture

``` text
Human QA
   |
   v
Corrections / Dispositions
   |
   v
Feedback Store
   |
   v
Curated Dataset
   |
   v
Evaluation
   |
   v
Rule / Model Improvement
   |
   v
Regression
   |
   v
Approval
   |
   v
Versioned Production Release
```

Do not implement uncontrolled automatic retraining.

------------------------------------------------------------------------

# 61. CI/CD Architecture

Recommended flow:

``` text
Developer
   |
   v
Git
   |
   v
CI
 |
 +-- Unit Tests
 +-- Static Analysis
 +-- Security Scan
 +-- Integration Tests
 +-- Regression Tests
 +-- Gold Dataset
 |
 v
Build Container
 |
 v
Staging
 |
 v
Acceptance
 |
 v
Production
 |
 v
Monitoring
```

Critical regression failures should prevent deployment.

------------------------------------------------------------------------

# 62. Recommended Repository Architecture

``` text
ai-map-qa/
│
├── README.md
├── architecture.md
├── requirements.md
├── pyproject.toml
├── .env.example
├── docker/
│
├── src/
│   ├── api/
│   ├── orchestration/
│   ├── ingestion/
│   ├── index/
│   ├── documents/
│   ├── providers/
│   ├── warnings/
│   ├── legends/
│   ├── aoi/
│   ├── pdf/
│   ├── vector/
│   ├── cv/
│   ├── ocr/
│   ├── spatial/
│   ├── reconciliation/
│   ├── evidence/
│   ├── policy/
│   ├── decision/
│   ├── qa/
│   ├── agent/
│   ├── audit/
│   ├── reporting/
│   └── observability/
│
├── configs/
│   ├── providers/
│   ├── warnings/
│   ├── legends/
│   ├── policies/
│   └── environments/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── regression/
│   └── fixtures/
│
├── datasets/
│   └── gold/
│
├── migrations/
│
├── scripts/
│
└── docs/
```

This is a recommended starting structure, not a requirement to create
every module immediately.

------------------------------------------------------------------------

# 63. Deployment Environments

Use environment separation:

``` text
DEV
 |
 v
TEST
 |
 v
STAGING
 |
 v
PRODUCTION
```

Configuration and secrets must not be mixed between environments.

------------------------------------------------------------------------

# 64. Production Processing Flow

For each index row:

``` text
1. Read row
2. Validate row
3. Resolve map
4. Validate map
5. Inspect PDF
6. Identify provider
7. Resolve warning catalogue
8. Resolve legend
9. Resolve AOI
10. Load upstream warnings
11. Run independent detection
12. Run spatial validation
13. Validate claimed warnings
14. Search for missed warnings
15. Reconcile results
16. Build evidence
17. Apply policy
18. Produce decision
19. Create QA task if required
20. Store audit
21. Generate outputs
```

No row may silently disappear.

------------------------------------------------------------------------

# 65. Critical Data Flow

``` text
                 BUSINESS TRUTH
                      |
               Warning Catalogue
                      |
                      v
                 What to detect
                      |
                      |
MAP -----> Legend ---> How it looks
  |                   |
  |                   v
  |                 AOI
  |                   |
  +-------> Independent Detection
                      |
                      v
               What was found
                      |
                      v
               Spatial Validation
                      |
                      v
                 Evidence
                      |
                      v
              Reconciliation
                      |
                      v
                  Policy
                      |
          +-----------+-----------+
          |           |           |
       CLEAR       REVIEW       BLOCK
```

------------------------------------------------------------------------

# 66. Architecture Decision: LLM Placement

### Decision

The LLM is **not** part of the mandatory safety-critical validation
chain.

### Rationale

This provides:

-   deterministic behavior;
-   lower hallucination risk;
-   reproducibility;
-   lower dependency on external model availability;
-   easier validation;
-   easier security review;
-   easier regression testing;
-   clearer auditability.

### LLM position

``` text
Validation System
       |
       v
Structured Evidence
       |
       v
QA Agent / LLM
       |
       v
Human QA Assistance
```

------------------------------------------------------------------------

# 67. Architecture Decision: Native PDF First

Use:

``` text
Native PDF/vector
```

before:

``` text
Raster CV
```

before:

``` text
Deep Learning
```

when the simpler evidence is sufficient.

This reduces:

-   computational cost;
-   unnecessary model dependence;
-   uncertainty;
-   false positives.

------------------------------------------------------------------------

# 68. Architecture Decision: Warning Catalogue as Business Truth

The system does not invent which warnings should exist.

Instead:

``` text
Approved Warning Catalogue
        ↓
Expected Warning Classes
        ↓
Detection
        ↓
Validation
```

Severity is business-defined.

The detection system determines whether the condition is present.

------------------------------------------------------------------------

# 69. Architecture Decision: Independent QA

The QA system must perform an independent search.

``` text
Upstream:
NO WARNING

        +

Independent QA:
SEARCH MAP

        ↓

Potential missed warning
```

This is essential to detect upstream false negatives.

------------------------------------------------------------------------

# 70. Architecture Decision: Human Abstention

The system is allowed to abstain.

``` text
Uncertain
    ↓
Human QA
```

not:

``` text
Uncertain
    ↓
Auto Clear
```

This is a core production safety principle.

------------------------------------------------------------------------

# 71. Architecture Decision: Fail Closed

If mandatory evidence cannot be produced:

``` text
No evidence
    ↓
No AUTO_CLEAR
```

If infrastructure failure prevents validation:

``` text
Validation incomplete
    ↓
BLOCKED / HUMAN_REVIEW
```

Never interpret processing failure as a clean map.

------------------------------------------------------------------------

# 72. Architecture Decision: No Generic Provider Logic

Provider semantics must be configured independently.

``` text
Common Framework
      |
      +--- SGN
      +--- UKPN
      +--- GTC
      +--- TFL
      +--- ESP
      +--- Clean Water
      +--- Waste Water
      +--- BT
      +--- VM
      +--- ...
```

A provider plugin/configuration should define its own semantics.

------------------------------------------------------------------------

# 73. Pilot Architecture

The supplied project specification recommends starting with:

``` text
SGN
UKPN
Clean Water
```

These are suitable because they exercise different combinations of:

-   legends;
-   line styles;
-   raster/vector content;
-   external references;
-   warning semantics.

After the common framework is stable, expand to additional providers.

------------------------------------------------------------------------

# 74. Implementation Sequence

The architecture should be implemented in this order:

``` text
1. Inspect actual project data
2. Inspect actual Excel structure
3. Build repository foundation
4. File inventory
5. Excel reader
6. Deterministic document resolver
7. PDF inspector
8. Native extraction
9. Provider/legend registry
10. AOI service
11. Warning catalogue
12. First provider validator
13. Independent warning discovery
14. Evidence engine
15. Deterministic decision engine
16. Human QA workflow
17. Audit/observability
18. QA Agent / LLM assistance
19. Gold-standard evaluation
20. Pilot
21. Provider expansion
```

Do not begin with a multi-agent swarm or LLM-only vision system.

------------------------------------------------------------------------

# 75. First Production Milestone

The first implementation milestone should be a deterministic pipeline
that accepts:

``` text
root_folder/
```

and produces:

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
→ Validate map
→ Inspect document
→ Resolve provider
→ Resolve warning definitions
→ Resolve legend
→ Resolve AOI
→ Run warning checks
→ Produce evidence
→ Produce deterministic result
```

This milestone must work without requiring an LLM.

------------------------------------------------------------------------

# 76. Architecture Non-Negotiables

1.  Production Excel remains immutable.
2.  Every index row is accounted for.
3.  Every expected map is resolved or explicitly blocked.
4.  Ambiguous mappings are never guessed.
5.  Provider semantics are explicit.
6.  Warning definitions come from approved business configuration.
7.  Severity comes from approved business configuration.
8.  Required legends must be resolved.
9.  AOI must be validated where required.
10. Upstream "no warning" is never proof of cleanliness.
11. Independent warning discovery is mandatory.
12. Native vector evidence is preferred where reliable.
13. Spatial validation is mandatory for spatial warning decisions.
14. Every decision must have evidence.
15. Confidence alone cannot authorize AUTO_CLEAR.
16. Uncertainty must abstain.
17. Critical unresolved warnings cannot AUTO_CLEAR.
18. The LLM cannot override safety gates.
19. Infrastructure failures cannot be interpreted as clean results.
20. Historical decisions must be reproducible.
21. All decision-relevant versions must be recorded.
22. Production AUTO_CLEAR requires locked evaluation evidence.
23. Human QA corrections must be auditable.
24. Model/rule changes require regression testing.
25. The system must optimize for low escaped-warning risk.

------------------------------------------------------------------------

# 77. Architecture Risks

  Risk                      Architectural Mitigation
  ------------------------- -----------------------------------------
  Upstream missed warning   Independent discovery
  False positive            Legend + geometry + evidence validation
  Wrong provider            Provider resolver + evidence
  Wrong map                 Deterministic document resolver
  Missing legend            No auto-clear
  Ambiguous AOI             Human/block
  Raster difficulty         CV/OCR fallback
  Vector inconsistency      Quality checks + CV fallback
  OCR error                 Multi-source evidence
  Model disagreement        Human review
  LLM hallucination         Structured evidence + bounded role
  Infrastructure failure    Fail-closed workflow
  Rule drift                Versioned configuration
  Legend drift              Versioned registry
  Regression                Locked gold dataset
  Audit failure             Immutable/versioned records

------------------------------------------------------------------------

# 78. Architecture Success Criteria

The architecture is successful when it provides:

### Correctness

Independent, evidence-based warning validation.

### Safety

Extremely low escaped-warning risk.

### Traceability

Every decision can be traced to evidence.

### Explainability

Human reviewers can understand why a case was escalated or cleared.

### Determinism

Release decisions follow explicit policy.

### Scalability

Multiple maps/providers can be processed concurrently.

### Maintainability

Provider rules and warning definitions are configuration-driven.

### Security

Sensitive infrastructure documents are protected.

### Observability

Failures and quality degradation are measurable.

### Reproducibility

Historical decisions can be reconstructed.

------------------------------------------------------------------------

# 79. Final Architecture

``` text
                              +----------------------+
                              |      ROOT FOLDER     |
                              | Excel / Maps / Docs  |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              |   API / JOB MANAGER  |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | FILE INVENTORY        |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | INDEX PROCESSOR       |
                              | Excel = READ ONLY     |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | DOCUMENT RESOLVER     |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | PDF INSPECTOR         |
                              | Vector/Raster/Hybrid  |
                              +----------+-----------+
                                         |
                   +---------------------+---------------------+
                   |                                           |
                   v                                           v
          +-------------------+                       +-------------------+
          | WARNING CATALOGUE |                       | LEGEND REGISTRY   |
          | Business Truth    |                       | Map Semantics     |
          +---------+---------+                       +---------+---------+
                    |                                           |
                    +------------------+------------------------+
                                       |
                                       v
                              +----------------------+
                              | AOI SERVICE           |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | INDEPENDENT MAP QA    |
                              +----------+-----------+
                                         |
                         +---------------+---------------+
                         |               |               |
                         v               v               v
                    +---------+     +---------+     +---------+
                    | VECTOR  |     |   CV    |     |   OCR   |
                    +----+----+     +----+----+     +----+----+
                         |               |               |
                         +---------------+---------------+
                                         |
                                         v
                              +----------------------+
                              | WARNING DISCOVERY    |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | SPATIAL VALIDATION   |
                              +----------+-----------+
                                         |
                                         v
                         +---------------+---------------+
                         |                               |
                         v                               v
                +-------------------+           +-------------------+
                | UPSTREAM WARNINGS  |           | INDEPENDENT QA    |
                +---------+---------+           +---------+---------+
                          |                               |
                          +---------------+---------------+
                                          |
                                          v
                              +----------------------+
                              | RECONCILIATION       |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | EVIDENCE ENGINE      |
                              +----------+-----------+
                                         |
                                         v
                              +----------------------+
                              | DETERMINISTIC POLICY |
                              +----------+-----------+
                                         |
                       +-----------------+-----------------+
                       |                 |                 |
                       v                 v                 v
                +-------------+   +-------------+   +-------------+
                | AUTO_CLEAR  |   | HUMAN_REVIEW|   |  BLOCKED    |
                +------+------+   +------+------+   +-------------+
                       |                 |
                       |                 v
                       |        +------------------+
                       |        | QA AGENT / LLM   |
                       |        | Optional         |
                       |        +--------+---------+
                       |                 |
                       |                 v
                       |        +------------------+
                       |        | HUMAN QA         |
                       |        +--------+---------+
                       |                 |
                       +-----------------+
                                         |
                                         v
                              +----------------------+
                              | FINAL DISPOSITION    |
                              +----------+-----------+
                                         |
                          +--------------+--------------+
                          |                             |
                          v                             v
                 +------------------+          +------------------+
                 | REPORTS / CLIENT |          | AUDIT / FEEDBACK |
                 +------------------+          +------------------+
```

------------------------------------------------------------------------

# 80. Final Architectural Statement

The production system is a **layered Map QA Validation Platform with an
optional agentic reasoning layer**.

The authoritative flow is:

``` text
SOURCE
→ INDEX VALIDATION
→ FILE VALIDATION
→ DOCUMENT RESOLUTION
→ PDF/VECTOR EXTRACTION
→ PROVIDER RESOLUTION
→ WARNING CATALOGUE
→ LEGEND RESOLUTION
→ AOI VALIDATION
→ INDEPENDENT WARNING DISCOVERY
→ CLAIMED WARNING VALIDATION
→ SPATIAL VALIDATION
→ RECONCILIATION
→ EVIDENCE FUSION
→ DETERMINISTIC POLICY
→ AUTO_CLEAR / HUMAN_REVIEW / BLOCKED
→ HUMAN QA WHEN REQUIRED
→ OUTPUT
→ AUDIT
→ FEEDBACK / EVALUATION
```

The **QA Agent/LLM is an assisting reasoning component**, not the safety
authority.

The **Policy Engine is the release authority**.

The **Warning Catalogue is the business definition of what must be
detected**.

The **Legend Registry is the semantic source for map symbols**.

The **map itself is the evidence source**.

The **independent QA pipeline is the protection against upstream missed
or incorrect warnings**.

And the primary production objective remains:

> **Minimize escaped real warnings while reducing unnecessary human QA
> effort.**
