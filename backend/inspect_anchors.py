from app.database import SessionLocal
from app.models import Event, Decision, Action, Outcome

db = SessionLocal()
try:
    for cust_id in ["cust_demo_wrongnum", "cust_demo_dispute", "cust_demo_nocontact", "cust_hero_demo"]:
        event = db.query(Event).filter(Event.customer_id == cust_id).first()
        if not event:
            print(f"Event {cust_id}: NOT FOUND")
            continue
        print(f"\n==========================================")
        print(f"CUSTOMER: {event.customer_id} | ID: {event.id} | Amount: Rs.{event.amount}")
        print(f"Transcript: {event.demo_transcript}")
        decisions = db.query(Decision).filter(Decision.event_id == event.id).order_by(Decision.attempt_number).all()
        for d in decisions:
            action = db.query(Action).filter(Action.decision_id == d.id).first()
            outcome = db.query(Outcome).filter(Outcome.action_id == action.id).first() if action else None
            status_val = outcome.status.value if outcome else "NO_OUTCOME"
            recovered_val = outcome.amount_recovered if outcome else 0.0
            print(f"  Attempt {d.attempt_number}: {d.chosen_action.value} -> Outcome: {status_val} (Recovered: Rs.{recovered_val})")
            if action and action.notes:
                print(f"    Notes: {action.notes[:160]}...")
finally:
    db.close()
