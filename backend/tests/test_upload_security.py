"""Security tests for file upload validation."""

import pytest

from app.security.upload import (
    generate_storage_filename,
    is_safe_path,
    sanitize_filename,
    validate_file_upload,
)

# ---------------------------------------------------------------------------
# sanitize_filename
# ---------------------------------------------------------------------------

def test_sanitize_strips_path_traversal():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\boot.ini") == "boot.ini"


def test_sanitize_removes_null_bytes_and_control_chars():
    assert sanitize_filename("file\x00name.txt") == "filename.txt"
    assert sanitize_filename("fi\nle.txt") == "file.txt"


def test_sanitize_truncates_long_names():
    long = "a" * 1000 + ".txt"
    out = sanitize_filename(long)
    assert len(out) <= 255


def test_sanitize_returns_fallback_for_empty():
    assert sanitize_filename("") == "unnamed"
    assert sanitize_filename("...") == "unnamed"


# ---------------------------------------------------------------------------
# generate_storage_filename
# ---------------------------------------------------------------------------

def test_generate_storage_is_random():
    a = generate_storage_filename("foo.pdf")
    b = generate_storage_filename("foo.pdf")
    assert a != b
    assert a.endswith(".pdf")


# ---------------------------------------------------------------------------
# validate_file_upload
# ---------------------------------------------------------------------------

class _FakeUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content_type = content_type
        self._content = content

    @property
    def file(self):
        return _FakeFile(self._content)


class _FakeFile:
    def __init__(self, content: bytes):
        self._content = content
        self._pos = 0

    def read(self):
        return self._content

    def seek(self, pos: int):
        self._pos = pos


def test_validate_rejects_dangerous_extensions():
    f = _FakeUploadFile("malware.sh", b"#!/bin/bash", "text/plain")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_file_upload(f, max_size_mb=5, allowed_extensions=["pdf", "docx", "txt"])
    assert exc_info.value.status_code == 400


def test_validate_rejects_disallowed_extension():
    f = _FakeUploadFile("image.png", b"\x89PNG\r\n\x1a\n", "image/png")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_file_upload(f, max_size_mb=5, allowed_extensions=["pdf", "docx", "txt"])
    assert exc_info.value.status_code == 400


def test_validate_rejects_empty_file():
    f = _FakeUploadFile("empty.txt", b"", "text/plain")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_file_upload(f, max_size_mb=5, allowed_extensions=["pdf", "docx", "txt"])
    assert exc_info.value.status_code == 400


def test_validate_rejects_oversized_file():
    big = b"x" * (10 * 1024 * 1024)  # 10 MB
    f = _FakeUploadFile("big.txt", big, "text/plain")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_file_upload(f, max_size_mb=5, allowed_extensions=["pdf", "docx", "txt"])
    assert exc_info.value.status_code == 413


def test_validate_magic_byte_mismatch():
    """A file claimed to be PDF but containing TXT bytes is rejected."""
    f = _FakeUploadFile("fake.pdf", b"This is not a PDF at all", "application/pdf")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_file_upload(f, max_size_mb=5, allowed_extensions=["pdf", "docx", "txt"])
    assert exc_info.value.status_code == 400


def test_validate_accepts_valid_pdf():
    pdf = b"%PDF-1.4\n%fake content\n%%EOF"
    f = _FakeUploadFile("doc.pdf", pdf, "application/pdf")
    storage, size = validate_file_upload(f, max_size_mb=5, allowed_extensions=["pdf", "docx", "txt"])
    assert size == len(pdf)
    assert storage.endswith(".pdf")


# ---------------------------------------------------------------------------
# is_safe_path
# ---------------------------------------------------------------------------

def test_is_safe_path_blocks_traversal(tmp_path):
    base = tmp_path / "uploads"
    base.mkdir()
    target = base / "ok.txt"
    target.write_text("x")
    assert is_safe_path(str(target), str(base))
    assert not is_safe_path(str(base / ".." / "etc" / "passwd"), str(base))
