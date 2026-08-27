import time
from app.database import SessionLocal
from app.routers.agent import process_batch
from app.routers.dashboard import get_metrics

db = SessionLocal()
try:
    print("Running batch passes until metrics stabilize...")
    last_recovered = -1
    last_stopped = -1
    
    pass_num = 1
    while True:
        res = process_batch(db)
        metrics = get_metrics(db)
        rec = metrics.total_recovered
        stop = metrics.stopped_count
        print(f"Pass {pass_num}: Processed={res['events_processed']}, Total Recovered=Rs.{rec:,.2f}, Stopped Count={stop}")
        
        if rec == last_recovered and stop == last_stopped:
            print(f"--> Convergence reached after {pass_num} passes! Metrics are stable.")
            break
            
        last_recovered = rec
        last_stopped = stop
        pass_num += 1
        if pass_num > 6:
            print("Max passes reached.")
            break
        time.sleep(1)
finally:
    db.close()
