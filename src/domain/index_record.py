from pydantic import BaseModel, Field
from typing import Optional
from .enums import DocumentResolutionStatus

class IndexRecord(BaseModel):
    index_record_id: str
    job_id: str
    row_index: int
    file_name: Optional[str] = None
    utility_name: str
    utility_type: str
    raw_status: str
    is_asset_present: bool
    raw_warning: Optional[str] = None
    raw_comments: Optional[str] = None
    resolution_status: DocumentResolutionStatus = DocumentResolutionStatus.MISSING
    resolved_file_id: Optional[str] = None
