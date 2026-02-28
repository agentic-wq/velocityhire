# ⚡ VelocityHire — Pitch Deck
> Complete.dev AI Agent Hackathon 2026 · 10 Slides

---

## SLIDE 1 — TITLE

**⚡ VelocityHire**
*AI-Powered Recruitment Intelligence*

> "Stop hiring by credentials. Start hiring by learning velocity."

- Built with LangGraph · Multi-agent · Multi-tenant
- Live Demo: https://q1inyxqs.run.complete.dev
- Complete.dev AI Agent Hackathon · February 2026

---

## SLIDE 2 — THE PROBLEM

**The best engineers don't look like the best engineers.**

Traditional ATS systems rank candidates by:
- ❌ Years of experience
- ❌ Previous company names
- ❌ Credential keywords

But in an AI-first world, the best startup engineers are defined by:
- ✅ Won a hackathon last month
- ✅ Learned LangGraph 3 months ago
- ✅ Shipped an LLM tool used by 500 people
- ✅ 89 GitHub commits in the last 30 days

> *"Every startup I've talked to has the same problem: they filter by credentials
> and get experienced-but-stuck engineers."*

---

## SLIDE 3 — THE INSIGHT

**Learning velocity > credential history**

| Candidate | Traditional ATS Rank | VelocityHire Rank |
|-----------|---------------------|-------------------|
| Jordan — 8 yrs Java, last commit 2yr ago | #1 | #4 |
| Elena — 6mo bootcamp, 89 commits, LLM tool | #5 | #1 |
| Marcus — AI hackathon winner last month | #3 | #2 |

**The Ranking Flip.** This is what VelocityHire is built to surface.

---

## SLIDE 4 — THE SOLUTION

**Three LangGraph AI agents working in sequence**

```
Candidate Profile
      ↓
┌─────────────────────────────┐
│  Agent 1 — Profile Analyzer │  Scores learning velocity (0–100)
│  Hackathons · Skills ·      │  40% hackathons · 25% skills
│  Certs · Recency            │  20% certs · 15% recency
└──────────────┬──────────────┘
               ↓ adaptability score
┌─────────────────────────────┐
│  Agent 2 — Job Matcher      │  Adaptability (60%) +
│  Role Fit · Culture Fit     │  Role fit (25%) + Culture (15%)
└──────────────┬──────────────┘
               ↓ match score + tier
┌─────────────────────────────┐
│  Agent 3 — Outreach Coord.  │  Auto-generates:
│  LinkedIn · Email ·         │  LinkedIn msg · Email ·
│  Follow-up · ATS Note       │  Follow-up · ATS recruiter note
└─────────────────────────────┘
```

One candidate profile in. Full personalised recruitment campaign out.

---

## SLIDE 5 — THE SCORING ENGINE

**Adaptability Score — 100 points**

| Dimension | Weight | What We Measure |
|-----------|--------|----------------|
| 🏆 Hackathons | 40 pts | Wins last 3mo = 20pts · 6mo = 15pts · 12mo = 10pts |
| ⚡ Skills | 25 pts | LangGraph · GenAI · Rust · Svelte adoption recency |
| 📚 Certifications | 20 pts | Cloud/AI certs · recency × relevance |
| 🕐 Recency | 15 pts | GitHub commits · blog posts · talks last 30/90 days |

**Threshold:** 70+ → Recommend for interview

**Outreach Tiers:**
- 🏆 85+ → PRIORITY — same-day fast-track
- ⭐ 70–84 → STANDARD — normal pipeline
- ✅ 55–69 → NURTURE — future-role framing
- 📋 <55 → ARCHIVE — passive acknowledgement

---

## SLIDE 6 — LIVE DEMO

**Try it now:** https://q1inyxqs.run.complete.dev

**What you'll see:**
1. ▶ Click "Run Full Pipeline Demo"
2. 5 candidates processed through all 3 agents in real time
3. Watch the ranking flip happen live
4. Agent 3 generates full outreach for each candidate automatically
5. Test a live Greenhouse/Lever/BambooHR webhook

**Demo highlights:**
- Marcus Rivera 🏆 — AI hackathon winner, LangGraph contributor → Score: 94
- Elena Voronova 🚀 — bootcamp grad, 89 commits, LLM tool → Score: 87
- Jordan Kim 📋 — 8 years Java, last commit 2yr ago → Score: 52

**2 commands to run locally:**
```bash
git clone https://github.com/agentic-wq/velocityhire
MOCK_MODE=true python -m uvicorn demo.app:app --port 8000
```

---

## SLIDE 7 — ENTERPRISE READY

**Not a toy. A production-ready intelligence layer.**

**ATS Integrations (live webhooks):**
| Provider | Event | Status |
|----------|-------|--------|
| 🌿 Greenhouse | candidate.created | ✅ Live |
| ⚙️ Lever | candidateCreated | ✅ Live |
| 🎋 BambooHR | employee.hired | ✅ Live |

**Multi-tenancy:**
- Full data isolation via `X-Company-ID` header
- Every API call scoped per company
- No separate DB instances needed

**Analytics dashboard:**
- Pipeline conversion rates
- Tier breakdown charts
- Predictive hiring insights

*The ATS doesn't change. The recruiter workflow doesn't change.
VelocityHire slots in as the intelligence layer.*

---

## SLIDE 8 — TECHNOLOGY

**Built on the right stack for agent systems**

| Layer | Technology | Why |
|-------|-----------|-----|
| Agent orchestration | LangGraph 0.2 (StateGraph) | Stateful, resumable, conditional routing |
| API framework | FastAPI + Uvicorn | Async, fast, OpenAPI auto-docs |
| Persistence | SQLite (demo) / PostgreSQL (prod) | Multi-tenant, 5 tables |
| Scoring | Rule-based MOCK_MODE / Deploy AI LLM | Works out-of-box, upgradeable |
| Analytics | Custom Python + Chart.js | Real-time pipeline dashboards |
| ATS | Webhook normalisers | Drop-in for existing tools |

**Why LangGraph specifically:**
Each agent is a separate `StateGraph` with conditional edges — extensible, swappable,
parallelisable per node without touching other agents.

---

## SLIDE 9 — BUSINESS MODEL & ROADMAP

**SaaS — per-seat or per-pipeline-run**

**Production roadmap (already written):**
| Phase | Timeline | Key Change |
|-------|----------|-----------|
| Phase 1 — Stabilise | 2 weeks | SQLite → PostgreSQL · Redis cache · JWT auth |
| Phase 2 — Scale | 6 weeks | LLM scoring live · Celery async · outcomes feedback |
| Phase 3 — Production | 8 weeks | Kubernetes · observability · HMAC webhook security |
| Phase 4 — Growth | Month 4+ | Multi-region · GDPR · LinkedIn API · GitHub direct |

**LLM cost at launch scale:**
~$0.02/candidate × 1,000 candidates/month = **$20/month**

**Market:**
- Global ATS market: $2.7B (2025) → $3.8B (2028)
- Target: Startups + boutique tech recruiters who need signal over noise

---

## SLIDE 10 — CLOSING

**The question we're answering:**

> *"Who's learning the fastest? — and for hiring in an AI-first world,
> that's the only question that matters."*

**What we built:**
- ✅ 3 LangGraph agents, fully functional
- ✅ Enterprise ATS integrations (Greenhouse · Lever · BambooHR)
- ✅ Multi-tenant architecture
- ✅ Scoring algorithm with learning velocity as core signal
- ✅ Auto-generated personalised outreach campaigns
- ✅ Production roadmap ready

**Try it:**
> 🔗 https://q1inyxqs.run.complete.dev

**Code:**
> 🐙 github.com/agentic-wq/velocityhire

---

*Built for the Complete.dev AI Agent Hackathon · February 2026*
*VelocityHire v5.0 · LangGraph · FastAPI · Multi-agent · Multi-tenant*
