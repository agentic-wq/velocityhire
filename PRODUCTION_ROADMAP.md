# VelocityHire — Production Roadmap

> From hackathon demo → production SaaS
> Current stack: FastAPI · LangGraph · SQLite · rule-based scoring · single-server
> Target stack: FastAPI · LangGraph · PostgreSQL · Redis · Deploy AI LLMs · Kubernetes

---

## Phase 1 — Stabilise (Week 1–2)

### 1.1 Database: SQLite → PostgreSQL

**Why**: SQLite is single-writer; concurrent recruiters will cause `database is locked` errors.

```bash
# Migration steps
pip install psycopg2-binary alembic
# 1. Replace DB_URL in shared/db_memory.py
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host/velocityhire")
# 2. Remove check_same_thread (SQLite-only)
# 3. Add connection pooling
_engine = create_engine(DB_URL, pool_size=10, max_overflow=20, pool_pre_ping=True)
# 4. alembic init → alembic revision --autogenerate → alembic upgrade head
```

**Schema changes needed:**
- Add index on `(company_id, created_at)` for all tables
- Add `updated_at` timestamp columns
- Convert `recommend_interview` from String("True"/"False") to Boolean

### 1.2 Replace In-Memory Cache with Redis

**Why**: `_PIPELINE_CACHE` is a dict that dies on restart and doesn't share across workers.

```python
# shared/cache.py
import redis, json, hashlib, os

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
CACHE_TTL = 3600  # 1 hour

def get_cached(profile_text: str, job_title: str):
    key = f"pipeline:{hashlib.md5(f'{profile_text}:{job_title}'.encode()).hexdigest()}"
    raw = _redis.get(key)
    return json.loads(raw) if raw else None

def set_cached(profile_text: str, job_title: str, result: dict):
    key = f"pipeline:{hashlib.md5(f'{profile_text}:{job_title}'.encode()).hexdigest()}"
    _redis.setex(key, CACHE_TTL, json.dumps(result))
```

### 1.3 API Authentication

**Why**: Currently anyone can POST to any endpoint. Multi-tenant isolation relies solely on `company_id` headers.

```python
# Add JWT auth middleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["company_id"]
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Protect all company-scoped routes
@app.post("/pipeline/run")
async def run_pipeline(company_id: str = Depends(verify_token)):
    ...
```

### 1.4 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/demo/score-one")
@limiter.limit("30/minute")
async def score_one(request: Request, req: ScoreOneRequest):
    ...
```

---

## Phase 2 — Scale (Month 1–2)

### 2.1 Enable Real LLM Scoring (Agent 1)

Agent 1 already has the correct Deploy AI OAuth2 flow in `_call_llm_legacy()`.
To activate:

```bash
# .env — production
MOCK_MODE=false
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
AUTH_URL=https://api-auth.deploy.ai/oauth2/token
API_URL=https://core-api.deploy.ai
```

**Cost optimisation:**
- Cache LLM responses in Redis (same key as pipeline cache)
- Only call LLM for Agent 1 (hackathon signal analysis) — Agents 2 & 3 stay rule-based
- Estimated cost: ~$0.01–0.03 per candidate with GPT-4o

### 2.2 Extend Agents 2 & 3 with LLM

**Agent 2** (Job Matcher) — add LLM path for nuanced role-fit assessment:
```python
# Current: rule-based skill overlap
# Target: LLM analyses soft skills, culture signals, growth trajectory
```

**Agent 3** (Outreach) — replace templates with LLM-generated personalisation:
```python
# Current: tier-based templates
# Target: LLM crafts unique messages per candidate using their specific highlights
```

### 2.3 Async Pipeline with Celery

**Why**: Running 3 agents × N candidates blocks the web worker thread.

```python
# tasks.py
from celery import Celery
app_celery = Celery("velocityhire", broker=os.getenv("REDIS_URL"))

@app_celery.task
def run_pipeline_task(run_id: str, company_id: str):
    _run_pipeline(run_id, company_id)

# In FastAPI route:
@app.post("/pipeline/run")
async def start_run(company_id: str = Depends(verify_token)):
    run_id = str(uuid.uuid4())[:8]
    run_pipeline_task.delay(run_id, company_id)
    return {"run_id": run_id}
```

### 2.4 Hiring Outcomes Feedback Loop

The `outcomes` table already exists. Connect it to scoring improvement:

```python
# When a hired candidate's outcome is recorded, update scoring weights
# High-velocity candidates who were hired → increase hackathon weight
# Low-velocity hires who succeeded → capture missed signals
```

---

## Phase 3 — Production (Month 2–4)

### 3.1 Infrastructure

```yaml
# docker-compose.prod.yml
services:
  api:
    image: velocityhire-api:latest
    replicas: 3
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379/0
      - MOCK_MODE=false

  worker:
    image: velocityhire-api:latest
    command: celery -A tasks worker --concurrency=4

  postgres:
    image: postgres:16
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
```

### 3.2 Observability

```python
# Add structured logging + metrics
import structlog
from prometheus_fastapi_instrumentator import Instrumentator

# Key metrics to track:
# - pipeline_duration_seconds (histogram by company)
# - agent_calls_total (counter by agent, status)
# - candidates_scored_total (counter by tier)
# - cache_hit_ratio (gauge)
```

### 3.3 ATS Webhook Security

Currently webhooks accept any POST. Add HMAC signature verification:

```python
import hmac, hashlib

def verify_greenhouse_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.post("/ats/{provider}/webhook")
async def ats_webhook(provider: str, request: Request):
    body = await request.body()
    sig = request.headers.get("X-Greenhouse-Signature", "")
    if not verify_greenhouse_signature(body, sig, GREENHOUSE_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
```

---

## Phase 4 — Growth (Month 4+)

### 4.1 Multi-Region Deployment
- Primary: AWS us-east-1
- Secondary: AWS eu-west-1 (GDPR compliance for EU customers)
- Read replicas for analytics queries

### 4.2 Compliance
- **GDPR**: Candidate data deletion endpoint, data retention policies
- **SOC 2 Type II**: Audit logging, access controls, pen testing
- **CCPA**: Data portability, opt-out mechanisms

### 4.3 API Partnerships
- **Greenhouse**: Official partner integration (not just webhook)
- **Lever**: Native ATS plugin
- **LinkedIn**: Profile import API
- **GitHub**: Direct commit history analysis (stronger recency signal)

---

## Current vs Target Architecture

```
CURRENT (Demo)                    TARGET (Production)
─────────────────────────────     ──────────────────────────────────
FastAPI (single process)          FastAPI × 3 replicas (load balanced)
SQLite (file-based)          →    PostgreSQL (managed, with replicas)
In-memory dict cache              Redis (persistent, shared)
MOCK_MODE=true (rule-based)       MOCK_MODE=false (Deploy AI LLMs)
No auth                           JWT + API keys
No rate limiting                  slowapi (30 req/min/IP)
Single server                     Kubernetes (EKS)
Manual restart                    Auto-scaling + health probes
```

---

## Estimated Timeline & Cost

| Phase | Duration | Infra Cost/Month | Engineering |
|-------|----------|-----------------|-------------|
| Phase 1 — Stabilise | 2 weeks | $50 (RDS + Redis) | 1 engineer |
| Phase 2 — Scale | 6 weeks | $150 | 2 engineers |
| Phase 3 — Production | 8 weeks | $400 | 3 engineers |
| Phase 4 — Growth | Ongoing | $800+ | 4+ engineers |

**LLM costs** (Agent 1 real mode): ~$0.02/candidate × 1,000 candidates/month = **$20/month** at launch scale.

---

*Generated: 2026-02-25 · VelocityHire v5.0 · Complete.dev Hackathon*
