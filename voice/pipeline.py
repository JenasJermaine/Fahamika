"""
Fahamika Voice Pipeline — Core Orchestrator
Wires together: STT → Pinecone retrieval → LLM simplification → TTS

This is the heart of the voice pipeline. It takes an audio recording
(or transcribed text for testing) and returns a spoken response.
"""

import logging
import time
from pathlib import Path
from shared.config import config
from voice.schemas import PipelineInput, PipelineResult
from voice.stt import transcribe_file, download_and_transcribe
from voice.retriever import search, build_retrieval_context
from voice.llm import simplify
from voice.tts import synthesize

logger = logging.getLogger(__name__)


def run(input_data: PipelineInput) -> PipelineResult:
    """
    Run the full Fahamika voice pipeline:

    1. Transcribe (audio → text)
    2. Retrieve (text → matched civic content via Pinecone)
    3. Simplify (content → spoken response via DeepSeek/Ollama)
    4. Synthesize (spoken response → audio via TTS)

    Args:
        input_data: PipelineInput with either audio_url, audio_path, or transcribed_text.

    Returns:
        PipelineResult with the simplified response, matched topic, and optional audio.
    """
    start = time.time()
    session_id = input_data.session_id

    # ── Step 1: Transcribe ────────────────────────────────────
    if input_data.transcribed_text:
        transcribed = input_data.transcribed_text
        logger.info(f"[{session_id}] Using pre-supplied transcript: {transcribed[:80]}...")
    elif input_data.audio_url:
        logger.info(f"[{session_id}] Downloading + transcribing from URL ...")
        transcribed = download_and_transcribe(input_data.audio_url, session_id)
    elif input_data.audio_path:
        logger.info(f"[{session_id}] Transcribing local file: {input_data.audio_path}")
        transcribed = transcribe_file(input_data.audio_path)
    else:
        ms = int((time.time() - start) * 1000)
        return PipelineResult(
            session_id=session_id,
            transcribed_text="",
            simplified_response="Samahani, hakuna sauti iliyopokelewa.",
            duration_ms=ms,
            error="No audio or text provided",
        )

    if not transcribed or len(transcribed) < 2:
        ms = int((time.time() - start) * 1000)
        return PipelineResult(
            session_id=session_id,
            transcribed_text=transcribed,
            simplified_response="Samahani, sikuelewa. Tafadhali jaribu tena.",
            duration_ms=ms,
            error="Transcription was empty or too short",
        )

    # ── Step 2: Retrieve from Pinecone ─────────────────────────
    context = None
    matched_topic = None

    if config.PINECONE_API_KEY:
        try:
            matches = search(transcribed, top_k=3)
            context = build_retrieval_context(matches, min_score=0.5)
            if matches and matches[0]["score"] >= 0.5:
                matched_topic = matches[0]["topic"]
        except Exception as e:
            logger.warning(f"[{session_id}] Pinecone search failed: {e}")
            context = None
    else:
        logger.warning(f"[{session_id}] No Pinecone API key — skipping retrieval.")

    # ── Step 3: Simplify with LLM ──────────────────────────────
    if context:
        # Normal path: simplify retrieved content
        response = simplify(transcribed, context)
    else:
        # Fallback: no Pinecone — LLM gives a graceful apology
        response = simplify(
            transcribed,
            "[No matching content found in the knowledge base.]",
        )

    # ── Step 4: Synthesize (TTS) ───────────────────────────────
    tts_path = None
    try:
        tts_path = synthesize(response, session_id=session_id)
    except Exception as e:
        logger.warning(f"[{session_id}] TTS synthesis failed: {e}")

    # ── Done ───────────────────────────────────────────────────
    ms = int((time.time() - start) * 1000)
    logger.info(f"[{session_id}] Pipeline complete in {ms}ms")

    return PipelineResult(
        session_id=session_id,
        transcribed_text=transcribed,
        matched_topic=matched_topic,
        matched_content=context,
        simplified_response=response,
        tts_audio_path=tts_path,
        duration_ms=ms,
    )
