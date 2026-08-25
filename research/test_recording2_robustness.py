"""
test_recording2_robustness.py
==============================
Tests whether extraction.py handles a real, imperfect Whisper transcription.

Transcript is taken verbatim from the Whisper output for recording2.mp4
(which contained the "shaantri aai ki" STT error), NOT from a corrected version.
"""
import datetime
import json
from extraction import extract_intent_and_promise

# ── verbatim Whisper transcription from recording2.mp4 ──────────────────────
TRANSCRIPT = "Kal shaantri aai ki, kal kar doonga."
CALL_DATE  = datetime.datetime(2026, 8, 22, 12, 0, 0)
# ────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("RECORDING 2 — ROBUSTNESS TEST (imperfect STT transcript)")
print("=" * 60)
print(f"Raw transcript  : {TRANSCRIPT}")
print(f"Call date       : {CALL_DATE.date()}")
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
print(f"PYTHON RESOLVED DATE : {result['resolved_promised_date']}")
print("=" * 60)
