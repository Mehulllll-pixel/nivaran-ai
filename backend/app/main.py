from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import events, agent, dashboard

# Creates tables if they don't exist yet. Fine for a hackathon;
# use Alembic migrations if this grows past the hackathon.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Revenue Recovery Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(agent.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "revenue-recovery-agent"}
