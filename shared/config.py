"""
Fahamika — Shared Configuration
Loads environment variables and provides a single config object for all pipelines.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from shared/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Central configuration — loaded from environment variables."""

    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    IS_DEV: bool = APP_ENV == "development"

    # Server
    VOICE_WEBHOOK_PORT: int = int(os.getenv("VOICE_WEBHOOK_PORT", "8000"))
    VOICE_WEBHOOK_HOST: str = os.getenv("VOICE_WEBHOOK_HOST", "0.0.0.0")

    # LLM — DeepSeek (primary, cloud) or Ollama (fallback, local)
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    # Which LLM provider to use — "deepseek" or "ollama"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")

    # Whisper (Speech-to-Text)
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")

    # Pinecone (Vector DB)
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "fahamika-content")

    # Embedding model (local HuggingFace model — no API key needed)
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

    # Africa's Talking
    AT_VOICE_API_KEY: str = os.getenv("AT_VOICE_API_KEY", "")

    # TTS
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "piper")
    SAUTI_API_URL: str = os.getenv("SAUTI_API_URL", "https://msingi-ai--sauti-inference-inferenceapi-asgi-app.modal.run/v1/synthesize")
    SAUTI_SPEAKER: int = int(os.getenv("SAUTI_SPEAKER", "1"))

    # Paths
    PROJECT_ROOT: Path = PROJECT_ROOT
    VOICE_DIR: Path = PROJECT_ROOT / "voice"
    AUDIO_DIR: Path = VOICE_DIR / "audio"

    @classmethod
    def display(cls) -> str:
        """Return a safe (no secrets) summary of the config."""
        lines = [
            f"APP_ENV: {cls.APP_ENV}",
            f"LLM_PROVIDER: {cls.LLM_PROVIDER}",
            f"WHISPER_MODEL_SIZE: {cls.WHISPER_MODEL_SIZE}",
            f"PINECONE_INDEX_NAME: {cls.PINECONE_INDEX_NAME}",
            f"TTS_PROVIDER: {cls.TTS_PROVIDER}",
            f"DEEPSEEK_MODEL: {cls.DEEPSEEK_MODEL}",
            f"VOICE_WEBHOOK_PORT: {cls.VOICE_WEBHOOK_PORT}",
        ]
        return "\n".join(lines)


# Singleton
config = Config()
