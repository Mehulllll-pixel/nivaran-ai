# Nivaran AI

Nivaran AI is an autonomous payment recovery agent that diagnoses transaction failures, extracts intent and commitment details from Hinglish voice transcripts via structured LLM outputs, and routes compliant recovery actions through a deterministic guardrail layer. It handles both automated retries and multi-channel interventions (SMS nudges, WhatsApp reminders, payment links, voice calls) while enforcing strict contact limits and compliance opt-out rules.

## Repository Structure

The repository is organized into three primary directories:

- `backend/`: FastAPI service containing the core database models (SQLAlchemy/SQLite), decision engine, action executors, voice extraction pipeline, and dashboard reporting API.
- `frontend/`: React dashboard (built with Vite) that provides real-time visibility into recovery metrics, revenue breakdown by channel, event search, batch execution simulation, and full decision-to-outcome case audit trails.
- `research/`: Standalone validation suite, test scripts, audio recordings, and benchmark tests used to build, iterate, and verify the Hinglish voice pipeline components (transcription, Groq structured JSON extraction, temporal date resolution, and guardrail routing) prior to backend integration.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Groq API key (for voice transcript extraction)

### 1. Backend Setup

Navigate to the `backend/` directory, create a virtual environment, install dependencies, and configure the environment:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=sqlite:///./dev.db
GROQ_API_KEY=your_groq_api_key_here
```

Seed the database with initial failure events:

```bash
python -m app.seed_data
```

Start the FastAPI application:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at `http://127.0.0.1:8000`. API documentation is accessible at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

In a separate terminal, navigate to the `frontend/` directory, install dependencies, and launch the Vite development server:

```bash
cd frontend
npm install
npm run dev
```

The dashboard will run at `http://127.0.0.1:5173`.

### 3. Voice Pipeline Research Suite

The `research/` directory contains standalone test harnesses and reference audio used during voice pipeline development:

- `test_amount_extraction.py`: Validates numerical amount parsing and currency handling.
- `test_temporal_resolver.py`: Tests categorical and relative date resolution for Hinglish expressions (e.g., "kal", "parso", "agle hafte").
- `test_guardrails.py`: Confirms deterministic enforcement of compliance opt-outs, dispute escalations, and payment reconciliations.
- `audio/`: Reference audio recordings used for end-to-end transcription and extraction testing.

To run tests in the research suite:

```bash
cd research
pytest
```
