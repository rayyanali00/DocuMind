import pytest

from app.services.youtube import YouTubeError, extract_video_id


def test_extract_id_watch():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_short():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_id_shorts():
    assert extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_rejects_non_youtube():
    with pytest.raises(YouTubeError):
        extract_video_id("https://vimeo.com/12345")


def test_rejects_bad_id():
    with pytest.raises(YouTubeError):
        extract_video_id("https://www.youtube.com/watch?v=short")
