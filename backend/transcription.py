from faster_whisper import WhisperModel
import ctranslate2
import os
from dotenv import load_dotenv

load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
MODEL_CACHE = {}

def get_whisper_model():
    """Lazy-load Whisper model (avoids reload on each call)"""
    global MODEL_CACHE
    if "model" not in MODEL_CACHE:
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        MODEL_CACHE["model"] = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute_type)
    return MODEL_CACHE["model"]

def transcribe_video(file_path: str) -> str:
    """
    Transcribe video file using Faster-Whisper.
    Returns full transcript text.
    """
    model = get_whisper_model()

    segments, info = model.transcribe(file_path, beam_size=5)

    # Combine all segments into single transcript
    transcript = " ".join([segment.text for segment in segments])

    return transcript

def transcribe_with_timestamps(file_path: str) -> list[dict]:
    """
    Transcribe and return segments with timestamps.
    Each item: {"start": float, "end": float, "text": str}
    """
    model = get_whisper_model()

    segments, info = model.transcribe(file_path, beam_size=5)

    result = []
    for segment in segments:
        result.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })

    return result
