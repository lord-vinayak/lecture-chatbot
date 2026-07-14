import re
import tempfile
from pathlib import Path
import yt_dlp

MAX_DURATION_SECONDS = 3 * 60 * 60

YOUTUBE_URL_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|embed/)|youtu\.be/)([\w-]{11})"
)


def extract_youtube_id(url: str) -> str | None:
    match = YOUTUBE_URL_RE.search(url)
    return match.group(1) if match else None


def download_audio(youtube_url: str) -> str:
    """
    Download just the audio track for a YouTube video into a temp file.
    Raises ValueError if the video exceeds MAX_DURATION_SECONDS.
    Returns the path to the downloaded audio file (caller must delete it).
    """
    tmp_dir = tempfile.mkdtemp(prefix="yt_audio_")
    out_template = str(Path(tmp_dir) / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # web client gets bot-checked on datacenter IPs (Hetzner etc.); android/ios skip that
        "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        duration = info.get("duration") or 0
        if duration > MAX_DURATION_SECONDS:
            raise ValueError(
                f"Video is {duration / 3600:.1f}h long, exceeds the 3h limit"
            )
        ydl.download([youtube_url])
        return ydl.prepare_filename(info)
