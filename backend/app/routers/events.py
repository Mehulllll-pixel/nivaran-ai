import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/events", tags=["events"])

_TRANSCRIPT_RE = re.compile(r"Transcript:\s*'(.*?)'\s*\|", re.DOTALL)


@router.post("/ingest", response_model=schemas.EventOut)
def ingest_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Entry point for a new revenue-risk signal: a failed payment,
    an abandoned checkout, a failed subscription renewal, or an
    overdue invoice. In production this would be called by a
    webhook from the payment gateway / checkout / billing system.
    """
    event = models.Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _extract_voice_transcript(event: models.Event) -> str | None:
    """
    Walk event.decisions -> actions looking for the first
    voice_call_hinglish action, then parse the transcript out of its
    notes string (format: "... | Transcript: '...' | ...").
    Returns None if the event never reached a voice call.
    """
    for decision in (event.decisions or []):
        for action in (decision.actions or []):
            if action.action_type == models.ActionType.VOICE_CALL_HINGLISH and action.notes:
                m = _TRANSCRIPT_RE.search(action.notes)
                if m:
                    return m.group(1).strip()
    return None


@router.get("/", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    events = (
        db.query(models.Event)
        .order_by(models.Event.created_at.desc())
        .all()
    )
    result = []
    for evt in events:
        out = schemas.EventOut.model_validate(evt)
        # voice_transcript is derived ONLY from the actual action history.
        # demo_transcript is a seed-time field that may exist on events that
        # never reached voice_call_hinglish (resolved via auto_retry / sms_nudge).
        # We must NOT display demo_transcript in the list unless the real NLU
        # pipeline actually ran on it — so always derive from action notes.
        out.voice_transcript = _extract_voice_transcript(evt)
        result.append(out)
    return result


