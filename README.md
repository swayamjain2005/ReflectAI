## ReflectAI - Local Run & Deployment

### Prerequisites
- Python 3.10+
- GROQ_API_KEY set in your environment (for LLM responses)

### Install
```bash
pip install -r requirements.txt
```

### Start the FastAPI backend (required by Solara UI)
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8765
```

Health check: `GET /healthz` should return `{ "status": "ok" }`.

### Start the Solara frontend
```bash
solara run solara_app.py --host 0.0.0.0 --port 7860
```

The Solara UI will POST to `http://localhost:8765/chat` by default (configurable via `FASTAPI_CHAT_URL`).

### Environment
- `GROQ_API_KEY`: API key for Groq SDK.

### Notes
- If you deploy separately, set `FASTAPI_CHAT_URL` in the environment where Solara runs.


