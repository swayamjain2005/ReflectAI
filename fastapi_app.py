import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.therapy_engine_groq import TherapyEngine


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str


app = FastAPI(title="ReflectAI API", version="1.0.0")

# Allow CORS for local dev and simple deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.user_id:
        raise HTTPException(status_code=400, detail="user_id and message are required")

    try:
        engine = TherapyEngine(req.user_id)
        reply = engine.process(req.message)
        if not isinstance(reply, str) or not reply:
            raise ValueError("Empty response from engine")
        return ChatResponse(response=reply)
    except HTTPException:
        raise
    except Exception as exc:
        # Surface a generic error while logging specifics inside the engine
        raise HTTPException(status_code=500, detail=f"Failed to process message: {exc}")


if __name__ == "__main__":
    # Local dev runner: uvicorn fastapi_app:app --host 0.0.0.0 --port 8765
    import uvicorn
    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=port, reload=False)


