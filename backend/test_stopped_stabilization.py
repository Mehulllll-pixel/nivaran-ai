"""
test_stopped_stabilization.py
=============================
Wipes dev.db, seeds 80 events, starts FastAPI app in-process or via client,
and runs process_batch 6 times in a row, reporting stopped_count and
recovered amount after every single pass to verify stabilization.
"""
import os, sys, time, json, urllib.request, threading

os.environ["DATABASE_URL"] = "sqlite:///./dev.db"
os.environ["PYTHONPATH"] = "."
os.environ["PYTHONIOENCODING"] = "utf-8"

# 1. Wipe dev.db
if os.path.exists("dev.db"):
    os.remove("dev.db")
    print("Deleted old dev.db")

# 2. Seed 80 events
from app.seed_data import seed
seed(80)

# 3. Start server
import uvicorn
def start_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()
time.sleep(3)

def get(path):
    with urllib.request.urlopen(f"http://127.0.0.1:8000{path}") as r:
        return json.loads(r.read())

def post(path):
    req = urllib.request.Request(f"http://127.0.0.1:8000{path}", method="POST", data=b"")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

print("\n--- Initial State (Pass 0) ---")
m0 = get("/dashboard/metrics")
print(f"Pass 0: Total Events={m0['total_events']}, Recovered={m0['total_recovered']}, Stopped Count={m0['stopped_count']}")

passes_data = []

for p in range(1, 7):
    print(f"\nRunning batch pass {p}...")
    res = post("/agent/process-batch")
    m = get("/dashboard/metrics")
    passes_data.append((p, m['stopped_count'], m['total_recovered'], m['recovery_rate_pct']))
    print(f"Pass {p} (Processed {res['events_processed']}): Stopped Count={m['stopped_count']}, Total Recovered={m['total_recovered']}, Rate={m['recovery_rate_pct']}%")

print("\n" + "=" * 60)
print("BATCH STABILIZATION SUMMARY TABLE:")
print("=" * 60)
print(f"{'Pass #':<8} | {'Stopped Count':<15} | {'Total Recovered (₹)':<20} | {'Recovery Rate %':<15}")
print("-" * 65)
for p, s, r, rate in passes_data:
    print(f"{p:<8} | {s:<15} | {r:<20} | {rate:<15}")

# Check stabilization between pass 4, 5, 6
s4, s5, s6 = passes_data[3][1], passes_data[4][1], passes_data[5][1]
r4, r5, r6 = passes_data[3][2], passes_data[4][2], passes_data[5][2]

if s4 == s5 == s6 and r4 == r5 == r6:
    print("\n✓ SUCCESS: stopped_count and total_recovered fully stabilized! No phantom growth on subsequent passes.")
else:
    print(f"\n✕ WARNING: Not stabilized: s4={s4}, s5={s5}, s6={s6}")
print("=" * 60)
