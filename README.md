# Recruiter AI Platform

Recruiter AI Platform is a production-grade agentic AI system that converts natural-language hiring queries into structured sourcing pipelines.

It supports async job orchestration, background AI processing, persistent storage, optional caching, REST API, HTML UI, and CLI interface.

--------------------------------------------------
SYSTEM OVERVIEW
--------------------------------------------------

Recruiter AI Platform allows recruiters to submit hiring queries like:

"Find senior AI engineers in Bangalore"

The system processes the query using an AI pipeline:
- Concept Reasoner
- Action Orchestrator
- Signal Judge
- Lead Generator

Each query runs asynchronously, returns a UUID, and can be tracked until completion.

--------------------------------------------------
ARCHITECTURE
--------------------------------------------------

[CLI / HTML UI / API Client]
            |
            v
        FastAPI Gateway
            |
            v
     Async Job Orchestrator
            |
            v
   AI Processing Pipeline
   - Concept Reasoner (LLM)
   - Action Orchestrator (Search APIs)
   - Signal Judge (Ranking)
            |
            v
       PostgreSQL Database
       Redis Cache (optional)

--------------------------------------------------
FEATURES
--------------------------------------------------

- Async job execution with UUID tracking
- Background AI pipeline
- Timeouts, retries, and zombie recovery
- PostgreSQL persistence
- Optional Redis caching
- REST API (FastAPI)
- HTML UI (HTMX)
- CLI client (Typer)
- Observability endpoints
- Full test suite

--------------------------------------------------
REPOSITORY STRUCTURE
--------------------------------------------------

recruiter-ai-backend/
│
├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── database.py
│   ├── config.py
│   └── utils/
│
├── cli.py
├── frontend/
├── tests/
├── requirements.txt
└── README.md

--------------------------------------------------
INSTALLATION
--------------------------------------------------

Prerequisites:
- Python 3.10+
- PostgreSQL
- Redis (optional)

Clone repository:
git clone https://github.com/ayushmantrivedi/recruiter-AI-agent.git
cd recruiter-AI-agent/recruiter-ai-backend

Create virtual environment:
python -m venv .venv

Activate environment:
Windows:
.venv\Scripts\activate

Linux / Mac:
source .venv/bin/activate

Install dependencies:
pip install -r requirements.txt

--------------------------------------------------
DATABASE SETUP
--------------------------------------------------

Create database:

CREATE DATABASE recruiter_ai;
CREATE USER recruiter_user WITH PASSWORD 'recruiter_password';
GRANT ALL PRIVILEGES ON DATABASE recruiter_ai TO recruiter_user;

--------------------------------------------------
ENV CONFIGURATION
--------------------------------------------------

Create .env file:

DATABASE_URL=postgresql://recruiter_user:recruiter_password@localhost:5432/recruiter_ai
REDIS_URL=redis://localhost:6379
LOG_LEVEL=info
LLM_API_KEY=your_api_key_here

--------------------------------------------------
START BACKEND
--------------------------------------------------

uvicorn app.main:app --reload

Open API Docs:
http://localhost:8000/docs

--------------------------------------------------
API USAGE (CMD)
--------------------------------------------------

Submit Query:

curl -X POST http://localhost:8000/api/recruiter/query -H "Content-Type: application/json" -d "{\"query\":\"Find senior AI engineers in Bangalore\",\"recruiter_id\":\"2\"}"

Check Status:

curl http://localhost:8000/api/recruiter/query/<query_id>

--------------------------------------------------
POWERSHELL API USAGE
--------------------------------------------------

$body = @{ query = "Find senior AI engineers in Bangalore"; recruiter_id = "2" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/recruiter/query" -ContentType "application/json" -Body $body

--------------------------------------------------
OBSERVABILITY ENDPOINTS
--------------------------------------------------

Health:
http://localhost:8000/api/recruiter/health

All Jobs:
http://localhost:8000/api/recruiter/jobs

Active Jobs:
http://localhost:8000/api/recruiter/jobs/active

Failed Jobs:
http://localhost:8000/api/recruiter/jobs/failed

Zombie Jobs:
http://localhost:8000/api/recruiter/jobs/zombie

--------------------------------------------------
CLI CLIENT
--------------------------------------------------

Submit query:
python cli.py submit --query "Find ML engineers in Pune" --recruiter-id 2

Check status:
python cli.py status --query-id <uuid>

--------------------------------------------------
TESTING
--------------------------------------------------

Run all tests:
pytest -q

Test groups:
- API tests
- Pipeline tests
- UI tests
- CLI tests

--------------------------------------------------
RELIABILITY GUARANTEES
--------------------------------------------------

- Per-job timeout
- Retry with exponential backoff
- Atomic database transactions
- Zombie job recovery
- Full pipeline instrumentation
- Structured logging

--------------------------------------------------
DEPLOYMENT
--------------------------------------------------

Recommended:
- Docker + docker-compose
- Kubernetes for scaling
- External job queue (Redis Streams / RabbitMQ)
- Prometheus + Grafana monitoring

--------------------------------------------------
SECURITY
--------------------------------------------------

- JWT authentication (recommended)
- TLS in production
- API rate limiting
- PII protection
- Prompt injection defense

--------------------------------------------------
MONETIZATION
--------------------------------------------------

- SaaS subscription
- API credits
- Enterprise licensing
- White-label deployments

--------------------------------------------------
LICENSE
--------------------------------------------------

MIT License

--------------------------------------------------
MAINTAINER
--------------------------------------------------

Ayushman Trivedi

--------------------------------------------------
FINAL NOTE
--------------------------------------------------

This is a production-grade AI job orchestration platform.
Designed for reliability, scalability, and real-world deployment.

--------------------------------------------------
