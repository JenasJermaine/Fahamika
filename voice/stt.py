"""
Fahamika Voice Pipeline — Speech-to-Text (Whisper)
"""

import os
import logging
import time
from pathlib import Path
import requests
from shared.config import config

logger = logging.getLogger(__name__)

# Lazy-loaded whisper model
_whisper_model = None


def _load_whisper():
    """Lazy-load the Whisper model (cached after first call)."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    import whisper
    model_size = config.WHISPER_MODEL_SIZE
    logger.info(f"Loading Whisper model: {model_size} ...")
    _whisper_model = whisper.load_model(model_size)
    logger.info(f"Whisper model '{model_size}' loaded.")
    return _whisper_model


def transcribe_file(audio_path: str) -> str:
    """
    Transcribe a local audio file using Whisper.
    Returns the transcribed text.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _load_whisper()
    result = model.transcribe(audio_path)
    text = result["text"].strip()
    logger.info(f"Transcribed ({len(text)} chars): {text[:100]}...")
    return text


def download_and_transcribe(audio_url: str, session_id: str) -> str:
    """
    Download an audio file from a URL (e.g., Africa's Talking recording URL),
    save locally, then transcribe.
    """
    config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    local_path = config.AUDIO_DIR / f"{session_id}.wav"

    logger.info(f"Downloading recording from {audio_url} ...")

    # AT may fire the recording callback before the audio file is fully
    # uploaded/available (especially with silence-timeout recordings).
    # Retry a few times with short delays before giving up.
    resp = None
    for attempt in range(3):
        resp = requests.get(audio_url, timeout=30)
        if resp.status_code == 200:
            break
        logger.warning(
            f"Download attempt {attempt + 1}/3 returned {resp.status_code}; "
            f"retrying in 3s ..."
        )
        time.sleep(3)
    else:
        resp.raise_for_status()  # exhausted retries → raise HTTP error

    local_path.write_bytes(resp.content)
    logger.info(f"Saved recording to {local_path}")

    return transcribe_file(str(local_path))
