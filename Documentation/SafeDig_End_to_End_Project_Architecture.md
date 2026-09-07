# SafeDig AI — End-to-End Project Architecture
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
