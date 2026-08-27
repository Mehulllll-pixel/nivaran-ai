"""
Seed data generator.

Run with:  python -m app.seed_data

Generates ~80 synthetic revenue-risk events across all four event types
with realistic weighting designed to give human-like recovery interventions
(including Hinglish voice calls for insufficient_funds, user_abandoned, and
invoice_unpaid) sufficient representation (~55% of the event pool).

Three additional "anchor" voice demo events are also seeded:
  - cust_demo_wrongnum   : wrong number transcript  -> STOPPED (compliance)
  - cust_demo_dispute    : dispute amount transcript -> PENDING (escalate human)
  - cust_demo_nocontact  : explicit refusal + no-contact -> STOPPED (compliance)

For each anchor event the seeding logic:
  1. Inserts the Event row.
  2. Writes a synthetic attempt-1 record (sms_nudge / whatsapp_nudge, FAILED)
     directly into the DB — bypassing the random executor so the coin flip
     cannot accidentally resolve the event before voice is reached.
  3. Calls _process_event(), which sees 1 prior attempt and advances to
     attempt 2 = voice_call_hinglish, feeding the real transcript to Groq
     so the outcome is genuinely determined by the NLU pipeline.
"""
import datetime
import random
from dotenv import load_dotenv

load_dotenv()

from faker import Faker


from app.database import SessionLocal, Base, engine
from app import models
from app.models import Event, EventType, Decision, Action, Outcome, RootCause, ActionType, OutcomeStatus

fake = Faker("en_IN")

# Weighted reason codes per event type to over-represent insufficient_funds
REASON_CODES_AND_WEIGHTS = {
    EventType.PAYMENT_FAILED: (
        ["insufficient_funds", "timeout", "otp_mismatch", "card_expired"],
        [0.50, 0.20, 0.15, 0.15],
    ),
    EventType.SUBSCRIPTION_FAILED: (
        ["insufficient_funds", "gateway_timeout", "card_expired"],
        [0.50, 0.25, 0.25],
    ),
    EventType.CHECKOUT_ABANDONED: ([None], [1.0]),  # maps directly to user_abandoned
    EventType.INVOICE_OVERDUE: ([None], [1.0]),     # maps directly to invoice_unpaid
}

EVENT_TYPE_WEIGHTS = {
    EventType.PAYMENT_FAILED: 0.35,
    EventType.CHECKOUT_ABANDONED: 0.25,
    EventType.SUBSCRIPTION_FAILED: 0.25,
    EventType.INVOICE_OVERDUE: 0.15,
}

GENERIC_TRANSCRIPTS = [
    "5000 rupaye kal dopahar tak UPI se transfer kar dunga.",
    "Kal shaam tak pakka payment clear kar deta hoon, tension mat lo.",
    "Meri salary 5 tarikh ko aayegi, uske baad pura payment clear kar dunga.",
    "Client ka cheque kal clear hone wala hai, uske turant baad transfer kar dunga.",
    "Maine kal hi payment kar diya tha NEFT se, apna account check karo.",
    "Abhi mere account mein 2500 rupaye hain, baaki bacha hua agle hafte de paunga.",
    "Abhi main driving kar raha hoon, kal subah 11 baje call karna tab kar dunga.",
    "Abhi thoda financial issue chal raha hai, mujhe teen-char din ka time chahiye.",
]


# Anchor voice demo events: each carries a compliance-critical transcript that
# must be read by the real NLU pipeline to produce a meaningful outcome.
VOICE_DEMO_EVENTS = [
    {
        "customer_id": "cust_demo_wrongnum",
        "amount": 4999.00,
        "event_type": EventType.PAYMENT_FAILED,
        "raw_reason_code": "insufficient_funds",
        # decision table: attempt1=sms_nudge, attempt2=voice_call_hinglish
        "attempt1_action": ActionType.SMS_NUDGE,
        "attempt1_root_cause": RootCause.INSUFFICIENT_FUNDS,
        "demo_transcript": "Aapne galat number dial kiya hai, yahan koi aisa nahi rehta.",
    },
    {
        "customer_id": "cust_demo_dispute",
        "amount": 8750.00,
        "event_type": EventType.PAYMENT_FAILED,
        "raw_reason_code": "insufficient_funds",
        # decision table: attempt1=sms_nudge, attempt2=voice_call_hinglish
        "attempt1_action": ActionType.SMS_NUDGE,
        "attempt1_root_cause": RootCause.INSUFFICIENT_FUNDS,
        "demo_transcript": "Yeh amount galat hai, mujhe itna nahi dena tha, invoice dekho.",
    },
    {
        "customer_id": "cust_demo_nocontact",
        "amount": 3200.00,
        "event_type": EventType.CHECKOUT_ABANDONED,
        "raw_reason_code": None,
        # decision table: attempt1=whatsapp_nudge, attempt2=voice_call_hinglish
        "attempt1_action": ActionType.WHATSAPP_NUDGE,
        "attempt1_root_cause": RootCause.USER_ABANDONED,
        "demo_transcript": "Main paise nahi dunga, dobara phone mat karna mujhe.",
    },
]


def seed_hero_demo_event(db=None) -> Event:
    """
    Seeds one specific, identifiable hero-demo event:
    - Customer ID: cust_hero_demo
    - Amount: 12000.00
    - Type: payment_failed (insufficient_funds) -> reaches voice_call_hinglish on attempt 2
    - Demo Transcript: "Bhai abhi paise nahi hai, kal salary aayegi, kal kar dunga"
    """
    should_close = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        should_close = True

    event = Event(
        event_type=EventType.PAYMENT_FAILED,
        customer_id="cust_hero_demo",
        amount=12000.00,
        currency="INR",
        raw_reason_code="insufficient_funds",
        demo_transcript="Bhai abhi paise nahi hai, kal salary aayegi, kal kar dunga",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    if should_close:
        db.close()

    return event


def _seed_voice_demo_event(spec: dict, db) -> Event:
    """
    Seeds one anchor voice demo event deterministically:
      1. Creates the Event row.
      2. Writes a synthetic attempt-1 (sms_nudge or whatsapp_nudge) that
         always fails — bypassing the random executor so the dice roll cannot
         resolve the event before voice is reached.
      3. Calls _process_event() from agent.py, which sees 1 prior attempt and
         therefore runs attempt 2 = voice_call_hinglish, feeding the actual
         demo_transcript to the real Groq NLU pipeline.
    """
    # Late import to avoid circular dependency at module-load time
    from app.routers.agent import _process_event

    event = Event(
        event_type=spec["event_type"],
        customer_id=spec["customer_id"],
        amount=spec["amount"],
        currency="INR",
        raw_reason_code=spec["raw_reason_code"],
        demo_transcript=spec["demo_transcript"],
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Synthetic attempt 1: write Decision + Action + Outcome(FAILED) directly,
    # no random executor involved.
    if spec["raw_reason_code"]:
        if spec["raw_reason_code"].strip().lower() != spec["attempt1_root_cause"].value:
            signal_desc = f"Raw code '{spec['raw_reason_code']}' classified as '{spec['attempt1_root_cause'].value}'"
        else:
            signal_desc = f"Raw code '{spec['raw_reason_code']}' mapped to '{spec['attempt1_root_cause'].value}'"
    else:
        signal_desc = f"Signal '{spec['event_type'].value}' mapped to '{spec['attempt1_root_cause'].value}'"

    reasoning = (
        f"{signal_desc}. "
        f"This is attempt 1 of 2 allowed. "
        f"Decision table maps this to '{spec['attempt1_action'].value}'."
    )

    decision1 = Decision(
        event_id=event.id,
        root_cause=spec["attempt1_root_cause"],
        chosen_action=spec["attempt1_action"],
        reasoning=reasoning,
        attempt_number=1,
    )
    db.add(decision1)
    db.commit()
    db.refresh(decision1)

    action1 = Action(
        decision_id=decision1.id,
        action_type=spec["attempt1_action"],
        channel_ref="demo-bypass",
        notes=(
            f"Synthetic attempt 1 ({spec['attempt1_action'].value}) — seeded as FAILED "
            f"so that attempt 2 deterministically reaches voice_call_hinglish."
        ),
    )
    db.add(action1)
    db.commit()
    db.refresh(action1)

    outcome1 = Outcome(
        action_id=action1.id,
        status=OutcomeStatus.FAILED,
        amount_recovered=0.0,
    )
    db.add(outcome1)
    db.commit()

    # Attempt 2: let _process_event run — it sees 1 prior attempt and routes
    # to voice_call_hinglish, feeding the real transcript to Groq.
    print(f"  [{spec['customer_id']}] Calling Groq NLU for attempt 2 (voice_call_hinglish)...")
    _process_event(event, db)
    print(f"  [{spec['customer_id']}] Done.")

    return event


def seed(n: int = 80):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed the hero demo event (fixed, identifiable for judging day)
        hero = seed_hero_demo_event(db)
        print(f"Seeded hero demo event: ID={hero.id} (cust_hero_demo, Rs 12000.00)")

        # 2. Seed the three anchor voice demo events deterministically
        print("Seeding anchor voice demo events (3 real Groq calls)...")
        for spec in VOICE_DEMO_EVENTS:
            ev = _seed_voice_demo_event(spec, db)
            print(f"  Seeded {spec['customer_id']}: ID={ev.id}, Rs {spec['amount']}")
        print("Anchor events done.")

        # 3. Seed the batch of random events — no demo_transcript assigned,
        #    since random resolution may never reach voice_call_hinglish.
        types = list(EVENT_TYPE_WEIGHTS.keys())
        weights = list(EVENT_TYPE_WEIGHTS.values())

        created = 0
        for _ in range(n):
            event_type = random.choices(types, weights=weights, k=1)[0]
            codes, code_weights = REASON_CODES_AND_WEIGHTS[event_type]
            reason_code = random.choices(codes, weights=code_weights, k=1)[0]

            if event_type == EventType.INVOICE_OVERDUE:
                amount = round(random.uniform(15000, 250000), 2)  # B2B invoices, larger amounts
            else:
                amount = round(random.uniform(299, 15000), 2)  # consumer payments

            event = Event(
                event_type=event_type,
                customer_id=f"cust_{fake.unique.random_number(digits=6)}",
                amount=amount,
                currency="INR",
                raw_reason_code=reason_code,
                demo_transcript=random.choice(GENERIC_TRANSCRIPTS),
            )
            db.add(event)
            created += 1


        db.commit()
        print(f"Seeded {created} batch events + 1 hero + 3 anchor = {created + 4} total.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
