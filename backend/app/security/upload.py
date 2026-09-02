"""File upload security utilities.

Provides defense-in-depth validation for resume uploads:
1. Extension whitelist (block dangerous extensions)
2. Magic-byte sniffing (verify actual file type regardless of browser-declared MIME)
3. Size enforcement
4. Randomized storage names (no original filename on disk)
5. Path-traversal checks
"""

from __future__ import annotations

import logging
import os
import re
import secrets
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

# Extensions that are always blocked regardless of MIME
DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".scr", ".msi", ".vbs", ".js",
    ".jar", ".sh", ".php", ".asp", ".aspx", ".jsp", ".py", ".rb",
    ".pl", ".cgi", ".html", ".htm", ".svg", ".ps1", ".wsf", ".pif",
    ".application", ".gadget", ".msh", ".msh1", ".msh2", ".mshxml",
    ".msh1xml", ".msh2xml", ".action", ".cpl", ".crt", ".reg",
    ".ps2", ".vbe", ".jse", ".ws", ".wf", ".scf", ".lnk",
    ".inf", ".inx", ".isp",
}

MAX_FILENAME_LENGTH = 255

# Magic-byte signatures: magic bytes → (expected extension, human label)
_MAGIC_SIGNATURES = {
    b"%PDF-":                           (".pdf", "PDF document"),
    b"PK\x03\x04":                      (".docx", "ZIP/DOCX file"),
    b"\xff\xd8\xff":                   (".jpg", "JPEG image"),
    b"\x89PNG\r\n\x1a\n":               (".png", "PNG image"),
}


def _sniff_magic(content: bytes) -> str | None:
    """Return the detected file type from magic bytes, or None if unknown."""
    for magic, (ext, _label) in _MAGIC_SIGNATURES.items():
        if content.startswith(magic):
            return ext
    # Fallback: check plain-text indicator
    try:
        content.decode("utf-8")
        return ".txt"
    except UnicodeDecodeError:
        pass
    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other attacks."""
    filename = os.path.basename(filename)
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    filename = filename.replace("/", "").replace("\\", "")
    filename = filename.lstrip(".")
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        filename = name[: MAX_FILENAME_LENGTH - len(ext)] + ext
    return filename or "unnamed"


def generate_storage_filename(original_filename: str) -> str:
    """Generate a randomized storage filename with a safe extension."""
    safe_name = sanitize_filename(original_filename)
    ext = Path(safe_name).suffix.lower()
    return f"{secrets.token_hex(16)}{ext}"


def validate_file_upload(
    file: UploadFile,
    max_size_mb: int,
    allowed_extensions: list,
) -> tuple[str, int]:
    """Validate an uploaded file for security.

    Performs:
    - Dangerous extension blocklist
    - Allowed extension whitelist
    - Magic-byte sniffing (detects real file type)
    - Size enforcement

    Returns:
        Tuple of (storage_filename, size_bytes)

    Raises:
        HTTPException on validation failure
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    if "\x00" in file.filename or "\0" in file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename contains invalid characters",
        )

    safe_original = sanitize_filename(file.filename)
    ext = Path(safe_original).suffix.lower()

    # 1. Dangerous extension blocklist (double-extension attacks, etc.)
    if ext in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' is not allowed",
        )

    # 2. Allowed extension whitelist
    allowed_set = {f".{e.lower().lstrip('.')}" for e in allowed_extensions}
    if ext not in allowed_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not supported. Allowed: {', '.join(sorted(allowed_set))}",
        )

    # 3. Read content
    content = file.file.read()
    size = len(content)

    # 4. Size enforcement
    max_bytes = max_size_mb * 1024 * 1024
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size_mb} MB",
        )

    # 5. Magic-byte sniffing: verify the file body matches the claimed type
    detected_ext = _sniff_magic(content)

    # Validation rule: a file claiming to be X must have magic bytes that are
    # either X, OR are compatible (e.g., DOCX is a ZIP container so its
    # magic bytes are PK\x03\x04).
    if ext == ".pdf":
        if detected_ext is None or detected_ext != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match its extension (expected PDF)",
            )
    elif ext == ".docx":
        # DOCX is a ZIP container: magic bytes must be PK\x03\x04
        if detected_ext != ".docx":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match its extension (expected DOCX)",
            )
    elif ext == ".txt":
        # TXT is a catch-all for any text content
        if detected_ext not in (".txt", ".docx", ".pdf", ".png", ".jpg"):
            # Binary content claiming to be .txt is suspicious
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not appear to be valid text",
            )

    logger.debug(
        "File validated: original=%s ext=%s detected=%s size=%d",
        safe_original, ext, detected_ext, size,
    )

    # Reset file pointer so downstream handlers can read again
    file.file.seek(0)

    return generate_storage_filename(safe_original), size


def is_safe_path(filepath: str, base_dir: str) -> bool:
    """Return True if filepath is within base_dir (no path traversal)."""
    base = Path(base_dir).resolve()
    target = Path(filepath).resolve()
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False
