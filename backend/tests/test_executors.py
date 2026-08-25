import pytest
import re
from dotenv import load_dotenv
load_dotenv()

from app.executors import execute_voice_call_hinglish
from app.models import ActionType, OutcomeStatus

def parse_action_and_status(notes: str) -> tuple[str, str]:
    at_match = re.search(r"ActionType: ([a-zA-Z_]+)", notes)
    os_match = re.search(r"OutcomeStatus: ([a-zA-Z_]+)", notes)
    at = at_match.group(1) if at_match else "unknown"
    os = os_match.group(1) if os_match else "unknown"
    return at, os

def test_clean_promise():
    success, recovered, channel_ref, notes = execute_voice_call_hinglish(
        amount=10000.0,
        transcript="5000 rupaye kal de dunga",
        root_cause="bank_timeout"
    )
    at, os = parse_action_and_status(notes)
    print("\n[TEST clean promise] Result:")
    print(f"  Success: {success}")
    print(f"  Recovered: {recovered}")
    print(f"  ActionType: {at}")
    print(f"  OutcomeStatus: {os}")
    print(f"  Notes: {notes}")
    
    assert success is True
    assert recovered == 5000.0
    assert "Promised: ₹5000" in notes
    assert at == ActionType.VOICE_CALL_HINGLISH.value
    assert os == OutcomeStatus.PENDING.value

def test_refusal():
    # Transcript: "Main paise nahi dunga, phone mat karo"
    success, recovered, channel_ref, notes = execute_voice_call_hinglish(
        amount=10000.0,
        transcript="Main paise nahi dunga, phone mat karo",
        root_cause="insufficient_funds"
    )
    at, os = parse_action_and_status(notes)
    print("\n[TEST refusal] Result:")
    print(f"  Success: {success}")
    print(f"  Recovered: {recovered}")
    print(f"  ActionType: {at}")
    print(f"  OutcomeStatus: {os}")
    print(f"  Notes: {notes}")
    
    import re
    intent_match = re.search(r"Intent: ([a-zA-Z_]+)", notes)
    intent = intent_match.group(1) if intent_match else "unknown"
    print(f"  --> CLASSIFIED INTENT: {intent}")
    
    # Assertions requested by user for the refusal case
    assert at == ActionType.STOPPED.value
    assert os == OutcomeStatus.STOPPED.value
    assert success is False
    assert recovered == 0.0

def test_event_based_promise():
    success, recovered, channel_ref, notes = execute_voice_call_hinglish(
        amount=10000.0,
        transcript="Salary aane ke baad payment karunga",
        root_cause="user_abandoned"
    )
    at, os = parse_action_and_status(notes)
    print("\n[TEST event-based] Result:")
    print(f"  Success: {success}")
    print(f"  Recovered: {recovered}")
    print(f"  ActionType: {at}")
    print(f"  OutcomeStatus: {os}")
    print(f"  Notes: {notes}")
    
    assert success is True
    assert recovered == 0.0
    assert at == ActionType.VOICE_CALL_HINGLISH.value
    assert os == OutcomeStatus.PENDING.value
