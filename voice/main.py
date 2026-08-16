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
from urllib.parse import quote
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
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
    AT calls this endpoint for ALL call events (fresh calls AND recording
    completions, since AT ignores our <Record callbackUrl>). We branch:
      - If the request has a recordingUrl → it's a recording callback → run pipeline
      - If not → fresh call → welcome + record
    """
    form_data = dict(await request.form())

    # DEBUG: log everything AT sends so we can confirm the fields
    logger.info(f"[DEBUG] Incoming form fields: {list(form_data.keys())}")

    # ── Branch 1: Recording callback ──────────────────────────
    recording_url = form_data.get("recordingUrl", "")
    if recording_url:
        session_id = form_data.get("sessionId", "unknown")
        logger.info(f"🎙️ Recording callback detected (session {session_id})")

        # Respond IMMEDIATELY with "please wait" + redirect to /voice/process.
        # The redirect gives the slow AI pipeline a fresh timeout window
        # (AT's callback timeout is ~30s; running inline would blow it).
        base_url = str(request.base_url).rstrip("/")
        process_url = (
            f"{base_url}/voice/process"
            f"?sessionId={session_id}&recordingUrl={quote(recording_url, safe='')}"
        )
        xml = at_xml.say_and_redirect(
            text="Asante. Please wait while we find your answer.",
            redirect_url=process_url,
        )
        return PlainTextResponse(xml, media_type="application/xml")

    # ── Branch 2: Fresh incoming call ─────────────────────────
    caller = ATCallerInfo.model_validate(form_data)

    logger.info(f"📞 Incoming call from {caller.caller_number} (session: {caller.session_id})")

    # Build the URL where AT should send the recording
    base_url = str(request.base_url).rstrip("/")
    recording_callback = f"{base_url}/voice/incoming"

    # Welcome + prompt + record
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

    logger.info(f"→ Sent Record command to AT for session {caller.session_id}")
    return PlainTextResponse(xml, media_type="application/xml")


@app.post("/voice/recording")
async def handle_recording(request: Request):
    """
    AT calls this after recording completes.
    We download the recording, transcribe it, then redirect
    to the process endpoint for the AI pipeline.
    """
    form_data = dict(await request.form())
    rec = ATRecordingInfo.model_validate(form_data)

    logger.info(f"🎙️ Recording received for session {rec.session_id}")
    logger.info(f"   Recording URL: {rec.recording_url}")

    if not rec.recording_url:
        logger.error(f"No recording URL for session {rec.session_id}")
        xml = at_xml.say_and_hangup("Samahani, hatukuweza kupokea sauti yako. Tafadhali jaribu tena.")
        return PlainTextResponse(xml, media_type="application/xml")

    # Store the recording URL in session — will transcribe in /process
    base_url = str(request.base_url).rstrip("/")
    process_url = f"{base_url}/voice/process?sessionId={rec.session_id}&recordingUrl={rec.recording_url}"

    # Tell AT to redirect to our processing endpoint
    xml = at_xml.say_and_redirect(
        text="Asante. Please wait while we find your answer.",
        redirect_url=process_url,
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
