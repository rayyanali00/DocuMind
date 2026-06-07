from __future__ import annotations

from pathlib import Path

# Supported extensions per FRD section 4.1
DOCUMENT_EXTENSIONS = {"pdf", "docx", "txt", "csv", "xlsx", "pptx"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "tiff", "tif"}
SUPPORTED_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS

# Executable / dangerous extensions to reject explicitly (NFR-009)
EXECUTABLE_EXTENSIONS = {
    "exe", "dll", "so", "bin", "bat", "cmd", "sh", "ps1", "msi",
    "app", "apk", "deb", "rpm", "dmg", "com", "scr", "vbs", "jar",
}

MIME_BY_EXTENSION: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "tiff": "image/tiff",
    "tif": "image/tiff",
}


class UnsupportedFileError(ValueError):
    pass


class RejectedFileError(ValueError):
    pass


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def is_supported(filename: str) -> bool:
    return get_extension(filename) in SUPPORTED_EXTENSIONS


def is_executable(filename: str) -> bool:
    return get_extension(filename) in EXECUTABLE_EXTENSIONS


def validate_upload(filename: str, size_bytes: int, max_size_bytes: int) -> str:
    """Validate an incoming upload. Returns the lower-cased extension on success."""
    if not filename:
        raise RejectedFileError("Filename is required")

    ext = get_extension(filename)
    if not ext:
        raise UnsupportedFileError("File has no extension")

    if ext in EXECUTABLE_EXTENSIONS:
        raise RejectedFileError(f"Executable files are not allowed (.{ext})")

    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileError(f"Unsupported file type: .{ext}")

    if size_bytes <= 0:
        raise RejectedFileError("Empty file")

    if size_bytes > max_size_bytes:
        raise RejectedFileError(
            f"File exceeds max size of {max_size_bytes // (1024 * 1024)} MB"
        )

    return ext


def guess_mime(filename: str) -> str | None:
    return MIME_BY_EXTENSION.get(get_extension(filename))
