"""
Seed data generator.

Run with:  python -m app.seed_data

Generates ~80 synthetic revenue-risk events across all four event types
with realistic weighting designed to give human-like recovery interventions
(including Hinglish voice calls for insufficient_funds, user_abandoned, and
invoice_unpaid) sufficient representation (~55% of the event pool).
"""
import random
from faker import Faker

from app.database import SessionLocal, Base, engine
from app.models import Event, EventType

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

# Varied, realistic Hinglish transcripts for demo/testing purposes.
# Covers: clean promise with amount+date, promise without amount, event-based
# (salary/cheque), plain refusal, refusal with explicit no-contact, payment
# already completed, dispute, wrong number, and partial payment offer.
DEMO_TRANSCRIPTS = [
    # 1. Clean promise — specific amount + tomorrow
    "5000 rupaye kal tak de dunga, pakka.",
    # 2. Promise — no specific amount, just a date
    "Kal tak kar deta hoon payment, tension mat lo.",
    # 3. Event-based — waiting for salary
    "Salary aane ke baad payment karunga, do-teen din mein aa jayegi.",
    # 4. Event-based — waiting for cheque clearance
    "Cheque clear hone ke baad immediately transfer karunga.",
    # 5. Plain refusal — no explicit stop-contact request
    "Abhi mere paas paisa nahi hai, baad mein baat karte hain.",
    # 6. Refusal + explicit no-contact request (triggers compliance override)
    "Main paise nahi dunga, dobara phone mat karna mujhe.",
    # 7. Payment already completed
    "Maine kal hi payment kar diya tha NEFT se, apna account check karo.",
    # 8. Dispute on amount
    "Yeh amount galat hai, mujhe itna nahi dena tha, invoice dekho.",
    # 9. Wrong number
    "Aapne galat number dial kiya hai, yahan koi aisa nahi rehta.",
    # 10. Partial payment offer
    "Abhi sirf 2000 de sakta hoon, baaki 3000 agle hafte kar dunga.",
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


def seed(n: int = 80):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed the hero demo event (fixed, identifiable for judging day)
        hero = seed_hero_demo_event(db)
        print(f"Seeded hero demo event: ID={hero.id} (cust_hero_demo, Rs 12000.00)")

        # 2. Seed the batch of random events
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
                demo_transcript=random.choice(DEMO_TRANSCRIPTS),
            )
            db.add(event)
            created += 1

        db.commit()
        print(f"Seeded {created} batch events + 1 hero event ({created + 1} total).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
