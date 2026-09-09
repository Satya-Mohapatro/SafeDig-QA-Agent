# SafeDig AI — Technology Stack Specification
**Classification**: Enterprise AI & Safety-Critical Engineering  
**Operating Standard**: UK HSG47 (Avoiding Danger from Underground Services) & CDM 2015  

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

## 3. Mandatory Safety Rule: Zero LLM Validation Authority

Under SafeDig enterprise policy:
- The LLM has **ADVISORY AUTHORITY ONLY**.
- No safety gate, auto-clear decision, or hazard finding can be overridden by model inferences.
- If the LLM produces a contradiction or becomes unresponsive, the system automatically defaults to deterministic safety rules with zero latency.
