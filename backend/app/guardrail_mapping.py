from app.models import ActionType, OutcomeStatus

# Mapping dictionary for guardrail actions
_MAPPING = {
    "schedule_follow_up": (ActionType.VOICE_CALL_HINGLISH, OutcomeStatus.PENDING),
    "reconcile_payment": (ActionType.VOICE_CALL_HINGLISH, OutcomeStatus.PENDING),
    "stop_channel_contact": (ActionType.STOPPED, OutcomeStatus.STOPPED),
    "escalate_dispute": (ActionType.ESCALATE_HUMAN, OutcomeStatus.PENDING),
    "generic_event_follow_up": (ActionType.VOICE_CALL_HINGLISH, OutcomeStatus.PENDING),
}


def map_guardrail_action(guardrail_action: str) -> tuple[ActionType, OutcomeStatus]:
    """
    Maps a voice pipeline's guardrail action string to a tuple of (ActionType, OutcomeStatus).
    Raises ValueError if the guardrail_action is unrecognized.
    """
    if guardrail_action not in _MAPPING:
        raise ValueError(f"Unrecognized guardrail action: {guardrail_action}")
    return _MAPPING[guardrail_action]