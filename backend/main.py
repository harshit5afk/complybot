"""
main.py
FastAPI backend for ComplyBot.
Exposes endpoints for chat, multi-agent pipeline routing, user authentication (JWT),
and persistent conversations and messages via SQLite and SQLAlchemy.
"""

import os
import sys
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

import agents
from database import init_db, get_db, User, Conversation, Message
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(title="ComplyBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = ""
    preferred_lang: Optional[str] = "en"


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    email: str
    display_name: str
    preferred_lang: str
    role: str


class UserProfileResponse(BaseModel):
    id: int
    email: str
    display_name: str
    preferred_lang: str
    role: str


class UserSettingsUpdate(BaseModel):
    display_name: Optional[str] = None
    preferred_lang: Optional[str] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"
    session_id: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    agent: Optional[str] = None
    domain: Optional[str] = None
    language: Optional[str] = "en"
    citations: List[str] = []
    confidence: Optional[float] = None
    created_at: str


class ConversationOut(BaseModel):
    id: int
    title: str
    session_id: Optional[str] = None
    created_at: str
    updated_at: str
    messages: List[MessageOut] = []


class ChatRequest(BaseModel):
    query: str
    language: Optional[str] = None  # "en" or "hi"; None = auto-detect
    conversation_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    agent: str
    domain: str
    language: str
    answer: str
    citations: List[str]
    confidence: float
    conversation_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------
@app.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    hashed = hash_password(req.password)
    user = User(
        email=req.email.lower(),
        password_hash=hashed,
        display_name=req.display_name or req.email.split("@")[0],
        preferred_lang=req.preferred_lang or "en",
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return AuthResponse(
        token=token,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        preferred_lang=user.preferred_lang,
        role=user.role,
    )


@app.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    return AuthResponse(
        token=token,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        preferred_lang=user.preferred_lang,
        role=user.role,
    )


@app.get("/me", response_model=UserProfileResponse)
def get_me(user: User = Depends(get_current_user)):
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        preferred_lang=user.preferred_lang,
        role=user.role,
    )


@app.put("/me", response_model=UserProfileResponse)
def update_me(
    settings: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if settings.display_name is not None:
        user.display_name = settings.display_name
    if settings.preferred_lang is not None:
        user.preferred_lang = settings.preferred_lang
    db.commit()
    db.refresh(user)
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        preferred_lang=user.preferred_lang,
        role=user.role,
    )


# ---------------------------------------------------------------------------
# Conversation & History Endpoints
# ---------------------------------------------------------------------------
@app.get("/conversations")
def list_conversations(
    session_id: Optional[str] = None,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Lists conversations for an authenticated user or matching a guest session_id."""
    query = db.query(Conversation)
    if user:
        query = query.filter(Conversation.user_id == user.id)
    elif session_id:
        query = query.filter(Conversation.session_id == session_id)
    else:
        return []

    conversations = query.order_by(Conversation.updated_at.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "session_id": c.session_id,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
            "message_count": len(c.messages),
        }
        for c in conversations
    ]


@app.post("/conversations")
def create_conversation(
    req: ConversationCreate,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    conv = Conversation(
        title=req.title or "New Chat",
        user_id=user.id if user else None,
        session_id=req.session_id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {
        "id": conv.id,
        "title": conv.title,
        "session_id": conv.session_id,
        "created_at": conv.created_at.isoformat(),
    }


@app.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if user and conv.user_id and conv.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this conversation.")

    return {
        "id": conv.id,
        "title": conv.title,
        "session_id": conv.session_id,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "agent": m.agent,
                "domain": m.domain,
                "language": m.language,
                "citations": m.citations or [],
                "confidence": m.confidence,
                "created_at": m.created_at.isoformat(),
            }
            for m in conv.messages
        ],
    }


@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    if user and conv.user_id and conv.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this conversation.")

    db.delete(conv)
    db.commit()
    return {"status": "deleted", "id": conversation_id}


# ---------------------------------------------------------------------------
# Chat Endpoint with Conversation Memory & Confidence
# ---------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        conv = None
        history_for_llm = []

        # Find or create persistent conversation
        if request.conversation_id:
            conv = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()

        if not conv:
            title = request.query[:42] + ("…" if len(request.query) > 42 else "")
            conv = Conversation(
                title=title,
                user_id=user.id if user else None,
                session_id=request.session_id,
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # Retrieve last 6 messages as context for conversation memory
        past_msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(6)
            .all()
        )
        for pm in reversed(past_msgs):
            history_for_llm.append({"role": pm.role, "content": pm.content})

        # Save user message to database
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=request.query,
            language=request.language or "en",
        )
        db.add(user_msg)
        db.commit()

        # Run through the multi-agent pipeline with conversation memory
        result = agents.handle_query(
            request.query,
            language=request.language,
            conversation_history=history_for_llm,
        )

        agent_name = str(result.get("agent", "ComplyBot"))
        domain = str(result.get("domain", "general"))
        lang = str(result.get("language", request.language or "en"))
        answer_text = str(result.get("answer", "No response generated."))
        citations = list(result.get("citations", []))
        confidence = float(result.get("confidence", 0.85))

        # Save assistant message to database
        bot_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer_text,
            agent=agent_name,
            domain=domain,
            language=lang,
            citations=citations,
            confidence=confidence,
        )
        db.add(bot_msg)
        conv.title = conv.title or request.query[:42]
        db.commit()

        return ChatResponse(
            agent=agent_name,
            domain=domain,
            language=lang,
            answer=answer_text,
            citations=citations,
            confidence=confidence,
            conversation_id=conv.id,
        )

    except Exception as e:
        return ChatResponse(
            agent="System",
            domain="error",
            language=request.language or "en",
            answer=f"Server error: {str(e)}",
            citations=[],
            confidence=0.0,
            conversation_id=request.conversation_id,
        )


# ---------------------------------------------------------------------------
# Static frontend serving
# ---------------------------------------------------------------------------
@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Serve any other static assets (css/js) if added later
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
