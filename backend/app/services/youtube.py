"""YouTube transcript ingestion (FR-027..FR-037)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from loguru import logger

_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


class YouTubeError(Exception):
    pass


@dataclass(slots=True)
class TranscriptSegment:
    text: str
    start: float
    duration: float


@dataclass(slots=True)
class YouTubeTranscript:
    video_id: str
    url: str
    title: str | None
    segments: list[TranscriptSegment]

    @property
    def full_text(self) -> str:
        return "\n".join(s.text for s in self.segments if s.text.strip())


def extract_video_id(url: str) -> str:
    """Validate and extract a YouTube video ID (FR-028)."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        raise YouTubeError(f"Not a YouTube URL: {url}")

    if host == "youtu.be":
        vid = parsed.path.lstrip("/")
    elif parsed.path == "/watch":
        vid = (parse_qs(parsed.query).get("v") or [""])[0]
    elif parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
        vid = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
    else:
        vid = ""

    if not _YOUTUBE_ID_RE.match(vid):
        raise YouTubeError(f"Could not extract video id from URL: {url}")
    return vid


def _fetch_title(url: str) -> str | None:
    try:
        import yt_dlp

        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("title") if info else None
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"yt-dlp title fetch failed for {url}: {exc}")
        return None


def fetch_transcript(url: str) -> YouTubeTranscript:
    """Fetch transcript segments for a public YouTube video."""
    video_id = extract_video_id(url)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            NoTranscriptFound,
            TranscriptsDisabled,
            VideoUnavailable,
        )
    except ImportError as exc:  # pragma: no cover
        raise YouTubeError(f"youtube-transcript-api not installed: {exc}") from exc

    try:
        raw = YouTubeTranscriptApi.get_transcript(video_id)
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        raise YouTubeError(f"No transcript available for video {video_id}") from exc
    except VideoUnavailable as exc:
        raise YouTubeError(f"Video unavailable: {video_id}") from exc
    except Exception as exc:  # noqa: BLE001
        raise YouTubeError(f"Failed to fetch transcript: {exc}") from exc

    segments = [
        TranscriptSegment(
            text=item.get("text", "").strip(),
            start=float(item.get("start", 0.0)),
            duration=float(item.get("duration", 0.0)),
        )
        for item in raw
        if item.get("text")
    ]

    return YouTubeTranscript(
        video_id=video_id,
        url=url,
        title=_fetch_title(url),
        segments=segments,
    )
