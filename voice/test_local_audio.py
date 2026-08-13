"""
Fahamika — Local Audio End-to-End Test
Runs the full pipeline on a local .wav file:
  STT (Whisper) -> Pinecone -> DeepSeek -> TTS (Piper)

Usage:
  python voice/test_local_audio.py

Requires:
  1. A .wav file at voice/audio/kenyan_voter_question.wav
  2. Piper model at voice/models/en_US-lessac-medium.onnx
  3. .env configured with DeepSeek + Pinecone keys
"""

import sys
from pathlib import Path

# Ensure project root is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voice.pipeline import run
from voice.schemas import PipelineInput


def main():
    audio_path = Path("voice/audio/kenyan_voter_question.wav")

    if not audio_path.exists():
        print(f"❌ Audio file not found: {audio_path}")
        print("   Place your .wav file at voice/audio/kenyan_voter_question.wav")
        sys.exit(1)

    print("=" * 60)
    print("Fahamika — Local Audio End-to-End Test")
    print("=" * 60)
    print(f"Audio file: {audio_path}")
    print()

    result = run(PipelineInput(
        audio_path=str(audio_path),
        session_id="local-test",
    ))

    print("-" * 60)
    print(f"Transcribed text : {result.transcribed_text}")
    print(f"Matched topic     : {result.matched_topic or '(no match)'}")
    print(f"Response          : {result.simplified_response}")
    print(f"TTS audio file    : {result.tts_audio_path or '(none)'}")
    print(f"Duration          : {result.duration_ms}ms")
    if result.error:
        print(f"Error             : {result.error}")
    print("-" * 60)


if __name__ == "__main__":
    main()
