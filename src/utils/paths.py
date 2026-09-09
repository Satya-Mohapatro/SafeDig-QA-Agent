import os
from pathlib import Path
from typing import Optional
from src.config.settings import settings
from src.config.logging import logger

def resolve_folder_path(folder_path: Optional[str]) -> str:
    """Resolve an incoming folder path portably across different machines.
    
    Handles:
    - Already valid path on the current machine -> returns normalized absolute path.
    - Relative path (e.g. 'Data/244414_201678' or '244414_201678') -> resolves relative
      to settings.data_dir or settings.project_root.
    - Stale absolute path from another machine (e.g. 'd:/Safedig_AG/Data/244414_201678'
      or '/opt/safedig/Data/244414_201678') -> extracts folder name and re-anchors
      it to the current machine's settings.data_dir.
    - Mistakenly passed file paths -> strips the filename and resolves the directory.
    """
    if not folder_path or not str(folder_path).strip():
        return str(settings.data_dir)
        
    raw = str(folder_path).strip()
    norm = raw.replace("\\", "/")
    
    # If a file path was mistakenly passed, extract its directory
    if norm.lower().endswith((".xlsx", ".xls", ".pdf", ".json", ".png", ".jpg", ".csv")):
        norm = os.path.dirname(norm)
        raw = os.path.dirname(raw)
        if not norm or not raw:
            return str(settings.data_dir)
            
    # 1. Exact path exists on this machine
    if os.path.exists(raw):
        return os.path.abspath(raw)
    if os.path.exists(norm):
        return os.path.abspath(norm)
        
    # 2. Try directly relative to data_dir
    cand_data = (settings.data_dir / norm.lstrip("/")).resolve()
    if cand_data.exists():
        return str(cand_data)
        
    # 3. Try directly relative to project_root
    cand_root = (settings.project_root / norm.lstrip("/")).resolve()
    if cand_root.exists():
        return str(cand_root)
        
    # 4. Handle paths containing 'data/' or 'Data/'
    norm_lower = norm.lower()
    if "/data/" in norm_lower:
        sub_rel = norm[norm_lower.index("/data/") + 6:].strip("/")
        cand_sub = (settings.data_dir / sub_rel).resolve()
        if cand_sub.exists():
            return str(cand_sub)
    elif norm_lower.startswith("data/"):
        sub_rel = norm[5:].strip("/")
        cand_sub = (settings.data_dir / sub_rel).resolve()
        if cand_sub.exists():
            return str(cand_sub)
            
    # 5. Extract just the folder name (e.g. '244414_201678' from 'd:/Safedig_AG/Data/244414_201678')
    basename = os.path.basename(norm.rstrip("/"))
    cand_base = (settings.data_dir / basename).resolve()
    if cand_base.exists():
        return str(cand_base)
        
    # 6. Check inside all subfolders of settings.data_dir
    if settings.data_dir.exists():
        for item in settings.data_dir.iterdir():
            if item.is_dir() and item.name.lower() == basename.lower():
                return str(item.resolve())
                
    # Fallback: return original raw path
    return raw


def inspect_index_columns(file_path: str) -> set:
    """Inspect the normalized column names of an Excel index candidate.
    
    Reads nrows=0 for maximum speed and minimal memory overhead.
    Normalizes column names to lowercase alphanumeric without underscores/spaces.
    """
    if not file_path or not os.path.exists(file_path) or not os.path.isfile(file_path):
        return set()
    try:
        import pandas as pd
        df = pd.read_excel(file_path, sheet_name=0, nrows=0)
        return {str(c).lower().replace("_", "").replace(" ", "") for c in df.columns}
    except Exception as e:
        logger.debug(f"Could not inspect columns of {file_path}: {e}")
        return set()


def score_index_candidate(file_path: str) -> tuple:
    """Score an index candidate workbook based on its column schema richness.
    
    Returns:
        (score, reason_string)
        
    Scoring tiers:
    - Contains FileName + UtilityName + UtilityType + Status -> Score 100
      (Richest index containing exact file mapping)
    - Contains FileName + UtilityName + Status -> Score 90
    - Contains FileName column -> Score 80
    - Standard index containing UtilityName + UtilityType + Status (no FileName) -> Score 50
    - Contains UtilityName + Status (no FileName) -> Score 40
    - Other readable Excel -> Score 10
    - Unreadable / missing -> Score 0
    """
    cols = inspect_index_columns(file_path)
    if not cols:
        return 0, "unreadable or empty excel file"
        
    has_fn = "filename" in cols
    has_util = "utilityname" in cols
    has_type = "utilitytype" in cols
    has_status = "status" in cols
    
    if has_fn and has_util and has_type and has_status:
        return 100, "contains FileName mapping columns"
    if has_fn and has_util and has_status:
        return 90, "contains FileName mapping columns"
    if has_fn:
        return 80, "contains FileName column"
    if has_util and has_type and has_status:
        return 50, "standard index containing UtilityName, UtilityType, and Status (no FileName)"
    if has_util and has_status:
        return 40, "contains UtilityName and Status (no FileName)"
    return 10, "basic excel workbook"


def select_best_index_workbook(candidate_paths: list) -> tuple:
    """Select the richest index workbook from a list of candidates based on column schema.
    
    Prefers workbooks containing FileName mapping columns (e.g. index_org.xlsx),
    while preserving fallback to index.xlsx/index.xls if no richer index exists.
    
    Returns:
        (best_file_path, selection_reason)
    """
    valid_candidates = []
    for p in candidate_paths:
        if not p or not os.path.exists(p) or not os.path.isfile(p):
            continue
        fname = os.path.basename(p).lower()
        if "warning" in fname:
            continue
        norm_p = os.path.abspath(p)
        if norm_p not in valid_candidates:
            valid_candidates.append(norm_p)
            
    if not valid_candidates:
        return "", "no valid candidate files found"
        
    if len(valid_candidates) == 1:
        score, reason = score_index_candidate(valid_candidates[0])
        selected_name = os.path.basename(valid_candidates[0])
        logger.info(f"Selected index workbook: {selected_name}")
        logger.info(f"Reason: {reason}")
        return valid_candidates[0], reason
        
    # Evaluate and rank each candidate
    scored = []
    for p in valid_candidates:
        score, reason = score_index_candidate(p)
        fname_lower = os.path.basename(p).lower()
        # Tie-breaker priority if scores are equal: index_org > index > others
        tie_breaker = 2 if "index_org" in fname_lower else (1 if "index" in fname_lower else 0)
        scored.append((score, tie_breaker, p, reason))
        
    # Sort descending by score, then tie_breaker
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best_score, _, best_path, best_reason = scored[0]
    
    selected_name = os.path.basename(best_path)
    logger.info(f"Selected index workbook: {selected_name}")
    logger.info(f"Reason: {best_reason}")
    
    return best_path, best_reason


def resolve_index_path(root_or_file: Optional[str], preferred_name: Optional[str] = None) -> str:
    """Resolve the index file path portably across environments with schema-aware selection.
    
    Inspection Pipeline:
    1. discover Excel index candidates
    2. inspect their columns/schema
    3. prefer an index containing FileName + UtilityName + UtilityType + Status (e.g. index_org.xlsx)
    4. fallback to index.xlsx / index.xls if no richer index exists
    """
    if not root_or_file or not str(root_or_file).strip():
        resolved_root = str(settings.data_dir)
    else:
        raw = str(root_or_file).strip().replace("\\", "/")
        if os.path.isfile(raw) and not preferred_name:
            folder_part = os.path.dirname(raw)
            resolved_root = resolve_folder_path(folder_part) if folder_part else os.path.dirname(os.path.abspath(raw))
        elif raw.lower().endswith((".xlsx", ".xls")):
            folder_part = os.path.dirname(raw)
            resolved_root = resolve_folder_path(folder_part) if folder_part else resolve_folder_path(root_or_file)
        else:
            resolved_root = resolve_folder_path(root_or_file)

    if not os.path.exists(resolved_root) or not os.path.isdir(resolved_root):
        default_file = "index_org.xlsx" if os.path.exists(os.path.join(resolved_root, "index_org.xlsx")) else "index.xlsx"
        return os.path.join(resolved_root, default_file)

    # 1. Discover all candidate Excel files in resolved_root
    candidate_paths = []
    try:
        entries = os.listdir(resolved_root)
        for e in entries:
            if e.lower().endswith((".xlsx", ".xls")) and "warning" not in e.lower():
                candidate_paths.append(os.path.abspath(os.path.join(resolved_root, e)))
    except Exception as e:
        logger.warning(f"Error listing files in {resolved_root}: {e}")

    # 2. Select the richest index candidate based on schema
    if candidate_paths:
        best_path, _ = select_best_index_workbook(candidate_paths)
        if best_path:
            return best_path

    # 3. Recursive fallback within data_dir
    target_names = ["index_org.xlsx", "index.xlsx"]
    if preferred_name:
        target_names.insert(0, preferred_name.lower())
    if settings.data_dir.exists():
        found_in_data = []
        for r, _, files in os.walk(str(settings.data_dir)):
            for f in files:
                if f.lower().endswith((".xlsx", ".xls")) and "warning" not in f.lower():
                    if f.lower() in target_names or "index" in f.lower():
                        found_in_data.append(os.path.abspath(os.path.join(r, f)))
        if found_in_data:
            best_path, _ = select_best_index_workbook(found_in_data)
            if best_path:
                return best_path

    default_file = "index_org.xlsx" if os.path.exists(os.path.join(resolved_root, "index_org.xlsx")) else "index.xlsx"
    return os.path.join(resolved_root, default_file)


def resolve_file_path(file_path: str, root_dir: Optional[str] = None) -> str:
    """Resolve a file path (e.g. PDF map) portably across environments."""
    if not file_path:
        return ""
    if os.path.exists(file_path):
        return os.path.abspath(file_path)
        
    norm = file_path.replace("\\", "/")
    if os.path.exists(norm):
        return os.path.abspath(norm)
        
    fname = os.path.basename(norm)
    
    # 1. If root_dir is provided or can be extracted from file_path
    target_root = root_dir
    if not target_root and os.path.dirname(norm):
        target_root = os.path.dirname(norm)
        
    if target_root:
        res_root = resolve_folder_path(target_root)
        p = os.path.join(res_root, fname)
        if os.path.exists(p):
            return os.path.abspath(p)
        if os.path.exists(res_root):
            for r, _, files in os.walk(res_root):
                for f in files:
                    if f.lower() == fname.lower():
                        return os.path.abspath(os.path.join(r, f))
                        
    # 2. Check directly in data_dir
    cand_data = settings.data_dir / fname
    if cand_data.exists():
        return str(cand_data.resolve())
        
    # 3. Check recursively in data_dir
    if settings.data_dir.exists():
        for r, _, files in os.walk(str(settings.data_dir)):
            for f in files:
                if f.lower() == fname.lower():
                    return os.path.abspath(os.path.join(r, f))
                    
    return file_path


def resolve_catalogue_path(catalogue_path: Optional[str] = None) -> str:
    """Resolve the warning catalogue excel path portably across environments."""
    candidates = []
    if catalogue_path and str(catalogue_path).strip():
        raw_p = Path(catalogue_path)
        candidates.append(raw_p)
        candidates.append(settings.project_root / catalogue_path)
        candidates.append(settings.data_dir / catalogue_path)
        candidates.append(settings.data_dir / raw_p.name)

    candidates.extend([
        settings.catalogue_path,
        settings.data_dir / "warnings_list.xlsx",
        settings.project_root / "Data" / "warnings_list.xlsx",
        Path("Data/warnings_list.xlsx"),
    ])

    for c in candidates:
        if c and c.exists() and c.is_file():
            return str(c.resolve())

    # Search Data dir for any warnings_list*.xlsx
    if settings.data_dir.exists():
        for f in settings.data_dir.iterdir():
            if f.is_file() and f.name.lower().startswith("warnings_list") and f.suffix.lower() in [".xlsx", ".xls"]:
                return str(f.resolve())

    return str(settings.catalogue_path)
