"""
SafeDig AI - Trainee Onboarding & Engineering Cookbook Generator
Outputs:
1. Documentation/SafeDig_Trainee_Onboarding_and_Engineering_Cookbook.md
2. Documentation/SafeDig_Trainee_Onboarding_and_Engineering_Cookbook.pdf
3. SafeDig_Trainee_Onboarding_and_Engineering_Cookbook.pdf (Root mirror)
"""

import os
import sys
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.markdown_pdf_compiler import compile_markdown_to_pdf

DOCS_DIR = r"D:\SafeDig_AG\Documentation"
ROOT_DIR = r"D:\SafeDig_AG"
MD_PATH = os.path.join(DOCS_DIR, "SafeDig_Trainee_Onboarding_and_Engineering_Cookbook.md")
PDF_PATH = os.path.join(DOCS_DIR, "SafeDig_Trainee_Onboarding_and_Engineering_Cookbook.pdf")
ROOT_PDF_PATH = os.path.join(ROOT_DIR, "SafeDig_Trainee_Onboarding_and_Engineering_Cookbook.pdf")

os.makedirs(DOCS_DIR, exist_ok=True)

MD_CONTENT = """# SafeDig AI — Trainee Onboarding & Engineering Cookbook
**The Comprehensive Practical Handbook for New Engineers & Safety Specialists**  
**Compliance Standard**: UK Health and Safety Guidance 47 (HSG47) & CDM 2015  
**Core Invariant**: Zero Escaped Hazards (`SAFE_MODE=True`)

---

## 1. Welcome to SafeDig: The Mission & Domain Context

Welcome to the SafeDig AI engineering team!

Before writing a single line of code, you must understand the real-world physical domain we operate in:
- In the United Kingdom, over **60,000 underground utility strikes occur annually**.
- Striking a buried **11,000 Volt (11kV)** or **33,000 Volt (33kV)** electricity cable generates an explosive arc-flash exceeding 4,000°C—vaporizing copper, causing fatal third-degree burns, and blacking out thousands of homes and hospitals.
- Striking a **High-Pressure (HP) gas main (>7 bar)** creates a catastrophic blast wave and massive fire, requiring neighborhood evacuations.
- Striking a **trunk fiber optic cable** severs emergency services communication and carries statutory fines running into millions of pounds.

### Why Civil Contractors Fail
Before breaking ground, excavators submit an enquiry to LinesearchbeforeUdig (LSBUD). Statutory undertakers (utility asset owners) return disclosure bundles containing summary cover letters and CAD drawings.

The fatal breakdown occurs when:
1. The cover letter says: *"We have reviewed your enquiry and have no assets in the boundary."*
2. But the attached 40-page technical CAD plan actually depicts an active 11kV cable slicing right through the proposed trench!
3. The civil site foreman trusts the letter, fails to read the complex drawing, digs with an excavator bucket, and strikes the cable.

**SafeDig was created to eliminate this failure mode forever.**

> [!IMPORTANT]
> **The SafeDig Safety Mandate**  
> SafeDig acts as the automated safety validator. We extract the excavation boundary (AOI), independently scan the real CAD drawing with sub-pixel computer vision, compute 2D spatial intersections, and enforce **The 17 Mandatory Release Gates**. If there is any hazard, ambiguity, or discrepancy, the system halts automated clearance and routes the job to a certified human safety engineer. **We never trade a false negative for a cleaner false positive.**

---

## 2. Core Mental Model: The "3 Truths"

Whenever you debug a pipeline issue or write a new feature, reason through the **3 Truths**:

```
 ┌────────────────────────────────────────────────────────┐
 │ TRUTH 1: The Declared Claim (index.xlsx)              │
 │ What the statutory undertaker stated in writing.       │
 │ E.g. Status = "No" (claims no assets affected).        │
 └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ TRUTH 2: The Physical CAD Drawing (The PDF Map)        │
 │ What actually exists on the engineering drawing.       │
 │ E.g. A solid red vector (RGB #FF0000) inside the sheet.│
 └──────────────────────────┬─────────────────────────────┘
                            │
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ TRUTH 3: The Excavation Area of Interest (AOI)         │
 │ Where the physical ground disturbance will occur.      │
 │ E.g. A closed polygon + statutory 500mm safety buffer. │
 └────────────────────────────────────────────────────────┘
```

The system's job is **Reconciliation**:
- If Truth 1 says "No" and Truth 2 + Truth 3 show **zero lines inside AOI**, the claim is verified: `CONFIRMED_CLEAN` ──► `AUTO_CLEAR`.
- If Truth 1 says "No" but Truth 2 + Truth 3 detect **buried lines inside AOI**, an omission occurred: `MISSED_WARNING` ──► **Immediate `HUMAN_REVIEW`**.
- If Truth 2 is unreadable, corrupted, or multiple plans conflict: ──► **Immediate `BLOCKED`**.

---

## 3. Local Developer Setup (Step-by-Step)

### Prerequisites
- **Operating System**: Windows 10/11, Ubuntu 22.04+, or macOS (Apple Silicon supported).
- **Python**: Version **3.11.x** (Strictly required; PyMuPDF and Shapely have pre-compiled wheels for 3.11).
- **Git**: Installed and configured.
- **Ollama**: (Optional for local LLM advisory summaries) Download from `ollama.ai`.

### Step 1: Create and Activate Virtual Environment
```bash
# In the project root (D:\SafeDig_AG)
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### Step 2: Install Production and Development Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```ini
SAFE_MODE=True
DEBUG=True
DATABASE_URL=sqlite:///safedig.db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
LOG_LEVEL=INFO
```

### Step 4: Run the Regression Test Suite
Verify your installation by running the test suite:
```bash
pytest tests/ -v
# Or run the standalone end-to-end regression test:
python run_e2e_test.py
```
If all tests pass, your local environment is 100% operational!

---

## 4. Day 1: Running Your First Pipeline Job

### Method A: Standalone CLI Runner
To process an enquiry pack from the terminal:
```bash
python -m src.pipeline Data/SampleJob
```
You will see structured console output detailing:
1. Index records parsed and self-healing paths resolved.
2. PDF modality inspection and drawing stream extraction.
3. AOI boundary detection and coordinate normalization.
4. Dual-engine vector and raster scans.
5. All 17 Release Gates evaluating in real time.
6. Final decision output: `AUTO_CLEAR`, `HUMAN_REVIEW`, or `BLOCKED`.

### Method B: Interactive Web Console
To launch the full web application:
```bash
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser and navigate to:
`http://127.0.0.1:8000/#qa-workspace`

Key UI components you will see:
1. **Radar Scanner Animation**: Modern SVG radar indicating pipeline activity.
2. **Hardware-Accelerated Canvas**: Smooth pan and zoom for massive A0 utility sheets.
3. **17-Gate Badge Matrix**: Live status indicators with green checkmarks or red failure badges.
4. **Human Review Actions**: Buttons for safety engineers to record risk acceptances or permit rejections.

---

## 5. The Trainee's Engineering Cookbook (Practical Recipes)

### Recipe 1: How to Add a New Statutory Utility Provider
When onboarding a new utility undertaker (e.g. *Wales & West Utilities*):
1. **Register the Provider Name** in `src/providers/registry.py`:
   ```python
   PROVIDER_ALIASES["Wales & West Utilities"] = "WALES_AND_WEST"
   ```
2. **Define Hazard Rules** in `src/warnings/catalogue.py`:
   ```python
   master_warning_catalogue.register(
       provider="WALES_AND_WEST",
       hazard_type="GAS",
       voltage_or_pressure="MEDIUM_PRESSURE",
       buffer_meters=5.0
   )
   ```
3. **Add Cartographic Legend Profile** in `src/legends/registry.py`:
   ```python
   LegendRegistry.register(
       legend_id="WALES_AND_WEST_GAS",
       target_colors=[(255, 165, 0)], # Orange / Yellow
       delta_e_max=28.0,
       min_stroke_width=0.3
   )
   ```

### Recipe 2: Calibrating Legend Color Tolerances (Delta-E)
Color values in CAD PDFs frequently shift due to JPEG compression, anti-aliasing, or display gamma.
- SafeDig uses **Delta-E (ΔE)** to measure human perceptual color difference.
- A value of `ΔE ≤ 2.0` is imperceptible to the human eye.
- For CAD vector lines, we calibrate `delta_e_max = 28.0`. This captures anti-aliased edge pixels while strictly rejecting unrelated colors (e.g. distinguishing red electrical lines from brown contours).
- To adjust tolerance: modify `delta_e_max` in the provider's `LegendProfile` in `src/legends/registry.py`.

### Recipe 3: How to Add or Modify a Release Gate
To add a new gate (e.g. `18_DEPTH_RECORDED`):
1. In `src/policy/gates.py`, add evaluation logic:
   ```python
   g18 = document.has_depth_annotations
   gates["18_DEPTH_RECORDED"] = GateCheck(
       gate_name="18_DEPTH_RECORDED",
       passed=g18,
       reason="Depth recorded" if g18 else "No depth annotations"
   )
   ```
2. In `src/policy/engine.py`, add gate precedence to the decision ladder:
   ```python
   if not gates["18_DEPTH_RECORDED"].passed:
       return PolicyResult(decision=Decision.HUMAN_REVIEW, ...)
   ```
3. Add a unit test in `tests/test_policy.py`.

### Recipe 4: Debugging a Rotated CAD Sheet
Utility drawings often declare an unrotated mediabox `(0, 0, 842, 595)` but set a page rotation attribute `/Rotate 90` or `/Rotate 270`.
- If your AOI or vectors appear shifted or rotated 90 degrees away from the map:
- Inspect `src/spatial/coordinates.py`.
- SafeDig transforms points using `pymupdf.Matrix(pymupdf.Identity).prerotate(rotation)`.
- Always verify that coordinates are normalized before passing to Shapely polygon constructors!

---

## 6. Debugging & Troubleshooting FAQ

### Q1: Why did a clean drawing fail with `BLOCKED`?
**Answer**: Check Gate 03 (`03_MAPPING_VALID`). If the job pack contained two PDFs matching the same provider name (e.g. `Electric_Map_1.pdf` and `Electric_Map_2.pdf`), the inventory matcher flags `AMBIGUOUS`. SafeDig refuses to guess which plan is authoritative. A safety engineer must select the correct plan in the QA Workspace.

### Q2: Why did an excavation plan trigger `MISSED_WARNING`?
**Answer**: The upstream `index.xlsx` sheet declared `Status = "No"` (no assets affected), but Channel A vector scan found a high-voltage cable vector intersecting the AOI buffer. This is SafeDig doing its core job: preventing a fatal utility strike caused by an inaccurate cover letter!

### Q3: What happens if Ollama is not installed or crashes?
**Answer**: SafeDig is 100% resilient to LLM failure. `src/agent/advisory_service.py` features a **0ms deterministic rule fallback**. If Ollama times out (>3.0s) or is unreachable, the system instantly synthesizes standardized technical advisory notes without crashing or slowing down.

---

## 7. Civil Engineering & SafeDig Glossary

| Term | Definition |
| :--- | :--- |
| **AOI** | **Area of Interest**: The closed polygon defining the proposed excavation trench or construction boundary. |
| **HSG47** | **Health and Safety Guidance 47**: The UK statutory regulatory standard for avoiding danger from underground services. |
| **LSBUD** | **LinesearchbeforeUdig**: The primary UK portal for statutory utility inquiries. |
| **Statutory Undertaker** | A licensed utility asset owner (e.g. UK Power Networks, Cadent Gas, Thames Water) legally responsible for buried infrastructure. |
| **Standoff Buffer** | A statutory safety margin (500mm hand-dig, 3m HV, 15m HP gas) surrounding the excavation boundary. |
| **Delta-E (ΔE)** | Mathematical metric representing perceptual difference between two colors in LAB color space. |
| **AUTO_CLEAR** | Automated permit clearance issued only when all 17 mandatory release gates pass simultaneously. |
| **HUMAN_REVIEW** | Mandatory escalation requiring inspection and sign-off by a certified human safety engineer. |
| **BLOCKED** | Execution halt triggered by corrupted files, missing drawings, or ambiguous multi-map disclosures. |
"""

def generate_trainee_cookbook():
    print(f"[1/2] Writing Markdown: {MD_PATH}")
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(MD_CONTENT)
        
    print(f"[2/2] Compiling PDF: {PDF_PATH}")
    compile_markdown_to_pdf(
        MD_PATH,
        PDF_PATH,
        title="SafeDig AI — Trainee Onboarding & Engineering Cookbook",
        subtitle="The Comprehensive Practical Handbook for New Engineers & Safety Specialists"
    )
    print("[SUCCESS] Trainee Onboarding & Cookbook generated successfully!")

if __name__ == "__main__":
    generate_trainee_cookbook()
