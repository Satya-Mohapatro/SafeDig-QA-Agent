# SafeDig AI — Complete End-to-End Execution & Code Working Mechanism
**UK Underground Utility Dig-Safety Map QA & Validation Platform**  
**Compliance Standard**: UK Health and Safety Guidance 47 (HSG47) & CDM 2015  
**Core Invariant**: Zero Escaped Hazards (`SAFE_MODE=True`)

---

## 1. High-Level Architectural Flow & System Overview

SafeDig is an automated, AI-augmented safety validation platform engineered to prevent underground utility strikes during civil excavations across the United Kingdom.

Under UK statutory regulations (**HSG47: Avoiding Danger from Underground Services**), striking buried infrastructure (high-voltage electricity lines, high-pressure gas mains, trunk fiber, or water mains) results in lethal explosions, arc-flash electrocution, service blackouts, and unlimited financial/criminal liability.

SafeDig enforces a non-negotiable architectural invariant:
> **Domain Safety Invariant (`SAFE_MODE=True`)**  
> SafeDig re-validates upstream utility warning claims against actual CAD/GIS engineering drawings within the excavation site. **The target is zero escaped hazards.** Every detected hazard is escalated to a certified human safety engineer. Every ambiguous, corrupted, contradictory, or degraded case must fail toward `HUMAN_REVIEW` or `BLOCKED`—**never toward `AUTO_CLEAR`**. A false negative is never traded for a cleaner false-positive metric.

```
[ User Action: Web Console (Upload/Click) OR CLI (run_map_qa_pipeline) ]
                                  │
                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 1: Intake & Self-Healing Path Resolution                                          │
 │ Modules: src/utils/paths.py ──► src/index/parser.py ──► src/ingestion/inventory.py      │
 │ • Repairs foreign machine paths dynamically                                            │
 │ • Reads master index.xlsx (Utility Name, Work Boundary, Status, Raw Comments)          │
 │ • Separates technical CAD maps from non-map brochures (letters, leaflets, valve advice) │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 2: PDF Document Ingestion & Modality Classification                               │
 │ Modules: src/pdf/ ──► src/domain/document.py                                            │
 │ • Opens byte stream in PyMuPDF (fitz)                                                   │
 │ • Calculates SHA-256 hash & validates %PDF- header magic                                │
 │ • Classifies document modality: VECTOR (native paths), RASTER (scanned), or HYBRID      │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 3: Knowledge Base & Cartographic Legend Resolution                                │
 │ Modules: src/legends/ ──► src/warnings/ ──► src/domain/legend.py                        │
 │ • Identifies statutory undertaker: UKPN, SGN, Cadent, NGET, Virgin Media, Openreach     │
 │ • Loads provider warning taxonomy (HSG47 voltage thresholds, gas pressures)             │
 │ • Loads drawing legend: RGB color bands (ΔE ≤ 28), stroke widths, line patterns         │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 4: Spatial AOI Extraction & Rotation Mapping                                      │
 │ Module: src/aoi/detector.py                                                             │
 │ • Detects red/magenta/yellow dashed dig-site boundary line                              │
 │ • Converts unrotated PDF mediabox coords ◄► visual rendered space (0°, 90°, 180°, 270°) │
 │ • Validates closed Shapely Polygon (coords[0] == coords[-1], area > 0, vertices ≥ 4)    │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 5: Dual-Engine Spatial Asset Detection                                            │
 │ Modules: src/detection/engine.py ──► src/vector/ ──► src/cv/                            │
 │ • Channel A (Vector Engine): Extracts raw PDF strokes; excludes dashed lines (AOI)      │
 │ • Channel B (CV Engine): 300 DPI rasterization, OpenCV HSV color mask & contour search   │
 │ • OCR/Text Booster: Scans AOI for electrical/gas label tags ("11kV", "HP", "SUBSTATION")│
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 6: Spatial Buffer Math & Reconciliation                                           │
 │ Modules: src/spatial/engine.py ──► src/reconciliation/engine.py                         │
 │ • Buffers AOI: 500mm hand-dig zone, 3.0m HV electric, 15.0m High-Pressure Gas          │
 │ • Computes 2D Shapely geometric intersection: polygon.intersects(vector_line)           │
 │ • Classifies outcome: CONFIRMED_CLEAN, MATCH, MISSED_WARNING, POSSIBLE_FALSE_POSITIVE   │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 7: The 17 Mandatory Release Gates & Policy Engine                                 │
 │ Modules: src/policy/gates.py ──► src/policy/engine.py                                   │
 │ • Evaluates Gates 01 to 17 deterministically                                            │
 │ • Priority Decision Ladder:                                                             │
 │     - All 17 Pass & Clean               ──► 🟢 AUTO_CLEAR                               │
 │     - MISSED_WARNING / HV Asset / Fail  ──► 🟡 HUMAN_REVIEW                             │
 │     - File Missing / Ambiguous Match    ──► 🔴 BLOCKED                                  │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │ PHASE 8: LangGraph Workflow, Advisory LLM & Forensic SQLite Audit                       │
 │ Modules: src/orchestration/graph.py ──► src/llm/ ──► src/db/persistence.py              │
 │ • LangGraph executes stateful DAG                                                       │
 │ • Ollama (Qwen 2.5 / Llama 3.2) generates operator summary (Zero Validation Authority)  │
 │ • Builds Evidence Package (AOI crop, whole-sheet context, neon overlay, GeoJSON)       │
 │ • Locks SHA-256 signatures, timestamps & gate states into safedig.db                    │
 └────────────────────────────────────────┬────────────────────────────────────────────────┘
                                          │
                                          ▼
 [ UI Render: Interactive Web Console at http://127.0.0.1:8000/#qa-workspace ]
 (Animated Radar Loader, Canvas Pan/Zoom, 17 Gate Badges, Human Review Sign-Off)
```

---

## 2. Chronological Deep Dive into the 8 Execution Phases

### Phase 1: Intake & Self-Healing Path Resolution
- **Source Modules**: `src/utils/paths.py`, `src/index/parser.py`, `src/ingestion/inventory.py`
- **Core Functions**: `resolve_folder_path()`, `parse_index_excel()`, `resolve_documents()`
- **Execution Details**:
  1. SafeDig resolves cross-environment path discrepancies via `resolve_folder_path()`. If a job folder was generated on another machine with hardcoded foreign paths (e.g. `d:/Safedig_AG/data/...`), the resolver extracts the directory basename and locates the matching folder in the active workspace.
  2. The parser reads `index.xlsx` to extract statutory disclosure records:
     - `utility_name`: Canonical provider name.
     - `is_asset_present`: Upstream claim (`Yes` vs `No`).
     - `raw_warning`: Upstream disclaimer or warning text.
     - `raw_comments`: Confidence score or survey details.
  3. The inventory matcher tokenizes all files in the folder. Non-map files (e.g. `UKPN Customer Letter.pdf`, `Nearest_Hospital.pdf`, `Valve safety advice.pdf`) are filtered out. Exactly one authoritative drawing is mapped to each index row with status `UNIQUE`.

### Phase 2: PDF Document Ingestion & Modality Classification
- **Source Modules**: `src/pdf/inspector.py`, `src/domain/document.py`
- **Core Functions**: `inspect_pdf()`, `pymupdf.open()`
- **Execution Details**:
  1. The physical PDF file is verified to exist on disk and have non-zero byte size.
  2. A SHA-256 cryptographic hash of the raw PDF bytes is computed for tamper-proof audit trails.
  3. PyMuPDF inspects the page stream contents:
     - If vector draw operations (`m`, `l`, `c`) exist $ightarrow$ `PDFModality.VECTOR`.
     - If only image XObjects exist $ightarrow$ `PDFModality.RASTER`.
     - If both exist $ightarrow$ `PDFModality.HYBRID`.
     - If file is corrupt or zero pages $ightarrow$ `PDFModality.UNREADABLE` (triggers `BLOCKED`).

### Phase 3: Knowledge Base & Cartographic Legend Resolution
- **Source Modules**: `src/legends/`, `src/warnings/`, `src/domain/legend.py`
- **Core Functions**: `resolve_legend()`, `master_warning_catalogue.get_definitions_for_provider()`
- **Execution Details**:
  1. Normalizes the provider to a registered UK statutory undertaker (UKPN, SGN, Cadent, National Grid, Virgin Media, Openreach, Thames Water, GTC).
  2. Loads the statutory warning catalogue defining HSG47 hazard levels (CRITICAL, HIGH, MEDIUM, LOW), voltage levels (11kV, 33kV, 132kV), and gas pressure bands (LP, MP, IP, HP).
  3. Resolves the cartographic legend profile containing target RGB values, stroke width bands in points (`pt`), and RGB tolerance $\Delta E \le 28.0$.

### Phase 4: Spatial AOI Extraction & Rotation Mapping
- **Source Modules**: `src/aoi/detector.py`, `src/domain/aoi.py`
- **Core Functions**: `detect_aoi_from_pdf()`, `_visual_to_unrotated()`, `_unrotated_to_visual()`
- **Execution Details**:
  1. **Rotation Math**: PyMuPDF's `get_drawings()` returns coordinates in unrotated mediabox space. CAD maps are frequently rotated by 90°, 180°, or 270°. SafeDig converts coordinates back and forth using custom transformation formulas.
  2. **Dashed Perimeter Search**: Scans for dashed vector lines forming the dig boundary. Excludes tiny legend boxes ($<15	ext{ pt}$) and page outer margins ($>98\%$).
  3. **Geometric Integrity**: Validates that the polygon is topologically closed (`coords[0] == coords[-1]`), non-degenerate, and resides within page canvas bounds. If no boundary line is found, SafeDig safely falls back to the entire map canvas.

### Phase 5: Dual-Engine Spatial Asset Detection
- **Source Modules**: `src/detection/engine.py`, `src/vector/analyzer.py`, `src/cv/`
- **Core Functions**: `detect_independent_warnings()`, `filter_drawings_by_style()`
- **Execution Details**:
  1. **Vector Scanning**: Extracts all vector drawing paths. Enforces `exclude_dashed=True` so that the dashed site boundary itself is never misidentified as an underground cable.
  2. **Color & Stroke Matching**: Compares solid line stroke colors against the legend profile using Euclidean color distance:
     $$\Delta E = \sqrt{(R_1 - R_2)^2 + (G_1 - G_2)^2 + (B_1 - B_2)^2}$$
  3. **Raster CV Scanning**: Concurrently runs 300 DPI raster image processing with OpenCV color thresholding and contour detection to catch point symbols (substations, link boxes, valves).
  4. **Text Booster**: Extracts text within the AOI to correlate asset tags (e.g. `"11kV"`, `"HP GAS"`).

### Phase 6: Spatial Buffer Math & Upstream Reconciliation
- **Source Modules**: `src/spatial/engine.py`, `src/reconciliation/engine.py`
- **Core Functions**: `reconcile_warnings()`, `spatial_engine.check_intersection()`
- **Execution Details**:
  1. Constructs statutory clearance buffers around the AOI: 500mm hand-dig safety zone, 3.0m high-voltage electric buffer, and 15.0m Cadent/SGN high-pressure gas buffer.
  2. Evaluates 2D Shapely geometric intersection: `polygon.intersects(asset_geom)` and `polygon.distance(asset_geom)`.
  3. Compares independent findings against upstream declarations:
     - `CONFIRMED_CLEAN`: Both claim and drawing show clean.
     - `MATCH`: Upstream declared assets and drawing confirms intersecting assets.
     - `MISSED_WARNING`: Upstream claimed "No assets", but SafeDig detected buried infrastructure inside the dig site.
     - `POSSIBLE_FALSE_POSITIVE`: Upstream claimed assets, but drawing is clear inside buffer.

### Phase 7: The 17 Mandatory Release Gates & Policy Routing
- **Source Modules**: `src/policy/gates.py`, `src/policy/engine.py`
- **Core Functions**: `evaluate_all_17_gates()`, `PolicyEngine.evaluate()`
- **Execution Details**:
  1. Evaluates all 17 gates simultaneously:
     `01_INDEX_VALID`, `02_MAP_EXISTS`, `03_MAPPING_VALID`, `04_MAP_READABLE`, `05_PROVIDER_RESOLVED`, `06_CATALOGUE_RESOLVED`, `07_LEGEND_RESOLVED`, `08_AOI_RESOLVED`, `09_AOI_VALIDATION_COMPLETED`, `10_INDEPENDENT_SCAN_COMPLETED`, `11_RECONCILIATION_COMPLETED`, `12_NO_UNRESOLVED_CRITICAL_WARNING`, `13_NO_DETECTOR_DISAGREEMENT`, `14_NO_IMAGE_QUALITY_ISSUE`, `15_PROVIDER_RULES_PASS`, `16_EVIDENCE_COMPLETE`, `17_AUDIT_PERSISTED`.
  2. **Deterministic Priority Routing**:
     - Early exit: `is_asset_present == False` $ightarrow$ `AUTO_CLEAR`.
     - Early exit: Missing/corrupt map or ambiguous document match $ightarrow$ `BLOCKED`.
     - Hazard exit: `MISSED_WARNING`, `POSSIBLE_FALSE_POSITIVE`, or confirmed 11kV/HP Gas (`Gate 12` fail) $ightarrow$ **`HUMAN_REVIEW`**.
     - Only if all 17 gates pass and evidence is complete $ightarrow$ **`AUTO_CLEAR`**.

### Phase 8: LangGraph Workflow, Advisory LLM & SQLite Audit
- **Source Modules**: `src/orchestration/graph.py`, `src/orchestration/nodes.py`, `src/db/persistence.py`
- **Core Functions**: `build_map_qa_graph()`, `llm_advisory_node()`, `persist_to_db_node()`
- **Execution Details**:
  1. LangGraph executes state machine nodes: `ingest_and_index_node` $ightarrow$ `process_qa_and_policy_node` $ightarrow$ (conditional edge) $ightarrow$ `llm_advisory_node` $ightarrow$ `finalize_report_node` $ightarrow$ `persist_to_db_node`.
  2. The LLM node queries local Ollama (`qwen2.5:7b` / `llama3.2:3b`) to synthesize natural-language operator advisory notes. **Zero Validation Authority**: The LLM cannot override, approve, or clear any gate. Offline fallback explainer operates with 0ms latency.
  3. The persistence service commits immutable decision records, SHA-256 digital signatures, timestamps, and gate booleans into `safedig.db`.

---

## 3. Web Console, Map Viewer & Human Review Workspace

- **Web Endpoints**:
  - `GET /api/v1/qa/workspace/{job_id}/{doc_id}`: Delivers complete review workspace payload.
  - `GET /api/v1/evidence/{job_id}/{doc_id}/map-image`: Streams full-sheet context image.
  - `GET /api/v1/evidence/{job_id}/{doc_id}/aoi-crop`: Streams high-resolution excavation cutout.
  - `POST /api/v1/qa/disposition/{job_id}/{doc_id}`: Records human engineer sign-off override.
- **Frontend Experience**:
  1. **Radar Pulse & Scanner Loader**: When an operator inspects a drawing, `#ws-map-loader` activates an animated radar scanner overlay with pulsing gradient rings while high-resolution map tiles stream from the backend. The loader automatically dismisses upon DOM image render.
  2. **Canvas Controls**: Hardware-accelerated pan (click-and-drag) and zoom (50% to 600%) with instant AOI centering.
  3. **Gate Status Panel**: Visual 17-gate breakdown with green checkmarks or red failure indicators. Clicking any gate highlights the relevant geometry on the map.
  4. **Human Review Override**: Certified safety engineers can record an override (Accept Risk / Reject Permit) with mandatory license/credential logging.

---

## 4. Execution Commands

### Run Standalone CLI Pipeline
```powershell
.\venv\Scripts\python.exe -c "from src.pipeline import run_map_qa_pipeline; res = run_map_qa_pipeline('Data/548357_172783'); print('Processed:', len(res['results']), 'Decision:', res['results'][0]['decision'])"
```

### Run LangGraph Stateful Graph
```powershell
.\venv\Scripts\python.exe -c "from src.orchestration.graph import map_qa_workflow; state = map_qa_workflow.invoke({'root_dir': 'Data/548357_172783'}); print('Overall Decision:', state['overall_decision'])"
```

### Launch Production Web Server & UI Console
```powershell
.\venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to `http://127.0.0.1:8000/#qa-workspace` to inspect jobs with the radar loader and interactive map controls.
