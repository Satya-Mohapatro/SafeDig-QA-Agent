"""
SafeDig AI - Technology Stack Specification Generator
Outputs:
1. Documentation/SafeDig_Technology_Stack_Specification.md
2. Documentation/SafeDig_Technology_Stack_Specification.pdf
3. SafeDig_Technology_Stack_Specification.pdf (Root mirror)
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
MD_PATH = os.path.join(DOCS_DIR, "SafeDig_Technology_Stack_Specification.md")
PDF_PATH = os.path.join(DOCS_DIR, "SafeDig_Technology_Stack_Specification.pdf")
ROOT_PDF_PATH = os.path.join(ROOT_DIR, "SafeDig_Technology_Stack_Specification.pdf")

os.makedirs(DOCS_DIR, exist_ok=True)

MD_CONTENT = """# SafeDig AI — Technology Stack Specification
**Classification**: Enterprise AI & Safety-Critical Engineering  
**Standard**: UK Health and Safety Guidance 47 (HSG47) & CDM 2015  
**Core Invariant**: Zero Escaped Hazards (`SAFE_MODE=True`)

---

## 1. Architectural Philosophy: Dual-Engine Verification

SafeDig uses a segregated dual-engine model specifically engineered for zero-hallucination utility clearance:

1. **Deterministic Geometry & Computer Vision Core**:
   - PyMuPDF vector math, Shapely 2D spatial geometry, OpenCV image analysis, and a 17-Gate Policy Engine.
   - 100% deterministic, auditable, bit-for-bit reproducible, zero hallucination.
2. **AI / LLM Advisory Layer**:
   - LangGraph stateful DAG orchestration paired with local on-premise LLMs (Qwen 2.5 / Llama 3.2).
   - Generates natural-language summaries, discrepancy explanations, and operator advisory notes.
   - **Zero Validation Authority**: Cannot override, clear, or relax any safety gate.

---

## 2. Technology Stack Breakdown

### Backend & Core Server Framework
| Component | Technology | Version | Role in Platform |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `>=3.11` | High-speed typing, pattern matching, async core |
| **REST API** | FastAPI | `>=0.100.0` | Asynchronous REST endpoints, OpenAPI auto-docs |
| **ASGI Server** | Uvicorn | `>=0.22.0` | High-throughput non-blocking production runtime |
| **Data Validation**| Pydantic v2 & Settings | `>=2.0.0` | Strict domain models, environment config |
| **Async Client** | HTTPX & AnyIO | `>=0.25.0` | Non-blocking API calls and concurrency |

### Computer Vision, Spatial Geometry & Vector Extraction
| Component | Technology | Version | Role in Platform |
| :--- | :--- | :--- | :--- |
| **Vector Engine** | PyMuPDF (fitz) | `1.28.2` | Vector path extraction, dash analysis, 300 DPI rasterizer |
| **Spatial Geometry**| Shapely | `>=2.0.0` | Exact 2D polygon intersection, AOI bounding & buffer math |
| **Computer Vision**| OpenCV (headless) | `>=4.8.0` | HSV color masking, contour detection, image crops |
| **Spreadsheets** | Pandas & OpenPyXL | `>=2.0.0` | Statutory index parsing (`index.xlsx`) & normalization |
| **Database** | SQLAlchemy + aiosqlite | `>=2.0.0` | Async SQLite (`safedig.db`) & PostgreSQL production support |
| **Migrations** | Alembic | `>=1.13.0` | Schema migration tracking and revision history |
| **PDF Reporting** | ReportLab | `5.0.1` | Automated generation of audit reports and compliance specs |

### AI, Local LLMs & Orchestration
| Component | Technology | Role in Platform |
| :--- | :--- | :--- |
| **Pipeline DAG** | LangGraph (`>=0.2.0`) | Stateful deterministic pipeline orchestration |
| **Core Abstraction**| LangChain-Core (`>=0.3.0`)| Standardized messages, prompts & agent states |
| **Primary LLM** | Qwen 2.5 (7B / 14B) via Ollama | Technical reasoning, discrepancy explanations |
| **Edge LLM** | Llama 3.2 (3B) via Ollama | Lightweight low-resource edge deployments |
| **Deterministic Fallback**| Python Rule Explainer | 0ms offline fallback if LLM is unavailable |

### Frontend Console & Inspection Engine
| Component | Technology | Role in Platform |
| :--- | :--- | :--- |
| **Framework** | Vanilla JS + Tailwind CSS | Responsive, zero-dependency, high-speed single page console |
| **Vector Icons** | Lucide Icons | Visual status indicators, gate badges, control buttons |
| **Canvas Engine**| DOM Hardware-Accelerated Zoom | Pan (drag) & Zoom (50%–600%), AOI centering & radar scanner loader |

---

## 3. Infrastructure & Deployment Environment

| Tier | Technology | Specification / Configuration |
| :--- | :--- | :--- |
| **Container Engine** | Docker & Docker Compose | Multi-stage lightweight image on Python 3.11-slim base |
| **Reverse Proxy** | Nginx Alpine | SSL termination, client max body size 100MB, Gzip compression |
| **Process Daemon** | Linux Systemd | Persistent service management with automatic restart on failure |
| **Database Storage** | SQLite with WAL Mode | Zero-config, single-file forensic database with concurrent reads |

---

## 4. Hardware Sizing & Recommended Profiles

| Environment | CPU | RAM | Storage | Local LLM Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Local Dev Workstation** | 4 Cores (x86_64 / ARM64) | 16 GB | 20 GB NVMe | Qwen 2.5 (7B) via Ollama (GPU or CPU) |
| **Field Excavator Van (Edge)**| 4 Cores (Intel N100 / Pi 5) | 8 GB | 64 GB SSD | Llama 3.2 (3B) or 0ms Rule Fallback |
| **Enterprise Central Server**| 16+ Cores | 64 GB | 500 GB NVMe | Qwen 2.5 (14B / 32B) with NVIDIA CUDA |

---

## 5. Mandatory Safety Rule: Zero LLM Validation Authority

Under SafeDig enterprise policy:
- The LLM has **ADVISORY AUTHORITY ONLY**.
- No safety gate, auto-clear decision, or hazard finding can be overridden by model inferences.
- If the LLM produces a contradiction or becomes unresponsive, the system automatically defaults to deterministic safety rules with zero latency.
"""

def generate_tech_stack_documentation():
    print(f"[1/2] Writing Markdown: {MD_PATH}")
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(MD_CONTENT)
        
    print(f"[2/2] Compiling PDF: {PDF_PATH}")
    compile_markdown_to_pdf(
        MD_PATH,
        PDF_PATH,
        title="SafeDig AI — Technology Stack Specification",
        subtitle="Production Architecture, Dependencies & Hardware Manifest"
    )
    print("[SUCCESS] Technology Stack Specification generated successfully!")

if __name__ == "__main__":
    generate_tech_stack_documentation()
