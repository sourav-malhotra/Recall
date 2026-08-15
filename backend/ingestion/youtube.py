"""
backend/ingestion/youtube.py

Extracts transcript + metadata from a YouTube URL.
No API key / OAuth required — uses youtube-transcript-api for captions
and yt-dlp for metadata (title, channel, duration).
"""

import re
import sys
from dataclasses import dataclass
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp

# Windows terminals default to cp1252, which can't print non-English text
# (e.g. Hindi transcripts). Force UTF-8 output so this doesn't crash.
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class YouTubeContent:
    video_id: str
    url: str
    title: str
    channel: str
    duration_seconds: int
    transcript: str  # full transcript as plain text


def extract_video_id(url: str) -> str:
    """
    Pulls the 11-character video ID out of any common YouTube URL format:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    """
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",   # watch?v= and most other forms
        r"youtu\.be\/([0-9A-Za-z_-]{11})",   # short links
        r"shorts\/([0-9A-Za-z_-]{11})",      # shorts
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract a video ID from URL: {url}")


def fetch_transcript(video_id: str) -> str:
    """
    Fetches the transcript for a video and returns it as clean English text.

    Design decision: the whole vector store is standardized on English, so
    retrieval quality doesn't depend on what language the question is asked
    in. This means:
      1. If an English transcript exists, use it directly.
      2. Otherwise, grab whatever transcript IS available and translate it
         to English.
      3. If translation isn't supported for that video, fall back to the
         original-language transcript rather than failing outright — some
         content to embed is better than none, even if not ideal.
    """
    ytt_api = YouTubeTranscriptApi()

    try:
        transcript_list = ytt_api.list(video_id)
    except TranscriptsDisabled:
        raise ValueError(f"Transcripts are disabled for video {video_id}")

    # 1. Prefer a native English transcript if one exists
    try:
        transcript = transcript_list.find_transcript(["en"])
        fetched = transcript.fetch()
        return " ".join(snippet.text for snippet in fetched.snippets)
    except NoTranscriptFound:
        pass

    # 2. No English available — grab whatever exists and translate it
    available = list(transcript_list)
    if not available:
        raise ValueError(f"No transcript found for video {video_id}")

    source_transcript = available[0]

    try:
        translated = source_transcript.translate("en")
        fetched = translated.fetch()
        return " ".join(snippet.text for snippet in fetched.snippets)
    except Exception:
        # 3. Translation unsupported for this video — return original language
        # rather than failing the whole ingestion.
        fetched = source_transcript.fetch()
        return " ".join(snippet.text for snippet in fetched.snippets)


def fetch_metadata(url: str) -> dict:
    """
    Uses yt-dlp to pull title/channel/duration without downloading the video.
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return {
        "title": info.get("title", "Unknown title"),
        "channel": info.get("uploader", "Unknown channel"),
        "duration_seconds": info.get("duration", 0),
    }


def process_youtube_url(url: str) -> YouTubeContent:
    """
    Main entry point — call this from the ingestion pipeline.
    Returns a fully populated YouTubeContent object ready for chunking.
    """
    video_id = extract_video_id(url)
    transcript = fetch_transcript(video_id)
    metadata = fetch_metadata(url)

    return YouTubeContent(
        video_id=video_id,
        url=url,
        title=metadata["title"],
        channel=metadata["channel"],
        duration_seconds=metadata["duration_seconds"],
        transcript=transcript,
    )


# --- Quick manual test ---
# Run directly: python youtube.py
if __name__ == "__main__":
    test_url = input("Paste a YouTube URL to test: ").strip()
    content = process_youtube_url(test_url)
    print(f"\nTitle: {content.title}")
    print(f"Channel: {content.channel}")
    print(f"Duration: {content.duration_seconds}s")
    print(f"Transcript length: {len(content.transcript)} characters")
    print(f"\nFirst 300 chars of transcript:\n{content.transcript[:300]}...")
