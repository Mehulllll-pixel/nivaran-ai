"""
guardrails.py
=============
Business/recovery action logic (Task 5).

Responsibilities:
  - Inspect the output of extract_intent_and_promise() and decide what action to take
  - Apply compliance guardrails for wrong_number, opt_out, dispute_amount, etc.
  - Flag event_based temporal cases for generic follow-up with a configurable delay

What this file does NOT do:
  - No Groq API calls
  - No date arithmetic (that lives in temporal_resolver.py)
  - No LLM prompting
"""

# ---------------------------------------------------------------------------
# Named, configurable constants — NOT hardcoded inside the date resolver
# ---------------------------------------------------------------------------
EVENT_FOLLOW_UP_DELAY_DAYS: int = 3      # Days to wait before following up on event-based promises
RECONCILIATION_FLAG: str = "RECONCILE"  # Flag label for payment_already_completed events


def determine_recovery_action(extraction_result: dict) -> dict:
    """
    Apply business guardrails to decide the next recovery action.

    Parameters
    ----------
    extraction_result : dict
        The dict returned by extract_intent_and_promise(), which contains:
          - "extraction"            : raw LLM dict
          - "resolved_promised_date": datetime | None
          - "raw_response"          : str
          - "fallback_mode"         : bool

    Returns
    -------
    dict with keys:
      - action             : str   — the action label
      - target_date        : datetime | None — when to follow up (if applicable)
      - compliance_block   : bool  — True means stop all contact on this channel
      - escalate_to_human  : bool  — True means route to a human agent
      - reconciliation_required : bool — True means cross-check payment records
      - generic_follow_up  : bool  — True means schedule a non-date-specific retry
      - follow_up_delay_days : int | None — delay days for generic follow-ups
      - reasoning          : str   — echoes LLM reasoning for traceability
    """
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

    # Guardrail 1 — Payment already completed
    # Do NOT schedule further contact; flag for reconciliation against actual records.
    if intent == "payment_already_completed":
        action_plan["action"] = "reconcile_payment"
        action_plan["target_date"] = None
        action_plan["reconciliation_required"] = True

    # Guardrail 2 — Wrong number or opt-out
    # Immediately stop ALL further attempts on this contact channel.
    # Compliance priority, same as opt_out.
    elif intent in ("wrong_number", "opt_out"):
        action_plan["action"] = "stop_channel_contact"
        action_plan["target_date"] = None
        action_plan["compliance_block"] = True

    # Guardrail 3 — Disputed amount
    # Do not log a promise-to-pay; escalate to a human agent.
    elif intent == "dispute_amount":
        action_plan["action"] = "escalate_dispute"
        action_plan["target_date"] = None
        action_plan["escalate_to_human"] = True

    # Guardrail 4 — Event-based temporal (salary arrival, etc.)
    # resolve_promised_date() already returned None for this case (see temporal_resolver.py).
    # Here we flag it for a generic follow-up after a configurable delay.
    elif temp_type == "event_based":
        action_plan["action"] = "generic_event_follow_up"
        action_plan["target_date"] = None
        action_plan["generic_follow_up"] = True
        action_plan["follow_up_delay_days"] = EVENT_FOLLOW_UP_DELAY_DAYS

    return action_plan
