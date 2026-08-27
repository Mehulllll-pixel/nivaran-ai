from app.database import SessionLocal
from app.routers.agent import process_batch

db = SessionLocal()
try:
    print("Running batch pass 1...")
    res1 = process_batch(db)
    print("Pass 1 result:", res1)
    
    print("Running batch pass 2...")
    res2 = process_batch(db)
    print("Pass 2 result:", res2)
finally:
    db.close()

print("All batch passes complete.")
