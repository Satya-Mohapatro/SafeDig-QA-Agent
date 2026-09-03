from typing import List, Dict, Any
from datetime import datetime
from src.domain.document import DiscoveredFile
from src.domain.enums import FileClassification

def build_manifest(job_id: str, root_dir: str, files: List[DiscoveredFile]) -> Dict[str, Any]:
    counts = {}
    for f in files:
        cls_name = f.classification.value
        counts[cls_name] = counts.get(cls_name, 0) + 1
        
    return {
        "job_id": job_id,
        "root_dir": root_dir,
        "created_at": datetime.utcnow().isoformat(),
        "total_files": len(files),
        "classification_summary": counts,
        "files": [f.model_dump() for f in files]
    }
