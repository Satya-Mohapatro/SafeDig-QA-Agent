import os
from typing import List
from src.config.logging import logger

class DirectoryScanner:
    @staticmethod
    def scan_for_job_folders(parent_dir: str, recursive: bool = False) -> List[str]:
        discovered_job_dirs = []
        if not os.path.exists(parent_dir):
            logger.warning(f"Parent directory does not exist: {parent_dir}")
            return []
            
        if recursive:
            for root, dirs, files in os.walk(parent_dir):
                has_index = any(f.lower() in ["index.xlsx", "index.xls"] for f in files)
                if has_index:
                    discovered_job_dirs.append(os.path.abspath(root))
        else:
            entries = os.listdir(parent_dir)
            for entry in sorted(entries):
                full_path = os.path.join(parent_dir, entry)
                if os.path.isdir(full_path):
                    files = os.listdir(full_path)
                    has_index = any(f.lower() in ["index.xlsx", "index.xls"] for f in files)
                    if has_index:
                        discovered_job_dirs.append(os.path.abspath(full_path))
                        
        logger.info(f"Scanned '{parent_dir}': discovered {len(discovered_job_dirs)} valid job folders.")
        return discovered_job_dirs

directory_scanner = DirectoryScanner()
