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


def resolve_index_path(root_or_file: str, preferred_name: Optional[str] = None) -> str:
    """Locate the index Excel file within a job root folder portably.
    
    Accepts:
    - Root folder path (e.g. 'Data/244414_201678', 'd:/Safedig_AG/Data/244414_201678')
    - Full index Excel file path (e.g. 'd:/Safedig_AG/Data/244414_201678/index.xlsx')
    
    Searches for:
    1. preferred_name (if provided)
    2. 'index.xlsx' (case-insensitive)
    3. 'index_org.xlsx' (case-insensitive)
    4. 'index.xls'
    5. Any other *.xlsx / *.xls file containing 'index' in root_dir
    6. Any *.xlsx / *.xls file in root_dir
    """
    if not root_or_file or not str(root_or_file).strip():
        resolved_root = str(settings.data_dir)
    else:
        raw = str(root_or_file).strip().replace("\\", "/")
        if os.path.isfile(raw):
            return os.path.abspath(raw)
        if os.path.isfile(root_or_file):
            return os.path.abspath(root_or_file)
            
        if raw.lower().endswith((".xlsx", ".xls")):
            if not preferred_name:
                preferred_name = os.path.basename(raw)
            folder_part = os.path.dirname(raw)
            resolved_root = resolve_folder_path(folder_part)
        else:
            resolved_root = resolve_folder_path(root_or_file)
            
    if preferred_name:
        p = os.path.join(resolved_root, preferred_name)
        if os.path.exists(p):
            return os.path.abspath(p)
            
    if not os.path.exists(resolved_root):
        return os.path.join(resolved_root, "index.xlsx")
        
    # Direct candidate check
    for cand in ["index.xlsx", "index_org.xlsx", "index.xls", "INDEX.xlsx", "INDEX.XLSX"]:
        p = os.path.join(resolved_root, cand)
        if os.path.exists(p):
            return os.path.abspath(p)
            
    # Directory walk check
    try:
        entries = os.listdir(resolved_root)
        for f in entries:
            if f.lower().endswith((".xlsx", ".xls")) and "index" in f.lower():
                return os.path.abspath(os.path.join(resolved_root, f))
        for f in entries:
            if f.lower().endswith((".xlsx", ".xls")):
                return os.path.abspath(os.path.join(resolved_root, f))
    except Exception as e:
        logger.warning(f"Error listing files in {resolved_root}: {e}")
        
    # Recursive fallback within data_dir matching preferred_name or index.xlsx
    target_name = (preferred_name or "index.xlsx").lower()
    if settings.data_dir.exists():
        for r, _, files in os.walk(str(settings.data_dir)):
            for f in files:
                if f.lower() == target_name:
                    return os.path.abspath(os.path.join(r, f))
                    
    return os.path.join(resolved_root, "index.xlsx")


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
