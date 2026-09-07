"""
SafeDig AI Documentation Generator
Generates:
1. Documentation/SafeDig_End_to_End_Project_Architecture.md & .pdf
2. Documentation/SafeDig_Codebase_File_by_File_Explanation.md & .pdf
And copies PDFs to project root.
"""

import os
import shutil
import pymupdf

DOCS_DIR = r"D:\SafeDig_AG\Documentation"
ROOT_DIR = r"D:\SafeDig_AG"
os.makedirs(DOCS_DIR, exist_ok=True)

NAVY = (15/255, 23/255, 42/255)
ACCENT_BLUE = (37/255, 99/255, 235/255)
ICE_BLUE = (239/255, 246/255, 255/255)
SLATE_TEXT = (51/255, 65/255, 85/255)
MUTED_TEXT = (100/255, 116/255, 139/255)
LINE_BORDER = (226/255, 232/255, 240/255)
GREEN_PASS = (22/255, 101/255, 52/255)
RED_FAIL = (153/255, 27/255, 27/255)
AMBER_WARN = (146/255, 64/255, 14/255)

def draw_header(page, title: str, subtitle: str, badge: str = "HSG47 COMPLIANT"):
    page.draw_rect(pymupdf.Rect(0, 0, 595, 75), color=None, fill=NAVY)
    page.insert_text(pymupdf.Point(40, 36), title, fontsize=16, fontname="helv", color=(1, 1, 1))
    page.insert_text(pymupdf.Point(40, 54), subtitle, fontsize=9.5, fontname="helv", color=(147/255, 197/255, 253/255))
    page.draw_rect(pymupdf.Rect(435, 24, 555, 48), color=None, fill=(30/255, 41/255, 59/255))
    page.insert_text(pymupdf.Point(445, 39), badge, fontsize=7.5, fontname="helv", color=(52/255, 211/255, 153/255))

def draw_footer(page, page_num: int, total_pages: int, doc_name: str):
    page.draw_line(pymupdf.Point(40, 805), pymupdf.Point(555, 805), color=LINE_BORDER, width=0.8)
    page.insert_text(pymupdf.Point(40, 818), f"{doc_name} — SafeDig AI Engineering Specification", fontsize=7.5, fontname="helv", color=MUTED_TEXT)
    page.insert_text(pymupdf.Point(505, 818), f"Page {page_num} of {total_pages}", fontsize=7.5, fontname="helv", color=MUTED_TEXT)


# ==============================================================================
# 1. END-TO-END PROJECT ARCHITECTURE (MD & PDF)
# ==============================================================================
E2E_MD = """# SafeDig AI — End-to-End Project Architecture
**UK Underground Utility Dig-Safety Map QA & Validation Platform**  
**Compliance Standard**: UK Health and Safety Guidance 47 (HSG47) & CDM 2015  
**Core Invariant**: Zero Escaped Hazards (`SAFE_MODE=True`)

---

## 1. Executive Summary & Purpose

In the United Kingdom, civil excavation contractors must submit statutory "dial-before-you-dig" inquiries (e.g. via LinesearchbeforeUdig - LSBUD) before breaking ground. In response, statutory asset owners (electricity distribution, gas networks, water authorities, and telecoms) return disclosure packs containing summary letters and technical CAD drawings.

SafeDig is an automated, AI-augmented safety validation platform engineered to solve the most hazardous failure modes in civil engineering:
1. **Omitted Hazard Claims**: Upstream summary letters incorrectly stating "No assets affected" when buried high-voltage or gas lines run directly through the dig site.
2. **Ambiguous Utility Packs**: Multi-document bundles with dozens of non-relevant PDFs (hospital maps, valve leaflets, safety guidelines) obscuring the real drawing.
3. **Cartographic Complexity**: Hairline utility vectors (0.25pt width) overlaid on dense Ordnance Survey base maps.
4. **Zero-Hallucination Mandate**: Unlike pure-LLM solutions which hallucinate spatial coordinates, SafeDig deploys an auditable deterministic spatial engine paired with advisory-only local LLMs.

---

## 2. End-to-End Pipeline Architecture (The 10 Stages)

```
[ Job Intake Folder ] (e.g., Data/548357_172783)
  │ Contains index.xlsx + Raw PDFs (UKPN, SGN, Cadent, BT, Water)
  ▼
Stage 1: Portable Path Resolution & Index Ingestion (src/utils/paths.py, src/index/parser.py)
  ▼
Stage 2: Deterministic Inventory Matching (src/ingestion/inventory.py)
  ▼
Stage 3: PDF Document Intake & Modality Classification (src/domain/document.py)
  ▼
Stage 4: Knowledge Resolution (Provider, Warning Catalogue & Legend Profiles)
  ▼
Stage 5: Spatial AOI Extraction & Validation (src/spatial/aoi_detector.py)
  ▼
Stage 6: Dual-Engine Spatial Asset Detection (PyMuPDF Vector + OpenCV 300 DPI Raster)
  ▼
Stage 7: Safety Buffer Math & Spatial Reconciliation (src/spatial/reconciler.py)
  ▼
Stage 8: The 17 Mandatory Release Gates (src/policy/gates.py & src/policy/engine.py)
  ▼
Stage 9: LangGraph Orchestration & Advisory LLM Summary (Qwen 2.5 / Fallback Explainer)
  ▼
Stage 10: Forensic Evidence Package & Immutable SQLite Audit Commit (safedig.db)
  │
  ├─► [ALL 17 GATES PASS] ──────► 🟢 AUTO_CLEAR (Dig Permit Safe)
  │
  └─► [ANY GATE FAILS / HAZARD] ─► 🟡 HUMAN_REVIEW / 🔴 BLOCKED
                                  (Rendered in QA Workspace Web UI)
```

---

## 3. Detailed Stage-by-Stage Breakdown

### Stage 1: Portable Path Resolution & Index Ingestion
- Ingests the statutory inquiry summary (`index.xlsx`).
- Resolves cross-machine directory mismatches via `src/utils/paths.py`. Automatically repairs absolute foreign machine paths (`d:/Safedig_AG/data/...`) into active host paths without crashing.
- Extracts utility provider name, statutory status (`Yes` / `No` / `Unknown`), enquiry ID, and work boundary coordinates.

### Stage 2: Deterministic Inventory Matching
- Matches each index record to its authoritative drawing file.
- Discards non-map collateral (customer letters, safety booklets, valve advice, nearest hospital maps).
- Enforces strict deterministic matching: `UNIQUE` (1-to-1 match), `EXCLUDED` (known non-map), or `AMBIGUOUS` (conflicting candidates).

### Stage 3: PDF Document Intake & Modality Classification
- Inspects physical PDF byte streams using PyMuPDF.
- Validates file integrity, page counts, encryption headers, and internal object structures.
- Categorizes document modality: `VECTOR` (native vector drawings), `RASTER` (scanned bitmap plans), or `HYBRID`.

### Stage 4: Knowledge Resolution
- Identifies statutory asset owners: UK Power Networks (UKPN), Southern Gas Networks (SGN), Cadent Gas, National Grid, Virgin Media, Openreach (BT), Thames Water, GTC.
- Activates provider-specific Master Warning Catalogues and Cartographic Legend Profiles (RGB color palettes, dash patterns, line widths).

### Stage 5: Spatial AOI Extraction & Validation
- Locates the excavation site boundary (Area of Interest - AOI).
- Detects red polygon boundaries (`#FF0000`), diagonal hatching fills, or corner coordinates.
- Validates geometric integrity via Shapely: topological closure, $\ge 4$ vertices, non-zero area, within drawing boundary.

### Stage 6: Dual-Engine Asset Detection
- **Vector Engine**: Parses PDF vector graphics paths, extracting strokes, line widths, and RGB values with zero rasterization loss.
- **Raster / Computer Vision Engine**: Renders drawing at 300 DPI, runs OpenCV color filtering, morphological closing, and Canny edge contour detection for scanned drawings.

### Stage 7: Safety Buffer Math & Spatial Reconciliation
- Constructs statutory safety clearance buffers around the excavation polygon (500mm hand-dig zone, 3m HV electrical buffer, 15m high-pressure gas buffer).
- Performs 2D geometric intersection calculations via Shapely.
- Reconciles findings against upstream declarations:
  - `CONFIRMED_CLEAN`: Both claim and drawing show clean.
  - `MATCH`: Both claim and drawing identify assets present.
  - `MISSED_WARNING`: Upstream declared clear, but SafeDig detected live underground assets in AOI.
  - `POSSIBLE_FALSE_POSITIVE`: Upstream declared assets, but drawing is clear within buffer.

### Stage 8: The 17 Mandatory Release Gates
- Evaluates the 17 deterministic safety checks (`src/policy/gates.py`).
- Routes through `PolicyEngine.evaluate`:
  - `AUTO_CLEAR`: Only if all 17 gates pass and zero critical warnings exist.
  - `HUMAN_REVIEW`: Triggered by any missed warning, high-voltage asset, ambiguity, or gate failure.
  - `BLOCKED`: Triggered by missing/corrupt PDFs or ambiguous document mappings.

### Stage 9: LangGraph Orchestration & Advisory LLM
- Executes the stateful pipeline DAG using LangGraph.
- LLM Node calls on-premise Ollama (Qwen 2.5 or Llama 3.2) to synthesize technical findings into plain-English operator notes.
- Invariant: Zero validation authority for LLM. If Ollama is offline, system uses instant deterministic fallback explainer.

### Stage 10: Evidence Package & Forensic Audit
- Generates high-resolution visual evidence artifacts:
  - AOI crop image (`aoi_crop.png`).
  - Full-sheet context plan (`map_image.png`).
  - High-visibility vector overlay rendering.
  - Machine-readable GeoJSON asset package.
- Computes SHA-256 cryptographic fingerprints of inputs, geometry, and gate states.
- Commits audit record to SQLite (`safedig.db`) for HSE statutory defensibility.

---

## 4. Web Console & Human Review Workspace

When a document requires human review:
1. Operator opens the SafeDig Web Console (`http://127.0.0.1:8000/#qa-workspace`).
2. Interactive radar scan animation displays while high-resolution drawing tiles load.
3. Operator views the 17 Gates status matrix, with failing gates highlighted in red.
4. Canvas provides hardware-accelerated zoom (50%–600%) and pan.
5. Operator signs off with human authorization override (recorded with timestamp and user ID in `safedig.db`).
"""

with open(os.path.join(DOCS_DIR, "SafeDig_End_to_End_Project_Architecture.md"), "w", encoding="utf-8") as f:
    f.write(E2E_MD)

def create_e2e_pdf(out_path: str):
    doc = pymupdf.open()
    
    # Page 1: Overview & Domain Invariants
    p1 = doc.new_page(width=595, height=842)
    draw_header(p1, "SafeDig AI Platform", "End-to-End Architecture & Operational Workflow")
    
    y = 95
    p1.insert_text(pymupdf.Point(40, y), "1. Executive Summary & Purpose", fontsize=12, fontname="helv", color=NAVY)
    y += 5
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 16

    intro = (
        "SafeDig is an automated, AI-augmented safety validation platform engineered to prevent utility strikes during\n"
        "civil engineering excavations in the United Kingdom. Under UK statutory frameworks (HSG47 and CDM 2015),\n"
        "striking buried infrastructure results in fatal injuries, gas explosions, electric flashovers, and major liabilities.\n"
        "SafeDig re-validates upstream utility warning disclosures against physical engineering drawings with ZERO ESCAPED HAZARDS."
    )
    p1.insert_text(pymupdf.Point(40, y), intro, fontsize=8, fontname="helv", color=SLATE_TEXT)
    y += 50

    # Core Invariant Callout
    p1.draw_rect(pymupdf.Rect(40, y, 555, y + 54), color=(254/255, 202/255, 202/255), fill=(254/255, 242/255, 242/255))
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(40, y + 54), color=(220/255, 38/255, 38/255), width=3)
    p1.insert_text(pymupdf.Point(48, y + 15), "NON-NEGOTIABLE DOMAIN INVARIANT (HSG47 COMPLIANCE)", fontsize=8.5, fontname="helv", color=RED_FAIL)
    inv_txt = (
        "SAFE_MODE is permanently active. Every detected hazard is escalated to a certified human engineer.\n"
        "Every ambiguous, corrupted, or contradictory document fails toward HUMAN_REVIEW or BLOCKED, never toward AUTO_CLEAR.\n"
        "The system never trades a false negative (escaped hazard) for a cleaner false-positive statistic."
    )
    p1.insert_text(pymupdf.Point(48, y + 28), inv_txt, fontsize=7.5, fontname="helv", color=(127/255, 29/255, 29/255))
    y += 70

    p1.insert_text(pymupdf.Point(40, y), "2. The 10-Stage Pipeline Flow", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=LINE_BORDER, width=1)
    y += 14

    stages = [
        ("Stage 1: Ingestion", "src/utils/paths.py", "Self-healing path resolution, parses master inquiry index.xlsx, repairs cross-machine paths."),
        ("Stage 2: Inventory", "src/ingestion/inventory.py", "Deterministic 1-to-1 matching. Separates technical maps from letters, booklets, and leaflets."),
        ("Stage 3: PDF Intake", "src/domain/document.py", "Inspects file magic, byte streams, and determines modality: VECTOR, RASTER, or HYBRID."),
        ("Stage 4: Knowledge", "src/domain/legend.py", "Resolves statutory provider (UKPN, SGN, Cadent), loads warning catalogues and color legends."),
        ("Stage 5: Spatial AOI", "src/spatial/aoi_detector.py", "Extracts excavation site polygon (Area of Interest), validates geometry closure and bounds."),
        ("Stage 6: Dual CV Scan", "src/vision/detector.py", "PyMuPDF vector path geometric extraction + OpenCV 300 DPI raster color contour analysis."),
        ("Stage 7: Reconciliation", "src/spatial/reconciler.py", "Computes Shapely 2D spatial intersection between AOI buffer and detected buried utility assets."),
        ("Stage 8: 17 Gates", "src/policy/gates.py", "Evaluates all 17 mandatory release gates. Prevents auto-clearing unverified or critical hazards."),
        ("Stage 9: Advisory AI", "src/orchestration/nodes.py", "LangGraph executes Ollama LLM (Qwen 2.5) for operator summary notes. Zero validation authority."),
        ("Stage 10: Audit Persist", "safedig.db (SQLAlchemy)", "Generates high-res visual evidence package and locks SHA-256 digital fingerprint in database.")
    ]

    p1.draw_rect(pymupdf.Rect(40, y, 555, y + 16), color=None, fill=(241/255, 245/255, 249/255))
    p1.insert_text(pymupdf.Point(45, y + 11), "Stage", fontsize=7.5, fontname="helv", color=NAVY)
    p1.insert_text(pymupdf.Point(165, y + 11), "Primary Component", fontsize=7.5, fontname="helv", color=NAVY)
    p1.insert_text(pymupdf.Point(295, y + 11), "Operational Function & Safety Scope", fontsize=7.5, fontname="helv", color=NAVY)
    y += 18

    for sname, scomp, sdesc in stages:
        p1.draw_line(pymupdf.Point(40, y + 14), pymupdf.Point(555, y + 14), color=LINE_BORDER, width=0.5)
        p1.insert_text(pymupdf.Point(45, y + 10), sname, fontsize=7.5, fontname="helv", color=NAVY)
        p1.insert_text(pymupdf.Point(165, y + 10), scomp, fontsize=7, fontname="helv", color=ACCENT_BLUE)
        p1.insert_text(pymupdf.Point(295, y + 10), sdesc[:60] + ("..." if len(sdesc) > 60 else ""), fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 17

    draw_footer(p1, 1, 3, "End-to-End Architecture")

    # Page 2: Spatial Reconciliation & Gate Routing
    p2 = doc.new_page(width=595, height=842)
    draw_header(p2, "SafeDig AI Platform", "Spatial Reconciliation & Decision Architecture")
    
    y = 95
    p2.insert_text(pymupdf.Point(40, y), "3. Spatial Reconciliation & Buffer Mechanics", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p2.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 16

    p2_txt = (
        "SafeDig does not rely on simple bounding boxes. It implements millimeter-accurate 2D polygon math via Shapely:\n"
        "1. Area of Interest (AOI): Extracted from site redline boundaries, verified closed (coords[0] == coords[-1]).\n"
        "2. Statutory Safety Buffers: SafeDig applies a 5.0m buffer for standard low-voltage and distribution pipelines,\n"
        "   and a statutory 15.0m buffer for Cadent / SGN High-Pressure gas transmission pipelines (HSG47).\n"
        "3. Geometric Intersection: Computes polygon.intersects(vector_line) and polygon.distance(vector_line).\n"
        "4. Reconciliation Matrix: Classifies interaction between upstream enquiry disclosures and physical drawing findings."
    )
    p2.insert_text(pymupdf.Point(40, y), p2_txt, fontsize=8, fontname="helv", color=SLATE_TEXT)
    y += 65

    reconcile_outcomes = [
        ("CONFIRMED_CLEAN", "Upstream: 'No Assets' | CV: Zero Intersecting Vectors", "AUTO_CLEAR", GREEN_PASS,
         "Both sources confirm complete absence of underground assets inside excavation buffer. Clearance approved."),
        ("MATCH (Low/Med)", "Upstream: 'Assets Present' | CV: Vectors Intersect AOI", "HUMAN_REVIEW", AMBER_WARN,
         "Detected underground utility confirmed. Surfaced to engineer for hand-dig permit condition assignment."),
        ("MATCH (High/Crit)", "Upstream: 'Assets Present' | CV: 11kV/33kV HV or HP Gas", "HUMAN_REVIEW", RED_FAIL,
         "CRITICAL LIFE-SAFETY: Gate 12 immediately blocks auto-clearance. Requires formal engineer sign-off."),
        ("MISSED_WARNING", "Upstream: 'No Assets' | CV: Live Utility Vectors Inside AOI", "HUMAN_REVIEW", RED_FAIL,
         "PRIMARY RESCUE: Catches dangerous omissions where utility letters claimed clear but drawings contain live mains.")
    ]

    for oname, oeval, odec, ocol, odesc in reconcile_outcomes:
        p2.draw_rect(pymupdf.Rect(40, y, 555, y + 42), color=LINE_BORDER, fill=(1, 1, 1))
        p2.insert_text(pymupdf.Point(48, y + 13), oname, fontsize=8.5, fontname="helv", color=NAVY)
        p2.insert_text(pymupdf.Point(180, y + 13), oeval, fontsize=7.5, fontname="helv", color=SLATE_TEXT)
        p2.insert_text(pymupdf.Point(465, y + 13), odec, fontsize=8, fontname="helv", color=ocol)
        p2.insert_text(pymupdf.Point(48, y + 27), odesc, fontsize=7, fontname="helv", color=MUTED_TEXT)
        y += 48

    y += 15
    p2.insert_text(pymupdf.Point(40, y), "4. Dual-Engine Spatial Asset Extraction", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p2.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 16

    dual_txt = (
        "SafeDig solves cartographic complexity by fusing two independent detection channels:\n"
        "• Channel A (PyMuPDF Vector Parsing): Extracts native PDF path objects directly from binary streams.\n"
        "  Yields exact coordinate geometries, stroke widths, and RGB values with zero pixelization or blur.\n"
        "• Channel B (OpenCV 300 DPI Computer Vision): Renders high-resolution bitmaps to analyze legacy scanned plans,\n"
        "  raster textures, and rasterized hatching patterns that lack native PDF vector paths.\n"
        "The reconciliation engine fuses both inventories into a single verified geospatial coordinate frame."
    )
    p2.insert_text(pymupdf.Point(40, y), dual_txt, fontsize=8, fontname="helv", color=SLATE_TEXT)
    
    draw_footer(p2, 2, 3, "End-to-End Architecture")

    # Page 3: Web Console, Forensic Evidence & Deployment
    p3 = doc.new_page(width=595, height=842)
    draw_header(p3, "SafeDig AI Platform", "Web Console, Forensic Evidence & Enterprise Deployment")
    
    y = 95
    p3.insert_text(pymupdf.Point(40, y), "5. Interactive QA Workspace & Evidence Dossier", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p3.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 16

    ws_txt = (
        "When an automated clearance is held for human review, the job is dispatched to the SafeDig QA Workspace UI:\n"
        "• High-Resolution Map Inspection: Interactive viewport featuring hardware-accelerated canvas pan & zoom (50%-600%).\n"
        "• Animated Radar Loader: Real-time visual feedback indicating map image and evidence bundle loading.\n"
        "• 17 Gates Live Status Panel: Visual badge breakdown showing exact pass/fail reasons for each gate.\n"
        "• Forensic Evidence Package: Pre-crops the excavation zone (AOI crop), full sheet context, and GeoJSON vectors.\n"
        "• Human Override Audit Trail: Engineers can confirm findings or record mitigation steps with cryptographic timestamps."
    )
    p3.insert_text(pymupdf.Point(40, y), ws_txt, fontsize=8, fontname="helv", color=SLATE_TEXT)
    y += 75

    p3.insert_text(pymupdf.Point(40, y), "6. Enterprise Production Deployment Architecture", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p3.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 16

    deploy_rows = [
        ("Containerization", "Docker & Multi-Stage Compose", "Hardened Debian-slim containers bundling PyMuPDF, OpenCV, and FastAPI."),
        ("Reverse Proxy", "Nginx Reverse Proxy", "SSL termination, rate limiting, static asset caching, and request buffering."),
        ("Process Manager", "Systemd / Windows Service", "safedig.service background daemon with automatic restart on failure."),
        ("Data Persistence", "SQLAlchemy + SQLite / Postgres", "safedig.db for local edge deployments; PostgreSQL for enterprise clustering."),
        ("Cross-Machine Ready", "Self-Healing Path Resolvers", "Dynamic directory translation ensures jobs run seamlessly across Windows/Linux.")
    ]

    for dtitle, dtech, ddesc in deploy_rows:
        p3.draw_rect(pymupdf.Rect(40, y, 555, y + 36), color=LINE_BORDER, fill=(1, 1, 1))
        p3.insert_text(pymupdf.Point(48, y + 13), dtitle, fontsize=8, fontname="helv", color=NAVY)
        p3.insert_text(pymupdf.Point(155, y + 13), dtech, fontsize=8, fontname="helv", color=ACCENT_BLUE)
        p3.insert_text(pymupdf.Point(48, y + 25), ddesc, fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 42

    draw_footer(p3, 3, 3, "End-to-End Architecture")

    page_cnt = len(doc)
    doc.save(out_path)
    doc.close()
    print(f"[OK] Generated E2E PDF ({page_cnt} pages): {out_path}")

create_e2e_pdf(os.path.join(DOCS_DIR, "SafeDig_End_to_End_Project_Architecture.pdf"))
shutil.copy2(os.path.join(DOCS_DIR, "SafeDig_End_to_End_Project_Architecture.pdf"), os.path.join(ROOT_DIR, "SafeDig_End_to_End_Project_Architecture.pdf"))
print("[OK] Copied E2E PDF to project root.")


# ==============================================================================
# 2. FILE-BY-FILE CODEBASE EXPLANATION (MD & PDF)
# ==============================================================================
FILE_MD = """# SafeDig AI — Codebase File-by-File Technical Guide
**Complete Architectural Walkthrough of all Source Modules & Subsystems**  
**Repository**: SafeDig AI Platform  

---

## 1. Directory Structure Overview

```
SafeDig_AG/
├── alembic/                # Database schema migrations
├── Data/                   # Real UK utility inquiry job folders
├── Documentation/          # Engineering specifications & compliance PDFs
├── info/                   # Domain specs & requirements traceability
├── qa_output/              # Output artifacts, evidence crops & job reports
├── src/                    # Primary application source code
│   ├── api/                # FastAPI application, routes & web UI
│   ├── config/             # Application configuration & logging
│   ├── domain/             # Strict Pydantic domain models & enums
│   ├── ingestion/          # Index spreadsheet parsing & inventory matcher
│   ├── llm/                # Ollama integration & deterministic explainer
│   ├── orchestration/      # LangGraph state machine & graph nodes
│   ├── policy/             # The 17 Release Gates & Policy Engine
│   ├── qa/                 # QA workspace services & override workflows
│   ├── spatial/            # AOI detector, vector parser & reconciler
│   ├── utils/              # Self-healing cross-machine path resolvers
│   ├── vision/             # OpenCV rasterizer, color filters & contours
│   └── pipeline.py         # End-to-end pipeline runner
├── tests/                  # PyTest unit & integration test suites
├── tools/                  # Verification & migration utilities
└── safedig.db              # SQLite forensic audit database
```

---

## 2. Root Configuration & Deployment Files

- **`pyproject.toml`**: Project configuration file defining build-system (`setuptools`), package metadata, pytest configuration (`asyncio_mode = "auto"`), and test discovery markers.
- **`requirements.txt`**: Production dependency manifest (FastAPI, Uvicorn, PyMuPDF, Shapely, OpenCV-headless, Pandas, OpenPyXL, Pydantic, SQLAlchemy, LangGraph, LangChain-Core).
- **`requirements-dev.txt`**: Development dependencies (PyTest, pytest-asyncio, pytest-cov, httpx).
- **`.env` / `.env.example`**: Environment configuration file defining database URLs, `SAFE_MODE=True`, log levels, host/port bindings, and Ollama model names (`qwen2.5:7b`).
- **`Dockerfile`**: Multi-stage production container image bundling Python 3.11, OpenCV runtime libraries (`libgl1-mesa-glx`, `libglib2.0-0`), and SafeDig services.
- **`docker-compose.yml`**: Compose stack defining the SafeDig API server and local Ollama LLM container.
- **`nginx_safedig.conf`**: Production reverse-proxy configuration managing SSL termination, client max body size (100M for large utility drawing uploads), and static caching.
- **`safedig.service`**: Linux systemd unit file ensuring persistent background execution and automatic restarts.

---

## 3. Core Source Modules (`src/`)

### Configuration Layer (`src/config/`)
- **`src/config/settings.py`**: Central Pydantic `BaseSettings` singleton. Validates environment variables, sets directory paths, toggle switches (`safe_mode`, `debug`), and LLM connection URLs.
- **`src/config/logging.py`**: Enterprise logging configuration providing structured log formatting, rotating file handlers, and colored console output.

### Domain Models Layer (`src/domain/`)
- **`src/domain/enums.py`**: Core domain enums: `Decision` (`AUTO_CLEAR`, `HUMAN_REVIEW`, `BLOCKED`), `PDFModality` (`VECTOR`, `RASTER`, `HYBRID`, `UNREADABLE`), `Severity` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), `ReconciliationOutcome` (`CONFIRMED_CLEAN`, `MATCH`, `MISSED_WARNING`, `POSSIBLE_FALSE_POSITIVE`), and `DocumentResolutionStatus`.
- **`src/domain/index_record.py`**: Pydantic model representing a parsed statutory enquiry line from `index.xlsx`.
- **`src/domain/document.py`**: Represents physical utility drawings, tracking file paths, page counts, hashes, and modality.
- **`src/domain/aoi.py`**: Encapsulates the excavation Area of Interest (AOI) polygon, coordinate vertices, and Shapely geometry.
- **`src/domain/legend.py`**: Defines cartographic legend profiles (RGB tolerances, line stroke widths, dash patterns) for UK utilities.
- **`src/domain/spatial_feature.py`**: Represents detected underground assets (cables, pipes, valves) with coordinate geometries.
- **`src/domain/reconciliation.py`**: Holds the mathematical reconciliation output between the AOI buffer and detected assets.
- **`src/domain/policy.py`**: Models individual gate evaluations (`GateCheck`) and composite policy outcomes (`PolicyResult`).
- **`src/domain/evidence.py`**: Defines the forensic evidence package containing cropped images, overlays, and GeoJSON.
- **`src/domain/warning_catalogue.py`**: Master taxonomy of utility hazard rules, voltage levels, and HSG47 actions.
- **`src/domain/audit.py`**: Models immutable audit trail records stored in the SQLite database.

### Ingestion Subsystem (`src/ingestion/`)
- **`src/ingestion/inventory.py`**: Matches index rows to physical PDF files using regex tokenization and fuzzy scoring. Separates technical drawings from letters and safety booklets.
- **`src/index/parser.py`**: Parses Excel disclosure sheets (`index.xlsx`), normalizes utility names, and applies portable path resolution.

### Spatial Math & Geometry Subsystem (`src/spatial/`)
- **`src/spatial/aoi_detector.py`**: Scans maps for red excavation polygons (`#FF0000`), hatching, and corner coordinates. Converts drawing points to geographical space.
- **`src/spatial/vector_parser.py`**: PyMuPDF vector graphics parser. Extracts vector lines, stroke colors, and dash patterns directly from PDF streams.
- **`src/spatial/reconciler.py`**: Evaluates 2D geometric intersections between the AOI (plus 5m / 15m safety buffers) and detected utility vectors via Shapely.
- **`src/spatial/geometry_utils.py`**: Geometric helper functions for coordinate transforms, rotation matrices, and polygon validation.

### Computer Vision Subsystem (`src/vision/`)
- **`src/vision/detector.py`**: Dual-engine coordinator combining vector extraction and raster computer vision.
- **`src/vision/rasterizer.py`**: Renders PDF pages into 300 DPI OpenCV BGR numpy arrays.
- **`src/vision/color_filter.py`**: HSV/RGB color masking to segment utility lines according to provider legend profiles.
- **`src/vision/contour_analyzer.py`**: Analyzes morphological contours to detect symbol markers (valves, manholes, chambers).

### Safety Policy Subsystem (`src/policy/`)
- **`src/policy/gates.py`**: Evaluates **The 17 Mandatory Release Gates**. Ensures zero unverified hazards.
- **`src/policy/engine.py`**: Implements the hierarchical decision ladder routing documents to `AUTO_CLEAR`, `HUMAN_REVIEW`, or `BLOCKED`.

### Artificial Intelligence & Advisory Subsystem (`src/llm/`)
- **`src/llm/client.py`**: Async client connecting to local Ollama runtime (Qwen 2.5 / Llama 3.2).
- **`src/llm/prompts.py`**: Few-shot system prompts instructing LLMs to generate technical discrepancy summaries.
- **`src/llm/explainer.py`**: Generates natural-language advisory notes. Includes 0ms deterministic rule fallback if Ollama is unavailable.

### Orchestration Subsystem (`src/orchestration/`)
- **`src/orchestration/graph.py`**: Assembles the LangGraph state machine DAG connecting all pipeline nodes.
- **`src/orchestration/state.py`**: Defines the typed state dictionary flowing through the LangGraph graph.
- **`src/orchestration/nodes.py`**: Individual graph execution nodes (ingestion, AOI, scan, reconciliation, policy, LLM, audit).

### QA Workspace & API Web Console (`src/qa/` & `src/api/`)
- **`src/qa/workspace.py`**: Assembles workspace models, renders visual map crops, and manages human review overrides.
- **`src/api/main.py`**: FastAPI application entry point. Configures CORS, middleware, static files, and mounts routes.
- **`src/api/routes/jobs.py`**: Endpoints for listing, uploading, and executing inquiry jobs.
- **`src/api/routes/qa.py`**: Endpoints serving workspace state and processing human review sign-offs.
- **`src/api/routes/evidence.py`**: Streams cropped map images, whole-sheet views, and vector overlays.
- **`src/api/routes/batch.py`**: Manages batch job execution across multiple folders.
- **`src/api/routes/eval.py`**: Evaluates system accuracy against ground-truth benchmarks.
- **`src/api/static/index.html`**: Single-page web console featuring interactive radar scanner loader and modern dashboard.
- **`src/api/static/app.js`**: Client-side application logic for hardware-accelerated map zoom/pan, gate rendering, and override actions.
- **`src/api/static/styles.css`**: Tailwind CSS and custom styling for high-contrast dark theme.

### Utilities & Pipeline Entry (`src/utils/` & `src/pipeline.py`)
- **`src/utils/paths.py`**: Self-healing path resolution utility. Translates foreign machine paths to the host environment dynamically.
- **`src/pipeline.py`**: Standalone pipeline entry point for processing jobs via CLI or automated batch schedulers.
"""

with open(os.path.join(DOCS_DIR, "SafeDig_Codebase_File_by_File_Explanation.md"), "w", encoding="utf-8") as f:
    f.write(FILE_MD)

def create_file_pdf(out_path: str):
    doc = pymupdf.open()
    
    # Page 1: Root & Core Architecture
    p1 = doc.new_page(width=595, height=842)
    draw_header(p1, "SafeDig AI Platform", "Codebase File-by-File Technical Guide — Part 1")
    
    y = 95
    p1.insert_text(pymupdf.Point(40, y), "1. Root Configuration & Deployment Files", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    root_files = [
        ("pyproject.toml", "Build & Test Config", "Specifies package metadata, dependencies, and pytest asyncio discovery settings."),
        ("requirements.txt", "Production Manifest", "Pins production dependencies: FastAPI, PyMuPDF, Shapely, OpenCV, Pandas, Pydantic."),
        (".env / .env.example", "Environment Config", "Configures database URLs, SAFE_MODE=True, log levels, host/port, and Ollama models."),
        ("Dockerfile", "Container Image", "Multi-stage Debian-slim container bundling Python 3.11, OpenCV runtime, and SafeDig."),
        ("docker-compose.yml", "Service Stack", "Orchestrates SafeDig API server alongside local Ollama LLM container."),
        ("nginx_safedig.conf", "Reverse Proxy", "Nginx config handling SSL termination, 100MB body size for large maps, and caching."),
        ("safedig.service", "Systemd Daemon", "Linux background service unit ensuring automatic restart and process persistence."),
        ("safedig.db", "Forensic Database", "Async SQLite database storing immutable audit trails, SHA-256 hashes, and overrides.")
    ]

    for fname, ftype, fdesc in root_files:
        p1.draw_rect(pymupdf.Rect(40, y, 555, y + 26), color=LINE_BORDER, fill=(1, 1, 1))
        p1.insert_text(pymupdf.Point(48, y + 11), fname, fontsize=8, fontname="helv", color=NAVY)
        p1.insert_text(pymupdf.Point(155, y + 11), ftype, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p1.insert_text(pymupdf.Point(260, y + 11), fdesc[:65], fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 30

    y += 10
    p1.insert_text(pymupdf.Point(40, y), "2. Configuration & Domain Models (src/config/, src/domain/)", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p1.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    domain_files = [
        ("src/config/settings.py", "Settings Singleton", "Pydantic BaseSettings singleton validating environment configuration."),
        ("src/config/logging.py", "Logging Subsystem", "Structured enterprise logging with rotating file handlers and colored console."),
        ("src/domain/enums.py", "Core Enums", "Defines Decision, PDFModality, Severity, ReconciliationOutcome, ResolutionStatus."),
        ("src/domain/index_record.py", "Index Model", "Pydantic model representing a statutory enquiry line from index.xlsx."),
        ("src/domain/document.py", "Document Model", "Represents physical utility map PDFs, tracking hashes, pages, and modality."),
        ("src/domain/aoi.py", "AOI Polygon", "Encapsulates excavation Area of Interest polygon, vertices, and Shapely geometry."),
        ("src/domain/legend.py", "Legend Profile", "Defines cartographic color bands, line stroke styles, and symbol archetypes."),
        ("src/domain/reconciliation.py", "Reconciliation Result", "Holds 2D geometric intersection calculations between AOI and detected assets."),
        ("src/domain/policy.py", "Policy Gate Models", "Data models for individual GateCheck items and overall PolicyResult.")
    ]

    for fname, ftype, fdesc in domain_files:
        p1.draw_rect(pymupdf.Rect(40, y, 555, y + 26), color=LINE_BORDER, fill=(1, 1, 1))
        p1.insert_text(pymupdf.Point(48, y + 11), fname, fontsize=8, fontname="helv", color=NAVY)
        p1.insert_text(pymupdf.Point(175, y + 11), ftype, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p1.insert_text(pymupdf.Point(280, y + 11), fdesc[:60], fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 30

    draw_footer(p1, 1, 3, "File-by-File Guide")

    # Page 2: Ingestion, Spatial Math, Computer Vision & Policy
    p2 = doc.new_page(width=595, height=842)
    draw_header(p2, "SafeDig AI Platform", "Codebase File-by-File Technical Guide — Part 2")
    
    y = 95
    p2.insert_text(pymupdf.Point(40, y), "3. Ingestion, Spatial Math & Computer Vision (src/spatial/, src/vision/)", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p2.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    spatial_files = [
        ("src/ingestion/inventory.py", "Inventory Matcher", "Fuzzy token matching linking index records to authoritative drawings."),
        ("src/index/parser.py", "Index Parser", "Parses statutory index.xlsx sheets with self-healing cross-machine pathing."),
        ("src/spatial/aoi_detector.py", "AOI Extraction", "Scans drawings for red boundary lines, hatching, and corner coordinates."),
        ("src/spatial/vector_parser.py", "Vector Engine", "PyMuPDF path extractor parsing line strokes, widths, and RGB values."),
        ("src/spatial/reconciler.py", "Spatial Reconciler", "Computes exact 2D polygon intersections between AOI buffers and utility vectors."),
        ("src/spatial/geometry_utils.py", "Geometry Math", "Shapely helper functions for coordinate transforms and polygon validation."),
        ("src/vision/detector.py", "Vision Coordinator", "Dual-engine coordinator fusing vector graphics and raster CV findings."),
        ("src/vision/rasterizer.py", "Map Rasterizer", "Renders high-resolution 300 DPI OpenCV BGR image arrays from PDF pages."),
        ("src/vision/color_filter.py", "Color Filter", "HSV/RGB color masking isolating utility lines per provider legend profiles."),
        ("src/vision/contour_analyzer.py", "Contour Engine", "Morphological analysis identifying point symbols (valves, manholes, link boxes).")
    ]

    for fname, ftype, fdesc in spatial_files:
        p2.draw_rect(pymupdf.Rect(40, y, 555, y + 26), color=LINE_BORDER, fill=(1, 1, 1))
        p2.insert_text(pymupdf.Point(48, y + 11), fname, fontsize=8, fontname="helv", color=NAVY)
        p2.insert_text(pymupdf.Point(185, y + 11), ftype, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p2.insert_text(pymupdf.Point(295, y + 11), fdesc[:55], fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 30

    y += 10
    p2.insert_text(pymupdf.Point(40, y), "4. Safety Policy Engine & Advisory LLM (src/policy/, src/llm/)", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p2.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    policy_files = [
        ("src/policy/gates.py", "17 Release Gates", "Evaluates all 17 mandatory release gates ensuring zero unverified hazards."),
        ("src/policy/engine.py", "Policy Engine", "Hierarchical decision ladder routing to AUTO_CLEAR, HUMAN_REVIEW, or BLOCKED."),
        ("src/llm/client.py", "Ollama Client", "Asynchronous HTTP client interfacing with local Ollama runtime (Qwen 2.5)."),
        ("src/llm/prompts.py", "System Prompts", "Few-shot safety-critical prompts directing LLM discrepancy explanation."),
        ("src/llm/explainer.py", "Advisory Explainer", "Synthesizes operator notes with 0ms deterministic rule fallback.")
    ]

    for fname, ftype, fdesc in policy_files:
        p2.draw_rect(pymupdf.Rect(40, y, 555, y + 26), color=LINE_BORDER, fill=(1, 1, 1))
        p2.insert_text(pymupdf.Point(48, y + 11), fname, fontsize=8, fontname="helv", color=NAVY)
        p2.insert_text(pymupdf.Point(185, y + 11), ftype, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p2.insert_text(pymupdf.Point(295, y + 11), fdesc[:55], fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 30

    draw_footer(p2, 2, 3, "File-by-File Guide")

    # Page 3: Orchestration, API, QA Workspace & Utilities
    p3 = doc.new_page(width=595, height=842)
    draw_header(p3, "SafeDig AI Platform", "Codebase File-by-File Technical Guide — Part 3")
    
    y = 95
    p3.insert_text(pymupdf.Point(40, y), "5. Orchestration, QA Workspace & REST API (src/orchestration/, src/api/)", fontsize=11, fontname="helv", color=NAVY)
    y += 5
    p3.draw_line(pymupdf.Point(40, y), pymupdf.Point(555, y), color=ACCENT_BLUE, width=1.5)
    y += 14

    api_files = [
        ("src/orchestration/graph.py", "LangGraph DAG", "Assembles stateful pipeline graph connecting ingestion, vision, policy, and LLM."),
        ("src/orchestration/nodes.py", "Pipeline Nodes", "Execution logic for individual graph nodes with failure trapping."),
        ("src/qa/workspace.py", "QA Workspace Service", "Assembles workspace models, renders visual crops, handles engineer overrides."),
        ("src/api/main.py", "FastAPI App Entry", "FastAPI entry point configuring CORS, static routes, and endpoint routers."),
        ("src/api/routes/jobs.py", "Jobs API", "Endpoints for job ingestion, listing, status checking, and report generation."),
        ("src/api/routes/qa.py", "QA Workspace API", "Serves workspace state, document metadata, and receives human sign-offs."),
        ("src/api/routes/evidence.py", "Evidence API", "Streams high-resolution AOI crops, whole sheet plans, and vector overlays."),
        ("src/api/static/index.html", "Web Console HTML", "Single-page dashboard with animated radar scanner and responsive layout."),
        ("src/api/static/app.js", "Console Frontend JS", "Client app logic: canvas pan/zoom, gate rendering, and override actions."),
        ("src/utils/paths.py", "Path Resolution", "Self-healing path resolver fixing cross-machine path discrepancies dynamically."),
        ("src/pipeline.py", "Pipeline CLI Entry", "Standalone execution script for processing jobs via terminal or batch jobs.")
    ]

    for fname, ftype, fdesc in api_files:
        p3.draw_rect(pymupdf.Rect(40, y, 555, y + 26), color=LINE_BORDER, fill=(1, 1, 1))
        p3.insert_text(pymupdf.Point(48, y + 11), fname, fontsize=8, fontname="helv", color=NAVY)
        p3.insert_text(pymupdf.Point(185, y + 11), ftype, fontsize=7.5, fontname="helv", color=ACCENT_BLUE)
        p3.insert_text(pymupdf.Point(295, y + 11), fdesc[:55], fontsize=7, fontname="helv", color=SLATE_TEXT)
        y += 30

    draw_footer(p3, 3, 3, "File-by-File Guide")

    page_cnt = len(doc)
    doc.save(out_path)
    doc.close()
    print(f"[OK] Generated File Guide PDF ({page_cnt} pages): {out_path}")

create_file_pdf(os.path.join(DOCS_DIR, "SafeDig_Codebase_File_by_File_Explanation.pdf"))
shutil.copy2(os.path.join(DOCS_DIR, "SafeDig_Codebase_File_by_File_Explanation.pdf"), os.path.join(ROOT_DIR, "SafeDig_Codebase_File_by_File_Explanation.pdf"))
print("[OK] Copied File Guide PDF to project root.")
