from app.database import SessionLocal
from app.models import Event, Decision, Action

db = SessionLocal()
try:
    print("=== SEARCHING SAMPLE EVENTS ===")
    events = db.query(Event).all()
    
    gt_event = None
    otp_event = None
    card_event = None
    
    for e in events:
        if e.raw_reason_code == "gateway_timeout" and not gt_event:
            gt_event = e
        elif e.raw_reason_code == "otp_mismatch" and not otp_event:
            otp_event = e
        elif e.raw_reason_code == "card_expired" and not card_event:
            card_event = e
            
    for label, ev in [("gateway_timeout", gt_event), ("otp_mismatch", otp_event), ("card_expired", card_event)]:
        if ev:
            print(f"\n[{label}] Customer: {ev.customer_id} (ID: {ev.id})")
            print(f"  Event Type: {ev.event_type.value}, Raw Code: {ev.raw_reason_code}")
            for d in ev.decisions:
                print(f"  Attempt #{d.attempt_number} (Root Cause: {d.root_cause.value}, Action: {d.chosen_action.value})")
                print(f"    Reasoning: {d.reasoning}")
finally:
    db.close()
