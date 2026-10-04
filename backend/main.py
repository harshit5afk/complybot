"""
main.py
FastAPI backend for ComplyBot. Exposes a single /chat endpoint that routes
the query through the multi-agent pipeline in agents.py, and serves the
static frontend.

Run with:
    uvicorn main:app --reload --port 8000

Then open http://localhost:8000 in your browser.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

import agents

app = FastAPI(title="ComplyBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


class ChatRequest(BaseModel):
    query: str
    language: str | None = None  # "en" or "hi"; None = auto-detect


class ChatResponse(BaseModel):
    agent: str
    domain: str
    language: str
    answer: str
    citations: list[str]


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = agents.handle_query(request.query, request.language)
        return ChatResponse(
            agent=str(result.get("agent", "ComplyBot")),
            domain=str(result.get("domain", "general")),
            language=str(result.get("language", request.language or "en")),
            answer=str(result.get("answer", "No response generated.")),
            citations=list(result.get("citations", [])),
        )
    except Exception as e:
        return ChatResponse(
            agent="System",
            domain="error",
            language=request.language or "en",
            answer=f"Server error: {str(e)}",
            citations=[],
        )


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Serve any other static assets (css/js) if you add them later
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
