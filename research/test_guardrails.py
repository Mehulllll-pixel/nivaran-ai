"""
test_guardrails.py
==================
Unit tests for determine_recovery_action() in guardrails.py.

No Groq calls, no mocking — guardrails.py takes plain dicts as input.
"""
import datetime
import pytest
from guardrails import determine_recovery_action, EVENT_FOLLOW_UP_DELAY_DAYS


def _make_input(intent: str, temporal_type: str = "none",
                resolved_date=None, reasoning: str = "test") -> dict:
    """Helper to build a minimal extraction_result dict."""
    return {
        "extraction": {
            "intent": intent,
            "sentiment": "neutral",
            "promised_amount": None,
            "temporal": {
                "type": temporal_type,
                "relative_keyword": None,
                "explicit_day": None,
                "explicit_month": None,
                "event_trigger": "salary_arrival" if temporal_type == "event_based" else None,
                "tense": None
            },
            "confidence": "high",
            "reasoning": reasoning
        },
        "resolved_promised_date": resolved_date,
        "raw_response": "{}",
        "fallback_mode": False
    }


# ---------------------------------------------------------------------------
# 1. payment_already_completed
#    Must NOT schedule further contact.
#    Must set reconciliation_required=True and target_date=None.
# ---------------------------------------------------------------------------
def test_payment_already_completed_sets_reconciliation():
    inp = _make_input("payment_already_completed", "relative",
                      resolved_date=datetime.datetime(2026, 8, 21, 12, 0, 0))
    action = determine_recovery_action(inp)

    assert action["reconciliation_required"] is True
    assert action["target_date"] is None, (
        "payment_already_completed must NOT carry a target_date forward"
    )
    assert action["compliance_block"] is False
    assert action["escalate_to_human"] is False
    assert action["generic_follow_up"] is False
    assert action["action"] == "reconcile_payment"


# ---------------------------------------------------------------------------
# 2. wrong_number
#    Compliance issue — must stop all contact on this channel.
#    Same priority as opt_out.
# ---------------------------------------------------------------------------
def test_wrong_number_sets_compliance_block():
    inp = _make_input("wrong_number")
    action = determine_recovery_action(inp)

    assert action["compliance_block"] is True
    assert action["target_date"] is None
    assert action["reconciliation_required"] is False
    assert action["escalate_to_human"] is False
    assert action["generic_follow_up"] is False
    assert action["action"] == "stop_channel_contact"


# ---------------------------------------------------------------------------
# 3. opt_out
#    Same compliance priority as wrong_number.
# ---------------------------------------------------------------------------
def test_opt_out_sets_compliance_block():
    inp = _make_input("opt_out")
    action = determine_recovery_action(inp)

    assert action["compliance_block"] is True
    assert action["target_date"] is None
    assert action["reconciliation_required"] is False
    assert action["escalate_to_human"] is False
    assert action["action"] == "stop_channel_contact"


# ---------------------------------------------------------------------------
# 4. dispute_amount
#    Must NOT log a promise-to-pay.
#    Must escalate to human; target_date must be None.
# ---------------------------------------------------------------------------
def test_dispute_amount_escalates_to_human():
    inp = _make_input("dispute_amount")
    action = determine_recovery_action(inp)

    assert action["escalate_to_human"] is True
    assert action["target_date"] is None
    assert action["compliance_block"] is False
    assert action["reconciliation_required"] is False
    assert action["generic_follow_up"] is False
    assert action["action"] == "escalate_dispute"


# ---------------------------------------------------------------------------
# 5. event_based temporal type
#    resolve_promised_date() already returns None for event_based.
#    Guardrails must flag generic_follow_up=True and use the
#    named constant EVENT_FOLLOW_UP_DELAY_DAYS (currently 3).
# ---------------------------------------------------------------------------
def test_event_based_sets_generic_follow_up():
    inp = _make_input("promise_future_payment", temporal_type="event_based",
                      resolved_date=None)
    action = determine_recovery_action(inp)

    assert action["generic_follow_up"] is True
    assert action["follow_up_delay_days"] == EVENT_FOLLOW_UP_DELAY_DAYS
    assert action["follow_up_delay_days"] == 3  # pin the current value explicitly
    assert action["target_date"] is None
    assert action["compliance_block"] is False
    assert action["escalate_to_human"] is False
    assert action["reconciliation_required"] is False
    assert action["action"] == "generic_event_follow_up"


# ---------------------------------------------------------------------------
# 6. Normal promise_future_payment with a resolved date
#    Should fall through all guardrails and schedule a standard follow-up.
# ---------------------------------------------------------------------------
def test_promise_future_schedules_follow_up():
    target = datetime.datetime(2026, 8, 23, 12, 0, 0)
    inp = _make_input("promise_future_payment", temporal_type="relative",
                      resolved_date=target)
    action = determine_recovery_action(inp)

    assert action["action"] == "schedule_follow_up"
    assert action["target_date"] == target
    assert action["compliance_block"] is False
    assert action["escalate_to_human"] is False
    assert action["reconciliation_required"] is False
    assert action["generic_follow_up"] is False


# ---------------------------------------------------------------------------
# 7. Reasoning is echoed through to the action plan for traceability.
# ---------------------------------------------------------------------------
def test_reasoning_is_echoed():
    inp = _make_input("unclear", reasoning="Customer was ambiguous.")
    action = determine_recovery_action(inp)
    assert action["reasoning"] == "Customer was ambiguous."
