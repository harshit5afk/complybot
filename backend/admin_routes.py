"""
admin_routes.py
Admin Dashboard and Knowledge Base Management API for ComplyBot.
Provides endpoints for monitoring compliance queries, auditing knowledge gaps,
reviewing low-confidence questions, and uploading new standards for re-ingestion.
"""

import os
import glob
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, User, Conversation, Message, UploadedDocument
from auth import get_optional_user, get_current_user
import ingest

router = APIRouter(prefix="/admin", tags=["admin"])
DATA_STANDARDS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "standards")


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """Aggregates analytics across users, queries, agents, and confidence scores."""
    total_users = db.query(User).count()
    total_convs = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    user_queries = db.query(Message).filter(Message.role == "user").count()
    bot_responses = db.query(Message).filter(Message.role == "assistant").count()

    # Agent breakdown
    agent_counts = (
        db.query(Message.agent, func.count(Message.id))
        .filter(Message.role == "assistant")
        .group_by(Message.agent)
        .all()
    )
    agents_dist = {a or "ComplyBot": count for a, count in agent_counts}

    # Low confidence / knowledge gap count
    low_conf_count = (
        db.query(Message)
        .filter(Message.role == "assistant")
        .filter((Message.confidence < 0.50) | (Message.domain == "error"))
        .count()
    )

    # Average confidence
    avg_conf = (
        db.query(func.avg(Message.confidence))
        .filter(Message.role == "assistant")
        .filter(Message.confidence.isnot(None))
        .scalar()
    )

    # Documents uploaded
    docs_count = db.query(UploadedDocument).count()

    return {
        "total_users": total_users,
        "total_conversations": total_convs,
        "total_messages": total_messages,
        "user_queries": user_queries,
        "bot_responses": bot_responses,
        "agent_distribution": agents_dist,
        "low_confidence_queries": low_conf_count,
        "average_confidence": round(float(avg_conf or 0.85), 2),
        "uploaded_documents": docs_count,
    }


@router.get("/unanswered")
def get_unanswered_queries(limit: int = 20, db: Session = Depends(get_db)):
    """Retrieves questions where the system returned low confidence or encountered gaps."""
    # Join user messages immediately preceding low-confidence assistant messages
    bot_msgs = (
        db.query(Message)
        .filter(Message.role == "assistant")
        .filter((Message.confidence < 0.50) | (Message.domain == "error"))
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for bm in bot_msgs:
        # Find preceding user message in same conversation
        prev_user_msg = (
            db.query(Message)
            .filter(Message.conversation_id == bm.conversation_id)
            .filter(Message.role == "user")
            .filter(Message.created_at <= bm.created_at)
            .order_by(Message.created_at.desc())
            .first()
        )
        results.append({
            "id": bm.id,
            "conversation_id": bm.conversation_id,
            "question": prev_user_msg.content if prev_user_msg else "Unknown question",
            "bot_answer": bm.content[:150] + ("..." if len(bm.content) > 150 else ""),
            "confidence": bm.confidence,
            "agent": bm.agent,
            "created_at": bm.created_at.isoformat(),
        })

    return results


@router.get("/standards")
def list_standards():
    """Lists current documents in the standards corpus."""
    files = glob.glob(os.path.join(DATA_STANDARDS_DIR, "*.md"))
    data = []
    for f in files:
        data.append({
            "filename": os.path.basename(f),
            "size_kb": round(os.path.getsize(f) / 1024, 2),
            "last_modified": os.path.getmtime(f),
        })
    return {"total": len(data), "standards": data}


@router.post("/standards/upload")
async def upload_standard_file(file: UploadFile = File(...)):
    """Uploads a new markdown standards file into the corpus."""
    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only markdown (.md) documents are accepted.")

    safe_name = os.path.basename(file.filename)
    dest_path = os.path.join(DATA_STANDARDS_DIR, safe_name)

    with open(dest_path, "wb") as out:
        content = await file.read()
        out.write(content)

    return {"status": "uploaded", "filename": safe_name, "path": dest_path}


@router.post("/reingest")
def trigger_reingest():
    """Re-runs the ChromaDB vector embeddings pipeline across the standards directory."""
    try:
        ingest.main()
        return {"status": "success", "message": "Standards re-ingested into ChromaDB successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-ingestion failed: {str(e)}")
