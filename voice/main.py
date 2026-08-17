"""
Fahamika Voice Pipeline — FastAPI Webhook Server
Receives callbacks from Africa's Talking Voice API and processes calls.

Endpoints:
  GET  /voice/health       — Health check
  POST /voice/incoming     — AT sends this when a call comes in
  POST /voice/recording    — AT sends this when recording completes
  POST /voice/process      — Internal: process a recorded question
  POST /voice/test         — Test endpoint (bypasses AT, accepts text directly)

Usage:
  uvicorn voice.main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse, FileResponse
from shared.config import config
from voice.schemas import PipelineInput, PipelineResult, HealthResponse, ATCallerInfo, ATRecordingInfo
from voice import at_xml
from voice.pipeline import run

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("voice.server")


# ── Startup: preload models once so the first call is fast ─────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload Whisper and the embedding model at server startup."""
    try:
        from voice.stt import _load_whisper
        _load_whisper()
        logger.info("Whisper model preloaded.")
    except Exception as e:
        logger.warning(f"Whisper preload failed (will lazy-load on first call): {e}")

    try:
        from voice.retriever import _get_embedding_model
        _get_embedding_model()
        logger.info("Embedding model preloaded.")
    except Exception as e:
        logger.warning(f"Embedding model preload failed (will lazy-load on first call): {e}")

    yield


# ── FastAPI App ───────────────────────────────────────────────────
app = FastAPI(
    title="Fahamika Voice Pipeline",
    description="AI-powered civic information voice line for persons with disabilities in Kenya.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── In-memory session store (replace with Redis/DB in production) ─
# Maps session_id → transcribed_text
_session_transcripts: dict[str, str] = {}


# ═══════════════════════════════════════════════════════════════════
#  Africa's Talking Webhook Endpoints
# ═══════════════════════════════════════════════════════════════════

@app.get("/voice/health")
async def health():
    """Health check endpoint."""
    return HealthResponse(
        llm_provider=config.LLM_PROVIDER,
        whisper_model=config.WHISPER_MODEL_SIZE,
        pinecone_ready=bool(config.PINECONE_API_KEY),
    )


@app.post("/voice/incoming")
async def handle_incoming_call(request: Request):
    """
    AT's dashboard callback URL. Receives TWO kinds of notifications:
      - isActive=1, no recordingUrl → fresh call → answer + record
      - isActive=0 → end-of-call notification (billing) → log only, no response

    The MID-CALL recording callback goes to /voice/recording (the callbackUrl
    inside our <Record> tag), NOT here.
    """
    form_data = dict(await request.form())
    is_active = form_data.get("isActive", "1")
    session_id = form_data.get("sessionId", "unknown")

    # ── End-of-call notification ─────────────────────────────
    if is_active == "0":
        logger.info(
            f"[END OF CALL] session {session_id} "
            f"duration={form_data.get('durationInSeconds')}s "
            f"amount={form_data.get('amount')} {form_data.get('currencyCode')}"
        )
        # AT expects no response for end-of-call notifications
        return PlainTextResponse("", media_type="text/plain")

    # ── Fresh incoming call ──────────────────────────────────
    caller_number = form_data.get("callerNumber", "unknown")
    logger.info(f"📞 Incoming call from {caller_number} (session: {session_id})")

    # The callbackUrl AT will POST to when recording finishes MID-CALL
    base_url = str(request.base_url).rstrip("/")
    recording_callback = f"{base_url}/voice/recording"

    # Welcome + prompt + record (Say NESTED inside Record per AT docs)
    welcome = (
        "Karibu Fahamika. Welcome to Fahamika. "
        "Please ask your question about civic services, rights, or government information "
        "after the beep. Press hash when done."
    )

    xml = at_xml.answer_say_and_record(
        prompt=welcome,
        recording_url_callback=recording_callback,
        max_length=30,
        finish_on_key="#",
    )

    logger.info(f"→ Sent Record command to AT for session {session_id}")
    return PlainTextResponse(xml, media_type="application/xml")


@app.get("/voice/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated TTS WAV files so AT's <Play> can stream them."""
    audio_path = config.AUDIO_DIR / filename
    if not audio_path.exists():
        raise HTTPException(404, "Audio file not found")
    return FileResponse(audio_path, media_type="audio/wav")


@app.post("/voice/recording")
async def handle_recording(request: Request):
    """
    AT POSTs here when recording finishes MID-CALL (the callbackUrl inside
    our <Record> tag). The call is still active (isActive=1), so we run the
    pipeline and respond with the answer + another recording (loop).
    """
    form_data = dict(await request.form())
    session_id = form_data.get("sessionId", "unknown")
    recording_url = form_data.get("recordingUrl", "")
    is_active = form_data.get("isActive", "1")

    # End-of-call duplicate — AT sends isActive=0 AFTER we've already
    # answered mid-call. Ignore it to avoid running the pipeline twice.
    if is_active == "0":
        logger.info(f"[END OF CALL] session {session_id} — ignoring (already answered mid-call)")
        return PlainTextResponse("", media_type="text/plain")

    logger.info(f"🎙️ Mid-call recording received (session {session_id}, isActive={is_active})")
    logger.info(f"   Recording URL: {recording_url}")

    if not recording_url:
        logger.error(f"No recording URL for session {session_id}")
        xml = at_xml.say_and_hangup("Samahani, hatukuweza kupokea sauti yako. Tafadhali jaribu tena.")
        return PlainTextResponse(xml, media_type="application/xml")

    # Run the pipeline INLINE (models preloaded at startup)
    try:
        result: PipelineResult = run(PipelineInput(
            audio_url=recording_url,
            session_id=session_id,
        ))
    except Exception as e:
        logger.exception(f"Pipeline failed for session {session_id}")
        xml = at_xml.say_and_hangup(
            "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena baadaye."
        )
        return PlainTextResponse(xml, media_type="application/xml")

    logger.info(f"✅ Pipeline result for {session_id}: {result.simplified_response[:100]}...")
    logger.info(f"   Duration: {result.duration_ms}ms")

    # Loop: speak the answer, then record the next question
    base_url = str(request.base_url).rstrip("/")
    recording_callback = f"{base_url}/voice/recording"

    # Loop: play OUR Sauti TTS audio, then record the next question
    if result.tts_audio_path:
        filename = Path(result.tts_audio_path).name
        audio_url = f"{base_url}/voice/audio/{filename}"
        xml = at_xml.play_and_record_again(
            audio_url=audio_url,
            recording_url_callback=recording_callback,
        )
    else:
        # Fallback: AT's <Say> voice
        xml = at_xml.say_and_record_again(
            answer=result.simplified_response,
            recording_url_callback=recording_callback,
        )
    return PlainTextResponse(xml, media_type="application/xml")


@app.post("/voice/process")
async def process_question(request: Request):
    """
    Internal endpoint: processes a recorded question through the AI pipeline.
    AT redirects here after /voice/incoming detects a recording callback.

    Accepts parameters from EITHER query string (redirect) or form body
    (in case AT forwards form data), so both are supported.
    """
    form = {}
    if "application/x-www-form-urlencoded" in request.headers.get("content-type", ""):
        form = dict(await request.form())
    query = dict(request.query_params)

    session_id = form.get("sessionId") or query.get("sessionId") or "unknown"
    recording_url = form.get("recordingUrl") or query.get("recordingUrl") or ""

    logger.info(f"⚙️ Processing question for session {session_id}")

    if not recording_url:
        xml = at_xml.say_and_hangup("Samahani, hatukuweza kupokea sauti yako.")
        return PlainTextResponse(xml, media_type="application/xml")

    try:
        result: PipelineResult = run(PipelineInput(
            audio_url=recording_url,
            session_id=session_id,
        ))
    except Exception as e:
        logger.exception(f"Pipeline failed for session {session_id}")
        xml = at_xml.say_and_hangup(
            "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena baadaye."
        )
        return PlainTextResponse(xml, media_type="application/xml")

    logger.info(f"✅ Pipeline result for {session_id}: {result.simplified_response[:100]}...")
    logger.info(f"   Duration: {result.duration_ms}ms")

    # Loop: speak answer, then offer another question
    base_url = str(request.base_url).rstrip("/")
    recording_callback = f"{base_url}/voice/incoming"
    xml = at_xml.say_and_record_again(
        answer=result.simplified_response,
        recording_url_callback=recording_callback,
    )
    return PlainTextResponse(xml, media_type="application/xml")


# ═══════════════════════════════════════════════════════════════════
#  Testing / Mock Endpoints (no Africa's Talking required)
# ═══════════════════════════════════════════════════════════════════

@app.post("/voice/test")
async def test_pipeline(
    text: str = Form(default=""),
    audio_url: str = Form(default=""),
):
    """
    Test endpoint — run the pipeline directly without AT callbacks.
    Pass either `text` (skips STT) or `audio_url`.

    Example:
      curl -X POST http://localhost:8000/voice/test -d "text=What are my voting rights?"
    """
    if not text and not audio_url:
        raise HTTPException(400, "Provide either 'text' or 'audio_url'")

    result = run(PipelineInput(
        transcribed_text=text or None,
        audio_url=audio_url or None,
        session_id="test-session",
    ))

    return JSONResponse(result.model_dump(mode="json"))
