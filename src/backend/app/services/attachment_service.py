from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/x-python",
    "text/x-java",
    "text/javascript",
    "text/typescript",
    "text/x-c++src",
    "text/x-csrc",
    "text/x-go",
    "text/x-ruby",
    "text/x-php",
    "text/html",
    "text/css",
}

# Block dangerous file extensions (executables, installers, system files)
BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".pif", ".scr",  # Windows executables
    ".app", ".deb", ".rpm", ".dmg", ".pkg",          # Installers
    ".sh", ".bash", ".zsh", ".ksh",                  # Shell scripts
    ".ps1", ".psm1",                                 # PowerShell
    ".vbs", ".wsf",                                  # VB scripts
    ".jar", ".class",                                # Java
    ".dll", ".sys", ".drv", ".ocx",                  # System files
    ".iso", ".img",                                  # Disk images
    ".zip", ".rar", ".7z", ".tar", ".gz",            # Archives (can contain executables)
}

MAX_FILE_SIZE = settings.max_upload_mb * 1024 * 1024


def _backend_root() -> Path:
    # attachment_service.py -> services -> app -> backend root
    return Path(__file__).resolve().parents[2]


def ensure_upload_dir() -> Path:
    """Ensure upload directory exists."""
    configured = Path(settings.upload_dir)
    upload_path = configured if configured.is_absolute() else (_backend_root() / configured)
    upload_path = upload_path.resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def validate_file(file_name: str, file_size: int, mime_type: str) -> tuple[bool, str]:
    """Validate file before upload. Returns (is_valid, error_message)."""
    # Check file extension
    file_ext = Path(file_name).suffix.lower()
    if file_ext in BLOCKED_EXTENSIONS:
        return False, f"File type {file_ext} is not allowed. Executable and installer files are blocked for security."
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Max size is {settings.max_upload_mb}MB."
    
    if mime_type not in ALLOWED_MIME_TYPES:
        return False, f"File type {mime_type} not supported."
    
    return True, ""


def save_uploaded_file(file_content: bytes, file_name: str, mime_type: str) -> str:
    """Save uploaded file and return file path."""
    upload_path = ensure_upload_dir()
    unique_id = str(uuid4())[:8]
    file_path = upload_path / f"{unique_id}_{file_name}"
    
    try:
        file_path.write_bytes(file_content)
        return str(file_path.resolve())
    except Exception as exc:
        logger.exception(f"Failed to save file: {file_name}")
        raise


def delete_file(file_path: str) -> None:
    """Delete file from disk."""
    try:
        Path(file_path).unlink(missing_ok=True)
    except Exception:
        logger.exception(f"Failed to delete file: {file_path}")


def get_file_content(file_path: str) -> bytes | None:
    """Retrieve file content from disk."""
    raw_path = Path(file_path)
    candidate_paths = [raw_path]
    if not raw_path.is_absolute():
        candidate_paths.append((_backend_root() / raw_path).resolve())

    try:
        for candidate in candidate_paths:
            if candidate.exists():
                return candidate.read_bytes()

        logger.error(f"File not found in any candidate path: {file_path}")
        return None
    except Exception:
        logger.exception(f"Failed to read file: {file_path}")
        return None
