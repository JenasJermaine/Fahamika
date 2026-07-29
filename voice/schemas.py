"""
Fahamika Voice Pipeline — Pydantic Schemas
Request/response models for the webhook server.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------- Africa's Talking Voice Callback ----------

class ATCallerInfo(BaseModel):
    """Caller details from AT's inbound webhook."""
    model_config = ConfigDict(populate_by_name=True)

    caller_number: str = Field(alias="callerNumber")
    session_id: str = Field(alias="sessionId")
    is_active: str = Field(alias="isActive", default="1")
    direction: str = Field(default="Inbound")
    dtmf_digits: Optional[str] = Field(alias="dtmfDigits", default=None)


class ATRecordingInfo(BaseModel):
    """Recording URL returned by AT after recording completes."""
    model_config = ConfigDict(populate_by_name=True)

    recording_url: Optional[str] = Field(alias="recordingUrl", default=None)
    recording_id: Optional[str] = Field(alias="recordingId", default=None)
    duration_in_seconds: Optional[int] = Field(alias="durationInSeconds", default=0)
    session_id: str = Field(alias="sessionId")


# ---------- Pipeline Internal Models ----------

class PipelineInput(BaseModel):
    """Input to the core AI pipeline."""
    audio_url: Optional[str] = None           # URL to fetch the recording
    audio_path: Optional[str] = None          # Local path (for testing)
    transcribed_text: Optional[str] = None    # Skip STT if already transcribed
    session_id: str = "test-session"


class PipelineResult(BaseModel):
    """Result from the core AI pipeline."""
    session_id: str
    transcribed_text: str
    matched_topic: Optional[str] = None
    matched_content: Optional[str] = None
    simplified_response: str
    tts_audio_path: Optional[str] = None
    duration_ms: int
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "0.1.0"
    llm_provider: str
    whisper_model: str
    pinecone_ready: bool
