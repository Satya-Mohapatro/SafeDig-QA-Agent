import os
from src.domain.enums import FileClassification

def classify_file(filename: str, relative_path: str = "") -> FileClassification:
    fn_lower = filename.lower()
    
    # 1. Excel index
    if fn_lower in ["index.xlsx", "index.xls", "index_org.xlsx", "index_org.xls"]:
        return FileClassification.INDEX
    if fn_lower.endswith(".xlsx") or fn_lower.endswith(".xls"):
        if "warning" in fn_lower:
            return FileClassification.REFERENCE
        if "index" in fn_lower:
            return FileClassification.INDEX
        return FileClassification.INDEX
        
    # 2. Legends & symbol guides
    if any(k in fn_lower for k in ["legend", "symbology", "symbol", "key"]):
        return FileClassification.LEGEND
        
    # 3. Safety Booklets / Non-map Reference Guidance
    if any(k in fn_lower for k in ["avoidance of danger", "look out look up", "charging structure", "guidance notes", "no assets affected letter"]):
        return FileClassification.SAFETY_REFERENCE
        
    if fn_lower.endswith(".pdf"):
        # Map documents vs Reference documents
        if any(k in fn_lower for k in ["booklet", "letter", "guidance", "terms"]):
            return FileClassification.REFERENCE
        return FileClassification.MAP
        
    # 4. JSON / Upstream Outputs
    if fn_lower.endswith(".json"):
        if "upstream" in fn_lower or "warning" in fn_lower:
            return FileClassification.UPSTREAM_OUTPUT
        return FileClassification.OTHER
        
    if fn_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        return FileClassification.MAP
        
    return FileClassification.OTHER
