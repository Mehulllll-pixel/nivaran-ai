"""
test_hero_transcript_extraction.py
==================================
BEFORE/AFTER: amount_at_risk context added to extraction pipeline.

Hero transcript: "Bhai abhi paise nahi hai, kal salary aayegi, kal kar dunga"
- BEFORE: promised_amount -> None (model didn't see call amount, returned null)
- AFTER:  promised_amount -> 12000.0 (model inherits call amount per rule 8)

Also runs 3 repeats to confirm stability.
"""
import os, json, datetime
from dotenv import load_dotenv
load_dotenv()

from app.voice_pipeline.extraction import extract_intent_and_promise

transcript = "Bhai abhi paise nahi hai, kal salary aayegi, kal kar dunga"
call_date = datetime.date(2026, 8, 25)
AMOUNT_AT_RISK = 12000.0

print("=" * 65)
print("BEFORE (no amount_at_risk context, old behaviour)")
print("=" * 65)
result_before = extract_intent_and_promise(transcript=transcript, call_date=call_date, amount_at_risk=None)
ex = result_before["extraction"]
print(f"  promised_amount : {ex.get('promised_amount')}")
print(f"  intent          : {ex.get('intent')}")
print(f"  temporal.type   : {ex.get('temporal', {}).get('type')}")
print(f"  resolved_date   : {result_before['resolved_promised_date']}")
print(f"  reasoning       : {ex.get('reasoning')}")

print()
print("=" * 65)
print(f"AFTER (amount_at_risk=₹{AMOUNT_AT_RISK}, new rule 8) — 3 runs for stability")
print("=" * 65)

results = []
for i in range(1, 4):
    result = extract_intent_and_promise(transcript=transcript, call_date=call_date, amount_at_risk=AMOUNT_AT_RISK)
    ex = result["extraction"]
    pa = ex.get("promised_amount")
    results.append(pa)
    print(f"\n  --- Run #{i} ---")
    print(f"  promised_amount : {pa}")
    print(f"  intent          : {ex.get('intent')}")
    print(f"  temporal.type   : {ex.get('temporal', {}).get('type')}")
    print(f"  resolved_date   : {result['resolved_promised_date']}")
    print(f"  reasoning       : {ex.get('reasoning')}")

print()
print("=" * 65)
consistent = all(r == results[0] for r in results)
print(f"STABILITY CHECK: all 3 runs returned promised_amount={results[0]} -> {'PASS' if consistent else 'INCONSISTENT'}")
expected = AMOUNT_AT_RISK
correct = all(r == expected for r in results)
print(f"CORRECTNESS CHECK: promised_amount == {expected} -> {'PASS' if correct else f'FAIL (got {results})'}")
print("=" * 65)
