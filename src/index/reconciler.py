from typing import List, Dict, Any
from src.domain.index_record import IndexRecord
from src.domain.enums import DocumentResolutionStatus

def account_for_all_rows(records: List[IndexRecord]) -> Dict[str, Any]:
    unaccounted = []
    summary = {
        DocumentResolutionStatus.UNIQUE.value: 0,
        DocumentResolutionStatus.EXCLUDED.value: 0,
        DocumentResolutionStatus.MISSING.value: 0,
        DocumentResolutionStatus.AMBIGUOUS.value: 0,
        DocumentResolutionStatus.INVALID.value: 0,
    }
    
    for r in records:
        st = r.resolution_status.value
        summary[st] = summary.get(st, 0) + 1
        if r.resolution_status == DocumentResolutionStatus.MISSING and r.is_asset_present:
            unaccounted.append(r)
            
    all_accounted = len(unaccounted) == 0
    return {
        "all_accounted_for": all_accounted,
        "total_rows": len(records),
        "summary": summary,
        "missing_or_unresolved_rows": [
            {"row": r.row_index, "utility": r.utility_name, "file_name": r.file_name}
            for r in unaccounted
        ]
    }
