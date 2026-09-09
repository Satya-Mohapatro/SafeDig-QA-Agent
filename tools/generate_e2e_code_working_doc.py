"""
SafeDig AI - Complete End-to-End Execution & Code Working Mechanism Document Generator
Outputs:
1. Documentation/SafeDig_Complete_End_to_End_Execution_and_Code_Working_Mechanism.md
2. Documentation/SafeDig_Complete_End_to_End_Execution_and_Code_Working_Mechanism.pdf
3. SafeDig_Complete_End_to_End_Execution_and_Code_Working_Mechanism.pdf (Root mirror)
"""

import os
import shutil
import pymupdf

DOCS_DIR = r"D:\SafeDig_AG\Documentation"
ROOT_DIR = r"D:\SafeDig_AG"
MD_PATH = os.path.join(DOCS_DIR, "SafeDig_Complete_End_to_End_Execution_and_Code_Working_Mechanism.md")
PDF_PATH = os.path.join(DOCS_DIR, "SafeDig_Complete_End_to_End_Execution_and_Code_Working_Mechanism.pdf")
ROOT_PDF_PATH = os.path.join(ROOT_DIR, "SafeDig_Complete_End_to_End_Execution_and_Code_Working_Mechanism.pdf")

os.makedirs(DOCS_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# 1. MARKDOWN DOCUMENT CONTENT
# ----------------------------------------------------------------------
MD_CONTENT = """# SafeDig AI — Complete End-to-End Execution & Code Working Mechanism
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
     - If vector draw operations (`m`, `l`, `c`) exist $\rightarrow$ `PDFModality.VECTOR`.
     - If only image XObjects exist $\rightarrow$ `PDFModality.RASTER`.
     - If both exist $\rightarrow$ `PDFModality.HYBRID`.
     - If file is corrupt or zero pages $\rightarrow$ `PDFModality.UNREADABLE` (triggers `BLOCKED`).

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
  2. **Dashed Perimeter Search**: Scans for dashed vector lines forming the dig boundary. Excludes tiny legend boxes ($<15\text{ pt}$) and page outer margins ($>98\%$).
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
     - Early exit: `is_asset_present == False` $\rightarrow$ `AUTO_CLEAR`.
     - Early exit: Missing/corrupt map or ambiguous document match $\rightarrow$ `BLOCKED`.
     - Hazard exit: `MISSED_WARNING`, `POSSIBLE_FALSE_POSITIVE`, or confirmed 11kV/HP Gas (`Gate 12` fail) $\rightarrow$ **`HUMAN_REVIEW`**.
     - Only if all 17 gates pass and evidence is complete $\rightarrow$ **`AUTO_CLEAR`**.

### Phase 8: LangGraph Workflow, Advisory LLM & SQLite Audit
- **Source Modules**: `src/orchestration/graph.py`, `src/orchestration/nodes.py`, `src/db/persistence.py`
- **Core Functions**: `build_map_qa_graph()`, `llm_advisory_node()`, `persist_to_db_node()`
- **Execution Details**:
  1. LangGraph executes state machine nodes: `ingest_and_index_node` $\rightarrow$ `process_qa_and_policy_node` $\rightarrow$ (conditional edge) $\rightarrow$ `llm_advisory_node` $\rightarrow$ `finalize_report_node` $\rightarrow$ `persist_to_db_node`.
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
.\\venv\\Scripts\\python.exe -c "from src.pipeline import run_map_qa_pipeline; res = run_map_qa_pipeline('Data/548357_172783'); print('Processed:', len(res['results']), 'Decision:', res['results'][0]['decision'])"
```

### Run LangGraph Stateful Graph
```powershell
.\\venv\\Scripts\\python.exe -c "from src.orchestration.graph import map_qa_workflow; state = map_qa_workflow.invoke({'root_dir': 'Data/548357_172783'}); print('Overall Decision:', state['overall_decision'])"
```

### Launch Production Web Server & UI Console
```powershell
.\\venv\\Scripts\\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Navigate to `http://127.0.0.1:8000/#qa-workspace` to inspect jobs with the radar loader and interactive map controls.
"""

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(MD_CONTENT)

print(f"[OK] Wrote Markdown: {MD_PATH}")


# ----------------------------------------------------------------------
# 2. MULTI-PAGE PROFESSIONAL PDF GENERATION VIA PYMUPDF
# ----------------------------------------------------------------------
def create_e2e_code_working_pdf(out_path: str):
    doc = pymupdf.open()
    
    NAVY = (15/255, 23/255, 42/255)
    ACCENT_BLUE = (37/255, 99/255, 235/255)
    ICE_BLUE = (239/255, 246/255, 255/255)
    SLATE_TEXT = (51/255, 65/255, 85/255)
    MUTED_TEXT = (100/255, 116/255, 139/255)
    LINE_BORDER = (226/255, 232/255, 240/255)
    GREEN_PASS = (22/255, 101/255, 52/255)
    RED_FAIL = (153/255, 27/255, 27/255)
    AMBER_WARN = (146/255, 64/255, 14/255)

    def draw_header(page, title: str, subtitle: str):
        page.draw_rect(pymupdf.Rect(0, 0, 595, 75), color=None, fill=NAVY)
        page.insert_text(pymupdf.Point(40, 36), title, fontsize=15, fontname="helv", color=(1, 1, 1))
        page.insert_text(pymupdf.Point(40, 54), subtitle, fontsize=9, fontname="helv", color=(147/255, 197/255, 253/255))
        page.draw_rect(pymupdf.Rect(435, 24, 555, 48), color=None, fill=(30/255, 41/255, 59/255))
        page.insert_text(pymupdf.Point(445, 39), "HSG47 COMPLIANT", fontsize=7.5, fontname="helv", color=(52/255, 211/255, 153/255))

    def draw_footer(page, page_num: int, total_pages: int):
        page.draw_line(pymupdf.Point(40, 805), pymupdf.Point(555, 805), color=LINE_BORDER, width=0.8)
        page.insert_text(pymupdf.Point(40, 818), "SafeDig AI Platform — Complete End-to-End Execution & Code Working Mechanism", fontsize=7.5, fontname="helv", color=MUTED_TEXT)
        page.insert_text(pymupdf.Point(505, 818), f"Page {page_num} of {total_pages}", fontsize=7.5, fontname="helv", color=MUTED_TEXT)

    # -------------------------------------------------------------
    # PAGE 1: Architecture Overview & The 8 Phases Summary
    # -------------------------------------------------------------
    p1 = doc.new_page(width=595, height=842)
    draw_header(p1, "SafeDig AI — End-to-End Execution & Code Mechanism", "Architectural Overview & Statutory Safety Compliance")
    
    y = 95
    p1.insert_text(pymupdf.Point(40, y), "1. Executive Summary & Safety Invariant", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 15

    intro_p1 = (
        "SafeDig is an automated, AI-augmented safety validation platform engineered to prevent utility strikes during\n"
        "civil excavations in the United Kingdom. Under UK statutory frameworks (HSG47 and CDM 2015), striking buried\n"
        "infrastructure carries catastrophic risks: gas explosions, electric flashovers, hospital blackouts, and unlimited\n"
        "financial and criminal liabilities. SafeDig re-validates upstream utility claims against physical drawings."
    )
    p1.insert_text(pymupdf.Point(40, y), intro_p1, fontsize=8, fontname="helv", color=SLATE_TEXT)
    y += 48

    p1.draw_rect(pymupdf.Rect(40, y, 555, y + 54), color=(254/255, 202/255, 202/255), fill=(254/255, 242/255, 242/255))
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(40, y + 54), color=(220/255, 38/255, 38/255), width=3)
    p1.insert_text(pymupdf.Point(48, y + 15), "NON-NEGOTIABLE DOMAIN INVARIANT (HSG47 COMPLIANCE)", fontsize=8.5, fontname="helv", color=RED_FAIL)
    inv_txt = (
        "SAFE_MODE is permanently active. Every detected hazard is surfaced to a certified human safety engineer.\n"
        "Zero escaped hazards is the non-negotiable target. Every ambiguous, corrupted, or contradictory document\n"
        "must fail toward HUMAN_REVIEW or BLOCKED, NEVER toward AUTO_CLEAR. A false negative is never traded for\n"
        "a cleaner false-positive statistic."
    )
    p1.insert_text(pymupdf.Point(48, y + 27), inv_txt, fontsize=7.5, fontname="helv", color=(127/255, 29/255, 29/255))
    y += 68

    p1.insert_text(pymupdf.Point(40, y), "2. The 8 Chronological Pipeline Phases", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=LINE_BORDER, width=1)
    y += 14

    phases_p1 = [
        ("Phase 1: Ingestion & Paths", "src/utils/paths.py, src/index/parser.py", "Self-healing path resolution; parses index.xlsx; separates technical CAD maps from brochures."),
        ("Phase 2: PDF Structure", "src/pdf/inspector.py, src/domain/document.py", "PyMuPDF opens byte stream, computes SHA-256 hash, classifies modality (VECTOR, RASTER, HYBRID)."),
        ("Phase 3: Knowledge Base", "src/legends/, src/warnings/", "Identifies statutory provider (UKPN, SGN, Cadent); loads warning catalogue & cartographic legend."),
        ("Phase 4: Spatial AOI", "src/aoi/detector.py", "Extracts red/magenta dashed site boundary; converts 0/90/180/270 deg rotation coords via Shapely."),
        ("Phase 5: Dual CV Scan", "src/detection/engine.py, src/vector/, src/cv/", "Channel A vector extraction (excludes dashed AOI) + Channel B 300 DPI raster CV & text booster."),
        ("Phase 6: Spatial Reconcile", "src/spatial/engine.py, src/reconciliation/", "Applies 5m LV / 15m HP Gas buffers; computes 2D intersection; reconciles against upstream claims."),
        ("Phase 7: The 17 Gates", "src/policy/gates.py, src/policy/engine.py", "Simultaneously evaluates all 17 gates. Priority routing to AUTO_CLEAR, HUMAN_REVIEW, or BLOCKED."),
        ("Phase 8: LangGraph & Audit", "src/orchestration/graph.py, safedig.db", "Stateful DAG execution; Ollama Qwen 2.5 advisory summary; locks SHA-256 forensic audit in SQLite.")
    ]

    p1.draw_rect(pymupdf.Rect(40, y, 555, y + 16), color=None, fill=(241/255, 245/255, 249/255))
    p1.insert_text(pymupdf.Point(45, y + 11), "Phase", fontsize=7.5, fontname="helv", color=NAVY)
    p1.insert_text(pymupdf.Point(165, y + 11), "Primary Code Modules", fontsize=7.5, fontname="helv", color=NAVY)
    p1.insert_text(pymupdf.Point(310, y + 11), "Operational Role & Scope", fontsize=7.5, fontname="helv", color=NAVY)
    y += 18

    for pname, pmods, pdesc in phases_p1:
        p1.draw_line(pymupdf.Point(40, y + 18), pymupdf.Point(555, y + 18), color=LINE_BORDER, width=0.5)
        p1.insert_text(pymupdf.Point(45, y + 12), pname, fontsize=7.5, fontname="helv", color=NAVY)
        p1.insert_text(pymupdf.Point(165, y + 12), pmods, fontsize=7, fontname="helv", color=ACCENT_BLUE)
        p1.insert_text(pymupdf.Point(310, y + 12), pdesc[:58] + ("..." if len(pdesc) > 58 else ""), fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 22

    draw_footer(p1, 1, 5)

    # -------------------------------------------------------------
    # PAGE 2: Deep Dive: Phases 1 to 3
    # -------------------------------------------------------------
    p2 = doc.new_page(width=595, height=842)
    draw_header(p2, "SafeDig AI — End-to-End Execution & Code Mechanism", "Phase 1 to Phase 3 Detailed Code Mechanics")
    
    y = 95
    p2.insert_text(pymupdf.Point(40, y), "Phase 1: Ingestion & Self-Healing Path Resolution", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p2.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    p2_phase1_items = [
        ("Self-Healing Path Translation", "src/utils/paths.py",
         "When repositories are cloned across different machines, index.xlsx and report metadata often store foreign machine paths (e.g. d:/Safedig_AG/data/...). resolve_folder_path() and resolve_file_path() dynamically inspect parent directories, resolving the folder basename without crashing.",
         "Solves 'Index file not found' across foreign workstations automatically."),
        ("Spreadsheet Parsing (index.xlsx)", "src/index/parser.py",
         "Reads index.xlsx via pandas and openpyxl. Extracts statutory disclosure fields: utility_name, is_asset_present (Status='Yes'/'No'), raw_warning, and raw_comments. Produces a typed IndexRecord list.",
         "Validates that all utility rows are parsed without loss or truncation."),
        ("Deterministic Inventory Matching", "src/ingestion/inventory.py",
         "A utility pack contains dozens of PDFs (customer letters, hospital directions, valve leaflets). inventory.py tokenizes filenames, computes fuzzy string similarity against utility_name, and filters out excluded keywords.",
         "Assigns DocumentResolutionStatus: UNIQUE (1-to-1 match), EXCLUDED, or AMBIGUOUS (triggers BLOCKED).")
    ]

    for title, mod, body, impact in p2_phase1_items:
        p2.draw_rect(pymupdf.Rect(40, y, 555, y + 54), color=LINE_BORDER, fill=(1, 1, 1))
        p2.insert_text(pymupdf.Point(48, y + 12), title, fontsize=8, fontname="helv", color=NAVY)
        p2.insert_text(pymupdf.Point(260, y + 12), mod, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p2.insert_text(pymupdf.Point(48, y + 25), body[:135], fontsize=7, fontname="helv", color=SLATE_TEXT)
        p2.insert_text(pymupdf.Point(48, y + 36), body[135:270], fontsize=7, fontname="helv", color=SLATE_TEXT)
        p2.insert_text(pymupdf.Point(48, y + 47), f"Impact: {impact}", fontsize=7, fontname="helv", color=MUTED_TEXT)
        y += 60

    y += 10
    p2.insert_text(pymupdf.Point(40, y), "Phase 2 & 3: PDF Structure & Knowledge Resolution", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p2.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    p2_phase23_items = [
        ("PDF Stream Health & Modality", "src/pdf/inspector.py, src/domain/document.py",
         "PyMuPDF opens the PDF file, computes a SHA-256 cryptographic byte hash, and inspects internal content stream operations. Classifies drawings as VECTOR (native path commands), RASTER (bitmap scans), or HYBRID.",
         "Rejects corrupted or password-encrypted files early with BLOCKED."),
        ("Statutory Warning Catalogue", "src/domain/warning_catalogue.py",
         "Loads the statutory hazard taxonomy for the provider: voltage classifications (11kV, 33kV, 132kV), gas pressure bands (LP, MP, IP, HP >7 bar), and required HSG47 safety controls (hand-dig, trial holes, clearance zones).",
         "Establishes legal compliance baseline before spatial analysis."),
        ("Cartographic Legend Profile", "src/domain/legend.py",
         "Loads the provider's drawing legend profile: target RGB colors (e.g. UKPN 11kV = #FF0000, SGN LP Gas = #FFCC00), line stroke widths in points, and color tolerance bands (Delta E <= 28.0 Euclidean RGB distance).",
         "Allows automated computer vision to discriminate between gas, electric, and water lines.")
    ]

    for title, mod, body, impact in p2_phase23_items:
        p2.draw_rect(pymupdf.Rect(40, y, 555, y + 54), color=LINE_BORDER, fill=(1, 1, 1))
        p2.insert_text(pymupdf.Point(48, y + 12), title, fontsize=8, fontname="helv", color=NAVY)
        p2.insert_text(pymupdf.Point(260, y + 12), mod, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p2.insert_text(pymupdf.Point(48, y + 25), body[:135], fontsize=7, fontname="helv", color=SLATE_TEXT)
        p2.insert_text(pymupdf.Point(48, y + 36), body[135:270], fontsize=7, fontname="helv", color=SLATE_TEXT)
        p2.insert_text(pymupdf.Point(48, y + 47), f"Impact: {impact}", fontsize=7, fontname="helv", color=MUTED_TEXT)
        y += 60

    draw_footer(p2, 2, 5)

    # -------------------------------------------------------------
    # PAGE 3: Deep Dive: Phases 4 & 5 (Spatial AOI & Dual-Engine Detection)
    # -------------------------------------------------------------
    p3 = doc.new_page(width=595, height=842)
    draw_header(p3, "SafeDig AI — End-to-End Execution & Code Mechanism", "Phase 4 & Phase 5: Spatial Geometry & Computer Vision")
    
    y = 95
    p3.insert_text(pymupdf.Point(40, y), "Phase 4: Spatial AOI Extraction & Rotation Mapping", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p3.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    aoi_text = (
        "The Area of Interest (AOI) represents the physical boundary of the planned civil excavation.\n"
        "SafeDig resolves three major cartographic challenges in src/aoi/detector.py:\n"
        "1. Rotation Coordinate Conversion: PyMuPDF's get_drawings() returns coords in unrotated mediabox space.\n"
        "   When drawings are rotated (0, 90, 180, 270 deg), detector.py translates visual page rects back to mediabox:\n"
        "   • 90 deg:  x_un = y_vis, y_un = mh - x_vis\n"
        "   • 180 deg: x_un = mw - x_vis, y_un = mh - y_vis\n"
        "   • 270 deg: x_un = mw - y_vis, y_un = x_vis\n"
        "2. Dashed Perimeter Search: Detects dashed vector boundaries forming the dig boundary (red, magenta, yellow).\n"
        "3. Topological Validation: Validates closed Shapely Polygon (coords[0] == coords[-1], vertices >= 4, area > 100).\n"
        "   Conservative Fallback: If no boundary line is found, uses the active map canvas so no assets are missed."
    )
    p3.insert_text(pymupdf.Point(40, y), aoi_text, fontsize=7.5, fontname="helv", color=SLATE_TEXT)
    y += 86

    p3.insert_text(pymupdf.Point(40, y), "Phase 5: Dual-Engine Spatial Asset Detection", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p3.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    cv_channels = [
        ("Channel A: PyMuPDF Vector Engine", "src/vector/analyzer.py",
         "Directly parses vector path commands (moveto, lineto, curveto). Yields zero pixel distortion.\n"
         "CRITICAL INVARIANT: Enforces exclude_dashed=True so that the dashed site boundary itself is never\n"
         "confused with an underground cable. Matches solid vectors against legend RGB and stroke width bands."),
        ("Channel B: OpenCV 300 DPI Raster CV", "src/cv/",
         "Renders high-resolution 300 DPI bitmaps to inspect legacy scanned maps that lack vector paths.\n"
         "Applies HSV color thresholding, morphological closing (cv2.morphologyEx), and contour hierarchy\n"
         "analysis to detect point symbols (substations, link boxes, valves, manholes, chambers)."),
        ("OCR / Text Label Booster", "src/pdf/extractor.py",
         "Extracts text blocks located inside the AOI bounding box.\n"
         "Correlates detected line vectors with technical abbreviations ('11kV', 'HV', 'HP GAS', 'SUBSTATION').\n"
         "If a high-voltage tag is found near a line, severity is immediately promoted to CRITICAL.")
    ]

    for title, mod, desc in cv_channels:
        p3.draw_rect(pymupdf.Rect(40, y, 555, y + 54), color=LINE_BORDER, fill=(1, 1, 1))
        p3.insert_text(pymupdf.Point(48, y + 12), title, fontsize=8, fontname="helv", color=NAVY)
        p3.insert_text(pymupdf.Point(260, y + 12), mod, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        lines = desc.split("\n")
        ly = y + 24
        for line in lines:
            p3.insert_text(pymupdf.Point(48, ly), line, fontsize=7, fontname="helv", color=SLATE_TEXT)
            ly += 10
        y += 60

    draw_footer(p3, 3, 5)

    # -------------------------------------------------------------
    # PAGE 4: Deep Dive: Phases 6 & 7 (Reconciliation & The 17 Gates)
    # -------------------------------------------------------------
    p4 = doc.new_page(width=595, height=842)
    draw_header(p4, "SafeDig AI — End-to-End Execution & Code Mechanism", "Phase 6 & Phase 7: Spatial Reconciliation & The 17 Gates")
    
    y = 95
    p4.insert_text(pymupdf.Point(40, y), "Phase 6: Spatial Buffer Math & Reconciliation Outcomes", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p4.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    reconcil_txt = (
        "Civil excavations cannot take place immediately adjacent to pressurized or high-voltage services.\n"
        "SafeDig expands the excavation polygon using Shapely 2D buffer geometry:\n"
        "• Standard Hand-Dig Zone: +5.0m buffer around all low/medium voltage cables and distribution pipes (HSG47).\n"
        "• High-Pressure Gas / EHV Corridor: +15.0m statutory clearance zone around Cadent/SGN transmission pipelines.\n"
        "Computes exact 2D geometric intersection: buffered_aoi.intersects(asset_geom) and aoi.distance(asset_geom)."
    )
    p4.insert_text(pymupdf.Point(40, y), reconcil_txt, fontsize=7.5, fontname="helv", color=SLATE_TEXT)
    y += 48

    outcomes_table = [
        ("CONFIRMED_CLEAN", "Upstream: 'No Assets' | SafeDig: Zero Intersecting Vectors", "AUTO_CLEAR", GREEN_PASS),
        ("MATCH (Low/Med)", "Upstream: 'Assets Present' | SafeDig: Detected Intersecting Lines", "HUMAN_REVIEW", AMBER_WARN),
        ("MATCH (High/Crit)", "Upstream: 'Assets Present' | SafeDig: Detected 11kV/HP Gas", "HUMAN_REVIEW", RED_FAIL),
        ("MISSED_WARNING", "Upstream: 'No Assets' | SafeDig: Detected Buried Infrastructure", "HUMAN_REVIEW", RED_FAIL),
        ("POSSIBLE_FALSE_POS", "Upstream: 'Assets Present' | SafeDig: Buffer Completely Clean", "HUMAN_REVIEW", AMBER_WARN)
    ]

    for oname, oeval, odec, ocol in outcomes_table:
        p4.draw_rect(pymupdf.Rect(40, y, 555, y + 20), color=LINE_BORDER, fill=(1, 1, 1))
        p4.insert_text(pymupdf.Point(48, y + 13), oname, fontsize=7.5, fontname="helv", color=NAVY)
        p4.insert_text(pymupdf.Point(170, y + 13), oeval, fontsize=7, fontname="helv", color=SLATE_TEXT)
        p4.insert_text(pymupdf.Point(460, y + 13), odec, fontsize=7.5, fontname="helv", color=ocol)
        y += 24

    y += 12
    p4.insert_text(pymupdf.Point(40, y), "Phase 7: The 17 Mandatory Release Gates & Policy Ladder", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p4.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    ladder_steps = [
        ("Step 1: Clean Claim Early Exit", "index_record.is_asset_present == False (Status='No')", "AUTO_CLEAR", GREEN_PASS),
        ("Step 2: Missing File Early Exit", "document is None OR document.is_corrupted", "BLOCKED", RED_FAIL),
        ("Step 3: Ambiguous Match Early Exit", "index_record.resolution_status == AMBIGUOUS", "BLOCKED", RED_FAIL),
        ("Step 4: Missed Warning Escalation", "reconciliation.outcome == MISSED_WARNING", "HUMAN_REVIEW", RED_FAIL),
        ("Step 5: False Positive Escalation", "reconciliation.outcome == POSSIBLE_FALSE_POSITIVE", "HUMAN_REVIEW", AMBER_WARN),
        ("Step 6: High Hazard Escalation", "outcome == MATCH and Gate 12 Fails (11kV / HP Gas)", "HUMAN_REVIEW", RED_FAIL),
        ("Step 7: Geometry/Legend Escalation", "Gate 07 (Legend) or Gate 08 (AOI) Failed", "HUMAN_REVIEW", AMBER_WARN),
        ("Step 8: Final Gate Sweep", "ALL 17 Gates passed and evidence package complete", "AUTO_CLEAR", GREEN_PASS)
    ]

    p4.draw_rect(pymupdf.Rect(40, y, 555, y + 16), color=None, fill=(241/255, 245/255, 249/255))
    p4.insert_text(pymupdf.Point(45, y + 11), "Ladder Priority", fontsize=7.5, fontname="helv", color=NAVY)
    p4.insert_text(pymupdf.Point(175, y + 11), "Trigger Condition", fontsize=7.5, fontname="helv", color=NAVY)
    p4.insert_text(pymupdf.Point(460, y + 11), "Decision", fontsize=7.5, fontname="helv", color=NAVY)
    y += 18

    for lstep, lcond, ldec, lcol in ladder_steps:
        p4.draw_line(pymupdf.Point(40, y + 12), pymupdf.Point(555, y + 12), color=LINE_BORDER, width=0.5)
        p4.insert_text(pymupdf.Point(45, y + 9), lstep, fontsize=7, fontname="helv", color=NAVY)
        p4.insert_text(pymupdf.Point(175, y + 9), lcond, fontsize=7, fontname="helv", color=SLATE_TEXT)
        p4.insert_text(pymupdf.Point(460, y + 9), ldec, fontsize=7.5, fontname="helv", color=lcol)
        y += 15

    draw_footer(p4, 4, 5)

    # -------------------------------------------------------------
    # PAGE 5: Phase 8 (LangGraph & Audit) + Web Console
    # -------------------------------------------------------------
    p5 = doc.new_page(width=595, height=842)
    draw_header(p5, "SafeDig AI — End-to-End Execution & Code Mechanism", "Phase 8: LangGraph, Audit & Web Console Workspace")
    
    y = 95
    p5.insert_text(pymupdf.Point(40, y), "Phase 8: LangGraph Workflow, Advisory LLM & Forensic Audit", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p5.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    p5_txt = (
        "LangGraph State Machine (src/orchestration/graph.py):\n"
        "• Orchestrates nodes: ingest_and_index ──► process_qa_and_policy ──► llm_advisory ──► finalize ──► persist_to_db.\n"
        "• Routes jobs requiring human review through llm_advisory_node; clean jobs proceed straight to finalize_report.\n\n"
        "Advisory LLM & Zero Validation Authority:\n"
        "• Queries local Ollama runtime (Qwen 2.5 7B / Llama 3.2 3B) to generate plain-English operator notes.\n"
        "• INVARIANT: The LLM has zero authority to override, alter, or auto-clear any safety gate.\n"
        "• 0ms offline fallback explainer operates with zero latency if Ollama is unavailable.\n\n"
        "Forensic Audit & SQLite Persistence (safedig.db):\n"
        "• Computes SHA-256 digital signatures of original PDF, index row, detection GeoJSON, and timestamps.\n"
        "• Persists immutable audit records via SQLAlchemy for legally defensible compliance under HSE inquiries."
    )
    p5.insert_text(pymupdf.Point(40, y), p5_txt, fontsize=7.5, fontname="helv", color=SLATE_TEXT)
    y += 98

    p5.insert_text(pymupdf.Point(40, y), "Interactive Web Console & QA Workspace (http://127.0.0.1:8000)", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p5.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    ui_features = [
        ("Animated Radar Scanner Loader", "src/api/static/index.html & app.js",
         "When an engineer inspects a job, #ws-map-loader displays an animated radar scanner with spinning gradient rings while high-resolution map tiles load. Automatically fades out when the DOM image finishes rendering."),
        ("Hardware-Accelerated Pan & Zoom", "Canvas / DOM Viewport",
         "Supports fluid drag-and-pan and zooming from 50% to 600%. Features instant AOI centering to immediately focus on the excavation boundary and detected hazards."),
        ("Live 17 Gates Status Grid", "Interactive Policy Matrix",
         "Renders the 17 gates dynamically with green checkmarks or red failure badges. Clicking any gate highlights the relevant geometry or displays the exact rejection rationale."),
        ("Human Override Sign-Off Audit", "src/api/routes/qa.py",
         "Certified safety engineers can record an override (Accept Risk & Authorize or Reject Permit). The engineer's credential, action, and timestamp are permanently written to safedig.db.")
    ]

    for title, mod, desc in ui_features:
        p5.draw_rect(pymupdf.Rect(40, y, 555, y + 42), color=LINE_BORDER, fill=(1, 1, 1))
        p5.insert_text(pymupdf.Point(48, y + 12), title, fontsize=8, fontname="helv", color=NAVY)
        p5.insert_text(pymupdf.Point(260, y + 12), mod, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p5.insert_text(pymupdf.Point(48, y + 24), desc[:135], fontsize=7, fontname="helv", color=SLATE_TEXT)
        p5.insert_text(pymupdf.Point(48, y + 35), desc[135:270], fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 48

    draw_footer(p5, 5, 5)

    page_cnt = len(doc)
    doc.save(out_path)
    doc.close()
    print(f"[OK] Generated E2E Code Working PDF ({page_cnt} pages): {out_path}")

create_e2e_code_working_pdf(PDF_PATH)
shutil.copy2(PDF_PATH, ROOT_PDF_PATH)
print(f"[OK] Copied PDF to root: {ROOT_PDF_PATH}")
