from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models import EventType, RootCause, ActionType, OutcomeStatus


class EventCreate(BaseModel):
    event_type: EventType
    customer_id: str
    amount: float
    currency: str = "INR"
    raw_reason_code: Optional[str] = None
    demo_audio_path: Optional[str] = None  # pre-recorded customer response clip, for the voice demo
    demo_transcript: Optional[str] = None


class EventOut(BaseModel):
    id: str
    event_type: EventType
    customer_id: str
    amount: float
    currency: str
    raw_reason_code: Optional[str]
    demo_audio_path: Optional[str] = None
    demo_transcript: Optional[str] = None
    # Populated server-side by the list endpoint: the real transcript fed to
    # the NLU pipeline, parsed from voice action notes. None if voice was
    # never reached for this event.
    voice_transcript: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionOut(BaseModel):
    id: str
    event_id: str
    root_cause: RootCause
    chosen_action: ActionType
    reasoning: Optional[str]
    attempt_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class ActionOut(BaseModel):
    id: str
    decision_id: str
    action_type: ActionType
    executed_at: datetime
    channel_ref: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class OutcomeOut(BaseModel):
    id: str
    action_id: str
    status: OutcomeStatus
    amount_recovered: float
    resolved_at: datetime

    class Config:
        from_attributes = True


class CaseTimeline(BaseModel):
    """One event with its full decision -> action -> outcome chain, for the audit trail UI."""
    event: EventOut
    decisions: list[DecisionOut]
    actions: list[ActionOut]
    outcomes: list[OutcomeOut]


class DashboardMetrics(BaseModel):
    total_events: int
    total_at_risk: float
    total_recovered: float
    recovery_rate_pct: float
    stopped_count: int
    by_action_type: dict[str, float]  # action_type -> amount recovered via that channel
