# Fahamika

**AI-powered civic information system for persons with disabilities in Kenya.**

- 📞 **Voice line** — Blind and low-vision users call in and ask questions in English or Kiswahili
- 💬 **SMS line** — Deaf users text in and receive simplified civic information

Built during the Mozilla × JKamilimu Buildathon (Top 7 of 42 teams). Now in the funded build-out phase.

---

## Architecture

```
Caller/SMS → Africa's Talking → Webhook → FastAPI (DigitalOcean VPS)
               ↓                                      ↓
          Voice API                           Whisper (STT)
          SMS API                             Pinecone (vector search)
                                              DeepSeek / Ollama (simplification)
                                              TTS (text-to-speech)
```

**Design principle:** The AI never generates civic facts — it only simplifies and translates pre-approved content stored in Pinecone.

---

## Project Structure

```
fahamika/
├── voice/              # Voice pipeline (Jenas)
│   ├── main.py         # FastAPI webhook server
│   ├── pipeline.py     # Core orchestrator (STT → retrieve → simplify → TTS)
│   ├── stt.py          # Whisper speech-to-text
│   ├── llm.py          # DeepSeek / Ollama LLM wrapper
│   ├── retriever.py    # Pinecone vector search
│   ├── tts.py          # Text-to-speech
│   ├── at_xml.py       # Africa's Talking VoiceXML builder
│   ├── schemas.py      # Pydantic models
│   └── test_mock.py    # Local tests (no AT/VPS needed)
├── sms/                # SMS pipeline (Christine)
├── shared/             # Shared config, schemas
├── docs/               # Architecture docs, handoff notes
└── requirements.txt    # (symlink to voice/requirements.txt)
```

---

## Quick Start

### 1. Clone and set up environment

```bash
git clone https://github.com/JenasJermaine/Fahamika.git
cd Fahamika

# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r voice/requirements.txt
```

### 2. Configure environment

```bash
cp voice/.env.example .env
# Edit .env with your API keys (DeepSeek, Pinecone, etc.)
```

### 3. Run the voice webhook server

```bash
uvicorn voice.main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000/docs for the interactive API documentation.

### 4. Test the pipeline locally

```bash
# Run mock tests (no AT/VPS required)
pytest voice/test_mock.py -v

# Or test a single question manually:
curl -X POST http://localhost:8000/voice/test \
  -d "text=What are my voting rights in Kenya?"
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/voice/health` | Health check |
| POST | `/voice/incoming` | AT callback: new incoming call |
| POST | `/voice/recording` | AT callback: recording completed |
| POST | `/voice/process` | Internal: run AI pipeline on recording |
| POST | `/voice/test` | Test: run pipeline with text (no AT) |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web framework | FastAPI (Python) |
| Speech-to-text | OpenAI Whisper |
| Vector database | Pinecone |
| LLM (cloud) | DeepSeek API |
| LLM (local) | Ollama (for VPS deployment) |
| Text-to-speech | Piper (prototype), Google Cloud TTS (candidate) |
| Call/SMS gateway | Africa's Talking |

---

## License

MIT — see [LICENSE](LICENSE)

---

## Team

- **Jenas Jermaine** — Voice pipeline (call handling, STT, TTS)
- **Christine Mugo** — SMS pipeline (inbound/outbound, AI simplification)
