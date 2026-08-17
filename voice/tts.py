"""
Fahamika Voice Pipeline — Text-to-Speech
Supports multiple TTS providers (Piper, Google Cloud TTS, Intron Sahara).

Current status: Piper is the default (used in prototype).
Google Cloud TTS and Intron Sahara are candidates for evaluation (Week 2).
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from shared.config import config

logger = logging.getLogger(__name__)


def synthesize(text: str, output_path: str | None = None, session_id: str = "unknown") -> str:
    """
    Convert text to speech audio file.

    Args:
        text: The text to synthesize.
        output_path: Where to save the audio file (auto-generated if None).
        session_id: Call session ID — used to create unique filenames per call.

    Returns:
        Path to the generated audio file.
    """
    provider = config.TTS_PROVIDER

    if output_path is None:
        config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(config.AUDIO_DIR / f"{session_id}_response.wav")

    if provider == "piper":
        return _synthesize_piper(text, output_path)
    elif provider == "sauti":
        return _synthesize_sauti(text, output_path)
    elif provider == "google-cloud":
        return _synthesize_google_cloud(text, output_path)
    elif provider == "intron-sahara":
        return _synthesize_intron_sahara(text, output_path)
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")


def _synthesize_piper(text: str, output_path: str) -> str:
    """
    Use Piper TTS (local, offline).
    Piper must be installed: https://github.com/rhasspy/piper
    """
    # Piper is called as a subprocess:
    #   echo "text" | piper --model en_US-lessac-medium.onnx --output_file output.wav

    model_dir = config.VOICE_DIR / "models"
    # Default: use English voice. For Kiswahili, a custom voice is needed.
    model_path = model_dir / "en_US-lessac-medium.onnx"
    model_config = model_dir / "en_US-lessac-medium.onnx.json"

    if not model_path.exists():
        logger.warning(
            f"Piper model not found at {model_path}. "
            "Download from: https://huggingface.co/rhasspy/piper-voices"
        )
        # Fall back to a simple beep/warning for now
        return _synthesize_fallback(text, output_path)

    logger.info(f"Synthesizing {len(text)} chars with Piper ...")
    result = subprocess.run(
        [
            "piper",
            "--model", str(model_path),
            "--config", str(model_config),
            "--output_file", output_path,
        ],
        input=text,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        logger.error(f"Piper failed: {result.stderr}")
        return _synthesize_fallback(text, output_path)

    logger.info(f"TTS audio saved to {output_path}")
    return output_path


def _synthesize_google_cloud(text: str, output_path: str) -> str:
    """
    Use Google Cloud Text-to-Speech (confirmed Kiswahili support).
    Requires: pip install google-cloud-texttospeech
    """
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="sw-KE",  # Swahili (Kenya) — change to "en-US" for English
        name="sw-KE-Standard-A",
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    )

    logger.info(f"Synthesizing {len(text)} chars with Google Cloud TTS ...")
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    Path(output_path).write_bytes(response.audio_content)
    logger.info(f"TTS audio saved to {output_path}")
    return output_path


def _synthesize_intron_sahara(text: str, output_path: str) -> str:
    """
    Intron's Sahara v2 — Africa-built TTS.
    Placeholder: pricing and API not yet public.
    """
    logger.warning("Intron Sahara TTS not yet integrated — using fallback.")
    return _synthesize_fallback(text, output_path)


def _synthesize_sauti(text: str, output_path: str) -> str:
    """
    Use the Sauti Kiswahili TTS API (Msingi AI).
    Open endpoint, no auth required.
    """
    import requests

    api_url = config.SAUTI_API_URL
    speaker = config.SAUTI_SPEAKER

    logger.info(f"Synthesizing {len(text)} chars with Sauti (speaker {speaker}) ...")
    resp = requests.post(
        api_url,
        params={"format": "wav"},
        json={"text": text, "speaker": speaker},
        timeout=60,
    )
    resp.raise_for_status()

    Path(output_path).write_bytes(resp.content)
    logger.info(f"TTS audio saved to {output_path}")
    return output_path


def _synthesize_fallback(text: str, output_path: str) -> str:
    """
    Fallback: save the text as-is with a note that TTS is not available.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(f"[TTS NOT AVAILABLE]\n\n{text}")
    logger.warning(f"TTS fallback: wrote text to {output_path}")
    return output_path
