"""
test_transcript_diversity.py
============================
Runs 5 distinct Hinglish transcripts (one per scenario) through
execute_voice_call_hinglish() and prints the full per-case output so
we can verify each produces genuinely different intent/action/outcome.
"""
import re
import pytest
from dotenv import load_dotenv
load_dotenv()

from app.executors import execute_voice_call_hinglish
from app.models import ActionType, OutcomeStatus

# Five transcripts chosen to cover deliberately different intent paths.
TEST_CASES = [
    {
        "label": "clean promise (amount + date)",
        "transcript": "5000 rupaye kal tak de dunga, pakka.",
        "root_cause": "insufficient_funds",
    },
    {
        "label": "event-based promise (salary)",
        "transcript": "Salary aane ke baad payment karunga, do-teen din mein aa jayegi.",
        "root_cause": "insufficient_funds",
    },
    {
        "label": "refusal + explicit no-contact",
        "transcript": "Main paise nahi dunga, dobara phone mat karna mujhe.",
        "root_cause": "bank_timeout",
    },
    {
        "label": "payment already completed",
        "transcript": "Maine kal hi payment kar diya tha NEFT se, apna account check karo.",
        "root_cause": "bank_timeout",
    },
    {
        "label": "dispute on amount",
        "transcript": "Yeh amount galat hai, mujhe itna nahi dena tha, invoice dekho.",
        "root_cause": "invoice_unpaid",
    },
]


def parse_field(notes: str, field: str) -> str:
    m = re.search(rf"{field}: ([^\|]+)", notes)
    return m.group(1).strip() if m else "unknown"


@pytest.mark.parametrize("case", TEST_CASES, ids=[c["label"] for c in TEST_CASES])
def test_per_transcript_outcome(case):
    success, recovered, channel_ref, notes = execute_voice_call_hinglish(
        amount=10000.0,
        transcript=case["transcript"],
        root_cause=case["root_cause"],
    )
    intent      = parse_field(notes, "Intent")
    action_type = parse_field(notes, "ActionType")
    outcome_st  = parse_field(notes, "OutcomeStatus")

    print(f"\n[{case['label']}]")
    print(f"  Transcript    : {case['transcript']}")
    print(f"  Intent        : {intent}")
    print(f"  ActionType    : {action_type}")
    print(f"  OutcomeStatus : {outcome_st}")
    print(f"  Success       : {success}")
    print(f"  Recovered     : {recovered}")

    # Basic sanity: fields must resolve to known enum values
    assert action_type in {e.value for e in ActionType}, \
        f"Unexpected ActionType '{action_type}'"
    assert outcome_st in {e.value for e in OutcomeStatus}, \
        f"Unexpected OutcomeStatus '{outcome_st}'"
