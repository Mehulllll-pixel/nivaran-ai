"""
Isolated one-shot test of extraction.py against a real Whisper-produced transcript.
Prints the raw Groq response, then the parsed extraction + resolved date.
"""
import datetime, json, sys
from extraction import extract_intent_and_promise

TRANSCRIPT = "Bhai, abhi payment nahin hain. Kal kar doonga."
CALL_DATE  = datetime.datetime(2026, 8, 22, 12, 0, 0)

print("=" * 60)
print("EXTRACTION TEST — real Whisper transcript")
print("=" * 60)
print(f"Transcript : {TRANSCRIPT}")
print(f"Call date  : {CALL_DATE.date()}")
print()

result = extract_intent_and_promise(TRANSCRIPT, CALL_DATE)

print("RAW GROQ RESPONSE:")
print(result["raw_response"])
print()

if result["fallback_mode"]:
    print("[!] Strict json_schema mode FAILED — json_object fallback was used.")
else:
    print("[OK] Strict json_schema mode succeeded.")

print()
print("PARSED EXTRACTION:")
print(json.dumps(result["extraction"], indent=2, default=str))
print()
print(f"PYTHON RESOLVED DATE: {result['resolved_promised_date']}")
print("=" * 60)
