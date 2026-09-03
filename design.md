# AI Map QA & Validation Agent

## Production UI/UX Design Specification

**Document:** `design.md`\
**Design Reference:** Dribbble --- "Multiple screens of Automation QA
Testing"\
**Reference URL:**
https://dribbble.com/shots/23183274-Multiple-screens-of-Automation-QA-Testing\
**Reference Product Context:** The Dribbble shot is described by its
creator as a mixture of screens from the SaaS product Preflight by
Applitools.\
**Design Goal:** Create a polished enterprise SaaS QA workspace inspired
by the reference's multi-screen automation/testing style, while
designing the product specifically for utility-map QA, evidence
inspection, warning validation, human review, and production operations.

------------------------------------------------------------------------

# 1. Design Objective

The UI should make a technically complex map-validation system feel:

-   simple;
-   trustworthy;
-   professional;
-   operational;
-   fast to understand;
-   evidence-driven;
-   safe;
-   enterprise-grade.

The application must **not look like a generic chatbot**.

It should look like a serious production QA platform.

The visual language should take inspiration from the referenced Dribbble
work's SaaS/testing orientation, particularly the idea of multiple
coordinated product screens rather than one overloaded dashboard. The
reference itself presents multiple screens for a SaaS automation QA
product.

Reference:

https://dribbble.com/shots/23183274-Multiple-screens-of-Automation-QA-Testing

------------------------------------------------------------------------

# 2. Product Design Concept

The product should be designed around one central question:

> **"What is the current QA state of my maps, and why did the system
> make that decision?"**

The primary user should be able to move from:

``` text
JOB
→ MAP
→ WARNING
→ EVIDENCE
→ DECISION
→ HUMAN REVIEW
```

without getting lost.

------------------------------------------------------------------------

# 3. Primary Users

## 3.1 QA Reviewer

Needs:

-   map inspection;
-   highlighted AOI;
-   highlighted warnings;
-   upstream vs independent comparison;
-   evidence;
-   legend;
-   decision controls;
-   comments;
-   review history.

## 3.2 QA Lead / Supervisor

Needs:

-   workload;
-   queue;
-   SLA;
-   escalations;
-   reviewer performance;
-   provider trends;
-   escaped-warning metrics.

## 3.3 Operations User

Needs:

-   job submission;
-   job status;
-   processing progress;
-   errors;
-   output download;
-   run history.

## 3.4 Technical/Admin User

Needs:

-   provider configuration;
-   warning catalogue;
-   legend registry;
-   rule versions;
-   model versions;
-   audit;
-   system health.

## 3.5 Management / Stakeholder

Needs:

-   high-level quality metrics;
-   auto-clear rate;
-   human-review rate;
-   blocked rate;
-   warning detection;
-   escaped-warning trend;
-   processing volume.

------------------------------------------------------------------------

# 4. Design Principles

## 4.1 Evidence before explanation

The UI should show evidence first.

Do not lead with:

> "AI thinks this is a warning."

Lead with:

``` text
Warning:
High Pressure Gas Line

Evidence:
✓ Legend matched
✓ Vector geometry detected
✓ AOI intersection confirmed
✓ Independent detection confirmed
✓ Upstream result: No warning
```

------------------------------------------------------------------------

# 4.2 Decision transparency

Every decision must answer:

``` text
WHAT?
WHY?
EVIDENCE?
RULE?
NEXT ACTION?
```

------------------------------------------------------------------------

# 4.3 No black-box feeling

The UI should visually expose the validation pipeline.

Example:

``` text
Index
 ✓
Map
 ✓
Legend
 ✓
AOI
 ✓
Independent Scan
 ✓
Reconciliation
 !
Evidence
 ✓
Policy
 !
Human QA
```

------------------------------------------------------------------------

# 4.4 Safety-first design

Use visual distinction between:

-   `AUTO CLEAR`
-   `HUMAN REVIEW`
-   `BLOCKED`

The user must immediately understand that these are different risk
states.

------------------------------------------------------------------------

# 4.5 Minimal cognitive load

Do not display every technical field on the first screen.

Use progressive disclosure:

``` text
Summary
  ↓
Details
  ↓
Evidence
  ↓
Technical metadata
```

------------------------------------------------------------------------

# 5. Overall Visual Direction

The design should be:

-   modern SaaS;
-   clean;
-   minimal;
-   dense enough for enterprise work;
-   visually polished;
-   subtle rounded corners;
-   clear hierarchy;
-   restrained color usage;
-   strong whitespace;
-   excellent typography;
-   compact tables;
-   interactive evidence panels.

Avoid:

-   excessive gradients;
-   excessive glassmorphism;
-   huge illustrations;
-   chatbot-first UI;
-   excessive animation;
-   overly colorful dashboards;
-   unnecessary 3D elements.

------------------------------------------------------------------------

# 6. Recommended Design Language

## 6.1 Theme

Primary recommendation:

``` text
Light enterprise SaaS
+
optional dark mode
```

The primary QA workspace should use a light interface because map
inspection already contains visually complex imagery.

------------------------------------------------------------------------

# 7. Color System

Colors should communicate **state**, not decoration.

Suggested semantic palette:

``` text
Primary
Deep Indigo / Blue

Success
Green

Warning
Amber

Critical
Red

Information
Blue

Neutral
Slate / Gray

Background
Very Light Gray / White
```

Example semantic mapping:

``` text
AUTO_CLEAR     → Green
HUMAN_REVIEW   → Amber
BLOCKED        → Red
PROCESSING     → Blue
QUEUED         → Gray/Blue
FAILED         → Red
```

Important:

> Do not rely on color alone.

Every state should also have:

-   label;
-   icon;
-   status text.

------------------------------------------------------------------------

# 8. Typography

Recommended:

``` text
Inter
```

or an equivalent enterprise UI font.

Hierarchy:

``` text
Page title       24–28px
Section title    16–20px
Card title       14–16px
Body             13–14px
Table            12–13px
Metadata         11–12px
```

Use font weight rather than large typography to create hierarchy.

------------------------------------------------------------------------

# 9. Layout System

Desktop-first.

Primary target:

``` text
1440 × 900
```

Also support:

``` text
1280 × 800
1920 × 1080
```

Recommended structure:

``` text
┌──────────────────────────────────────────────────────┐
│ Top Bar                                               │
├───────────────┬──────────────────────────────────────┤
│ Sidebar       │ Main Workspace                       │
│               │                                      │
│ Navigation    │ Content                              │
│               │                                      │
│               │                                      │
└───────────────┴──────────────────────────────────────┘
```

------------------------------------------------------------------------

# 10. Global Navigation

Sidebar items:

``` text
Overview
Jobs
Maps
QA Queue
Evidence
Warnings
Providers
Legends
Reports
Evaluation
Audit
Settings
```

Recommended ordering:

### Operations

-   Overview
-   Jobs
-   QA Queue

### Validation

-   Maps
-   Evidence
-   Warnings

### Governance

-   Providers
-   Legends
-   Rules
-   Evaluation
-   Audit

### Administration

-   Settings

------------------------------------------------------------------------

# 11. Top Navigation

Top bar:

``` text
[Logo] AI Map QA

Search...

                    Notifications
                    Help
                    User
```

Optional:

``` text
Environment: Production
```

The environment indicator should be clearly visible to authorized users.

------------------------------------------------------------------------

# 12. Screen Inventory

The product should include the following major screens:

1.  Overview Dashboard
2.  Jobs
3.  New Job / Root Folder Submission
4.  Job Details
5.  Map Inventory
6.  Map QA Detail
7.  Warning Detail
8.  Evidence Explorer
9.  Human QA Queue
10. Human QA Review Workspace
11. QA Agent Panel
12. Warning Catalogue
13. Provider Management
14. Legend Registry
15. Rules & Policy
16. Reports
17. Evaluation / Gold Dataset
18. Audit Trail
19. System Health
20. Settings

The design should feel like a connected SaaS product rather than
disconnected pages.

------------------------------------------------------------------------

# 13. Screen 1 --- Overview Dashboard

## Purpose

Give users an immediate understanding of production QA health.

### Layout

``` text
┌───────────────────────────────────────────────────────────────┐
│ AI Map QA                                      Today ▼        │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Maps Processed     Auto Clear      Human QA       Blocked    │
│      1,284             71%            23%             6%      │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  QA Health                         Warning Detection          │
│  ┌───────────────────────┐         ┌──────────────────────┐   │
│  │ Escape Rate           │         │ Warnings Found       │   │
│  │       0.18%           │         │       347            │   │
│  │ ↓ 12% vs last week    │         │ ↑ 8%                 │   │
│  └───────────────────────┘         └──────────────────────┘   │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│ Recent Jobs                                                   │
│                                                               │
│ Job ID    Maps    Status       Auto Clear    Review    Time  │
│ JOB-102   240     Complete       74%         21%     18m   │
│ JOB-101   180     Complete       69%         27%     14m   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 14. Dashboard KPI Cards

Primary cards:

### Maps Processed

Shows:

``` text
Total maps
Change vs previous period
```

### AUTO_CLEAR

Shows:

``` text
Percentage
Trend
```

### HUMAN_REVIEW

Shows:

``` text
Percentage
Open cases
```

### BLOCKED

Shows:

``` text
Percentage
Top blocking reason
```

### Escaped Warning Rate

This is the most important safety KPI.

Use prominent placement.

------------------------------------------------------------------------

# 15. Dashboard Charts

Recommended:

### Processing trend

``` text
Maps/day
```

### Decision distribution

``` text
AUTO_CLEAR
HUMAN_REVIEW
BLOCKED
```

### Warning categories

``` text
Gas
Electricity
Water
Telecom
Heat
```

### Provider performance

``` text
Provider
Recall
Review Rate
Escape Rate
```

Avoid chart overload.

------------------------------------------------------------------------

# 16. Screen 2 --- Jobs

The Jobs screen is the operational control center.

### Table

``` text
Job ID
Source
Created
Maps
Progress
Status
Auto Clear
Human QA
Blocked
Duration
Actions
```

Example:

``` text
JOB-1042
/root/customer/project-21
Today 10:32
124
██████████████░ 92%
Processing
—
—
—
12m
View
```

------------------------------------------------------------------------

# 17. Job Status

Use:

``` text
QUEUED
PROCESSING
COMPLETED
PARTIALLY_COMPLETED
HUMAN_REVIEW
BLOCKED
FAILED
```

------------------------------------------------------------------------

# 18. Screen 3 --- New Job

The user should not need to understand the backend.

### Layout

``` text
New QA Job

Root Folder
┌─────────────────────────────────────────────┐
│ C:\Projects\Customer\Job-1024               │
└─────────────────────────────────────────────┘
                              [Browse]

Detected:
✓ Excel Index
✓ 124 Map PDFs
✓ 8 Legend Documents
✓ Upstream Output

Validation Profile
[ Production Default ▼ ]

[ Start QA Run ]
```

Before starting, show a preflight summary.

------------------------------------------------------------------------

# 19. Preflight Validation

Before processing:

``` text
✓ Root folder accessible
✓ Index found
✓ Index schema valid
✓ Maps discovered
✓ Legends discovered
✓ Warning catalogue available
✓ Upstream output available
```

If something fails:

``` text
✕ Required legend set incomplete

[View Details]
```

Do not let users start a run that is obviously invalid unless they have
an explicit override permission.

------------------------------------------------------------------------

# 20. Screen 4 --- Job Details

This screen should visualize the pipeline.

``` text
Job JOB-1042

Overall Progress
██████████████████░░ 88%

Ingestion             ✓
Index Validation      ✓
Document Resolution   ✓
PDF Inspection        ✓
Legend Resolution     ✓
AOI Detection         ✓
Independent QA        ●
Reconciliation        ○
Evidence              ○
Policy                ○
```

Use a stepper similar to modern automation/testing products.

------------------------------------------------------------------------

# 21. Job Details --- Summary

Cards:

``` text
124 Maps
116 Completed
5 Human Review
2 Blocked
1 Processing
```

Then:

``` text
Warnings
63 detected
11 missed upstream
4 false positives
```

------------------------------------------------------------------------

# 22. Screen 5 --- Map Inventory

This is the main map list.

Columns:

``` text
Map
Provider
Utility
Pages
AOI
Upstream
Independent QA
Decision
Risk
Actions
```

Example:

``` text
42336412_SGN.pdf
SGN
Gas
4
✓
No Warning
Warning Found
HUMAN REVIEW
HIGH
View
```

------------------------------------------------------------------------

# 23. Map Status Badges

Example:

``` text
AUTO CLEAR
HUMAN REVIEW
BLOCKED
PROCESSING
```

Use consistent semantic styling across the entire application.

------------------------------------------------------------------------

# 24. Screen 6 --- Map QA Detail

This is the most important screen.

It should be designed as a **three-panel workspace**.

``` text
┌────────────────────────────────────────────────────────────────────┐
│ SGN Map / 42336412                         HUMAN REVIEW   HIGH     │
├──────────────┬──────────────────────────────┬─────────────────────┤
│ Map Pages    │                              │ Validation          │
│              │                              │                     │
│ [Page 1]     │        MAP VIEWER            │ ✓ Index             │
│ [Page 2]     │                              │ ✓ Document          │
│ [Page 3]     │      AOI + WARNINGS          │ ✓ Legend            │
│ [Page 4]     │                              │ ✓ AOI               │
│              │                              │ ! Warning mismatch  │
│              │                              │ ! Human review      │
├──────────────┴──────────────────────────────┴─────────────────────┤
│ Evidence / Warnings / Legend / Audit / QA Agent                   │
└────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 25. Map Viewer

The map viewer must support:

-   zoom;
-   pan;
-   page navigation;
-   fit AOI;
-   fit warning;
-   toggle layers;
-   show/hide annotations;
-   show/hide upstream findings;
-   show/hide independent findings;
-   evidence highlighting;
-   screenshot/crop generation.

------------------------------------------------------------------------

# 26. Map Viewer Layers

Layers:

``` text
Original Map
AOI
Upstream Warnings
Independent Warnings
Validated Warnings
Rejected Warnings
Uncertain Candidates
Evidence Regions
```

Allow independent toggling.

------------------------------------------------------------------------

# 27. Visual Comparison

One of the most valuable features:

``` text
UPSTREAM
vs
INDEPENDENT QA
```

Provide a toggle:

``` text
[ Upstream ] [ Independent ] [ Compare ]
```

Compare mode should make discrepancies visually obvious.

------------------------------------------------------------------------

# 28. Warning Overlay

When a warning is selected:

``` text
Map
   ↓
Highlight geometry
   ↓
Show AOI relationship
   ↓
Show evidence crop
```

Example:

``` text
Warning #W-104

High Pressure Gas Line
Severity: HIGH

Status:
MISSED BY UPSTREAM

Spatial:
Intersects AOI

Evidence:
3 items
```

------------------------------------------------------------------------

# 29. Validation Panel

Right-side panel:

``` text
VALIDATION

Index
✓ Passed

Document
✓ Passed

Provider
✓ SGN

Legend
✓ SGN Legend v1.2

AOI
✓ Valid

Independent Scan
✓ Completed

Upstream
No Warning

Independent QA
Warning Found

Reconciliation
⚠ Missed Warning

Policy
⚠ Human Review Required
```

This is one of the most important UI elements.

------------------------------------------------------------------------

# 30. Screen 7 --- Warning Detail

Clicking a warning should open detailed information.

``` text
High Pressure Gas Line

Severity
HIGH

Provider
SGN

Status
MISSED WARNING

Upstream
Not Detected

Independent QA
Detected

AOI
Intersects

Legend
Matched

Evidence
3 items
```

Then:

``` text
Detection Evidence
Spatial Evidence
Legend Evidence
Upstream Evidence
```

------------------------------------------------------------------------

# 31. Evidence Panel

Evidence should be displayed visually.

Example:

``` text
Evidence

[ Map Crop ]
Page 2 · Region 04

[ Legend Crop ]
SGN Legend · v1.2

[ Geometry ]
AOI intersection

[ Vector Evidence ]
Path #183

[ OCR ]
"HP GAS"
Confidence 0.94
```

Each evidence object should show:

``` text
Source
Method
Version
Confidence
Timestamp
```

------------------------------------------------------------------------

# 32. Evidence Timeline

Show:

``` text
10:31:02
PDF extracted

10:31:04
Legend matched

10:31:05
AOI detected

10:31:08
Independent warning detected

10:31:09
Upstream reconciliation

10:31:10
Human review required
```

This helps debugging and audit.

------------------------------------------------------------------------

# 33. Screen 8 --- Human QA Queue

The QA queue should feel like an enterprise work queue.

### Top filters

``` text
Severity
Provider
Warning Type
SLA
Age
Assigned To
Status
```

### Table

``` text
Priority
Map
Provider
Issue
Severity
Age
SLA
Assignee
Status
```

Example:

``` text
P1
42336412_SGN.pdf
SGN
Missed Warning
HIGH
18m
32m
Unassigned
Open
```

------------------------------------------------------------------------

# 34. Queue Prioritization

Visual priority:

``` text
P1 Critical
P2 High
P3 Medium
P4 Low
```

But severity and priority must be governed by actual business policy.

------------------------------------------------------------------------

# 35. Screen 9 --- Human QA Review Workspace

This should be the **primary reviewer screen**.

Recommended layout:

``` text
┌──────────────────────────────────────────────────────────────┐
│ QA Case #QA-00124                  HIGH    SLA 18m remaining │
├───────────────┬─────────────────────────────┬───────────────┤
│ Evidence      │          MAP                │ Case Summary  │
│               │                             │               │
│ AOI           │       [MAP VIEWER]          │ Warning       │
│ Legend        │                             │ Evidence      │
│ Vector        │                             │ Reason        │
│ OCR           │                             │               │
│ Spatial       │                             │               │
├───────────────┴─────────────────────────────┴───────────────┤
│ QA Agent Summary                                            │
│ "Independent analysis detected..."                          │
├──────────────────────────────────────────────────────────────┤
│ [Approve] [Reject] [Add Warning] [Remove Warning] [Comment] │
└──────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 36. QA Agent Panel

The QA Agent should look like an assistant panel, not the main
application.

Example:

``` text
QA AGENT

Summary

The upstream system reported no warning.

Independent analysis detected a High Pressure
Gas Line intersecting the AOI.

Evidence:
✓ Legend match
✓ Vector match
✓ AOI intersection

Recommendation:
Review the highlighted line on page 2.

[View Evidence]
```

The agent should always reference actual evidence IDs.

------------------------------------------------------------------------

# 37. QA Agent Trust Design

Display:

``` text
AI-generated summary
```

and provide:

``` text
Evidence-backed
```

links.

Do not present LLM output as authoritative.

Example:

``` text
QA Agent Interpretation

Based on:
E-102
E-103
E-104
```

------------------------------------------------------------------------

# 38. Screen 10 --- Warning Catalogue

This is an administrative/business screen.

### Table

``` text
Provider
Utility
Warning
Severity
Geometry
AOI Required
Version
Status
```

Example:

``` text
SGN
Gas
High Pressure Gas Line
HIGH
LINE
Yes
v1.0
Active
```

------------------------------------------------------------------------

# 39. Warning Detail Editor

``` text
Warning Definition

Provider
[ SGN ]

Utility Type
[ Gas ]

Warning Code
SGN_HIGH_PRESSURE_GAS

Business Warning
There is a High Pressure Gas Line in this area

Severity
[ HIGH ]

Geometry
[ LINE ]

AOI Required
[ Yes ]

Detection Profile
[ SGN_HP_GAS_v2 ]

Status
[ Active ]

Version
1.0
```

Production editing should require appropriate permissions.

------------------------------------------------------------------------

# 40. Screen 11 --- Provider Management

Provider cards:

``` text
SGN
Gas
Active
Warning Definitions: 8
Legend Versions: 3
Validation Rules: 4
```

Clicking opens:

``` text
Overview
Warnings
Legends
Detection
AOI
Rules
Performance
```

------------------------------------------------------------------------

# 41. Screen 12 --- Legend Registry

Table:

``` text
Provider
Legend
Version
Source
Effective Date
Status
Used By
```

Example:

``` text
SGN
SGN Legend
v1.2
Approved PDF
2026-05-12
Active
3,421 maps
```

------------------------------------------------------------------------

# 42. Legend Detail

Display:

``` text
Legend Preview
+
Extracted Symbols
+
Color Definitions
+
Line Styles
+
Dash Patterns
+
Mapped Warning Codes
```

Example:

``` text
[Red solid line]
→ High Pressure Gas Line
→ HIGH
```

------------------------------------------------------------------------

# 43. Screen 13 --- Rules & Policy

This screen should make release policy visible.

Example:

``` text
AUTO CLEAR POLICY

✓ Map valid
✓ Provider resolved
✓ Legend resolved
✓ AOI resolved
✓ Independent scan completed
✓ Evidence complete
✓ No critical warning
✓ No unresolved conflict
✓ Audit persisted

All conditions required.
```

Use read-only view for most users.

------------------------------------------------------------------------

# 44. Screen 14 --- Reports

Reports should include:

``` text
Job Summary
Map Results
Warning Results
Provider Results
Human QA
Blocked Cases
Evidence Summary
Audit Summary
```

Export:

``` text
PDF
CSV
JSON
Excel
```

The source production Excel itself must remain unchanged.

------------------------------------------------------------------------

# 45. Screen 15 --- Evaluation

This is important for a production AI system.

Show:

``` text
Gold Dataset
Model Version
Rule Version
Legend Version
Provider
Recall
Precision
False Negative
False Positive
Escape Rate
```

Example:

``` text
SGN

Recall              99.2%
Precision           97.8%
Escape Rate          0.18%
Human Review Rate    21%
```

Never imply that these values are real until measured.

------------------------------------------------------------------------

# 46. Evaluation Comparison

Allow:

``` text
Version A
vs
Version B
```

Compare:

``` text
Recall
Precision
Escape Rate
Review Rate
Processing Time
```

------------------------------------------------------------------------

# 47. Screen 16 --- Audit Trail

Audit table:

``` text
Timestamp
User/System
Action
Job
Map
Component
Version
Decision
```

Example:

``` text
10:32:12
QA Engine
Warning Detected
DOC-123
SGN
CV v2.1
—

10:32:14
Policy Engine
Human Review
DOC-123
Rule v3.2
HUMAN_REVIEW
```

------------------------------------------------------------------------

# 48. Screen 17 --- System Health

For technical/admin users.

Cards:

``` text
API
Healthy

Queue
Healthy

Workers
12 / 12

Database
Healthy

Object Storage
Healthy

OCR
Healthy

CV
Healthy

LLM
Available
```

Important:

> LLM being unavailable should not mean the core QA pipeline is
> unavailable.

------------------------------------------------------------------------

# 49. Screen 18 --- Settings

Sections:

``` text
General
Users & Roles
Security
Notifications
Integrations
Storage
Processing
QA
LLM
Retention
Audit
```

------------------------------------------------------------------------

# 50. Responsive Design

Primary target is desktop.

### Desktop

Full three-panel map workspace.

### Tablet

Collapse:

``` text
Evidence
Validation
```

into tabs/drawers.

### Mobile

Not recommended for detailed map QA.

Mobile may support:

-   dashboard;
-   notifications;
-   job status;
-   QA queue overview.

------------------------------------------------------------------------

# 51. Component Library

Create reusable components:

``` text
Button
IconButton
StatusBadge
SeverityBadge
KPI Card
DataTable
FilterBar
Search
Tabs
Stepper
ProgressBar
Drawer
Modal
Toast
Tooltip
EvidenceCard
MapViewer
MapLayerControl
Timeline
WarningCard
DecisionCard
QA Case Card
Empty State
Error State
Loading State
```

------------------------------------------------------------------------

# 52. Status Badge Design

Example:

``` text
● AUTO CLEAR
● HUMAN REVIEW
● BLOCKED
● PROCESSING
● FAILED
```

Status badges should be consistent everywhere.

------------------------------------------------------------------------

# 53. Severity Badge Design

``` text
HIGH
MEDIUM
LOW
```

Severity should never be represented only by color.

------------------------------------------------------------------------

# 54. Decision Card

Example:

``` text
┌──────────────────────────────────┐
│ HUMAN REVIEW REQUIRED             │
│                                  │
│ Missed warning detected          │
│                                  │
│ Severity        HIGH              │
│ Evidence        3 items           │
│ AOI             Intersects        │
│                                  │
│ [Open QA Case]                   │
└──────────────────────────────────┘
```

------------------------------------------------------------------------

# 55. Empty States

Example:

``` text
No human QA cases

All current maps have completed
their validation workflow.
```

Avoid generic empty states.

------------------------------------------------------------------------

# 56. Error States

Example:

``` text
Document could not be processed

Reason:
PDF is corrupted or unreadable.

Decision:
BLOCKED

[View Technical Details]
```

Never say:

``` text
AI failed
```

without explaining the operational consequence.

------------------------------------------------------------------------

# 57. Loading States

Use skeletons and step progress.

Example:

``` text
Inspecting PDF...
████████████░░░░ 72%

Extracting vector geometry
```

------------------------------------------------------------------------

# 58. Map Interaction Design

Controls:

``` text
Zoom +
Zoom -
Fit Map
Fit AOI
Fit Warning
Reset
Layers
Evidence
Compare
```

Keyboard shortcuts can be provided for QA reviewers.

------------------------------------------------------------------------

# 59. Evidence Interaction

Selecting evidence:

``` text
Evidence Card
      ↓
Map jumps to location
      ↓
Region highlighted
      ↓
Metadata displayed
```

This is critical for reducing reviewer time.

------------------------------------------------------------------------

# 60. Compare Mode

Compare mode:

``` text
┌─────────────────────┬─────────────────────┐
│ UPSTREAM            │ INDEPENDENT QA      │
│                     │                     │
│ No warning          │ Warning detected    │
│                     │                     │
│                     │ [Highlighted]       │
└─────────────────────┴─────────────────────┘
```

For page-level comparisons, provide synchronized zoom/pan where
technically practical.

------------------------------------------------------------------------

# 61. Information Architecture

``` text
AI Map QA
│
├── Overview
│
├── Jobs
│   ├── Job List
│   ├── New Job
│   └── Job Detail
│
├── Maps
│   ├── Map Inventory
│   └── Map Detail
│
├── QA Queue
│   ├── My Cases
│   ├── Team Queue
│   └── Review Workspace
│
├── Evidence
│
├── Warnings
│   ├── Catalogue
│   └── Warning Detail
│
├── Providers
│
├── Legends
│
├── Rules
│
├── Reports
│
├── Evaluation
│
├── Audit
│
└── Settings
```

------------------------------------------------------------------------

# 62. Main User Journey

## Operations user

``` text
Login
 ↓
Overview
 ↓
New Job
 ↓
Select Root Folder
 ↓
Preflight
 ↓
Start
 ↓
Job Progress
 ↓
Map Results
 ↓
Final Report
```

------------------------------------------------------------------------

# 63. QA Reviewer Journey

``` text
Login
 ↓
QA Queue
 ↓
Open High-Priority Case
 ↓
Map Workspace
 ↓
Inspect AOI
 ↓
Inspect Warning
 ↓
Compare Upstream / Independent
 ↓
Inspect Evidence
 ↓
Read QA Agent Summary
 ↓
Make Decision
 ↓
Submit
 ↓
Audit
```

------------------------------------------------------------------------

# 64. QA Reviewer Decision UX

Buttons should be explicit.

Possible actions:

``` text
[ Confirm Warning ]

[ Reject Warning ]

[ Add Missed Warning ]

[ Remove False Positive ]

[ Request Further Review ]
```

The actual actions should map exactly to approved business workflow.

------------------------------------------------------------------------

# 65. AI Agent UX

The QA Agent should be a **contextual side panel**.

It should appear:

-   when a case is ambiguous;
-   when evidence conflicts;
-   when a reviewer requests help.

It should not continuously interrupt the reviewer.

------------------------------------------------------------------------

# 66. QA Agent Example

``` text
QA AGENT

I found a conflict:

Upstream:
No warning

Independent:
High Pressure Gas Line detected

Supporting evidence:
• Legend match — E-204
• Vector geometry — E-205
• AOI intersection — E-206

Recommended:
Review the highlighted line on page 2.

[Open E-204]
[Open E-205]
[Open E-206]
```

This is the preferred UX pattern.

------------------------------------------------------------------------

# 67. Design for Trust

Trust indicators:

``` text
Evidence-backed
Policy-approved
Versioned
Audited
```

Avoid:

``` text
AI confidence 98%
```

as the dominant UI element.

Confidence can be shown, but it should not visually imply that it is the
release authority.

------------------------------------------------------------------------

# 68. Design for Safety

For AUTO_CLEAR:

``` text
AUTO CLEAR
All mandatory checks passed
```

For HUMAN_REVIEW:

``` text
HUMAN REVIEW REQUIRED
System cannot safely auto-clear
```

For BLOCKED:

``` text
BLOCKED
Required validation could not be completed
```

The wording should be clear and operational.

------------------------------------------------------------------------

# 69. Design for Explainability

Every decision should provide:

``` text
Decision
Reason
Evidence
Rules
Next Action
```

Example:

``` text
HUMAN REVIEW

Reason:
Independent QA found a High Pressure Gas Line
that was not reported upstream.

Evidence:
3 items

Rule:
HIGH severity missed warning → human review
```

------------------------------------------------------------------------

# 70. Design for Auditability

The UI should allow:

``` text
Decision
→ Evidence
→ Processing Step
→ Version
→ Timestamp
```

Example:

``` text
Decision: HUMAN_REVIEW
Policy: v3.2
Legend: SGN v1.2
CV: v2.1
OCR: v1.4
Timestamp: 2026-08-30 10:31:08
```

------------------------------------------------------------------------

# 71. Design for Production Operations

Operations users should never have to inspect raw logs.

Instead:

``` text
Processing Failed

Document:
42336412_SGN.pdf

Stage:
PDF Inspection

Reason:
Corrupted PDF

Action:
Map blocked

[Technical Details]
```

Technical details can reveal:

``` text
error code
stack trace
worker
request ID
```

only to authorized users.

------------------------------------------------------------------------

# 72. Design for Performance

The interface should support large jobs.

For example:

``` text
2,400 maps
```

Do not load all rows into the browser.

Use:

-   pagination;
-   server-side filtering;
-   server-side sorting;
-   virtualized tables;
-   lazy loading;
-   progressive evidence loading.

------------------------------------------------------------------------

# 73. Accessibility

Target:

``` text
WCAG 2.1 AA
```

Requirements:

-   keyboard navigation;
-   visible focus;
-   sufficient contrast;
-   screen-reader labels;
-   non-color status indicators;
-   accessible tables;
-   accessible modal/dialog behavior.

------------------------------------------------------------------------

# 74. Notifications

Users can receive:

``` text
Job completed
Job blocked
High-priority QA case
SLA approaching
QA case assigned
Processing failure
System incident
```

Notifications should be actionable.

------------------------------------------------------------------------

# 75. Search

Global search should support:

``` text
Job ID
Document ID
Map filename
Provider
Warning code
Warning text
QA case ID
```

Example:

``` text
Search:
42336412
```

Results:

``` text
Map
Job
Warnings
QA Case
Evidence
Audit
```

------------------------------------------------------------------------

# 76. Filtering

Common filters:

``` text
Provider
Utility Type
Warning
Severity
Decision
Job
Date
Reviewer
SLA
Processing Status
```

Filters should persist during navigation where appropriate.

------------------------------------------------------------------------

# 77. Design Tokens

Recommended token categories:

``` text
color.*
spacing.*
radius.*
shadow.*
font.*
motion.*
z-index.*
```

Do not hard-code visual values across components.

------------------------------------------------------------------------

# 78. Spacing System

Use a consistent 4/8-based spacing system.

Example:

``` text
4
8
12
16
20
24
32
40
48
64
```

------------------------------------------------------------------------

# 79. Border Radius

Suggested:

``` text
Small controls: 6px
Cards: 10–12px
Large panels: 12–16px
```

Avoid excessive rounded/pill UI.

Use pill shapes primarily for statuses/tags.

------------------------------------------------------------------------

# 80. Shadows

Use subtle elevation:

``` text
Card:
very light shadow

Modal:
stronger shadow

Floating controls:
medium shadow
```

Avoid heavy neumorphism.

------------------------------------------------------------------------

# 81. Motion

Animation should communicate state.

Examples:

-   job progress;
-   queue updates;
-   panel transitions;
-   evidence highlighting;
-   loading.

Avoid decorative animation in production QA workflows.

------------------------------------------------------------------------

# 82. Map-Specific Visual Language

The map viewer should preserve the source map's colors.

Do not recolor the actual map unnecessarily.

Use an independent annotation layer for:

``` text
AOI
Warning
Evidence
Upstream
Independent
```

This avoids altering the meaning of the source document.

------------------------------------------------------------------------

# 83. Map Annotation Colors

Recommended semantic annotation scheme:

``` text
AOI
Blue outline

Upstream warning
Purple/blue annotation

Independent warning
Orange annotation

Confirmed warning
Red annotation

Uncertain candidate
Amber annotation

Rejected/false positive
Gray annotation
```

Exact colors should be validated for accessibility and should not
obscure source-map semantics.

------------------------------------------------------------------------

# 84. Annotation Legend

Always show:

``` text
Map Layers

□ AOI
□ Upstream
□ Independent
□ Confirmed
□ Uncertain
□ Evidence
```

Users should be able to hide layers.

------------------------------------------------------------------------

# 85. QA Case Detail Layout

Recommended hierarchy:

``` text
1. Decision / Severity
2. Why it was escalated
3. Map
4. Warning
5. Evidence
6. Upstream vs Independent
7. Legend
8. Rules
9. QA Agent
10. Audit
```

This order follows the reviewer's decision-making process.

------------------------------------------------------------------------

# 86. Design Anti-Patterns

Do not create:

### Anti-pattern 1

Huge chatbot as homepage.

### Anti-pattern 2

Single "AI confidence" number controlling everything.

### Anti-pattern 3

One giant dashboard with every metric.

### Anti-pattern 4

Map viewer with no evidence linkage.

### Anti-pattern 5

Warning list without map location.

### Anti-pattern 6

Map image with no source/page metadata.

### Anti-pattern 7

AI recommendation without evidence IDs.

### Anti-pattern 8

AUTO_CLEAR with no explanation.

### Anti-pattern 9

Raw technical logs as primary UX.

### Anti-pattern 10

Editing production Excel from the UI.

------------------------------------------------------------------------

# 87. Reference-Inspired Design Decisions

The supplied Dribbble reference is useful primarily as a
**visual/product-design reference**, not as a technical architecture
reference.

The reference is described as a mixture of multiple SaaS automation QA
screens for Preflight by Applitools. citeturn0view0

For this project, the useful design characteristics to carry forward
are:

-   multi-screen SaaS product;
-   focused testing workflow;
-   modern dashboard;
-   clear test/run status;
-   compact data views;
-   workflow-oriented screens;
-   reusable cards and controls;
-   clean enterprise interface.

We should **not copy the reference literally**.

Instead, adapt the design language to the specific map-QA workflow.

------------------------------------------------------------------------

# 88. Design Difference from the Reference

Reference concept:

``` text
Automation QA
→ Tests
→ Runs
→ Results
```

Our product:

``` text
Map QA
→ Jobs
→ Maps
→ Warnings
→ Evidence
→ Decisions
→ Human QA
```

Therefore, our most important screen should be the **Map QA Workspace**,
not a generic test editor.

------------------------------------------------------------------------

# 89. Final Navigation Concept

``` text
                    AI MAP QA
                        |
       +----------------+----------------+
       |                |                |
   OPERATIONS        VALIDATION       GOVERNANCE
       |                |                |
   Overview             Maps          Warnings
   Jobs                 Evidence      Providers
   QA Queue             Reports       Legends
                                         Rules
                                         Evaluation
                                         Audit
```

------------------------------------------------------------------------

# 90. Final Product Experience

The ideal user experience is:

``` text
1. Submit folder
       ↓
2. See job progress
       ↓
3. See which maps passed
       ↓
4. See which maps need review
       ↓
5. Open one case
       ↓
6. Immediately see the map
       ↓
7. See AOI
       ↓
8. See warning
       ↓
9. Compare upstream vs independent
       ↓
10. Inspect evidence
       ↓
11. Understand why
       ↓
12. Make decision
       ↓
13. Finish
```

The reviewer should not need to understand:

-   vector extraction;
-   OpenCV;
-   OCR;
-   PostGIS;
-   queues;
-   model versions;

unless they explicitly open technical details.

------------------------------------------------------------------------

# 91. MVP Screen Priority

Build in this order.

## P0 --- Must Have

1.  Login
2.  Overview
3.  Jobs
4.  New Job
5.  Job Detail
6.  Map Inventory
7.  Map QA Detail
8.  Human QA Queue
9.  Human QA Workspace
10. Evidence Viewer

## P1 --- Production Governance

11. Warning Catalogue
12. Providers
13. Legends
14. Rules
15. Reports
16. Audit

## P2 --- Advanced

17. Evaluation
18. System Health
19. Advanced QA Agent
20. Advanced analytics

------------------------------------------------------------------------

# 92. MVP Primary Screen

If only one screen receives exceptional design attention, it should be:

> **Map QA Review Workspace**

Because this is where the system's actual value is delivered.

It should combine:

``` text
Map
+
AOI
+
Warning
+
Upstream
+
Independent QA
+
Evidence
+
Policy
+
QA Agent
+
Human Decision
```

without overwhelming the reviewer.

------------------------------------------------------------------------

# 93. Final UI Architecture

``` text
                    AI MAP QA PLATFORM
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
   OPERATIONS          QA WORKSPACE       GOVERNANCE
       |                   |                   |
       v                   v                   v
    Overview          Map QA Detail       Catalogue
    Jobs              Evidence            Providers
    New Job           Comparison           Legends
    Reports           QA Agent             Rules
                      Human Decision        Audit
                                              |
                                              v
                                          Evaluation
```

------------------------------------------------------------------------

# 94. Final Map QA Workspace Architecture

``` text
┌──────────────────────────────────────────────────────────────────────┐
│ AI MAP QA  /  JOB-1042  /  42336412_SGN.pdf                          │
│                                              HUMAN REVIEW   HIGH     │
├─────────────┬──────────────────────────────────┬─────────────────────┤
│ PAGES       │                                  │ VALIDATION          │
│             │                                  │                     │
│ Page 1      │                                  │ ✓ Index             │
│ Page 2  ◉   │          MAP VIEWER              │ ✓ Document          │
│ Page 3      │                                  │ ✓ Provider          │
│ Page 4      │        AOI + WARNINGS            │ ✓ Legend            │
│             │                                  │ ✓ AOI               │
│             │                                  │ ✓ Independent QA    │
│             │                                  │ ⚠ Reconciliation    │
│             │                                  │ ⚠ Policy            │
├─────────────┴──────────────────────────────────┴─────────────────────┤
│ Warnings | Evidence | Legend | Comparison | QA Agent | Audit         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Selected Warning                                                     │
│ High Pressure Gas Line                                               │
│ HIGH · MISSED WARNING · AOI INTERSECTION                             │
│                                                                      │
│ [Evidence] [Open QA Case]                                            │
└──────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 95. Final Design Philosophy

The product should feel like:

> **"A control center for trustworthy automated map QA."**

Not:

> "An AI chatbot that analyzes PDFs."

The UI should continuously communicate:

``` text
What did the system check?
What did it find?
What evidence supports it?
What does policy say?
Does a human need to act?
```

------------------------------------------------------------------------

# 96. Definition of Design Done

The design is complete when:

-   all P0 screens are defined;
-   primary workflows are defined;
-   map QA workspace is fully specified;
-   warning/evidence interactions are specified;
-   human QA flow is specified;
-   QA Agent interaction is bounded;
-   decision states are visually consistent;
-   responsive behavior is defined;
-   accessibility is considered;
-   component library is defined;
-   design tokens are defined;
-   empty/error/loading states are defined;
-   audit/evidence views are defined;
-   production operations are supported;
-   the design can be implemented directly in Figma/frontend without
    inventing missing UX behavior.

------------------------------------------------------------------------

# 97. Final Design Statement

The final product should combine the **clean, modern, multi-screen
SaaS/testing feel** of the referenced Dribbble work with a specialized
**map-review workspace** designed around evidence, spatial inspection,
warning reconciliation, and human QA.

The most important design principle is:

> **Make the complexity of the backend invisible, but make the evidence
> behind every decision visible.**

Reference inspiration:

https://dribbble.com/shots/23183274-Multiple-screens-of-Automation-QA-Testing
