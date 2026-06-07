import pytest

from app.pipelines.validators import (
    RejectedFileError,
    UnsupportedFileError,
    is_supported,
    validate_upload,
)

MAX = 10 * 1024 * 1024


def test_supported_documents():
    for name in ("a.pdf", "b.DOCX", "c.txt", "d.csv", "e.xlsx", "f.pptx"):
        assert is_supported(name)


def test_supported_images():
    for name in ("a.png", "b.JPG", "c.jpeg", "d.tiff"):
        assert is_supported(name)


def test_rejects_executable():
    with pytest.raises(RejectedFileError):
        validate_upload("malware.exe", 100, MAX)


def test_rejects_unsupported():
    with pytest.raises(UnsupportedFileError):
        validate_upload("notes.md", 100, MAX)


def test_rejects_oversize():
    with pytest.raises(RejectedFileError):
        validate_upload("big.pdf", MAX + 1, MAX)


def test_accepts_valid():
    assert validate_upload("doc.pdf", 1024, MAX) == "pdf"
