"""Unit tests for security sanitization and path validation."""

import os
import pytest
from src.utils.security import sanitize_path, is_safe_filename, validate_pdf_safety, SecurityError

def test_is_safe_filename_valid():
    assert is_safe_filename("42332089_WWU.pdf") is True
    assert is_safe_filename("index.xlsx") is True
    assert is_safe_filename("report_2026-09-03.json") is True
    assert is_safe_filename("document-123_abc.PDF") is True

def test_is_safe_filename_invalid_and_malicious():
    assert is_safe_filename("../../../etc/passwd") is False
    assert is_safe_filename("..\\..\\windows\\system32") is False
    assert is_safe_filename("file\x00.pdf") is False
    assert is_safe_filename("") is False
    assert is_safe_filename(None) is False
    assert is_safe_filename("file;rm -rf /") is False
    assert is_safe_filename("file|calc.exe") is False

def test_sanitize_path_valid(tmp_path):
    base = str(tmp_path)
    safe_file = tmp_path / "sub" / "valid.pdf"
    safe_file.parent.mkdir(parents=True, exist_ok=True)
    safe_file.write_text("dummy")

    resolved = sanitize_path(base, "sub/valid.pdf")
    assert resolved == os.path.abspath(str(safe_file))

def test_sanitize_path_traversal_detection(tmp_path):
    base = str(tmp_path / "sandbox")
    os.makedirs(base, exist_ok=True)
    
    with pytest.raises(SecurityError, match="Path traversal detected"):
        sanitize_path(base, "../../../secret.txt")

    with pytest.raises(SecurityError, match="Path traversal detected"):
        sanitize_path(base, "..\\..\\windows")

def test_validate_pdf_safety_non_existent(tmp_path):
    res = validate_pdf_safety(str(tmp_path / "non_existent.pdf"))
    assert res["is_safe"] is False
    assert res["is_empty"] is True

def test_validate_pdf_safety_zero_byte(tmp_path):
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    res = validate_pdf_safety(str(empty))
    assert res["is_safe"] is False
    assert res["is_empty"] is True

def test_validate_pdf_safety_not_pdf(tmp_path):
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"THIS IS NOT A PDF HEADER")
    res = validate_pdf_safety(str(fake))
    assert res["is_safe"] is False
    assert res["is_corrupt"] is True

def test_validate_pdf_safety_valid_header(tmp_path):
    valid = tmp_path / "valid.pdf"
    valid.write_bytes(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n")
    res = validate_pdf_safety(str(valid))
    assert res["is_safe"] is True
    assert res["is_corrupt"] is False
