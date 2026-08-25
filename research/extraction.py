"""
extraction.py
=============
Groq API call + extract_intent_and_promise() (Task 1 + Task 4).

Responsibilities:
  - Build the strict JSON schema for structured outputs
  - Craft the system prompt instructing the LLM on language/tense understanding
  - Call Groq and return the raw extraction
  - Import resolve_promised_date from temporal_resolver and combine both outputs

What this file does NOT do:
  - No date arithmetic (that lives in temporal_resolver.py)
  - No business/scheduling guardrails (that lives in guardrails.py)
"""

import json
import datetime
from groq import Groq
from temporal_resolver import resolve_promised_date

MODEL_NAME = "openai/gpt-oss-20b"

# ---------------------------------------------------------------------------
# JSON Schema for Groq Structured Outputs
# ---------------------------------------------------------------------------
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
        "explicit_day": {
            "type": ["integer", "null"]
        },
        "explicit_month": {
            "type": ["integer", "null"]
        },
        "event_trigger": {
            "type": ["string", "null"]
        },
        "tense": {
            "type": ["string", "null"],
            "enum": ["past", "future", None]
        }
    },
    "required": [
        "type", "relative_keyword", "explicit_day", "explicit_month",
        "event_trigger", "tense"
    ],
    "additionalProperties": False
}

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "agree_to_pay",
                "promise_future_payment",
                "payment_already_completed",
                "asks_why",
                "cannot_pay",
                "payment_refusal",
                "dispute_amount",
                "wrong_number",
                "opt_out",
                "unclear"
            ]
        },
        "sentiment": {
            "type": "string",
            "enum": ["neutral", "cooperative", "frustrated", "angry"]
        },
        "promised_amount": {
            "type": ["number", "null"]
        },
        "temporal": TEMPORAL_SCHEMA,
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"]
        },
        "reasoning": {
            "type": "string"
        }
    },
    "required": [
        "intent", "sentiment", "promised_amount", "temporal", "confidence", "reasoning"
    ],
    "additionalProperties": False
}

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "payment_intent",
        "strict": True,
        "schema": EXTRACTION_SCHEMA
    }
}

SYSTEM_PROMPT = (
    "You are a payment-recovery intent extraction system.\n\n"
    "Understand the meaning of the customer's Hinglish statement using the full "
    "sentence and context. Pay special attention to verb tense and temporal context.\n\n"
    "The same word can refer to different temporal directions depending on context.\n"
    "For example:\n"
    "  - 'Parso payment kar dunga.' → future payment commitment (relative).\n"
    "  - 'Parso hi payment kar diya tha.' → payment completed in the past (relative).\n\n"
    "CRITICAL INSTRUCTIONS:\n"
    "1. NEVER output a resolved calendar date or invent a year. "
    "Only populate the categorical temporal fields (type, relative_keyword, "
    "explicit_day, explicit_month, event_trigger, tense).\n"
    "2. Differentiate intent strictly:\n"
    "   - 'agree_to_pay': customer commits to pay but gives NO date or timeframe "
    "(e.g. 'haan sir, payment kar dunga', 'theek hai, kar dunga').\n"
    "   - 'promise_future_payment': customer explicitly commits to a future point "
    "in time (e.g. 'kal payment kar dunga', 'agle hafte kar dunga').\n"
    "   If any date or timeframe is present in the temporal structure, the intent "
    "MUST be 'promise_future_payment', never 'agree_to_pay'.\n"
    "3. Do not perform calendar arithmetic — that is done by the calling system.\n"
    "4. event_trigger MUST be null unless temporal.type is exactly 'event_based'. "
    "Never populate event_trigger for any other temporal type, even if there is "
    "leftover, ambiguous, or garbled text in the transcript. "
    "If temporal.type is 'relative', 'explicit_date', 'vague_period', or 'none', "
    "set event_trigger to null unconditionally.\n"
    "5. Mixed-clause event sentences: if a sentence contains BOTH a leading "
    "inability or delay ('abhi nahi kar sakta', 'abhi mushkil hai', etc.) AND a "
    "conditional future commitment tied to a real-world event (salary arrival, "
    "cheque clearing, job start, bonus, etc.), classify temporal.type as "
    "'event_based' — NOT 'relative'. The event condition governs the temporal "
    "classification, not the leading inability clause. "
    "Examples that MUST be event_based:\n"
    "  - 'Abhi payment nahi kar sakta, salary aane ke baad karunga.'\n"
    "  - 'Abhi mushkil hai, cheque clear hone ke baad dunga.'\n"
    "  - 'Is waqt nahi ho sakta, job milne ke baad karunga.'\n"
    "6. Partial or split payments: if the customer offers a partial amount now "
    "and promises the remainder later, set promised_amount to only the immediate "
    "committed amount (the one being offered right now). Describe the remainder "
    "and its timeframe in the reasoning field. Do not set promised_amount to null "
    "just because a second installment exists."
)


def _call_groq_structured(transcript: str) -> tuple[dict, str]:
    """
    Attempt Groq call using strict json_schema response_format.
    Returns (parsed_dict, raw_response_string).
    Raises on API error so the caller can fall back if needed.
    """
    client = Groq()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": transcript}
        ],
        response_format=RESPONSE_FORMAT,
        temperature=0.0
    )
    raw = completion.choices[0].message.content
    return json.loads(raw), raw


def _call_groq_json_object(transcript: str) -> tuple[dict, str]:
    """
    Fallback: use json_object response mode and validate manually.
    Returns (parsed_dict, raw_response_string).
    """
    client = Groq()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    SYSTEM_PROMPT
                    + "\n\nRespond ONLY with a single JSON object matching the schema. "
                    "No markdown fences, no extra text."
                )
            },
            {"role": "user", "content": transcript}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    raw = completion.choices[0].message.content
    parsed = json.loads(raw)
    # Minimal field presence validation
    required_top = {"intent", "sentiment", "promised_amount", "temporal", "confidence", "reasoning"}
    missing = required_top - parsed.keys()
    if missing:
        raise ValueError(f"json_object fallback response missing fields: {missing}")
    return parsed, raw


def extract_intent_and_promise(
    transcript: str,
    call_date: datetime.datetime
) -> dict:
    """
    Extract customer intent and temporal reference via Groq, then resolve the
    promised date deterministically.

    Returns:
    {
        "extraction": <raw LLM dict>,
        "raw_response": <raw JSON string from model>,
        "resolved_promised_date": <datetime or None>,
        "fallback_mode": <bool>  # True if strict mode failed and json_object was used
    }
    """
    fallback_mode = False
    raw_response = ""

    try:
        extraction, raw_response = _call_groq_structured(transcript)
    except Exception as strict_err:
        print(f"[extraction.py] Strict json_schema mode failed: {strict_err}")
        print("[extraction.py] Falling back to json_object mode.")
        fallback_mode = True
        extraction, raw_response = _call_groq_json_object(transcript)

    resolved_date = resolve_promised_date(extraction, call_date)

    return {
        "extraction": extraction,
        "raw_response": raw_response,
        "resolved_promised_date": resolved_date,
        "fallback_mode": fallback_mode
    }
