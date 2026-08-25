# Nivaran AI — Pipeline Notes

## Known Simplifications and Post-Hackathon Improvements

### Partial Payment Handling

**Status:** Implemented as a known simplification.

When a customer offers a split/partial payment (e.g. "Sir 2000 abhi hai mere paas, baaki agle hafte de dunga"), the pipeline captures only the **immediate committed amount** in `promised_amount` and describes the remainder and its timeframe in the `reasoning` field.

**What is NOT captured:**
- The second installment amount
- A separate follow-up date for the remainder
- Any structured representation of the two-part payment plan

**Why this was not implemented now:**
Full split-payment support would require changes to both the JSON schema (replacing the scalar `promised_amount` field with a structured installment list) and the guardrails layer (scheduling two separate follow-ups with different dates and amounts). This is a non-trivial schema change with downstream impacts on the recovery scheduler. Deferred as a post-hackathon improvement.

**Post-hackathon improvement (tracked here):**
- Add `partial_payment_offer` intent to the enum, OR keep `promise_future_payment` and extend the schema with:
  ```json
  "payment_plan": [
    { "amount": 2000, "due": "now" },
    { "amount": null, "due": "next_week" }
  ]
  ```
- Update guardrails to schedule two distinct follow-up actions.

---

## Intent Enum Coverage

The current intent enum covers:

| Intent | Trigger |
|--------|---------|
| `agree_to_pay` | Commits to pay, no date/amount |
| `promise_future_payment` | Commits with a specific date or timeframe |
| `payment_already_completed` | Claims payment was already made |
| `asks_why` | Asks reason for the call/debt |
| `cannot_pay` | States inability to pay (no future commitment) |
| `payment_refusal` | Explicit refusal |
| `dispute_amount` | Contests the amount owed |
| `wrong_number` | Not the intended recipient |
| `opt_out` | Requests no further contact |
| `unclear` | Cannot be classified |

**Known gap:** Partial/split payment offers collapse into `promise_future_payment`.

---

## Temporal Handling

Date arithmetic is performed **entirely in Python** by `resolve_promised_date()` in `temporal_resolver.py`. The LLM is never asked to compute a calendar date. This prevents year hallucination and ensures deterministic, testable date resolution.

**Known limitation:** `event_based` temporal type (salary arrival, cheque clearing, etc.) returns `resolved_promised_date = None`. The guardrail schedules a generic follow-up after `EVENT_FOLLOW_UP_DELAY_DAYS = 3` days rather than waiting for the actual event. Tracking the real event (e.g. salary credit date) is a post-hackathon improvement.
