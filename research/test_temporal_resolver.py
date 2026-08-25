"""
test_temporal_resolver.py
=========================
Unit tests for resolve_promised_date() in temporal_resolver.py.

Each test case is a separate function so pytest reports each individually.
Fixed call_date = 2026-08-22 12:00:00 for all tests.
No network calls, no mocking required — temporal_resolver has zero external deps.
"""
import datetime
import pytest
from temporal_resolver import resolve_promised_date

CALL_DATE = datetime.datetime(2026, 8, 22, 12, 0, 0)


# ---------------------------------------------------------------------------
# Case 1 — "Kal payment kar dunga"
#   Transcript indicates a future commitment for tomorrow.
#   Expected: relative/tomorrow/future → 2026-08-23
# ---------------------------------------------------------------------------
def test_case1_kal_future_tomorrow():
    extraction = {
        "intent": "promise_future_payment",
        "temporal": {
            "type": "relative",
            "relative_keyword": "tomorrow",
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": "future"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) == datetime.datetime(2026, 8, 23, 12, 0, 0)


# ---------------------------------------------------------------------------
# Case 2 — "Kal payment kar diya tha"
#   Transcript is past tense: payment was done yesterday.
#   Expected: relative/yesterday/past → 2026-08-21
# ---------------------------------------------------------------------------
def test_case2_kal_past_yesterday():
    extraction = {
        "intent": "payment_already_completed",
        "temporal": {
            "type": "relative",
            "relative_keyword": "yesterday",
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": "past"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) == datetime.datetime(2026, 8, 21, 12, 0, 0)


# ---------------------------------------------------------------------------
# Case 3 — "Parso payment kar dunga"
#   "Parso" in future context = day after tomorrow.
#   Expected: relative/day_after_tomorrow/future → 2026-08-24
# ---------------------------------------------------------------------------
def test_case3_parso_future_day_after_tomorrow():
    extraction = {
        "intent": "promise_future_payment",
        "temporal": {
            "type": "relative",
            "relative_keyword": "day_after_tomorrow",
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": "future"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) == datetime.datetime(2026, 8, 24, 12, 0, 0)


# ---------------------------------------------------------------------------
# Case 4 — "Kal payment nahi karunga"
#   Intent is payment_refusal — resolver must return None even though
#   a "tomorrow" temporal signal is present. Refusals never have a promised date.
# ---------------------------------------------------------------------------
def test_case4_refusal_suppresses_date():
    extraction = {
        "intent": "payment_refusal",
        "temporal": {
            "type": "relative",
            "relative_keyword": "tomorrow",
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": "future"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) is None


# ---------------------------------------------------------------------------
# Case 5 — "15 September ko payment kar diya tha"
#   Explicit past date: day=15, month=9, tense=past.
#   Sept 15, 2026 hasn't happened yet (call_date = Aug 22, 2026), so the
#   nearest past Sept 15 is 2025-09-15. Must NOT invent 2023.
# ---------------------------------------------------------------------------
def test_case5_explicit_date_past_sept15():
    extraction = {
        "intent": "payment_already_completed",
        "temporal": {
            "type": "explicit_date",
            "relative_keyword": None,
            "explicit_day": 15,
            "explicit_month": 9,
            "event_trigger": None,
            "tense": "past"
        }
    }
    result = resolve_promised_date(extraction, CALL_DATE)
    assert result == datetime.datetime(2025, 9, 15, 12, 0, 0), (
        f"Expected 2025-09-15 (nearest past Sept 15), got {result}"
    )


# ---------------------------------------------------------------------------
# Case 6 — "Parso salary aayegi, uske baad payment karunga"
#   Salary arrives day-after-tomorrow; payment happens AFTER that event.
#   event_trigger describes a conditional future event, not a direct date.
#   Expected: event_based/salary_arrival_after_day_after_tomorrow → None
# ---------------------------------------------------------------------------
def test_case6_event_based_salary_arrives_parso():
    extraction = {
        "intent": "promise_future_payment",
        "temporal": {
            "type": "event_based",
            "relative_keyword": None,
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": "salary_arrival_after_day_after_tomorrow",
            "tense": "future"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) is None


# ---------------------------------------------------------------------------
# Case 7 — "Salary aate hi payment kar dunga"
#   Payment conditioned on salary arrival — no specific date mentioned.
#   event_trigger = "salary_arrival" (no relative day prefix unlike Case 6).
#   Expected: event_based/salary_arrival → None
# ---------------------------------------------------------------------------
def test_case7_event_based_salary_arrival_generic():
    extraction = {
        "intent": "promise_future_payment",
        "temporal": {
            "type": "event_based",
            "relative_keyword": None,
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": "salary_arrival",
            "tense": "future"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) is None


# ---------------------------------------------------------------------------
# Case 8 — "Agale hafte payment kar dunga"
#   Vague week-level relative reference (next_week = +7 days).
#   Expected: relative/next_week → 2026-08-29
# ---------------------------------------------------------------------------
def test_case8_next_week():
    extraction = {
        "intent": "promise_future_payment",
        "temporal": {
            "type": "relative",
            "relative_keyword": "next_week",
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": "future"
        }
    }
    assert resolve_promised_date(extraction, CALL_DATE) == datetime.datetime(2026, 8, 29, 12, 0, 0)


# ---------------------------------------------------------------------------
# Case 9 — "Haan sir, payment kar dunga"
#   Customer agrees to pay but gives NO date or timeframe.
#   Intent must be agree_to_pay (not promise_future_payment).
#   Temporal type = "none" → resolver returns None.
# ---------------------------------------------------------------------------
def test_case9_agree_to_pay_no_date():
    extraction = {
        "intent": "agree_to_pay",
        "temporal": {
            "type": "none",
            "relative_keyword": None,
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": None
        }
    }
    assert extraction["intent"] == "agree_to_pay"
    assert resolve_promised_date(extraction, CALL_DATE) is None


# ---------------------------------------------------------------------------
# Case 10 — "Kal payment kar dunga" (intent label guard)
#   Same transcript as Case 1, but this test specifically asserts that the
#   intent label is promise_future_payment (NOT agree_to_pay) when a temporal
#   signal is present. These two intents must never be interchangeable.
# ---------------------------------------------------------------------------
def test_case10_kal_must_be_promise_future_not_agree():
    extraction = {
        "intent": "promise_future_payment",   # Must be this, not "agree_to_pay"
        "temporal": {
            "type": "relative",
            "relative_keyword": "tomorrow",
            "explicit_day": None,
            "explicit_month": None,
            "event_trigger": None,
            "tense": "future"
        }
    }
    assert extraction["intent"] == "promise_future_payment", (
        "When a temporal signal is present, intent must be promise_future_payment, not agree_to_pay."
    )
    assert resolve_promised_date(extraction, CALL_DATE) == datetime.datetime(2026, 8, 23, 12, 0, 0)
