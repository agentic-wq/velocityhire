# ⚡ VelocityHire — 3-Minute Demo Script

> **Complete.dev Hackathon 2026**
> Audience: Judges · Format: Live demo at https://q1inyxqs.run.complete.dev

---

## 0:00 — The Problem (30 seconds)

> *"Every startup I've talked to has the same hiring problem:
> they filter by credentials and get experienced-but-stuck engineers.
> The best people at an AI-first startup aren't the ones with 10 years on their CV —
> they're the ones who learned LangGraph last month, won a hackathon last week,
> and shipped something 500 people use today.*
>
> *Traditional ATS systems can't see that. VelocityHire can."*

**Key point to land:** The innovation is the scoring signal, not the pipeline automation.
We rank by **learning trajectory**, not credential history.

---

## 0:30 — Architecture overview (20 seconds)

Point to the pipeline diagram on screen:

> *"Three LangGraph agents working in sequence.
> Agent 1 scores adaptability — hackathons, recent tech adoption, fresh certifications, recency.
> Agent 2 combines that with role fit and culture fit to get a job match score.
> Agent 3 generates a fully personalised outreach campaign — LinkedIn message,
> email, follow-up, and ATS recruiter note — automatically tiered by priority."*

---

## 0:50 — Live pipeline demo (60 seconds)

**Click ▶ Run Full Pipeline Demo**

> *"I'm running five real candidate profiles right now — watch the agents work."*

Point out as cards animate:

- **Marcus Rivera 🏆** — "Won an AI hackathon last month, LangGraph contributor — watch that score"
- **Elena Voronova 🚀** — "Six-month bootcamp grad, but 89 GitHub commits last month and an LLM tool with 500 users — she beats the 10-year Java developer"
- **Jordan Kim 📋** — "Senior Java dev, 8 years experience, last commit 2 years ago — scores last"

When results appear:

> *"Look at the ranking. Elena — 6 months experience — scores higher than Jordan's 8 years
> because her **learning velocity** is off the charts. That's the insight traditional hiring misses."*

Scroll to Outreach section — click a PRIORITY candidate's tabs:

> *"And Agent 3 already wrote the LinkedIn message, the email, the follow-up,
> and the internal ATS note. The recruiter just clicks send."*

---

## 1:50 — Enterprise ATS integrations (30 seconds)

Scroll to the ATS section — click **🌿 Test Greenhouse Webhook**:

> *"This is what makes it enterprise-ready. A real Greenhouse webhook fires,
> VelocityHire normalises the payload, runs it through Agent 1 instantly,
> and returns a score. Same for Lever and BambooHR.*
>
> *The ATS doesn't change. The recruiter workflow doesn't change.
> VelocityHire just slots in as the intelligence layer."*

---

## 2:20 — Analytics & multi-tenancy (20 seconds)

> *"Everything persists to a shared SQLite database, fully multi-tenant —
> each company's data is isolated by `X-Company-ID` header.*
>
> *The analytics dashboard shows pipeline conversion rates, tier breakdowns,
> and predictive insights — like which adaptability score threshold
> correlates with interview success."*

---

## 2:40 — Closing (20 seconds)

> *"The system is live, the code is on GitHub, and it runs in two commands:*
>
> `git clone https://github.com/agentic-wq/velocityhire`
> `MOCK_MODE=true python -m uvicorn demo.app:app --port 8000`
>
> *The question we're answering isn't 'who has the most experience?'
> It's 'who's learning the fastest?' — and for hiring in an AI-first world,
> that's the only question that matters."*

---

## Likely judge questions + answers

**Q: Why LangGraph specifically?**
> "LangGraph gives us stateful, resumable agent graphs with conditional routing.
> Each agent is a separate StateGraph — we can extend, swap, or parallelise
> individual nodes without touching the others. It's the right tool for a
> multi-step, multi-signal scoring pipeline."

**Q: What's MOCK_MODE?**
> "Rule-based deterministic scoring — no LLM API key needed to run.
> We designed it so the system works out of the box.
> Flip `MOCK_MODE=false` and wire in a Deploy AI or OpenAI key
> to get LLM-enhanced reasoning on each score dimension."

**Q: How does multi-tenancy work?**
> "Every API call accepts an `X-Company-ID` header.
> All DB reads and writes are scoped to that company_id —
> full data isolation with no separate DB instances needed."

**Q: Could this be gamed by people padding their profiles with hackathon claims?**
> "Great question — yes, in the current version.
> A production system would cross-reference GitHub activity,
> hackathon databases like Devpost, and LinkedIn event attendance.
> The scoring model is the MVP; the data validation layer is the roadmap."

**Q: What's the business model?**
> "SaaS, per-seat or per-pipeline-run. The multi-tenant architecture
> is already production-ready. The ATS integrations make it a drop-in
> for any company already using Greenhouse or Lever."

---

## Demo tips

- **Run the pipeline once before the presentation** so analytics charts are pre-populated
- **Have the ATS event log visible** when you start — shows prior scoring activity = credibility
- **Keep Marcus Rivera and Elena Voronova** as the story — the contrast between the 🏆 hackathon winner
  and the bootcamp grad beating the senior Java developer is the most compelling moment
- If the pipeline takes > 15 seconds: *"You can see it's processing each agent in sequence —
  in production this would run in parallel for sub-second scoring"*
