"""
Dry-run: test Groq extraction for the cust_demo_nocontact transcript.
Run from the backend directory.
Command: python -m app.dryrun_nocontact
"""
import sys
import json
import datetime

# Force UTF-8 output so rupee and tick symbols print safely
sys.stdout.reconfigure(encoding="utf-8")

from app.voice_pipeline.extraction import extract_intent_and_promise
from app.voice_pipeline.guardrails import determine_recovery_action

TRANSCRIPT = "Main paise nahi dunga, dobara phone mat karna mujhe."
AMOUNT = 3200.00

print("=" * 60)
print("DRY-RUN: cust_demo_nocontact transcript extraction")
print(f"Transcript : {TRANSCRIPT!r}")
print(f"Amount     : Rs.{AMOUNT}")
print("=" * 60)

result = extract_intent_and_promise(
    transcript=TRANSCRIPT,
    call_date=datetime.datetime.utcnow(),
    amount_at_risk=AMOUNT,
)

extraction = result["extraction"]
print("\n--- Raw extraction (full JSON) ---")
print(json.dumps(extraction, indent=2, ensure_ascii=True))
print()
print(f"intent              : {extraction.get('intent')}")
print(f"requests_no_contact : {extraction.get('requests_no_contact')}")
print(f"sentiment           : {extraction.get('sentiment')}")
print(f"confidence          : {extraction.get('confidence')}")
print(f"reasoning           : {extraction.get('reasoning')}")
print(f"fallback_mode       : {result.get('fallback_mode')}")
print()

action_plan = determine_recovery_action(result)
print("--- Guardrail decision ---")
print(json.dumps(action_plan, indent=2, default=str, ensure_ascii=True))
print()
print(f"EXPECTED : action=stop_channel_contact, compliance_block=True")
print(f"ACTUAL   : action={action_plan['action']}, compliance_block={action_plan['compliance_block']}")
print()
match = (
    action_plan["action"] == "stop_channel_contact"
    and action_plan["compliance_block"] is True
)
print(f"MATCH    : {'YES - guardrail fires correctly' if match else 'NO - MISMATCH, DO NOT PROCEED'}")
