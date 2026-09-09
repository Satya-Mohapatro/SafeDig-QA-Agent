# SafeDig AI — Codebase File-by-File Technical Guide
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
