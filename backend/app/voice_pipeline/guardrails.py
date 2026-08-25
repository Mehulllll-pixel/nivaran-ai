"""
guardrails.py
=============
Business/recovery action logic.
"""

EVENT_FOLLOW_UP_DELAY_DAYS: int = 3
RECONCILIATION_FLAG: str = "RECONCILE"


def determine_recovery_action(extraction_result: dict) -> dict:
    extraction = extraction_result.get("extraction", {})
    resolved_date = extraction_result.get("resolved_promised_date")

    intent = extraction.get("intent", "unclear")
    temporal = extraction.get("temporal", {})
    temp_type = temporal.get("type", "none")

    action_plan = {
        "action": "schedule_follow_up",
        "target_date": resolved_date,
        "compliance_block": False,
        "escalate_to_human": False,
        "reconciliation_required": False,
        "generic_follow_up": False,
        "follow_up_delay_days": None,
        "reasoning": extraction.get("reasoning", "")
    }

    # Compliance short-circuit override
    if extraction.get("requests_no_contact") is True:
        action_plan["action"] = "stop_channel_contact"
        action_plan["target_date"] = None
        action_plan["compliance_block"] = True
        return action_plan

    if intent == "payment_already_completed":
        action_plan["action"] = "reconcile_payment"
        action_plan["target_date"] = None
        action_plan["reconciliation_required"] = True

    elif intent in ("wrong_number", "opt_out"):
        action_plan["action"] = "stop_channel_contact"
        action_plan["target_date"] = None
        action_plan["compliance_block"] = True

    elif intent == "dispute_amount":
        action_plan["action"] = "escalate_dispute"
        action_plan["target_date"] = None
        action_plan["escalate_to_human"] = True

    elif temp_type == "event_based":
        action_plan["action"] = "generic_event_follow_up"
        action_plan["target_date"] = None
        action_plan["generic_follow_up"] = True
        action_plan["follow_up_delay_days"] = EVENT_FOLLOW_UP_DELAY_DAYS

    return action_plan
