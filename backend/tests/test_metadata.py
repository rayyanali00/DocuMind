from app.ai.metadata_extractor import extract_keywords, extract_metadata, extract_summary, extract_title


def test_title_first_line():
    text = "\n\nQuarterly Report 2026\nThis document outlines..."
    assert extract_title(text) == "Quarterly Report 2026"


def test_title_fallback():
    assert extract_title("", fallback="fallback.pdf") == "fallback.pdf"


def test_summary_truncates():
    text = "A" * 1000
    s = extract_summary(text, max_chars=100)
    assert s is not None and len(s) <= 101  # 100 + ellipsis


def test_keywords_filters_stopwords():
    text = "The quick brown fox jumps over the lazy dog. The fox is quick and brown."
    kws = extract_keywords(text, top_k=5)
    assert "the" not in kws
    assert "fox" in kws
    assert "quick" in kws


def test_extract_metadata_bundle():
    meta = extract_metadata("Hello World\nSome body text about pipelines and pipelines.")
    assert meta.title == "Hello World"
    assert meta.summary is not None
    assert "pipelines" in meta.keywords
