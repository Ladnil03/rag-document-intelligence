"""Filesystem helpers for uploaded document bytes.

Centralised so the document service does not touch ``open()``/``os.remove``
directly. The actual directory lives at ``backend/storage/`` and is
configured by ``app.core.config.STORAGE_DIR``.
"""

import os

from app.core import config


def ensure_storage_dir() -> None:
    """Create the storage directory if it does not exist."""
    os.makedirs(config.STORAGE_DIR, exist_ok=True)


def save_upload_bytes(absolute_path: str, contents: bytes) -> None:
    """Write upload bytes to disk, raising ``OSError`` on failure."""
    ensure_storage_dir()
    with open(absolute_path, "wb") as f:
        f.write(contents)


def remove_file(absolute_path: str) -> None:
    """Remove a file from disk, raising ``OSError`` on failure."""
    os.remove(absolute_path)


def storage_is_writable() -> bool:
    return os.path.exists(config.STORAGE_DIR) and os.access(config.STORAGE_DIR, os.W_OK)
