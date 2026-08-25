import os
os.environ['DATABASE_URL'] = 'sqlite:///./dev.db'
os.environ['PYTHONPATH'] = '.'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app.database import SessionLocal
from app import models

db = SessionLocal()
events = db.query(models.Event).all()
total = len(events)

recovered_events = []
stopped_events = []
pending_events = []
no_decision_events = []
failed_only_events = []

for e in events:
    decisions = db.query(models.Decision).filter(models.Decision.event_id == e.id).order_by(models.Decision.attempt_number).all()
    if not decisions:
        no_decision_events.append(e)
        continue
    
    d_ids = [d.id for d in decisions]
    actions = db.query(models.Action).filter(models.Action.decision_id.in_(d_ids)).all()
    a_ids = [a.id for a in actions]
    outcomes = db.query(models.Outcome).filter(models.Outcome.action_id.in_(a_ids)).all()
    
    statuses = [o.status.value for o in outcomes]
    
    if 'recovered' in statuses:
        recovered_events.append(e)
    elif 'stopped' in statuses:
        stopped_events.append(e)
    elif 'pending' in statuses:
        pending_events.append(e)
    else:
        failed_only_events.append((e, statuses, [d.chosen_action.value for d in decisions]))

print(f"Total Events: {total}")
print(f"  1. RECOVERED : {len(recovered_events)}")
print(f"  2. STOPPED   : {len(stopped_events)}")
print(f"  3. PENDING   : {len(pending_events)}")
print(f"  4. NO DECISIONS: {len(no_decision_events)}")
print(f"  5. OTHER/FAILED ONLY: {len(failed_only_events)}")
print(f"Sum check: {len(recovered_events) + len(stopped_events) + len(pending_events) + len(no_decision_events) + len(failed_only_events)} / {total}")

print("\n--- Details of PENDING events (Awaiting Promise Fulfillment or Human Resolution) ---")
for p in pending_events:
    last_d = db.query(models.Decision).filter(models.Decision.event_id == p.id).order_by(models.Decision.attempt_number.desc()).first()
    d_count = db.query(models.Decision).filter(models.Decision.event_id == p.id).count()
    print(f"  [{p.customer_id}] type={p.event_type.value:<20} attempts={d_count} last_action={last_d.chosen_action.value:<20} transcript=\"{p.demo_transcript}\"")

db.close()
