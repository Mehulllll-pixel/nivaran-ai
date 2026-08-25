"""
test_amount_extraction.py
=========================
Tests promised_amount capture across 3 transcripts:
  1. Full amount + relative date
  2. Partial payment offer (amount now + remainder later)
  3. Full amount + "kal tak" deadline

Run in the terminal where GROQ_API_KEY is set.
Do NOT modify extraction.py or guardrails.py.
"""
import datetime
import json
from extraction import extract_intent_and_promise
from guardrails import determine_recovery_action

CALL_DATE = datetime.datetime(2026, 8, 22, 12, 0, 0)
DIVIDER   = "=" * 65

# Current intent enum (from extraction.py schema) — used in gap analysis
KNOWN_INTENTS = {
    "agree_to_pay", "promise_future_payment", "payment_already_completed",
    "asks_why", "cannot_pay", "payment_refusal", "dispute_amount",
    "wrong_number", "opt_out", "unclear"
}

TESTS = [
    {
        "id": "A",
        "transcript": "5000 rupaye kal de dunga.",
        "expect_amount": 5000.0,
        "expect_intent": "promise_future_payment",
        "expect_date":   datetime.datetime(2026, 8, 23, 12, 0, 0),
        "note": "Full amount + relative tomorrow"
    },
    {
        "id": "B",
        "transcript": "Sir 2000 abhi hai mere paas, baaki agle hafte de dunga.",
        "expect_amount": None,   # unclear — model may capture 2000 or total; flag either way
        "expect_intent": None,   # explicitly checking for enum gap
        "expect_date":   None,
        "note": "Partial payment offer — potential intent enum gap"
    },
    {
        "id": "C",
        "transcript": "Poora 12000 kal tak kar dunga.",
        "expect_amount": 12000.0,
        "expect_intent": "promise_future_payment",
        "expect_date":   datetime.datetime(2026, 8, 23, 12, 0, 0),
        "note": "Full amount + kal tak deadline"
    },
]

for t in TESTS:
    print(DIVIDER)
    print(f"TEST {t['id']}: {t['note']}")
    print(DIVIDER)
    print(f"Transcript : {t['transcript']}")
    print()

    result = extract_intent_and_promise(t["transcript"], CALL_DATE)
    action = determine_recovery_action(result)
    ext    = result["extraction"]

    print("RAW GROQ RESPONSE:")
    print(result["raw_response"])
    print()

    print("PARSED EXTRACTION:")
    print(json.dumps(ext, indent=2, default=str))
    print()

    print(f"PYTHON RESOLVED DATE : {result['resolved_promised_date']}")
    print()

    print("RECOVERY ACTION:")
    print(json.dumps(action, indent=2, default=str))
    print()

    # ── Verdict ────────────────────────────────────────────────────────────
    actual_amount = ext.get("promised_amount")
    actual_intent = ext.get("intent")
    actual_date   = result["resolved_promised_date"]

    print("── VERDICT ──────────────────────────────────────────────────")

    # Amount check
    if t["expect_amount"] is not None:
        if actual_amount == t["expect_amount"]:
            print(f"  PASS  promised_amount = {actual_amount} ✓")
        else:
            print(f"  FAIL  promised_amount: expected {t['expect_amount']}, got {actual_amount} ✗")
    else:
        # Test B — just report what came back; evaluate for gap
        print(f"  INFO  promised_amount captured as: {actual_amount!r}")

    # Intent check
    if t["expect_intent"] is not None:
        if actual_intent == t["expect_intent"]:
            print(f"  PASS  intent = '{actual_intent}' ✓")
        else:
            print(f"  FAIL  intent: expected '{t['expect_intent']}', got '{actual_intent}' ✗")
    else:
        # Test B — check whether the returned intent cleanly covers the scenario
        in_enum = actual_intent in KNOWN_INTENTS
        print(f"  INFO  intent returned: '{actual_intent}' (in enum: {in_enum})")

        # Gap analysis for partial payment
        print()
        print("  ── INTENT ENUM GAP ANALYSIS (Test B) ──────────────────")
        print(f"  Sentence contains: partial amount NOW + remainder LATER")
        print(f"  Model chose intent: '{actual_intent}'")
        if actual_intent == "promise_future_payment":
            print("  ASSESSMENT: 'promise_future_payment' is close but imprecise.")
            print("    — It does not distinguish a partial payment offer from a full")
            print("      one. The partial/full split is lost. This is a real gap:")
            print("      a 'partial_payment_offer' intent would let downstream logic")
            print("      log the partial amount separately and schedule two follow-ups.")
        elif actual_intent == "agree_to_pay":
            print("  ASSESSMENT: 'agree_to_pay' loses BOTH the amounts and dates.")
            print("    — Clear gap: no intent captures the two-part payment structure.")
        elif actual_intent == "unclear":
            print("  ASSESSMENT: Model punted to 'unclear' — the partial-payment")
            print("    structure genuinely doesn't fit the current enum.")
        else:
            print(f"  ASSESSMENT: '{actual_intent}' does not cleanly describe a")
            print("    partial payment. The partial/full distinction is unrepresented")
            print("    in the current intent enum. Flagged as a real gap.")
        print("  ────────────────────────────────────────────────────────")

    # Date check
    if t["expect_date"] is not None:
        if actual_date == t["expect_date"]:
            print(f"  PASS  resolved_date = {actual_date} ✓")
        else:
            print(f"  FAIL  resolved_date: expected {t['expect_date']}, got {actual_date} ✗")
    else:
        print(f"  INFO  resolved_date: {actual_date!r}")

    print()
