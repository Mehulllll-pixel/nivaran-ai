"""
Action executors.

Each function simulates executing one intervention and returns
(success: bool, amount_recovered: float, channel_ref: str, notes: str).

These are mocked with realistic-ish success rates so your batch demo
produces a believable recovered-₹ number. Swap in real SMS/WhatsApp/
telephony APIs here when you have keys — the interface stays the same.
"""
import random
import uuid


def _ref():
    return str(uuid.uuid4())[:8]


def execute_auto_retry(amount: float) -> tuple[bool, float, str, str]:
    success = random.random() < 0.45  # ~45% of retries succeed
    recovered = amount if success else 0.0
    return success, recovered, _ref(), "Simulated auto-retry via payment gateway."


def execute_sms_nudge(amount: float) -> tuple[bool, float, str, str]:
    success = random.random() < 0.25
    recovered = amount if success else 0.0
    return success, recovered, _ref(), "Simulated SMS nudge with retry link."


def execute_whatsapp_nudge(amount: float) -> tuple[bool, float, str, str]:
    success = random.random() < 0.30
    recovered = amount if success else 0.0
    return success, recovered, _ref(), "Simulated WhatsApp nudge with retry link."


def execute_voice_call_hinglish(
    amount: float,
    root_cause: str = "unknown",
    customer_response_audio_path: str | None = None,
    transcript: str = "5000 rupaye kal de dunga",
) -> tuple[bool, float, str, str]:
    """
    Real Hinglish voice recovery call, using the pipeline in voice_pipeline package:
      1. Pick an opening script based on root cause
      2. Extract intent + promise-to-pay via Groq
      3. Apply guardrails and log the outcome
    """
    import datetime
    from app.voice_pipeline import get_opening_script
    from app.voice_pipeline.extraction import extract_intent_and_promise
    from app.voice_pipeline.guardrails import determine_recovery_action
    from app.guardrail_mapping import map_guardrail_action
    from app.models import ActionType, OutcomeStatus

    opening = get_opening_script(root_cause)

    # Perform extraction using the transcript
    extraction_result = extract_intent_and_promise(
        transcript, datetime.datetime.utcnow(), amount_at_risk=amount
    )
    
    # Determine recovery action plan
    action_plan = determine_recovery_action(extraction_result)

    # Map the guardrail action string to ActionType and OutcomeStatus enums
    action_type, outcome_status = map_guardrail_action(action_plan["action"])

    # Success is True if the OutcomeStatus is PENDING or RECOVERED
    success = outcome_status in (OutcomeStatus.PENDING, OutcomeStatus.RECOVERED)

    # Recovered amount logic:
    # If promised_amount is not null AND the guardrail action is schedule_follow_up -> recovered = promised_amount
    # In all other cases -> recovered = 0.0
    extraction = extraction_result.get("extraction", {})
    promised_amount = extraction.get("promised_amount")
    
    if promised_amount is not None and action_plan["action"] == "schedule_follow_up":
        recovered = float(promised_amount)
    else:
        recovered = 0.0

    resolved_date = extraction_result.get("resolved_promised_date")
    promised_date_str = resolved_date.isoformat() if resolved_date else "None"
    promised_amount_val = promised_amount if promised_amount is not None else "None"
    intent = extraction.get("intent", "unclear")
    confidence = extraction.get("confidence", "low")
    guardrail_reasoning = action_plan.get("reasoning", "")

    notes = (
        f"Opening: '{opening}' | Transcript: '{transcript}' | "
        f"Intent: {intent} | Promised: ₹{promised_amount_val} by {promised_date_str} | "
        f"Confidence: {confidence} | Reasoning: {guardrail_reasoning} | "
        f"ActionType: {action_type.value} | OutcomeStatus: {outcome_status.value}"
    )

    return success, recovered, _ref(), notes


def execute_new_payment_link(amount: float) -> tuple[bool, float, str, str]:
    success = random.random() < 0.40
    recovered = amount if success else 0.0
    return success, recovered, _ref(), "Simulated new payment link generated and sent."


def execute_invoice_reminder(amount: float) -> tuple[bool, float, str, str]:
    success = random.random() < 0.20
    recovered = amount if success else 0.0
    return success, recovered, _ref(), "Simulated invoice reminder email sent."


def execute_escalate_human(amount: float) -> tuple[bool, float, str, str]:
    # Escalation itself doesn't recover money immediately — outcome is PENDING.
    return False, 0.0, _ref(), "Escalated to human agent for manual follow-up."


EXECUTOR_MAP = {
    "auto_retry": execute_auto_retry,
    "sms_nudge": execute_sms_nudge,
    "whatsapp_nudge": execute_whatsapp_nudge,
    "voice_call_hinglish": execute_voice_call_hinglish,
    "new_payment_link": execute_new_payment_link,
    "invoice_reminder": execute_invoice_reminder,
    "escalate_human": execute_escalate_human,
}
