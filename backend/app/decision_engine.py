"""
Decision engine: diagnose -> decide.

Deliberately rule-based and inspectable rather than a black-box LLM call —
judges (and you, debugging at 2am) need to be able to see exactly why an
action was chosen. Swap in an LLM classifier later ONLY for the ambiguous
cases that fall through to UNKNOWN, if time allows.
"""
from app.models import EventType, RootCause, ActionType


# --- Stage 1: classify root cause from the raw signal -----------------------

# In a real system this raw_reason_code comes from the payment gateway.
# Map the common Razorpay-style gateway codes/keywords to a root cause.
REASON_CODE_MAP = {
    "timeout": RootCause.BANK_TIMEOUT,
    "gateway_timeout": RootCause.BANK_TIMEOUT,
    "insufficient_funds": RootCause.INSUFFICIENT_FUNDS,
    "otp_mismatch": RootCause.OTP_FAILED,
    "otp_expired": RootCause.OTP_FAILED,
    "card_expired": RootCause.CARD_EXPIRED,
}


def classify_root_cause(event_type: EventType, raw_reason_code: str | None) -> RootCause:
    if event_type == EventType.CHECKOUT_ABANDONED:
        return RootCause.USER_ABANDONED
    if event_type == EventType.INVOICE_OVERDUE:
        return RootCause.INVOICE_UNPAID
    if raw_reason_code:
        key = raw_reason_code.strip().lower()
        if key in REASON_CODE_MAP:
            return REASON_CODE_MAP[key]
    return RootCause.UNKNOWN


# --- Stage 2: decision table (cause -> action), with stopping rules ---------

# Max attempts allowed per root cause before the agent stops and (optionally)
# escalates to a human. This is the compliance/anti-spam guardrail.
MAX_ATTEMPTS = {
    RootCause.BANK_TIMEOUT: 3,
    RootCause.INSUFFICIENT_FUNDS: 2,
    RootCause.OTP_FAILED: 2,
    RootCause.CARD_EXPIRED: 1,  # retrying won't help — go straight to a new payment link, once
    RootCause.USER_ABANDONED: 2,
    RootCause.INVOICE_UNPAID: 4,  # receivables get a longer, escalating cadence
    RootCause.UNKNOWN: 1,
}

# What to do on a given attempt number for a given root cause.
# Falls back to ESCALATE_HUMAN if attempt_number exceeds what's defined here.
ACTION_SEQUENCE = {
    RootCause.BANK_TIMEOUT: {
        1: ActionType.AUTO_RETRY,
        2: ActionType.AUTO_RETRY,
        3: ActionType.SMS_NUDGE,
    },
    RootCause.INSUFFICIENT_FUNDS: {
        1: ActionType.SMS_NUDGE,
        2: ActionType.VOICE_CALL_HINGLISH,
    },
    RootCause.OTP_FAILED: {
        1: ActionType.AUTO_RETRY,
        2: ActionType.SMS_NUDGE,
    },
    RootCause.CARD_EXPIRED: {
        1: ActionType.NEW_PAYMENT_LINK,
    },
    RootCause.USER_ABANDONED: {
        1: ActionType.WHATSAPP_NUDGE,
        2: ActionType.VOICE_CALL_HINGLISH,
    },
    RootCause.INVOICE_UNPAID: {
        1: ActionType.INVOICE_REMINDER,
        2: ActionType.INVOICE_REMINDER,
        3: ActionType.VOICE_CALL_HINGLISH,
        4: ActionType.ESCALATE_HUMAN,
    },
    RootCause.UNKNOWN: {
        1: ActionType.ESCALATE_HUMAN,
    },
}


def decide_action(root_cause: RootCause, attempt_number: int) -> tuple[ActionType, str]:
    """
    Returns (chosen_action, human_readable_reasoning).
    Enforces the stopping rule: if attempt_number exceeds MAX_ATTEMPTS,
    the agent stops rather than escalating indefinitely.
    """
    max_attempts = MAX_ATTEMPTS.get(root_cause, 1)

    if attempt_number > max_attempts:
        return (
            ActionType.STOPPED,
            f"Stopping rule triggered: {attempt_number - 1} attempts already made "
            f"for root cause '{root_cause.value}' (max allowed: {max_attempts}). "
            f"No further automated contact.",
        )

    sequence = ACTION_SEQUENCE.get(root_cause, {})
    action = sequence.get(attempt_number, ActionType.ESCALATE_HUMAN)

    reasoning = (
        f"Root cause classified as '{root_cause.value}'. "
        f"This is attempt {attempt_number} of {max_attempts} allowed. "
        f"Decision table maps this to '{action.value}'."
    )
    return action, reasoning
