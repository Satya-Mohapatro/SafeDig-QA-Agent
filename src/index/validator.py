from typing import List, Dict, Any
from src.domain.index_record import IndexRecord

def validate_index_records(records: List[IndexRecord]) -> Dict[str, Any]:
    total = len(records)
    with_asset = [r for r in records if r.is_asset_present]
    without_asset = [r for r in records if not r.is_asset_present]
    with_warning = [r for r in records if r.raw_warning]
    
    # An index is valid if it has records and utilities defined
    is_valid = total > 0 and len(with_asset) > 0
    
    return {
        "total_records": total,
        "assets_present_count": len(with_asset),
        "assets_absent_count": len(without_asset),
        "claimed_warnings_count": len(with_warning),
        "is_valid": is_valid,
        "validation_errors": []
    }
