import pytest
from app.guardrail_mapping import map_guardrail_action
from app.models import ActionType, OutcomeStatus
from app.voice_pipeline.guardrails import determine_recovery_action

def test_schedule_follow_up():
    action, status = map_guardrail_action("schedule_follow_up")
    assert action == ActionType.VOICE_CALL_HINGLISH
    assert status == OutcomeStatus.PENDING

def test_reconcile_payment():
    action, status = map_guardrail_action("reconcile_payment")
    assert action == ActionType.VOICE_CALL_HINGLISH
    assert status == OutcomeStatus.PENDING

def test_stop_channel_contact():
    action, status = map_guardrail_action("stop_channel_contact")
    assert action == ActionType.STOPPED
    assert status == OutcomeStatus.STOPPED

def test_escalate_dispute():
    action, status = map_guardrail_action("escalate_dispute")
    assert action == ActionType.ESCALATE_HUMAN
    assert status == OutcomeStatus.PENDING

def test_generic_event_follow_up():
    action, status = map_guardrail_action("generic_event_follow_up")
    assert action == ActionType.VOICE_CALL_HINGLISH
    assert status == OutcomeStatus.PENDING

def test_unknown_action_raises_error():
    with pytest.raises(ValueError) as excinfo:
        map_guardrail_action("some_unknown_action_string")
    assert "Unrecognized guardrail action" in str(excinfo.value)

# New Guardrail Action Logic Tests:
def test_guardrail_no_contact_with_refusal():
    # 1. requests_no_contact=True with intent=payment_refusal -> stop_channel_contact
    extraction_result = {
        "extraction": {
            "intent": "payment_refusal",
            "requests_no_contact": True,
            "sentiment": "frustrated",
            "promised_amount": None,
            "temporal": {"type": "none"},
            "confidence": "high",
            "reasoning": "User refused to pay and requested no calls."
        },
        "resolved_promised_date": None
    }
    action_plan = determine_recovery_action(extraction_result)
    assert action_plan["action"] == "stop_channel_contact"
    assert action_plan["compliance_block"] is True
    assert action_plan["target_date"] is None

def test_guardrail_no_contact_with_promise():
    # 2. requests_no_contact=True with intent=promise_future_payment -> stop_channel_contact
    extraction_result = {
        "extraction": {
            "intent": "promise_future_payment",
            "requests_no_contact": True,
            "sentiment": "neutral",
            "promised_amount": 5000,
            "temporal": {"type": "relative", "relative_keyword": "tomorrow"},
            "confidence": "high",
            "reasoning": "User promised to pay but asked not to be called again."
        },
        "resolved_promised_date": None
    }
    action_plan = determine_recovery_action(extraction_result)
    assert action_plan["action"] == "stop_channel_contact"
    assert action_plan["compliance_block"] is True
    assert action_plan["target_date"] is None

def test_guardrail_plain_refusal_gets_follow_up():
    # 3. requests_no_contact=False with intent=payment_refusal -> schedule_follow_up
    extraction_result = {
        "extraction": {
            "intent": "payment_refusal",
            "requests_no_contact": False,
            "sentiment": "frustrated",
            "promised_amount": None,
            "temporal": {"type": "none"},
            "confidence": "high",
            "reasoning": "User refused to pay but did not ask to stop calls."
        },
        "resolved_promised_date": None
    }
    action_plan = determine_recovery_action(extraction_result)
    assert action_plan["action"] == "schedule_follow_up"
    assert action_plan["compliance_block"] is False
