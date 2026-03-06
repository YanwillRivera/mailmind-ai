"""
Emails Router
─────────────
REST API endpoints that the React dashboard calls.

GET  /emails/          → list all processed emails (sorted by urgency)
GET  /emails/{id}      → get one email with full analysis
POST /emails/run       → trigger pipeline manually
POST /emails/{id}/reply → send the draft reply
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlmodel import Session, select
from typing import Optional
from pydantic import BaseModel

from app.database import get_session, EmailRecord
from app.services.pipeline import run_pipeline
from app.services.gmail_service import send_reply

router = APIRouter()

URGENCY_ORDER = {"Alta": 0, "Media": 1, "Baja": 2}


# ── List emails ───────────────────────────────────────────────────────────────
@router.get("/")
def list_emails(
    urgencia:  Optional[str] = None,   # Filter: Alta / Media / Baja
    categoria: Optional[str] = None,   # Filter by category
    status:    Optional[str] = None,   # Filter: pending / analyzed / replied
    session:   Session = Depends(get_session)
):
    query = select(EmailRecord)

    if urgencia:  query = query.where(EmailRecord.urgencia  == urgencia)
    if categoria: query = query.where(EmailRecord.categoria == categoria)
    if status:    query = query.where(EmailRecord.status    == status)

    emails = session.exec(query).all()

    # Sort by urgency (Alta first), then by received date
    emails.sort(key=lambda e: (
        URGENCY_ORDER.get(e.urgencia, 9),
        -(e.received_at.timestamp() if e.received_at else 0)
    ))

    return {"emails": emails, "total": len(emails)}


# ── Get one email ─────────────────────────────────────────────────────────────
@router.get("/{email_id}")
def get_email(email_id: int, session: Session = Depends(get_session)):
    email = session.get(EmailRecord, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


# ── Run pipeline manually ─────────────────────────────────────────────────────
@router.post("/run")
def run_pipeline_endpoint(background_tasks: BackgroundTasks):
    """
    Trigger the full Gmail → Claude → DB → Notion pipeline.
    Runs in the background so the request returns immediately.
    """
    background_tasks.add_task(run_pipeline)
    return {"message": "Pipeline started in background ⚡"}


# ── Send reply ────────────────────────────────────────────────────────────────
class ReplyRequest(BaseModel):
    body: str  # The reply text (pre-filled with AI draft, editable by user)

@router.post("/{email_id}/reply")
def send_email_reply(
    email_id: int,
    payload:  ReplyRequest,
    session:  Session = Depends(get_session)
):
    email = session.get(EmailRecord, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    try:
        send_reply(
            to_email=email.sender_email,
            subject=email.subject,
            body=payload.body,
            thread_id=email.gmail_id,   # Gmail uses this to keep it in the same thread
        )
        email.status = "replied"
        session.add(email)
        session.commit()
        return {"message": f"Reply sent to {email.sender_email} ✅"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Stats for the dashboard header ───────────────────────────────────────────
@router.get("/stats/summary")
def get_stats(session: Session = Depends(get_session)):
    emails = session.exec(select(EmailRecord)).all()
    urgency_counts = {"Alta": 0, "Media": 0, "Baja": 0}
    for e in emails:
        if e.urgencia in urgency_counts:
            urgency_counts[e.urgencia] += 1

    return {
        "total":         len(emails),
        "analyzed":      sum(1 for e in emails if e.status != "pending"),
        "replied":       sum(1 for e in emails if e.status == "replied"),
        "urgency_counts": urgency_counts,
    }
