"""
Core schema for the Revenue Recovery agent.

Five tables, each mapping to one stage of the loop:
    Event            -> something went wrong (detect)
    Decision          -> what the agent decided to do about it (diagnose + decide)
    Action            -> what was actually executed (act)
    Outcome           -> whether it worked (measure)
    PromiseToPay      -> tracked commitments from B2B/receivables flows
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, Integer, Enum, Text, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class EventType(str, enum.Enum):
    PAYMENT_FAILED = "payment_failed"
    CHECKOUT_ABANDONED = "checkout_abandoned"
    SUBSCRIPTION_FAILED = "subscription_failed"
    INVOICE_OVERDUE = "invoice_overdue"


class RootCause(str, enum.Enum):
    BANK_TIMEOUT = "bank_timeout"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    OTP_FAILED = "otp_failed"
    CARD_EXPIRED = "card_expired"
    USER_ABANDONED = "user_abandoned"
    INVOICE_UNPAID = "invoice_unpaid"
    UNKNOWN = "unknown"


class ActionType(str, enum.Enum):
    AUTO_RETRY = "auto_retry"
    SMS_NUDGE = "sms_nudge"
    WHATSAPP_NUDGE = "whatsapp_nudge"
    VOICE_CALL_HINGLISH = "voice_call_hinglish"
    NEW_PAYMENT_LINK = "new_payment_link"
    INVOICE_REMINDER = "invoice_reminder"
    ESCALATE_HUMAN = "escalate_human"
    STOPPED = "stopped"  # stopping rule triggered, no further action taken


class OutcomeStatus(str, enum.Enum):
    RECOVERED = "recovered"
    FAILED = "failed"
    PENDING = "pending"
    STOPPED = "stopped"


class Event(Base):
    """A single detected revenue-risk event, e.g. one failed payment."""
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=gen_uuid)
    event_type = Column(Enum(EventType), nullable=False)
    customer_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    raw_reason_code = Column(String, nullable=True)  # e.g. gateway error code
    demo_audio_path = Column(String, nullable=True)  # pre-recorded customer response clip, for the voice demo
    demo_transcript = Column(String, nullable=True)   # hand-written or pre-transcribed Hinglish transcript for demo/testing
    created_at = Column(DateTime, default=datetime.utcnow)

    decisions = relationship("Decision", back_populates="event")


class Decision(Base):
    """The agent's diagnosis + chosen intervention for a given event."""
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, default=gen_uuid)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    root_cause = Column(Enum(RootCause), nullable=False)
    chosen_action = Column(Enum(ActionType), nullable=False)
    reasoning = Column(Text, nullable=True)  # human-readable "why", for the audit trail
    attempt_number = Column(Integer, default=1)  # 1st retry, 2nd retry, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    next_retry_after = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="decisions")
    actions = relationship("Action", back_populates="decision")


class Action(Base):
    """What was actually executed for a decision."""
    __tablename__ = "actions"

    id = Column(String, primary_key=True, default=gen_uuid)
    decision_id = Column(String, ForeignKey("decisions.id"), nullable=False)
    action_type = Column(Enum(ActionType), nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    channel_ref = Column(String, nullable=True)  # e.g. SMS id, call id, payment link id
    notes = Column(Text, nullable=True)

    decision = relationship("Decision", back_populates="actions")
    outcome = relationship("Outcome", back_populates="action", uselist=False)


class Outcome(Base):
    """Whether the action worked — this is what feeds the recovered-₹ metric."""
    __tablename__ = "outcomes"

    id = Column(String, primary_key=True, default=gen_uuid)
    action_id = Column(String, ForeignKey("actions.id"), nullable=False)
    status = Column(Enum(OutcomeStatus), nullable=False)
    amount_recovered = Column(Float, default=0.0)
    resolved_at = Column(DateTime, default=datetime.utcnow)

    action = relationship("Action", back_populates="outcome")


class PromiseToPay(Base):
    """Tracked commitments, mainly for the B2B receivables / invoice flow."""
    __tablename__ = "promises_to_pay"

    id = Column(String, primary_key=True, default=gen_uuid)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    promised_date = Column(DateTime, nullable=False)
    promised_amount = Column(Float, nullable=False)
    fulfilled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
