from app.database import SessionLocal
from app.models import Event, Action, ActionType
import re

db = SessionLocal()
try:
    events = db.query(Event).limit(10).all()
    print("=== 10 RAW EVENTS FROM DATABASE ===")
    for e in events:
        voice_transcript = None
        for d in e.decisions:
            for a in d.actions:
                if a.action_type == ActionType.VOICE_CALL_HINGLISH and a.notes:
                    m = re.search(r"Transcript:\s*'(.*?)'\s*\|", a.notes)
                    if m:
                        voice_transcript = m.group(1)
        print(f"Customer: {e.customer_id:20} | Amount: Rs.{e.amount:9.2f} | Raw demo_transcript: {repr(e.demo_transcript):30} | Voice Action Notes Transcript: {repr(voice_transcript)}")
finally:
    db.close()
