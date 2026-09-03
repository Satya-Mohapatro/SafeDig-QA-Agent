import os
import pandas as pd
from typing import List, Optional
from src.domain.index_record import IndexRecord
from src.domain.enums import DocumentResolutionStatus
from src.config.logging import logger

def parse_index_excel(excel_path: str, job_id: str) -> List[IndexRecord]:
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Index Excel file not found: {excel_path}")
        
    df = pd.read_excel(excel_path, sheet_name=0)
    
    # Strip whitespace from column headers
    df.columns = [str(c).strip() for c in df.columns]
    
    records: List[IndexRecord] = []
    
    for idx, row in df.iterrows():
        # Check if 'FileName' column exists in this workbook
        file_name = None
        if "FileName" in df.columns:
            fn_val = row.get("FileName")
            if pd.notnull(fn_val) and str(fn_val).strip() not in ["", "nan", "NaN"]:
                file_name = str(fn_val).strip()
                
        util_name = str(row.get("UtilityName", "")).strip()
        util_type = str(row.get("UtilityType", "")).strip()
        
        # Skip completely empty trailing rows
        if not util_name and not util_type and not file_name:
            continue
            
        raw_status = str(row.get("Status", "No")).strip()
        is_asset = raw_status.lower() in ["yes", "true", "1"]
        
        raw_warning_val = row.get("Warning")
        raw_warning = None
        if pd.notnull(raw_warning_val):
            w_str = str(raw_warning_val).strip()
            if w_str not in ["", "nan", "NaN"]:
                raw_warning = w_str
                
        raw_comm_val = row.get("Comments") if "Comments" in df.columns else None
        raw_comments = None
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
