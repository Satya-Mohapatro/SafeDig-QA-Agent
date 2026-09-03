import os
import mimetypes
from typing import List, Dict
from src.domain.document import DiscoveredFile
from .hasher import compute_sha256
from .classifier import classify_file
from src.config.logging import logger

def scan_root_folder(root_dir: str) -> List[DiscoveredFile]:
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"Root folder does not exist: {root_dir}")
        
    discovered: List[DiscoveredFile] = []
    file_counter = 1
    
    for root, _, files in os.walk(root_dir):
        for fname in sorted(files):
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, root_dir)
            ext = os.path.splitext(fname)[1].lower()
            mime, _ = mimetypes.guess_type(full_path)
            mime = mime or "application/octet-stream"
            
            try:
                size_bytes = os.path.getsize(full_path)
                sha256 = compute_sha256(full_path)
                classification = classify_file(fname, rel_path)
                
                df = DiscoveredFile(
                    file_id=f"FIL-{file_counter:04d}",
                    relative_path=rel_path.replace("\\", "/"),
                    filename=fname,
                    extension=ext,
                    mime_type=mime,
                    size_bytes=size_bytes,
                    sha256=sha256,
                    classification=classification,
                    metadata={"full_path": full_path}
                )
                discovered.append(df)
                file_counter += 1
            except Exception as e:
                logger.error(f"Error reading file {full_path}: {e}")
                
    logger.info(f"Scanned root folder '{root_dir}': {len(discovered)} files discovered.")
    return discovered
