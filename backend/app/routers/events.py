from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/events", tags=["events"])


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


@router.get("/", response_model=list[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.Event).order_by(models.Event.created_at.desc()).all()
