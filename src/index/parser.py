import os
import pandas as pd
from typing import List, Optional
from src.domain.index_record import IndexRecord
from src.domain.enums import DocumentResolutionStatus
from src.config.logging import logger

def parse_index_excel(excel_path: str, job_id: str) -> List[IndexRecord]:
    if os.path.isdir(excel_path) or not os.path.exists(excel_path):
        from src.utils.paths import resolve_index_path
        resolved = resolve_index_path(excel_path)
        if os.path.exists(resolved) and os.path.isfile(resolved):
            logger.info(f"Portably resolved index path from '{excel_path}' to '{resolved}'")
            excel_path = resolved
        else:
            raise FileNotFoundError(f"Index Excel file not found: {excel_path}")
        
    df = pd.read_excel(excel_path, sheet_name=0)
    
    # Robust column mapping (case-insensitive, ignore spaces and underscores)
    col_map = {str(c).lower().replace("_", "").replace(" ", ""): c for c in df.columns}
    fn_col = col_map.get("filename")
    util_col = col_map.get("utilityname")
    type_col = col_map.get("utilitytype")
    status_col = col_map.get("status")
    warn_col = col_map.get("warning")
    comm_col = col_map.get("comments")
    
    records: List[IndexRecord] = []
    
    for idx, row in df.iterrows():
        # Check if 'FileName' column exists in this workbook
        file_name = None
        if fn_col:
            fn_val = row.get(fn_col)
            if pd.notnull(fn_val) and str(fn_val).strip() not in ["", "nan", "NaN"]:
                file_name = str(fn_val).strip()
                
        util_name = str(row.get(util_col, "")).strip() if util_col else ""
        util_type = str(row.get(type_col, "")).strip() if type_col else ""
        
        # Skip completely empty trailing rows
        if not util_name and not util_type and not file_name:
            continue
            
        raw_status = str(row.get(status_col, "No")).strip() if status_col else "No"
        is_asset = raw_status.lower() in ["yes", "true", "1"]
        
        raw_warning = None
        if warn_col:
            raw_warning_val = row.get(warn_col)
            if pd.notnull(raw_warning_val):
                w_str = str(raw_warning_val).strip()
                if w_str not in ["", "nan", "NaN"]:
                    raw_warning = w_str
                    
        raw_comments = None
        if comm_col:
            raw_comm_val = row.get(comm_col)
            if pd.notnull(raw_comm_val):
                c_str = str(raw_comm_val).strip()
                if c_str not in ["", "nan", "NaN"]:
                    raw_comments = c_str
                    
        init_res = DocumentResolutionStatus.MISSING if is_asset else DocumentResolutionStatus.EXCLUDED
        
        rec = IndexRecord(
            index_record_id=f"IDX-{job_id}-{idx + 1:03d}",
            job_id=job_id,
            row_index=idx + 1,
            file_name=file_name,
            utility_name=util_name,
            utility_type=util_type,
            raw_status=raw_status,
            is_asset_present=is_asset,
            raw_warning=raw_warning,
            raw_comments=raw_comments,
            resolution_status=init_res,
        )
        records.append(rec)
        
    logger.info(f"Parsed {len(records)} index records from {excel_path}")
    return records
