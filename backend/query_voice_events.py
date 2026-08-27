from app.database import SessionLocal
from app.models import Event, Action, ActionType, Decision, Outcome
import re

db = SessionLocal()
try:
    print("=== EVENTS THAT REACHED VOICE_CALL_HINGLISH ===")
    
    # Query actions that are VOICE_CALL_HINGLISH
    voice_actions = db.query(Action).filter(Action.action_type == ActionType.VOICE_CALL_HINGLISH).all()
    
    seen_events = set()
    count = 0
    for a in voice_actions:
        decision = db.query(Decision).filter(Decision.id == a.decision_id).first()
        if not decision or decision.event_id in seen_events:
            continue
        seen_events.add(decision.event_id)
        
        event = db.query(Event).filter(Event.id == decision.event_id).first()
        outcome = db.query(Outcome).filter(Outcome.action_id == a.id).first()
        
        notes = a.notes or ""
        intent_m = re.search(r"Intent:\s*(\w+)", notes)
        intent = intent_m.group(1) if intent_m else "unknown"
        
        status = outcome.status.value if outcome else "None"
        recovered = outcome.amount_recovered if outcome else 0.0
        
        print(f"\n[{count+1}] Customer: {event.customer_id} (Amount: Rs.{event.amount:,.2f})")
        print(f"    Transcript: \"{event.demo_transcript}\"")
        print(f"    Groq Intent: {intent} | Action Outcome: {status} | Recovered Credited: Rs.{recovered:,.2f}")
        
        count += 1
        if count >= 15:
            break
            
finally:
    db.close()
