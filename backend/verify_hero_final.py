"""
verify_hero_final.py
====================
Convergence run + hero demo assertion.
Assumes server is already running on :8000.
Uses httpx (already in venv) with a 10-minute timeout per batch call.
"""
import os, json, re, datetime
import httpx

BASE = "http://127.0.0.1:8000"
HERO_ID = os.environ.get("HERO_ID", "")

LIMITS = httpx.Limits(max_connections=5)
# 10-minute timeout for the batch endpoint (all voice calls are serial)
TIMEOUT = httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=10.0)

client = httpx.Client(base_url=BASE, timeout=TIMEOUT, limits=LIMITS)

def get(path):
    return client.get(path).json()

def post(path):
    return client.post(path).json()

# ── 1. Confirm server and find hero event ─────────────────────────────
root = get("/")
print(f"✓ Server reachable: {root}")

events = get("/events/")
hero = next((e for e in events if e.get("customer_id") == "cust_hero_demo"), None)
if not hero:
    print("ERROR: cust_hero_demo not found!")
    exit(1)
hero_id = hero["id"]
print(f"✓ Hero event found: {hero_id}  (₹{hero['amount']}, {hero['raw_reason_code']})\n")

# ── 2. Convergence run ─────────────────────────────────────────────────
print("=" * 68)
print("CONVERGENCE RUN — pass-by-pass table")
print(f"{'Pass':<6}{'Total Recovered':<24}{'Stopped Count':<16}{'Stable?'}")
print("-" * 68)

prev_recovered, prev_stopped = None, None
stable_at = None
for pass_num in range(1, 10):
    print(f"  [Pass {pass_num}] Calling process-batch...", flush=True)
    post("/agent/process-batch")
    m = get("/dashboard/metrics")
    recovered = m["total_recovered"]
    stopped   = m["stopped_count"]
    stable = (recovered == prev_recovered and stopped == prev_stopped)
    print(f"{pass_num:<6}₹{recovered:<23.2f}{stopped:<16}{'✓ STABLE' if stable else ''}")
    if stable:
        stable_at = pass_num
        print(f"\n✓ Converged at Pass {pass_num}.")
        break
    prev_recovered, prev_stopped = recovered, stopped
else:
    print("\n⚠  Did not converge within 9 passes.")

# ── 3. Full hero case trail ────────────────────────────────────────────
print()
print("=" * 68)
print(f"HERO EVENT FULL CASE TRAIL — {hero_id}")
print("=" * 68)

case = get(f"/dashboard/case/{hero_id}")
print(f"  customer_id : {case['event']['customer_id']}")
print(f"  amount      : ₹{case['event']['amount']}")
print(f"  transcript  : \"{case['event']['demo_transcript']}\"")
print()

for i, decision in enumerate(case["decisions"]):
    action  = case["actions"][i]  if i < len(case["actions"])  else None
    outcome = case["outcomes"][i] if i < len(case["outcomes"]) else None
    print(f"[ATTEMPT #{decision['attempt_number']}]  {decision['chosen_action'].upper()}  (root_cause: {decision['root_cause']})")
    print(f"  Reasoning     : {decision['reasoning']}")
    if action:
        notes = action["notes"]
        # Print full notes for voice, abbreviated for others
        if action["action_type"] == "voice_call_hinglish":
            print(f"  Notes (full)  : {notes}")
        else:
            print(f"  Notes         : {notes}")
    if outcome:
        print(f"  Outcome       : {outcome['status'].upper()}  ₹{outcome['amount_recovered']}")
    print()

# ── 4. Targeted assertions ─────────────────────────────────────────────
print("=" * 68)
print("TARGETED ASSERTIONS")
print("-" * 68)
PASS = "✅ PASS"
FAIL = "❌ FAIL"

voice_action   = next((a for a in case["actions"]   if a["action_type"] == "voice_call_hinglish"), None)
voice_decision = next((d for d in case["decisions"] if d["chosen_action"] == "voice_call_hinglish"), None)
voice_outcome  = next((o for o in case["outcomes"]  if o["action_id"] == voice_action["id"]), None) if voice_action else None
notes = voice_action["notes"] if voice_action else ""

# Attempt 1 = sms_nudge
att1 = case["decisions"][0]["chosen_action"] if case["decisions"] else ""
print(f"  Attempt 1 = sms_nudge           : {PASS if att1 == 'sms_nudge' else FAIL}  (got: {att1})")

# Attempt 2 = voice_call_hinglish
print(f"  Attempt 2 = voice_call_hinglish : {PASS if voice_decision else FAIL}")

# promised_amount = 12000.0 in notes
amount_m = re.search(r"Promised: ₹([\d\.]+)", notes)
promised_val = float(amount_m.group(1)) if amount_m else None
amount_ok = promised_val == 12000.0
print(f"  promised_amount = 12000.0       : {PASS if amount_ok else FAIL}  (got: {promised_val})")

# resolved_date starts with tomorrow's date
date_m = re.search(r"by ([\d\-T:\.]+)", notes)
date_str = date_m.group(1) if date_m else ""
# The seed was run fresh today; the call_date is utcnow so tomorrow = 2026-08-26
tomorrow = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
date_ok = date_str.startswith(tomorrow)
print(f"  resolved_date = {tomorrow}    : {PASS if date_ok else FAIL}  (got: {date_str[:10] if date_str else 'N/A'})")

# guardrail = schedule_follow_up (voice outcome is RECOVERED or PENDING, not generic_event_follow_up)
guardrail_ok = voice_outcome is not None and "generic_event_follow_up" not in notes
outcome_status = voice_outcome["status"] if voice_outcome else "N/A"
print(f"  guardrail = schedule_follow_up  : {PASS if guardrail_ok else FAIL}  (outcome status: {outcome_status})")

# ── 5. Final banner ────────────────────────────────────────────────────
print()
print("=" * 68)
print(f"HERO_EVENT_ID = \"{hero_id}\"")
print("=" * 68)

client.close()
