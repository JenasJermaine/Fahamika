"""
Fahamika Voice Pipeline — Local Mock Tests
Run these against a local server to test the pipeline without
Africa's Talking or a VPS.

Usage:
  pytest voice/test_mock.py -v

  Or run a single test manually:
  python voice/test_mock.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from voice.main import app

client = TestClient(app)


def test_health_check():
    """Health endpoint should return ok."""
    resp = client.get("/voice/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "llm_provider" in data


def test_incoming_call_returns_xml():
    """Incoming call should return VoiceXML with Record command."""
    resp = client.post("/voice/incoming", data={
        "sessionId": "test-123",
        "callerNumber": "+254712345678",
        "isActive": "1",
    })
    assert resp.status_code == 200
    assert "<Response>" in resp.text
    assert "<Record" in resp.text
    assert "finishOnKey" in resp.text


def test_recording_endpoint():
    """Recording callback should return XML (inline pipeline or graceful error)."""
    resp = client.post("/voice/recording", data={
        "sessionId": "test-456",
        "recordingUrl": "https://example.com/recording.wav",
    })
    assert resp.status_code == 200
    # With a fake recording URL, pipeline download fails → graceful error XML
    assert "<Response>" in resp.text


def test_test_endpoint_with_text():
    """Test endpoint should work with direct text (no STT/Pinecone needed)."""
    resp = client.post("/voice/test", data={
        "text": "What are my rights as a person with disability in Kenya?",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "simplified_response" in data
    assert len(data["simplified_response"]) > 10
    assert data["session_id"] == "test-session"


# ═══════════════════════════════════════════════════════════════════
#  Manual smoke test (run directly with: python voice/test_mock.py)
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Fahamika Voice Pipeline — Smoke Test")
    print("=" * 60)

    # 1. Health
    resp = client.get("/voice/health")
    print(f"\n[OK] Health: {resp.json()}")

    # 2. Incoming call XML
    resp = client.post("/voice/incoming", data={
        "sessionId": "smoke-1",
        "callerNumber": "+254700000000",
    })
    print(f"[OK] Incoming call XML: {len(resp.text)} chars")
    print(f"   Sample: {resp.text[:200]}...")

    # 3. Recording callback
    resp = client.post("/voice/recording", data={
        "sessionId": "smoke-1",
        "recordingUrl": "https://example.com/recording.wav",
    })
    print(f"[OK] Recording callback: {len(resp.text)} chars")

    # 4. Test pipeline with text (no STT/Pinecone needed — hits DeepSeek/Ollama)
    print("\n--- Testing pipeline with DeepSeek ---")
    resp = client.post("/voice/test", data={
        "text": "How do I register to vote in Kenya?",
    })
    result = resp.json()
    print(f"[OK] Pipeline response ({result['duration_ms']}ms):")
    print(f"   Transcribed: {result['transcribed_text'][:80]}")
    print(f"   Matched topic: {result['matched_topic'] or '(no Pinecone)'}")
    print(f"   Response: {result['simplified_response'][:300]}")
    if result.get("error"):
        print(f"   ⚠️ Error: {result['error']}")
