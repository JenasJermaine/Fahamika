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

# ── FastAPI App ───────────────────────────────────────────────────
app = FastAPI(
    title="Fahamika Voice Pipeline",
    description="AI-powered civic information voice line for persons with disabilities in Kenya.",
    version="0.1.0",
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
    AT calls this when a user dials the Fahamika number.
    We respond with XML that answers, plays a welcome message,
    and records the caller's question.
    """
    form_data = dict(await request.form())
    caller = ATCallerInfo.model_validate(form_data)

    logger.info(f"📞 Incoming call from {caller.caller_number} (session: {caller.session_id})")

    # Build the URL where AT should send the recording
    base_url = str(request.base_url).rstrip("/")
    recording_callback = f"{base_url}/voice/recording"

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
async def process_question(
    sessionId: str = Form(default="unknown"),
    recordingUrl: str = Form(default=""),
):
    """
    Internal endpoint: processes a recorded question through the AI pipeline.
    AT redirects here after /voice/recording.

    This is where the real AI work happens:
      STT → Pinecone → DeepSeek → TTS → Speak result

    IMPORTANT: This must complete within AT's callback timeout (~30s).
    If it takes longer, we need to switch to an async polling pattern.
    """
    logger.info(f"⚙️ Processing question for session {sessionId}")

    try:
        result: PipelineResult = run(PipelineInput(
            audio_url=recordingUrl,
            session_id=sessionId,
        ))
    except Exception as e:
        logger.exception(f"Pipeline failed for session {sessionId}")
        xml = at_xml.say_and_hangup(
            "Samahani, kuna tatizo la kiufundi. Tafadhali jaribu tena baadaye."
        )
        return PlainTextResponse(xml, media_type="application/xml")

    logger.info(f"✅ Pipeline result for {sessionId}: {result.simplified_response[:100]}...")
    logger.info(f"   Duration: {result.duration_ms}ms")

    # Loop: speak answer, then offer another question
    base_url = str(request.base_url).rstrip("/")
    recording_callback = f"{base_url}/voice/recording"
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
