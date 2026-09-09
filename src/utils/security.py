"""Security and Input Sanitization Utilities for SafeDig AI Map QA.

Prevents directory traversal, validates PDF structural integrity,
and enforces strict filepath boundaries.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

class SecurityError(Exception):
    """Raised when a security validation or traversal attempt fails."""
    pass


def is_safe_filename(filename: str) -> bool:
    """Validate that a filename contains no directory traversal, null bytes, or dangerous chars."""
    if not filename or not isinstance(filename, str):
        return False
    if "\x00" in filename:
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    # Allowed alphanumeric + standard punctuation
    return bool(re.match(r"^[A-Za-z0-9_\-\. ]+$", filename))


def sanitize_path(base_dir: str, relative_or_abs_target: str) -> str:
    """Ensure that the target path resolves strictly within base_dir.
    
    Raises SecurityError if a directory traversal attempt is detected.
    """
    base_resolved = os.path.abspath(os.path.realpath(base_dir))
    
    if os.path.isabs(relative_or_abs_target):
        target_resolved = os.path.abspath(os.path.realpath(relative_or_abs_target))
    else:
        target_resolved = os.path.abspath(os.path.realpath(os.path.join(base_resolved, relative_or_abs_target)))
        
    # Check if target starts with base_resolved
    if not (target_resolved == base_resolved or target_resolved.startswith(base_resolved + os.sep)):
        raise SecurityError(
            f"Path traversal detected: Target '{relative_or_abs_target}' is outside base '{base_dir}'"
        )
    return target_resolved


def validate_pdf_safety(file_path: str, max_size_bytes: int = 150 * 1024 * 1024) -> Dict[str, Any]:
    """Validate PDF file header, size, and readability before heavy processing.
    
    Returns a status dictionary:
    {
        "is_safe": bool,
        "size_bytes": int,
        "is_empty": bool,
        "is_corrupt": bool,
        "is_encrypted": bool,
        "error_message": Optional[str]
    }
    """
    if not os.path.exists(file_path):
        return {
            "is_safe": False,
            "size_bytes": 0,
            "is_empty": True,
            "is_corrupt": False,
            "is_encrypted": False,
            "error_message": f"File does not exist: {file_path}"
        }
        
    size = os.path.getsize(file_path)
    if size == 0:
        return {
            "is_safe": False,
            "size_bytes": 0,
            "is_empty": True,
            "is_corrupt": False,
            "is_encrypted": False,
            "error_message": "Zero-byte file cannot be processed"
        }
        
    if size > max_size_bytes:
        return {
            "is_safe": False,
            "size_bytes": size,
            "is_empty": False,
            "is_corrupt": False,
            "is_encrypted": False,
            "error_message": f"File size ({size} bytes) exceeds maximum limit ({max_size_bytes} bytes)"
        }
        
    # Check magic header
    try:
        with open(file_path, "rb") as f:
            header = f.read(1024)
            if b"%PDF-" not in header:
                return {
                    "is_safe": False,
                    "size_bytes": size,
                    "is_empty": False,
                    "is_corrupt": True,
                    "is_encrypted": False,
                    "error_message": "Invalid PDF magic header (not a PDF file)"
                }
    except Exception as e:
        return {
            "is_safe": False,
            "size_bytes": size,
            "is_empty": False,
            "is_corrupt": True,
            "is_encrypted": False,
            "error_message": f"Read error: {str(e)}"
        }

    return {
        "is_safe": True,
        "size_bytes": size,
        "is_empty": False,
        "is_corrupt": False,
        "is_encrypted": False,
        "error_message": None
    }
