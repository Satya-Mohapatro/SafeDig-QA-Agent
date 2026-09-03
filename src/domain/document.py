from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .enums import FileClassification, PDFModality

class DiscoveredFile(BaseModel):
    file_id: str
    relative_path: str
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    sha256: str
    classification: FileClassification
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentPage(BaseModel):
    page_num: int
    width_pt: float
    height_pt: float
    dpi: int = 72
    has_text: bool = False
    text_snippet: Optional[str] = None
    vector_paths_count: int = 0
    images_count: int = 0
    modality: PDFModality = PDFModality.VECTOR

class Document(BaseModel):
    document_id: str
    job_id: str
    file_id: str
    filename: str
    sha256: str
    page_count: int
    pages: List[DocumentPage] = Field(default_factory=list)
    provider: Optional[str] = None
    utility_type: Optional[str] = None
    modality: PDFModality = PDFModality.VECTOR
    is_corrupted: bool = False
