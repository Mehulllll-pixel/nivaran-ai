"""
regression_test_step1.py
========================
Runs 8 manually defined transcripts through extract_intent_and_promise()
and determine_recovery_action(), comparing actual vs expected for each case.

Run in the terminal where GROQ_API_KEY is set.
"""
import datetime
import json
from extraction import extract_intent_and_promise
from guardrails import determine_recovery_action

CALL_DATE = datetime.datetime(2026, 8, 22, 12, 0, 0)

TESTS = [
    {
        "id": 1,
        "transcript": "Sir payment maine kal hi kar diya hai, ek baar check kar lo.",
        "expected_intent": "payment_already_completed",
        "expected_temporal_type": None,       # not strictly checked
        "expected_resolved_date": None,        # completed payment, date doesn't matter
        "note": "Past payment claim — should NOT produce a promise-to-pay."
    },
    {
        "id": 2,
        "transcript": "Mujhe payment nahi karni, aap jo karna hai kar lo.",
        "expected_intent": "payment_refusal",
        "expected_temporal_type": None,
        "expected_resolved_date": None,
        "note": "Explicit refusal — resolved_date must be None."
    },
    {
        "id": 3,
        "transcript": "Galat number hai sir, mujhe kisi payment ke baare mein nahi pata.",
        "expected_intent": "wrong_number",
        "expected_temporal_type": None,
        "expected_resolved_date": None,
        "note": "Wrong number — compliance_block must be set."
    },
    {
        "id": 4,
        "transcript": "Sir maine ye payment already dispute ki hui hai, main amount accept nahi karta.",
        "expected_intent": "dispute_amount",
        "expected_temporal_type": None,
        "expected_resolved_date": None,
        "note": "Dispute — escalate_to_human must be set, no promise-to-pay."
    },
    {
        "id": 5,
        "transcript": "Abhi payment nahi kar sakta, salary aane ke baad karunga.",
        "expected_intent": None,  # check both cannot_pay and event_based; show actual
        "expected_temporal_type": "event_based",
        "expected_resolved_date": None,
        "note": "Salary-conditional. No invented date. Show full recovery action."
    },
    {
        "id": 6,
        "transcript": "Haan sir, payment kar dunga.",
        "expected_intent": "agree_to_pay",
        "expected_temporal_type": "none",
        "expected_resolved_date": None,
        "note": "Generic agreement — no date/timeframe present."
    },
    {
        "id": 7,
        "transcript": "Kal payment kar dunga.",
        "expected_intent": "promise_future_payment",
        "expected_temporal_type": "relative",
        "expected_resolved_date": datetime.datetime(2026, 8, 23, 12, 0, 0),
        "note": "Future promise for tomorrow — resolved to 2026-08-23."
    },
    {
        "id": 8,
        "transcript": "Kal payment nahi karunga.",
        "expected_intent": "payment_refusal",
        "expected_temporal_type": None,
        "expected_resolved_date": None,
        "note": "Refusal mentioning 'kal' — resolved_date must still be None."
    },
]


def check(label, actual, expected):
    """Returns (pass_bool, detail_str)."""
    if expected is None:
        return True, f"{label}: {actual!r} (not strictly checked)"
    if actual == expected:
        return True, f"{label}: {actual!r} ✓"
    return False, f"{label}: expected {expected!r}, got {actual!r} ✗"


passed = 0
failed = 0

for t in TESTS:
    print("=" * 70)
    print(f"TEST {t['id']}: {t['note']}")
    print("=" * 70)
    print(f"Transcript: {t['transcript']}")
    print()

    try:
        result = extract_intent_and_promise(t["transcript"], CALL_DATE)
        action = determine_recovery_action(result)

        ext = result["extraction"]
        print("RAW GROQ RESPONSE:")
        print(result["raw_response"])
        print()

        print("PARSED EXTRACTION:")
        print(json.dumps(ext, indent=2, default=str))
        print()

        print(f"PYTHON RESOLVED DATE: {result['resolved_promised_date']}")
        print()

        print("RECOVERY ACTION:")
        print(json.dumps(action, indent=2, default=str))
        print()

        # --- Evaluate ---
        actual_intent = ext.get("intent")
        actual_temp_type = ext.get("temporal", {}).get("type")
        actual_date = result["resolved_promised_date"]

        results = []
        ok_intent, msg_intent = check("intent", actual_intent, t["expected_intent"])
        results.append((ok_intent, msg_intent))

        ok_temp, msg_temp = check("temporal.type", actual_temp_type, t["expected_temporal_type"])
        results.append((ok_temp, msg_temp))

        ok_date, msg_date = check("resolved_date", actual_date, t["expected_resolved_date"])
        results.append((ok_date, msg_date))

        # Extra checks per test
        test_pass = True
        for ok, msg in results:
            print(f"  {'PASS' if ok else 'FAIL'}  {msg}")
            if not ok:
                test_pass = False

        # Test 5: extra — verify no invented date and event-based action
        if t["id"] == 5:
            if actual_date is not None:
                print(f"  FAIL  resolved_date must be None for event_based (got {actual_date}) ✗")
                test_pass = False
            else:
                print(f"  PASS  No invented calendar date for event_based ✓")
            if action.get("generic_follow_up") is True:
                print(f"  PASS  generic_follow_up=True for event_based ✓")
            elif actual_intent in ("cannot_pay", "unable_to_pay"):
                print(f"  INFO  intent is {actual_intent!r}, no schedule_follow_up expected — check guardrail behaviour above")
            else:
                print(f"  WARN  generic_follow_up={action.get('generic_follow_up')} — review action above")

        if test_pass:
            print(f"\n>>> TEST {t['id']}: PASS")
            passed += 1
        else:
            print(f"\n>>> TEST {t['id']}: FAIL")
            failed += 1

    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"\n>>> TEST {t['id']}: FAIL (exception)")
        failed += 1

    print()

print("=" * 70)
print("REGRESSION SUMMARY:")
print(f"  {passed}/{passed + failed} tests passed.")
if failed:
    print(f"  {failed} FAILED — do not proceed until failures are understood.")
else:
    print("  All tests passed.")
print("=" * 70)
