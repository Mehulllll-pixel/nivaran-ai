"""
extraction.py
=============
Groq API call + extract_intent_and_promise().

This is now the canonical, more advanced version — hinglish-test's copy is intentionally frozen and not being kept in sync.
"""

import json
import datetime
from groq import Groq
from app.voice_pipeline.temporal_resolver import resolve_promised_date

MODEL_NAME = "openai/gpt-oss-20b"

TEMPORAL_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["relative", "explicit_date", "event_based", "vague_period", "none"]
        },
        "relative_keyword": {
            "type": ["string", "null"],
            "enum": ["tomorrow", "day_after_tomorrow", "yesterday",
                     "day_before_yesterday", "next_week", None]
        },
        "explicit_day": {"type": ["integer", "null"]},
        "explicit_month": {"type": ["integer", "null"]},
        "event_trigger": {"type": ["string", "null"]},
        "tense": {"type": ["string", "null"], "enum": ["past", "future", None]}
    },
    "required": ["type", "relative_keyword", "explicit_day", "explicit_month", "event_trigger", "tense"],
    "additionalProperties": False
}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "agree_to_pay", "promise_future_payment", "payment_already_completed",
                "asks_why", "cannot_pay", "payment_refusal", "dispute_amount",
                "wrong_number", "opt_out", "unclear"
            ]
        },
        "requests_no_contact": {"type": "boolean"},
        "sentiment": {"type": "string", "enum": ["neutral", "cooperative", "frustrated", "angry"]},
        "promised_amount": {"type": ["number", "null"]},
        "temporal": TEMPORAL_SCHEMA,
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "reasoning": {"type": "string"}
    },
    "required": ["intent", "requests_no_contact", "sentiment", "promised_amount", "temporal", "confidence", "reasoning"],
    "additionalProperties": False
}

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {"name": "payment_intent", "strict": True, "schema": EXTRACTION_SCHEMA}
}

SYSTEM_PROMPT = (
    "You are a payment-recovery intent extraction system.\n\n"
    "Understand the meaning of the customer's Hinglish statement using the full "
    "sentence and context. Pay special attention to verb tense and temporal context.\n\n"
    "The same word can refer to different temporal directions depending on context.\n"
    "For example:\n"
    "  - 'Parso payment kar dunga.' -> future payment commitment (relative).\n"
    "  - 'Parso hi payment kar diya tha.' -> payment completed in the past (relative).\n\n"
    "CRITICAL INSTRUCTIONS:\n"
    "1. NEVER output a resolved calendar date or invent a year. "
    "Only populate the categorical temporal fields.\n"
    "2. Differentiate intent strictly:\n"
    "   - 'agree_to_pay': commits to pay, NO date/timeframe.\n"
    "   - 'promise_future_payment': commits to a future point in time.\n"
    "   If any date or timeframe is present, intent MUST be 'promise_future_payment'.\n"
    "3. Do not perform calendar arithmetic — done by the calling system.\n"
    "4. event_trigger MUST be null unless temporal.type is exactly 'event_based'.\n"
    "5. Mixed-clause event sentences: leading inability + conditional event = "
    "temporal.type 'event_based', NOT 'relative'. Examples:\n"
    "  - 'Abhi payment nahi kar sakta, salary aane ke baad karunga.'\n"
    "  - 'Abhi mushkil hai, cheque clear hone ke baad dunga.'\n"
    "  - 'Is waqt nahi ho sakta, job milne ke baad karunga.'\n"
    "6. Partial/split payments: set promised_amount to only the immediate "
    "committed amount; describe remainder in reasoning.\n"
    "7. requests_no_contact is INDEPENDENT of intent — set it to true "
    "whenever the customer explicitly asks not to be contacted/called again "
    "(e.g. 'phone mat karo', 'dobara call mat karo', 'mujhe contact mat "
    "karo', 'don't call me'), regardless of what their payment intent is. "
    "This can be true even when intent is payment_refusal, "
    "promise_future_payment, or anything else — it's a separate signal about "
    "contact preference, not payment stance. Default to false if no such "
    "request is present.\n"
    "8. If the customer commits to paying but does not state a specific amount, "
    "assume it matches the amount they were called about (given in context) — "
    "unless they explicitly dispute or state a different amount."
)


def _build_user_message(transcript: str, amount_at_risk: float | None) -> str:
    if amount_at_risk is not None:
        return f"Amount the customer was called about: \u20b9{amount_at_risk}\nTranscript: \"{transcript}\""
    return transcript


def _call_groq_structured(transcript: str, amount_at_risk: float | None = None) -> tuple[dict, str]:
    client = Groq()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(transcript, amount_at_risk)}
        ],
        response_format=RESPONSE_FORMAT,
        temperature=0.0
    )
    raw = completion.choices[0].message.content
    return json.loads(raw), raw


def _call_groq_json_object(transcript: str, amount_at_risk: float | None = None) -> tuple[dict, str]:
    client = Groq()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + "\n\nRespond ONLY with a single JSON object matching the schema. No markdown fences, no extra text."},
            {"role": "user", "content": _build_user_message(transcript, amount_at_risk)}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    raw = completion.choices[0].message.content
    parsed = json.loads(raw)
    required_top = {"intent", "requests_no_contact", "sentiment", "promised_amount", "temporal", "confidence", "reasoning"}
    missing = required_top - parsed.keys()
    if missing:
        raise ValueError(f"json_object fallback response missing fields: {missing}")
    return parsed, raw


def extract_intent_and_promise(
    transcript: str,
    call_date: datetime.datetime,
    amount_at_risk: float | None = None,
) -> dict:
    fallback_mode = False
    raw_response = ""

    try:
        extraction, raw_response = _call_groq_structured(transcript, amount_at_risk=amount_at_risk)
    except Exception as strict_err:
        print(f"[extraction.py] Strict json_schema mode failed: {strict_err}")
        print("[extraction.py] Falling back to json_object mode.")
        fallback_mode = True
        extraction, raw_response = _call_groq_json_object(transcript, amount_at_risk=amount_at_risk)

    resolved_date = resolve_promised_date(extraction, call_date)

    return {
        "extraction": extraction,
        "raw_response": raw_response,
        "resolved_promised_date": resolved_date,
        "fallback_mode": fallback_mode
    }
