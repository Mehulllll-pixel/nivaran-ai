import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.decision_engine import classify_root_cause, decide_action
from app.executors import EXECUTOR_MAP

router = APIRouter(prefix="/agent", tags=["agent"])

_PROMISE_PATTERN = re.compile(r"Promised: ₹([\d.]+) by ([^\|]+)")


def _parse_relative_date(date_str: str) -> datetime | None:
    """
    Groq extraction may return a relative phrase ('tomorrow', 'kal') instead
    of an ISO date. Handle the common cases; anything else is left for a
    human to resolve (still logged, just without a parsed promised_date).
    """
    date_str = date_str.strip().lower()
    if date_str in ("tomorrow", "kal"):
        return datetime.utcnow() + timedelta(days=1)
    if date_str in ("today", "aaj"):
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None


def _maybe_log_promise_to_pay(event: models.Event, notes: str, db: Session):
    """
    Parses the voice call's notes for a promise-to-pay extraction and, if
    found, writes a PromiseToPay row. This is what powers the follow-up
    scheduling and the hero-demo "payment succeeds tomorrow" beat.
    """
    match = _PROMISE_PATTERN.search(notes)
    if not match:
        return  # no promise extracted (e.g. simulated fallback, or customer declined)

    amount_str, date_str = match.group(1), match.group(2)
    promised_date = _parse_relative_date(date_str)
    if promised_date is None:
        return  # couldn't parse a usable date — skip rather than log garbage

    promise = models.PromiseToPay(
        event_id=event.id,
        promised_date=promised_date,
        promised_amount=float(amount_str),
        fulfilled=False,
    )
    db.add(promise)
    db.commit()


def _process_event(event: models.Event, db: Session) -> models.Decision:
    """
    Runs one diagnose -> decide -> act -> log cycle for a single event.
    attempt_number = how many decisions already exist for this event + 1.
    """
    # Short-circuit: if this event is already in a terminal state (RECOVERED or
    # STOPPED by compliance rule), there is nothing left to do.
    already_terminal = (
        db.query(models.Outcome)
        .join(models.Action, models.Outcome.action_id == models.Action.id)
        .join(models.Decision, models.Action.decision_id == models.Decision.id)
        .filter(
            models.Decision.event_id == event.id,
            models.Outcome.status.in_([models.OutcomeStatus.RECOVERED, models.OutcomeStatus.STOPPED]),
        )
        .first()
    )
    if already_terminal:
        return (
            db.query(models.Decision)
            .filter(models.Decision.event_id == event.id)
            .order_by(models.Decision.attempt_number.desc())
            .first()
        )

    prior_attempts = (
        db.query(models.Decision)
        .filter(models.Decision.event_id == event.id)
        .count()
    )
    attempt_number = prior_attempts + 1

    root_cause = classify_root_cause(event.event_type, event.raw_reason_code)
    chosen_action, reasoning = decide_action(root_cause, attempt_number)

    decision = models.Decision(
        event_id=event.id,
        root_cause=root_cause,
        chosen_action=chosen_action,
        reasoning=reasoning,
        attempt_number=attempt_number,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    # If the stopping rule fired, log it and stop — no action executed.
    if chosen_action == models.ActionType.STOPPED:
        action = models.Action(
            decision_id=decision.id,
            action_type=models.ActionType.STOPPED,
            channel_ref=None,
            notes=reasoning,
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        outcome = models.Outcome(
            action_id=action.id,
            status=models.OutcomeStatus.STOPPED,
            amount_recovered=0.0,
        )
        db.add(outcome)
        db.commit()
        return decision

    # Otherwise execute the chosen intervention.
    executor = EXECUTOR_MAP[chosen_action.value]

    if chosen_action == models.ActionType.VOICE_CALL_HINGLISH:
        # Use per-event demo_transcript when available; executor's hardcoded
        # default ("5000 rupaye kal de dunga") kicks in automatically when None.
        call_kwargs = dict(
            amount=event.amount,
            root_cause=root_cause.value,
        )
        if event.demo_transcript:
            call_kwargs["transcript"] = event.demo_transcript
        success, recovered, channel_ref, notes = executor(**call_kwargs)
        # If the notes contain a genuine promise-to-pay extraction, log it.
        _maybe_log_promise_to_pay(event, notes, db)
    else:
        success, recovered, channel_ref, notes = executor(event.amount)

    action = models.Action(
        decision_id=decision.id,
        action_type=chosen_action,
        channel_ref=channel_ref,
        notes=notes,
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    if chosen_action == models.ActionType.ESCALATE_HUMAN:
        status = models.OutcomeStatus.PENDING
    else:
        status = models.OutcomeStatus.RECOVERED if success else models.OutcomeStatus.FAILED

    outcome = models.Outcome(
        action_id=action.id,
        status=status,
        amount_recovered=recovered,
    )
    db.add(outcome)
    db.commit()

    return decision


@router.post("/process/{event_id}", response_model=schemas.DecisionOut)
def process_single_event(event_id: str, db: Session = Depends(get_db)):
    """Run the agent loop once for a specific event (one attempt)."""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    decision = _process_event(event, db)
    return decision


@router.post("/fulfill-promise/{promise_id}")
def fulfill_promise(promise_id: str, db: Session = Depends(get_db)):
    """
    Marks a promise-to-pay as fulfilled and logs the recovered amount as
    an outcome. This is the "payment succeeds" beat in the hero demo —
    call this after showing the promise was logged, to show the dashboard
    updating with the recovered ₹.
    """
    promise = db.query(models.PromiseToPay).filter(models.PromiseToPay.id == promise_id).first()
    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")

    promise.fulfilled = True

    # Find the most recent decision/action for this event to attach the outcome to,
    # so the audit trail stays linked to the voice call that generated the promise.
    decision = (
        db.query(models.Decision)
        .filter(models.Decision.event_id == promise.event_id)
        .order_by(models.Decision.attempt_number.desc())
        .first()
    )
    if decision:
        action = (
            db.query(models.Action)
            .filter(models.Action.decision_id == decision.id)
            .first()
        )
        if action:
            outcome = models.Outcome(
                action_id=action.id,
                status=models.OutcomeStatus.RECOVERED,
                amount_recovered=promise.promised_amount,
            )
            db.add(outcome)

    db.commit()
    return {"status": "fulfilled", "amount_recovered": promise.promised_amount}


@router.post("/process-batch")
def process_batch(db: Session = Depends(get_db)):
    """
    Run one agent attempt across ALL events currently in the system.
    This is what you call repeatedly in the demo to show retries
    escalating over successive passes (simulating time passing).
    """
    events = db.query(models.Event).all()
    processed = 0
    for event in events:
        _process_event(event, db)
        processed += 1
    return {"events_processed": processed}
