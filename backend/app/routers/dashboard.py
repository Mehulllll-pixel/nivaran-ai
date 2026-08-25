from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=schemas.DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    outcomes = db.query(models.Outcome).all()
    actions = db.query(models.Action).all()

    total_events = len(events)
    total_at_risk = sum(e.amount for e in events)
    total_recovered = sum(o.amount_recovered for o in outcomes)
    stopped_count = (
        db.query(models.Decision.event_id)
        .join(models.Action, models.Action.decision_id == models.Decision.id)
        .filter(models.Action.action_type == models.ActionType.STOPPED)
        .distinct()
        .count()
    )

    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0

    # Amount recovered broken down by the action/channel that recovered it.
    by_action: dict[str, float] = {}
    action_by_id = {a.id: a for a in actions}
    for o in outcomes:
        a = action_by_id.get(o.action_id)
        if a and o.amount_recovered > 0:
            key = a.action_type.value
            by_action[key] = by_action.get(key, 0.0) + o.amount_recovered

    return schemas.DashboardMetrics(
        total_events=total_events,
        total_at_risk=round(total_at_risk, 2),
        total_recovered=round(total_recovered, 2),
        recovery_rate_pct=round(recovery_rate, 2),
        stopped_count=stopped_count,
        by_action_type={k: round(v, 2) for k, v in by_action.items()},
    )


@router.get("/case/{event_id}", response_model=schemas.CaseTimeline)
def get_case_timeline(event_id: str, db: Session = Depends(get_db)):
    """Full audit trail for one event: every decision, action, and outcome."""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    decisions = (
        db.query(models.Decision)
        .filter(models.Decision.event_id == event_id)
        .order_by(models.Decision.attempt_number)
        .all()
    )
    decision_ids = [d.id for d in decisions]
    actions = (
        db.query(models.Action)
        .filter(models.Action.decision_id.in_(decision_ids))
        .all()
        if decision_ids else []
    )
    action_ids = [a.id for a in actions]
    outcomes = (
        db.query(models.Outcome)
        .filter(models.Outcome.action_id.in_(action_ids))
        .all()
        if action_ids else []
    )

    return schemas.CaseTimeline(
        event=event,
        decisions=decisions,
        actions=actions,
        outcomes=outcomes,
    )
