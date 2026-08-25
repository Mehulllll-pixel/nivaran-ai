import os
os.environ['DATABASE_URL'] = 'sqlite:///./dev.db'
os.environ['PYTHONPATH'] = '.'
os.environ['PYTHONIOENCODING'] = 'utf-8'

from collections import Counter
from app.database import SessionLocal
from app import models

db = SessionLocal()
events = db.query(models.Event).all()

recovered_attempts = []
stopped_root_causes = []
recovered_channels = Counter()

for e in events:
    decisions = db.query(models.Decision).filter(models.Decision.event_id == e.id).order_by(models.Decision.attempt_number).all()
    d_ids = [d.id for d in decisions]
    actions = db.query(models.Action).filter(models.Action.decision_id.in_(d_ids)).all()
    action_map = {a.id: a for a in actions}
    outcomes = db.query(models.Outcome).filter(models.Outcome.action_id.in_([a.id for a in actions])).all()
    
    statuses = [o.status.value for o in outcomes]
    if 'recovered' in statuses:
        # Find which action recovered
        for o in outcomes:
            if o.status.value == 'recovered' and o.amount_recovered > 0:
                act = action_map.get(o.action_id)
                if act:
                    recovered_channels[act.action_type.value] += 1
        recovered_attempts.append(len(decisions))
    elif 'stopped' in statuses:
        last_d = decisions[-1]
        stopped_root_causes.append((last_d.root_cause.value, len(decisions)))

print("--- RECOVERED Breakdowns (64 Events) ---")
print("Attempts taken to recover:", Counter(recovered_attempts))
print("Channels that recovered revenue:", dict(recovered_channels))

print("\n--- STOPPED Breakdowns (16 Events) ---")
print("Root cause & attempt count for STOPPED:", Counter(stopped_root_causes))

db.close()
