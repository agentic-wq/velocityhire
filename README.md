# ⚡ VelocityHire — AI-Powered Recruitment Intelligence

> **Complete.dev Hackathon 2026** · Built with LangGraph · Multi-agent · Multi-tenant

[![CI / CD](https://github.com/agentic-wq/velocityhire/actions/workflows/ci-cd.yaml/badge.svg?branch=master)](https://github.com/agentic-wq/velocityhire/actions/workflows/ci-cd.yaml)

VelocityHire identifies candidates with the highest **learning velocity** — not just years of experience.
Three LangGraph agents collaborate to score adaptability, match candidates to roles, and generate
personalised outreach campaigns automatically.

**Live Demo →** https://q1inyxqs.run.complete.dev

---

## The Problem

Traditional recruitment filters by credentials and years of experience.
The best engineers in an AI-first world are defined by **how fast they learn and ship** — not their résumé.

**VelocityHire measures what matters:**
- 🏆 Hackathon wins and frequency (40% weight)
- ⚡ Recent technology adoption (25%)
- 📚 Fresh certifications (20%)
- 🕐 Recency of all signals (15%)

---

## Architecture — 3 LangGraph Agents

```
Candidate Profile
      │
      ▼
┌─────────────────────┐
│  Agent 1            │  LangGraph · 7 nodes
│  Profile Analyzer   │  Scores learning velocity (0-100)
│  /analyze           │  Hackathons · Skills · Certs · Recency
└────────┬────────────┘
         │ adaptability_score + tier
         ▼
┌─────────────────────┐
│  Agent 2            │  LangGraph · 5 nodes
│  Job Matcher        │  Adaptability (60%) + Role Fit (25%) + Culture (15%)
│  /match             │  Outputs total_match_score + recommendation
└────────┬────────────┘
         │ match_score + matched_skills
         ▼
┌─────────────────────┐
│  Agent 3            │  LangGraph · 6 nodes
│  Outreach Coord.    │  PRIORITY / STANDARD / NURTURE / ARCHIVE tiers
│  /generate          │  LinkedIn · Email · Follow-up · ATS Note
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Shared SQLite DB   │  Multi-tenant · 5 tables · analytics
│  shared/db_memory   │  Scoped by X-Company-ID header
└─────────────────────┘
```

---

## Scoring Algorithm

### Agent 1 — Adaptability Score (0-100)

| Dimension | Weight | Signals |
|-----------|--------|---------|
| Hackathons | 40 pts | Wins in last 3 months = 20pts, 6mo = 15pts, 12mo = 10pts |
| Skills | 25 pts | Recent tech adoption: LangGraph, Rust, Svelte, GenAI, etc. |
| Certifications | 20 pts | Recency × relevance (cloud/AI certs score highest) |
| Recency | 15 pts | GitHub commits, blog posts, talks in last 30/90 days |

**Threshold:** 70+ → recommend for interview

### Agent 2 — Job Match Score (0-100)

| Dimension | Weight | Method |
|-----------|--------|--------|
| Adaptability | 60% | Agent 1 score × 0.6 |
| Role Fit | 25% | Skills coverage + experience level + domain match |
| Culture Fit | 15% | Startup experience + collaboration signals + shipping velocity |

### Agent 3 — Outreach Tier

| Score | Tier | Action |
|-------|------|--------|
| 85+ | 🏆 PRIORITY | Same-day fast-track, exec referral |
| 70–84 | ⭐ STANDARD | Standard interview pipeline |
| 55–69 | ✅ NURTURE | Warm hold, future-role framing |
| <55 | 📋 ARCHIVE | Passive acknowledgement |

---

## Project Structure

```
velocityhire/
├── agent1/
│   ├── agent_1.py          # LangGraph graph (7 nodes)
│   └── app.py              # FastAPI: /analyze, /history, /ats/*, /companies, /outcomes
├── agent2/
│   ├── agent_2.py          # LangGraph graph (5 nodes)
│   └── app.py              # FastAPI: /match, /history
├── agent3/
│   ├── agent_3.py          # LangGraph graph (6 nodes)
│   └── app.py              # FastAPI: /generate, /history, /pipeline, /analytics
├── demo/
│   └── app.py              # Unified demo orchestrator — start here!
├── shared/
│   ├── db_memory.py        # SQLite ORM · 5 tables · multi-tenant CRUD
│   ├── analytics.py        # 7 analytics functions + get_full_analytics()
│   └── ats_integrations.py # Greenhouse · Lever · BambooHR normalisers
├── logs/                   # JSON-structured logs (auto-created)
└── velocityhire.db         # SQLite database (auto-created)
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/agentic-wq/velocityhire.git
cd velocityhire

# Install dependencies (demo app — covers all agents)
pip install -r demo/requirements.txt
```

### 2. Run the unified demo

```bash
MOCK_MODE=true python -m uvicorn demo.app:app --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** and click **▶ Run Full Pipeline Demo**.

That's it. The demo:
1. Runs 5 pre-seeded candidates through all 3 agents
2. Shows real-time progress per candidate
3. Displays ranked results, generated outreach, and analytics
4. Lets you test Greenhouse / Lever / BambooHR webhooks live

### 3. Run individual agents

```bash
# Agent 1 — Profile Analyzer
MOCK_MODE=true python -m uvicorn agent1.app:app --port 8001

# Agent 2 — Job Matcher
MOCK_MODE=true python -m uvicorn agent2.app:app --port 8002

# Agent 3 — Outreach Coordinator
MOCK_MODE=true python -m uvicorn agent3.app:app --port 8003
```

---

## API Reference

### Demo Orchestrator (`demo/app.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Full demo UI |
| `POST` | `/demo/run` | Start 5-candidate pipeline, returns `run_id` |
| `GET` | `/demo/progress/{run_id}` | Live progress (poll at 600ms) |
| `GET` | `/analytics/data` | Full analytics JSON |
| `POST` | `/ats/{provider}/test` | Fire mock ATS webhook (greenhouse/lever/bamboohr) |
| `GET` | `/health` | Status check |

### Agent 1 — Profile Analyzer

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Score a candidate profile (body: `{profile_text}`) |
| `GET` | `/history` | Recent scores (tenant-scoped via `X-Company-ID`) |
| `POST` | `/ats/{provider}/webhook` | Live ATS webhook receiver |
| `POST` | `/ats/{provider}/test` | Mock ATS test |
| `GET` | `/ats/integrations` | List ATS providers + status |
| `POST` | `/companies` | Register tenant company |
| `GET` | `/companies` | List all tenants |
| `POST` | `/outcomes` | Record hiring outcome |

### Agent 2 — Job Matcher

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/match` | Match candidate to job (body: profile + job + agent1 scores) |
| `GET` | `/history` | Recent matches (tenant-scoped) |

### Agent 3 — Outreach Coordinator

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Generate full outreach campaign |
| `GET` | `/history` | Recent campaigns (tenant-scoped) |
| `GET` | `/pipeline` | Cross-agent pipeline dashboard (HTML) |
| `GET` | `/analytics` | Chart.js analytics dashboard (HTML) |
| `GET` | `/analytics/data` | Raw analytics JSON |

---

## Multi-Tenant Usage

All endpoints accept an `X-Company-ID` header for tenant isolation:

```bash
# Analyse a candidate for tenant "acme-corp"
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -H "X-Company-ID: acme-corp" \
  -d '{"profile_text": "Jane Doe — AI Engineer..."}'

# Retrieve only acme-corp's history
curl http://localhost:8001/history \
  -H "X-Company-ID: acme-corp"
```

---

## ATS Integrations

VelocityHire accepts live webhooks from:

| Provider | Event | Endpoint |
|----------|-------|----------|
| 🌿 Greenhouse | `candidate.created` | `POST /ats/greenhouse/webhook` |
| ⚙️ Lever | `candidateCreated` | `POST /ats/lever/webhook` |
| 🎋 BambooHR | `employee.hired` | `POST /ats/bamboohr/webhook` |

**Test without a real ATS connection:**
```bash
curl -X POST http://localhost:8000/ats/greenhouse/test
# → Aisha Nakamura: 94/100 Top Performer 🚀 Fast-track to interview
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `true` | Use rule-based scoring (no LLM API needed) |
| `DB_PATH` | `./velocityhire.db` | SQLite database path |
| `AGENT1_URL` | — | Agent 1 base URL (for Agent 3 cross-agent calls) |
| `AGENT2_URL` | — | Agent 2 base URL |

> **Note:** `MOCK_MODE=true` uses deterministic rule-based scoring — no external API key required.
> Set `MOCK_MODE=false` and configure Deploy AI credentials to use LLM-enhanced scoring.

---

## Key Innovation

Most ATS systems rank by **credentials** — degrees, years of experience, previous companies.

VelocityHire ranks by **learning trajectory**:

- A bootcamp grad who won 2 hackathons last month and published an LLM tool used by 500 people
  scores **higher** than a 10-year Java developer with no recent activity.
- Startup founding-team experience is weighted over big-company tenure.
- A GCP cert from last month scores higher than an Oracle cert from 2016.

This reflects how the best startup engineering teams actually evaluate candidates.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent orchestration | LangGraph 0.2.x (StateGraph, conditional edges) |
| API framework | FastAPI + Uvicorn |
| Persistence | SQLite via SQLAlchemy 2.0 (multi-tenant) |
| Analytics | Custom Python + Chart.js |
| ATS integrations | Webhook normalisers (Greenhouse, Lever, BambooHR) |
| Scoring | Rule-based (MOCK_MODE) / Deploy AI LLM (production) |

---

## Logs

All agents write structured JSON logs to `logs/`:

```bash
tail -f logs/demo.log    # Demo orchestrator
tail -f logs/agent1.log  # Profile Analyzer
tail -f logs/agent3.log  # Outreach Coordinator
```

---

## CI / CD — Deployment Pipeline

**Current deployment status:** ✅ Active — Workload Identity Federation is configured and all GCP secrets are set.

Every commit triggers the **CI / CD** GitHub Actions workflow (`ci-cd.yaml`):

```
push / pull_request → master
         │
         ▼
  ┌─────────────┐
  │ Lint & Test │  flake8 + pytest (all branches)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │    Build    │  docker build (all branches — smoke-test only)
  └──────┬──────┘
         │ only on push to master ↓
         ▼
  ┌─────────────────────────────┐
  │ Deploy to Google Cloud Run  │  push image → Artifact Registry
  │                             │  gcloud run deploy velocityhire
  └─────────────────────────────┘
```

### Current deployment status

| Job | Status |
|-----|--------|
| Lint & Test | ✅ Passing |
| Build Docker Image | ✅ Passing |
| Deploy to Google Cloud Run | ✅ Passing |

Authentication uses **keyless Workload Identity Federation** (no long-lived JSON key).  
No JSON service-account key is stored anywhere — GitHub's OIDC token is exchanged for
short-lived GCP credentials at run time.

### GCP-side WIF setup (already completed)

Workload Identity Federation has been configured for this repository.  
The script below is provided for reference or to re-create the setup in a new project:

```bash
export GCP_PROJECT_ID=my-project-id   # your GCP project
export GCP_REGION=us-central1          # optional, default us-central1
bash scripts/setup-wif.sh
```

The script performs these steps automatically:

| Step | What it does |
|------|--------------|
| 1 | Enables `iamcredentials`, `cloudresourcemanager`, `run`, and `artifactregistry` APIs |
| 2 | Creates service account `velocityhire-deploy@<project>.iam.gserviceaccount.com` with roles `artifactregistry.writer`, `run.admin`, `iam.serviceAccountUser` |
| 3 | Creates Workload Identity Pool `github-pool` |
| 4 | Creates GitHub OIDC provider `github-provider` with the attribute condition `attribute.repository == "agentic-wq/velocityhire"` |
| 5 | Binds the service account to the pool so only this repository can impersonate it |
| 6 | Prints the exact values to paste into GitHub secrets |

---

*Built for the Complete.dev Hackathon · February 2026*
