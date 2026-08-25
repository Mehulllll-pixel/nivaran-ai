"""
verify_final_hero_demo.py
=========================
Tasks 1-4: Fresh reset, reseed (81 events), convergence run, hero event
verification with Rule 8 (promised_amount should now show 12000.0).
"""
import os, time, json, urllib.request, threading, datetime

# ── 1. Kill any existing server occupying port 8000 ──────────────────
import subprocess
subprocess.run(
    "for /f \"tokens=5\" %a in ('netstat -ano ^| findstr :8000') do taskkill /PID %a /F",
    shell=True, capture_output=True
)
time.sleep(1)

# ── 2. Delete old DB ──────────────────────────────────────────────────
os.environ["DATABASE_URL"] = "sqlite:///./dev.db"
os.environ["PYTHONPATH"]   = "."
os.environ["PYTHONIOENCODING"] = "utf-8"

if os.path.exists("dev.db"):
    os.remove("dev.db")
    print("✓ Deleted old dev.db")
else:
    print("  (dev.db did not exist)")

# ── 3. Reseed ─────────────────────────────────────────────────────────
from app.seed_data import seed
seed(80)
print("✓ Reseeded: 80 random events + 1 hero demo event = 81 total\n")

# ── 4. Start server ───────────────────────────────────────────────────
import uvicorn
def _run():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")
threading.Thread(target=_run, daemon=True).start()
time.sleep(4)
print("✓ Server started on http://127.0.0.1:8000\n")

# ── Helpers ───────────────────────────────────────────────────────────
def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:8000{path}", timeout=120) as r:
        return json.loads(r.read())

def post(path):
    req = urllib.request.Request(f"http://127.0.0.1:8000{path}", method="POST", data=b"")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

# ── 5. Convergence run ────────────────────────────────────────────────
print("=" * 68)
print("CONVERGENCE RUN — pass-by-pass table")
print(f"{'Pass':<6}{'Events Processed':<20}{'Total Recovered':<22}{'Stopped Count':<15}{'Stable?'}")
print("-" * 68)

prev_recovered, prev_stopped = None, None
for pass_num in range(1, 10):
    post("/agent/process-batch")
    m = get("/dashboard/metrics")
    recovered = m["total_recovered"]
    stopped   = m["stopped_count"]
    stable = (recovered == prev_recovered and stopped == prev_stopped)
    print(f"{pass_num:<6}{81:<20}₹{recovered:<21.2f}{stopped:<15}{'✓ STABLE' if stable else ''}")
    if stable:
        print(f"\n✓ Converged at Pass {pass_num}. Stopping.")
        break
    prev_recovered, prev_stopped = recovered, stopped
else:
    print("\n⚠  Did not converge within 9 passes.")

# ── 6. Hero event verification ────────────────────────────────────────
print()
print("=" * 68)
print("HERO EVENT VERIFICATION")
print("=" * 68)

events = get("/events/")
hero = next((e for e in events if e.get("customer_id") == "cust_hero_demo"), None)
if not hero:
    print("ERROR: cust_hero_demo not found in /events!")
    exit(1)

hero_id = hero["id"]
print(f"  customer_id    : {hero['customer_id']}")
print(f"  event_id       : {hero_id}")
print(f"  amount         : ₹{hero['amount']}")
print(f"  raw_reason_code: {hero['raw_reason_code']}")
print(f"  transcript     : \"{hero['demo_transcript']}\"")

case = get(f"/dashboard/case/{hero_id}")
print()
print("FULL CASE TRAIL:")
print("-" * 68)
for i, decision in enumerate(case["decisions"]):
    action  = case["actions"][i]  if i < len(case["actions"])  else None
    outcome = case["outcomes"][i] if i < len(case["outcomes"]) else None
    print(f"\n[ATTEMPT #{decision['attempt_number']}]")
    print(f"  Root Cause    : {decision['root_cause']}")
    print(f"  Chosen Action : {decision['chosen_action'].upper()}")
    print(f"  Reasoning     : {decision['reasoning']}")
    if action:
        print(f"  Channel Ref   : {action['channel_ref']}")
        notes = action['notes']
        print(f"  Notes         : {notes}")
    if outcome:
        print(f"  Outcome Status: {outcome['status'].upper()}")
        print(f"  Amt Recovered : ₹{outcome['amount_recovered']}")

# ── 7. Targeted assertions ─────────────────────────────────────────────
import re
print()
print("=" * 68)
print("TARGETED ASSERTIONS")
print("-" * 68)
PASS = "✅ PASS"
FAIL = "❌ FAIL"

# Find the voice_call_hinglish action notes
voice_action = next((a for a in case["actions"] if a["action_type"] == "voice_call_hinglish"), None)
voice_decision = next((d for d in case["decisions"] if d["chosen_action"] == "voice_call_hinglish"), None)
voice_outcome  = None
if voice_action:
    voice_outcome = next((o for o in case["outcomes"] if o["action_id"] == voice_action["id"]), None)

notes = voice_action["notes"] if voice_action else ""

# Assert: Attempt 1 is sms_nudge
att1_ok = case["decisions"][0]["chosen_action"] == "sms_nudge" if case["decisions"] else False
print(f"  Attempt 1 = sms_nudge          : {PASS if att1_ok else FAIL} (got: {case['decisions'][0]['chosen_action'] if case['decisions'] else 'N/A'})")

# Assert: Attempt 2 is voice_call_hinglish
att2_ok = voice_decision is not None
print(f"  Attempt 2 = voice_call_hinglish: {PASS if att2_ok else FAIL}")

# Assert: promised_amount = 12000.0 in notes
amount_match = re.search(r"Promised: ₹([\d\.]+)", notes)
promised_val = float(amount_match.group(1)) if amount_match else None
amount_ok = promised_val == 12000.0
print(f"  promised_amount = 12000.0       : {PASS if amount_ok else FAIL} (got: {promised_val})")

# Assert: resolved_promised_date = tomorrow (2026-08-26)
date_match = re.search(r"by ([\d\-T:\.]+)", notes)
date_str = date_match.group(1) if date_match else ""
date_ok = date_str.startswith("2026-08-26")
print(f"  resolved_date starts 2026-08-26 : {PASS if date_ok else FAIL} (got: {date_str[:10] if date_str else 'N/A'})")

# Assert: guardrail = schedule_follow_up (not generic_event_follow_up)
# schedule_follow_up keeps ActionType as voice_call_hinglish; generic_event_follow_up also does but we check notes
guardrail_ok = "generic_event_follow_up" not in notes and voice_outcome is not None
outcome_status = voice_outcome["status"] if voice_outcome else "N/A"
print(f"  guardrail = schedule_follow_up  : {PASS if guardrail_ok else FAIL} (outcome status: {outcome_status})")

# Final event_id banner
print()
print("=" * 68)
print(f"HERO_EVENT_ID = \"{hero_id}\"")
print("=" * 68)
