"""
VelocityHire — Demo Orchestrator
=================================
Unified hackathon demo app that runs all 3 LangGraph agents in a
single end-to-end pipeline with a visually rich UI.

  GET  /           → Main demo UI (full-screen, dark theme)
  POST /demo/run   → Start background pipeline run, returns run_id
  GET  /demo/progress/{run_id} → Live progress JSON (poll at 600ms)
  GET  /analytics/data         → Full analytics JSON
  GET  /health                 → Status check
"""

import sys
import json
import logging
import threading
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
WORKSPACE = str(ROOT)
LOG_DIR   = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")
os.environ.setdefault("MOCK_MODE", "true")

sys.path.insert(0, WORKSPACE)
sys.path.insert(0, str(ROOT / "agent1"))
sys.path.insert(0, str(ROOT / "agent2"))
sys.path.insert(0, str(ROOT / "agent3"))

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
    handlers=[
        logging.FileHandler(LOG_DIR / "demo.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("velocityhire.demo")

# ── Import agents ─────────────────────────────────────────────────────────────
from agent_1 import analyze_profile
from agent_2 import match_candidate
from agent_3 import generate_outreach

logger.info("All 3 agents imported successfully")

# ── Import shared DB & analytics ──────────────────────────────────────────────
try:
    from shared.db_memory import (
        save_candidate_score, save_job_match, save_outreach,
        get_pipeline_summary, get_db_stats,
    )
    DB_ENABLED = True
    logger.info("Shared DB layer enabled")
except ImportError as e:
    DB_ENABLED = False
    logger.warning("DB layer not available: %s", e)
    def save_candidate_score(*a, **kw): return None
    def save_job_match(*a, **kw):       return None
    def save_outreach(*a, **kw):        return None
    def get_pipeline_summary(*a, **kw): return {}
    def get_db_stats(*a, **kw):         return {}

try:
    from shared.analytics import get_full_analytics
    ANALYTICS_ENABLED = True
    logger.info("Analytics module enabled")
except ImportError:
    ANALYTICS_ENABLED = False
    def get_full_analytics(*a, **kw): return {}

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="VelocityHire Demo", version="5.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ── Demo data ─────────────────────────────────────────────────────────────────
DEMO_JOB = {
    "job_title":       "Senior AI Engineer",
    "job_description": (
        "We are building the next generation of AI-powered developer tools. "
        "Looking for a senior engineer who can ship fast, work with LLMs, build agents, "
        "and thrive in a startup environment. You'll own features end-to-end and drive "
        "technical decisions. Startup experience, hackathon wins, and LangChain/LangGraph "
        "knowledge are strong positives."
    ),
    "required_skills": [
        "Python", "LangChain", "LangGraph", "FastAPI", "React",
        "AWS", "LLM", "Vector DB", "TypeScript",
    ],
    "company_name":  "VelocityHire",
    "recruiter_name":"Sarah Chen",
}

DEMO_CANDIDATES: List[Dict] = [
    {
        "name":  "Marcus Rivera",
        "emoji": "🏆",
        "profile": (
            "Marcus Rivera — Senior Software Engineer\n"
            "Skills: Python, TypeScript, React, Next.js, FastAPI, LangChain, LangGraph, "
            "PostgreSQL, AWS, Svelte\n"
            "Experience:\n"
            "  - NeuralStack (2022-present): Lead engineer. Built AI-powered code review "
            "system with LangGraph multi-agent pipeline. Shipped v1 in 6 weeks.\n"
            "  - RapidStart (2020-2022): Full-stack engineer at seed-stage startup. "
            "Founding-team member. Shipped MVP in 3 months.\n"
            "Hackathons:\n"
            "  - AI Builders Summit (1 month ago) — WINNER, built multi-agent recruitment "
            "tool in 48 hours using LangGraph. Won best AI/ML hack.\n"
            "  - Junction Helsinki (3 months ago) — Finalist, GenAI travel planner with "
            "vector search, led team of 5.\n"
            "  - HackMIT (8 months ago) — Participant.\n"
            "Certifications:\n"
            "  - AWS Certified Developer (2 months ago)\n"
            "  - LangChain & LangGraph Advanced Bootcamp (1 month ago)\n"
            "GitHub: 67 commits last month. Active open-source contributor to LangGraph.\n"
            "Blog post on multi-agent systems published 2 weeks ago. "
            "Built a vector DB benchmark tool that went viral on HN.\n"
            "Startup experience: seed-stage founding team at RapidStart."
        ),
    },
    {
        "name":  "Priya Sharma",
        "emoji": "⭐",
        "profile": (
            "Priya Sharma — ML Engineer\n"
            "Skills: Python, TensorFlow, PyTorch, AWS SageMaker, FastAPI, Docker, "
            "Kubernetes, LLM fine-tuning, LangChain, Pinecone vector DB\n"
            "Experience:\n"
            "  - DeepMind (2021-present): ML engineer. LLM fine-tuning, evaluation "
            "pipelines, and agent orchestration. Led team of 3.\n"
            "  - DataFlow Startup (2019-2021): Early-stage Series A startup. Built ML "
            "platform from scratch, shipped 4 products.\n"
            "Hackathons:\n"
            "  - Google AI Hackathon (2 months ago) — WINNER, best use of Gemini, "
            "led team of 4. Shipped RAG-based search tool.\n"
            "Certifications:\n"
            "  - AWS Certified Machine Learning Specialty (3 months ago)\n"
            "  - Google Cloud Professional Data Engineer (5 months ago)\n"
            "GitHub: 42 commits last month. Regular contributor to HuggingFace.\n"
            "Published blog: Fine-tuning LLMs for recruitment (last month).\n"
            "Cross-functional work: Led product and engineering collaboration for 6 months.\n"
            "Startup experience at DataFlow — Series A, early employee."
        ),
    },
    {
        "name":  "Alex Chen",
        "emoji": "✅",
        "profile": (
            "Alex Chen — Full-Stack Developer\n"
            "Skills: JavaScript, React, Node.js, Python, PostgreSQL, Docker, GCP, "
            "Next.js, TypeScript\n"
            "Experience:\n"
            "  - Acme Corp (2020-present): Senior developer. Led migration to "
            "microservices. Managed team of 4 engineers.\n"
            "  - WebAgency (2018-2020): Front-end developer, built 20+ client sites.\n"
            "Hackathons:\n"
            "  - Local Startup Weekend (6 months ago) — Finalist, built SaaS prototype.\n"
            "Certifications:\n"
            "  - GCP Professional Cloud Developer (4 months ago)\n"
            "GitHub: 18 commits last month. Started learning Next.js and AI integrations.\n"
            "Recently started exploring LangChain in side projects."
        ),
    },
    {
        "name":  "Jordan Kim",
        "emoji": "📋",
        "profile": (
            "Jordan Kim — Backend Developer\n"
            "Skills: Java, Spring Boot, MySQL, REST APIs, Jenkins, Maven\n"
            "Experience:\n"
            "  - Enterprise Corp (2018-present): Backend developer, maintaining legacy "
            "payment processing systems. Works on well-established codebase.\n"
            "  - Tech Solutions (2015-2018): Junior developer, internal tooling.\n"
            "No hackathon participation.\n"
            "Certifications:\n"
            "  - Oracle Java SE Certification (2 years ago)\n"
            "GitHub: 5 commits last month, mostly minor bug fixes.\n"
            "No recent new technology adoption or learning signals detected."
        ),
    },
    {
        "name":  "Elena Voronova",
        "emoji": "🚀",
        "profile": (
            "Elena Voronova — AI Developer (Career Transition)\n"
            "Skills: Python, FastAPI, LangChain, LangGraph, React, Svelte, PostgreSQL, "
            "Pinecone vector DB, Docker\n"
            "Experience:\n"
            "  - Independent AI Developer (2023-present): Built and shipped 3 AI-powered "
            "SaaS tools independently. MVP to 500+ users in 3 months.\n"
            "  - Full-stack + AI Bootcamp graduate (6 months ago). Top of cohort.\n"
            "Hackathons:\n"
            "  - AI App Challenge (2 months ago) — WINNER, best AI product, solo "
            "project, RAG-based document Q&A. Judges called it production-ready.\n"
            "  - Web3 Buildathon (4 months ago) — Participant.\n"
            "Certifications:\n"
            "  - LangChain Developer Certification (1 month ago)\n"
            "  - FastAPI Advanced Course (2 months ago)\n"
            "GitHub: 89 commits last month — building AI tools in public.\n"
            "Shipped an LLM-powered resume analyzer used by 500+ people (last month).\n"
            "Startup-mode experience: running her own solo products, shipped and launched.\n"
            "Founding member of local AI meetup, 200+ members."
        ),
    },
]

# ── In-memory run store ───────────────────────────────────────────────────────
_runs: Dict[str, Any] = {}


def _run_pipeline(run_id: str, company_id: str = "demo") -> None:
    """Execute all 3 agents for all demo candidates (runs in background thread)."""
    run = _runs[run_id]
    run["status"]     = "running"
    run["started_at"] = datetime.utcnow().isoformat()

    results = []

    for idx, cand in enumerate(DEMO_CANDIDATES):
        name    = cand["name"]
        profile = cand["profile"]

        run["current_candidate"] = name
        run["current_idx"]       = idx

        try:
            # ── Agent 1: Profile Analysis ────────────────────────────────────
            run["candidates"][idx]["stage"] = "agent1"
            logger.info("[%s] Agent 1 → %s", run_id, name)

            a1           = analyze_profile(profile)
            adapt_score  = a1.get("adaptability_score", 50)
            adapt_tier   = a1.get("tier", "Standard")
            recommend_a1 = a1.get("recommend_interview", False)

            run["candidates"][idx]["adaptability_score"] = adapt_score
            run["candidates"][idx]["adaptability_tier"]  = adapt_tier

            if DB_ENABLED:
                try:
                    save_candidate_score(
                        profile, a1,
                        candidate_name=name,
                        company_id=company_id,
                    )
                except Exception as e:
                    logger.warning("save_candidate_score failed (non-fatal): %s", e)

            # ── Agent 2: Job Matching ─────────────────────────────────────────
            run["candidates"][idx]["stage"] = "agent2"
            logger.info("[%s] Agent 2 → %s", run_id, name)

            a2 = match_candidate(
                job_title=DEMO_JOB["job_title"],
                job_description=DEMO_JOB["job_description"],
                required_skills=DEMO_JOB["required_skills"],
                candidate_name=name,
                candidate_profile=profile,
                adaptability_score=adapt_score,
                adaptability_tier=adapt_tier,
            )

            match_score     = a2.get("total_match_score", 50)
            match_tier      = a2.get("match_tier", "Standard")
            breakdown       = a2.get("score_breakdown", {})
            matched_skills  = breakdown.get("role_fit", {}).get("matched_skills", [])
            startup_exp     = breakdown.get("culture_fit", {}).get("startup_experience", False)
            recommend       = a2.get("recommend_interview", False)
            reasoning       = a2.get("reasoning", "")

            run["candidates"][idx]["match_score"] = match_score
            run["candidates"][idx]["match_tier"]  = match_tier

            if DB_ENABLED:
                try:
                    save_job_match(
                        {
                            **a2,
                            "candidate_name": name,
                            "job_title":      DEMO_JOB["job_title"],
                        },
                        company_id=company_id,
                    )
                except Exception as e:
                    logger.warning("save_job_match failed (non-fatal): %s", e)

            # ── Agent 3: Outreach Generation ──────────────────────────────────
            run["candidates"][idx]["stage"] = "agent3"
            logger.info("[%s] Agent 3 → %s", run_id, name)

            a3 = generate_outreach(
                candidate_name=name,
                candidate_profile=profile,
                job_title=DEMO_JOB["job_title"],
                company_name=DEMO_JOB["company_name"],
                recruiter_name=DEMO_JOB["recruiter_name"],
                total_match_score=match_score,
                match_tier=match_tier,
                adaptability_score=adapt_score,
                adaptability_tier=adapt_tier,
                matched_skills=matched_skills,
                startup_experience=startup_exp,
                recommend_interview=recommend,
                reasoning=reasoning,
            )

            outreach_tier = a3.get("outreach_tier", "ARCHIVE")
            campaign      = a3.get("campaign", {})

            run["candidates"][idx]["outreach_tier"] = outreach_tier
            run["candidates"][idx]["stage"]         = "done"

            if DB_ENABLED:
                try:
                    save_outreach(
                        {
                            "candidate_name":    name,
                            "job_title":         DEMO_JOB["job_title"],
                            "company_name":      DEMO_JOB["company_name"],
                            "recruiter_name":    DEMO_JOB["recruiter_name"],
                            "total_match_score": match_score,
                            "adaptability_score":adapt_score,
                            "outreach_tier":     outreach_tier,
                            "tone":              a3.get("tone", ""),
                            "key_highlights":    json.dumps(a3.get("key_highlights", [])),
                            "linkedin_message":  campaign.get("linkedin_message", ""),
                            "email_subject":     campaign.get("email", {}).get("subject", ""),
                            "email_body":        campaign.get("email", {}).get("body", ""),
                            "followup_subject":  campaign.get("followup", {}).get("subject", ""),
                            "followup_body":     campaign.get("followup", {}).get("body", ""),
                            "recruiter_note":    campaign.get("recruiter_note", ""),
                        },
                        company_id=company_id,
                    )
                except Exception as e:
                    logger.warning("save_outreach failed (non-fatal): %s", e)

            results.append({
                "name":               name,
                "emoji":              cand["emoji"],
                "adaptability_score": adapt_score,
                "adaptability_tier":  adapt_tier,
                "match_score":        match_score,
                "match_tier":         match_tier,
                "outreach_tier":      outreach_tier,
                "recommend":          recommend,
                "key_highlights":     a3.get("key_highlights", []),
                "linkedin_message":   campaign.get("linkedin_message", ""),
                "email_subject":      campaign.get("email", {}).get("subject", ""),
                "email_body":         campaign.get("email", {}).get("body", ""),
                "followup_subject":   campaign.get("followup", {}).get("subject", ""),
                "followup_body":      campaign.get("followup", {}).get("body", ""),
                "recruiter_note":     campaign.get("recruiter_note", ""),
            })

            logger.info("[%s] ✅ Done → %s  adapt=%d match=%d tier=%s",
                        run_id, name, adapt_score, match_score, outreach_tier)

        except Exception as exc:
            logger.error("[%s] ❌ Pipeline error for %s: %s", run_id, name, exc)
            run["candidates"][idx]["stage"] = "error"
            run["candidates"][idx]["error"] = str(exc)

    run["status"]       = "done"
    run["results"]      = results
    run["completed_at"] = datetime.utcnow().isoformat()
    logger.info("[%s] Pipeline complete — %d candidates processed", run_id, len(results))


# ── HTML ──────────────────────────────────────────────────────────────────────
DEMO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VelocityHire — AI Recruitment Intelligence</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg:#080812; --surface:#10101e; --surface2:#16162a; --border:#2a2a4a;
  --primary:#6c63ff; --primary-l:#a78bfa; --success:#22c55e; --warn:#f59e0b;
  --danger:#ef4444; --text:#e2e8f0; --muted:#94a3b8; --faint:#64748b;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Inter',-apple-system,sans-serif;min-height:100vh}

/* ── Hero ── */
.hero{background:linear-gradient(135deg,#060610 0%,#12082a 50%,#061220 100%);
  border-bottom:1px solid var(--border);padding:56px 24px 48px;text-align:center;
  position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;inset:-50%;
  background:radial-gradient(circle at 50% 50%,rgba(108,99,255,.08) 0%,transparent 60%);
  animation:hpulse 5s ease-in-out infinite}
@keyframes hpulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.12);opacity:.6}}
.logo{font-size:2.6rem;font-weight:900;position:relative;
  background:linear-gradient(135deg,#6c63ff,#a78bfa 45%,#22c55e);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.tagline{color:var(--muted);font-size:1.05rem;margin-bottom:4px;position:relative}
.sub{color:var(--faint);font-size:.83rem;position:relative;margin-bottom:20px}
.badges{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:16px 0;position:relative}
.badge{background:rgba(108,99,255,.12);border:1px solid rgba(108,99,255,.35);
  color:#a78bfa;padding:4px 12px;border-radius:20px;font-size:.78rem;font-weight:500}
.run-btn{background:linear-gradient(135deg,#6c63ff,#a78bfa);color:#fff;border:none;
  padding:16px 52px;border-radius:12px;font-size:1.05rem;font-weight:700;cursor:pointer;
  transition:all .2s;box-shadow:0 0 32px rgba(108,99,255,.45);position:relative;margin-top:8px}
.run-btn:hover{transform:translateY(-2px);box-shadow:0 0 55px rgba(108,99,255,.65)}
.run-btn:disabled{opacity:.55;cursor:not-allowed;transform:none}
.status-msg{text-align:center;padding:14px;color:var(--muted);font-size:.9rem;margin-top:12px}
.status-msg.running{color:var(--primary)}

/* ── Layout ── */
.container{max-width:1380px;margin:0 auto;padding:36px 20px}
.section-title{font-size:1.15rem;font-weight:700;margin-bottom:18px;
  display:flex;align-items:center;gap:10px}
.dot{width:8px;height:8px;border-radius:50%;background:var(--primary);flex-shrink:0}

/* ── Pipeline diagram ── */
.pipe-flow{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:0;
  margin-bottom:36px;padding:20px 24px;background:var(--surface);
  border-radius:16px;border:1px solid var(--border)}
.pipe-step{display:flex;flex-direction:column;align-items:center;gap:5px;padding:12px 20px}
.pipe-icon{width:50px;height:50px;border-radius:13px;display:flex;align-items:center;
  justify-content:center;font-size:1.5rem;background:rgba(108,99,255,.12);
  border:1px solid rgba(108,99,255,.28)}
.pipe-label{font-size:.78rem;color:var(--muted);font-weight:600;text-align:center}
.pipe-sub{font-size:.7rem;color:var(--faint);text-align:center}
.pipe-arrow{color:var(--border);font-size:1.3rem;padding:0 6px}
.pipe-divider{width:1px;height:60px;background:var(--border);margin:0 24px}
.pipe-meta{padding:0 20px;text-align:left}
.pipe-meta-title{font-size:.72rem;color:var(--faint);text-transform:uppercase;
  letter-spacing:.05em;margin-bottom:5px}
.pipe-meta-val{font-size:.9rem;font-weight:700}
.pipe-meta-sub{font-size:.75rem;color:var(--muted);margin-top:2px}
.pipe-weights{display:grid;grid-template-columns:1fr 1fr;gap:3px 16px;margin-top:4px}
.pw{font-size:.75rem;color:var(--text)}
.pw span{color:var(--primary);font-weight:700}

/* ── Candidates ── */
.candidates-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:36px}
@media(max-width:1100px){.candidates-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:680px){.candidates-grid{grid-template-columns:repeat(2,1fr)}}

.c-card{background:var(--surface);border:1px solid var(--border);
  border-radius:16px;padding:20px;transition:all .35s}
.c-card.active{border-color:var(--primary);box-shadow:0 0 22px rgba(108,99,255,.25)}
.c-card.done{border-color:var(--success);box-shadow:0 0 16px rgba(34,197,94,.15)}
.c-card.error{border-color:var(--danger)}
.c-emoji{font-size:2rem;margin-bottom:8px}
.c-name{font-weight:700;font-size:.92rem;margin-bottom:4px;line-height:1.2}
.c-stage{font-size:.73rem;color:var(--muted);margin-bottom:12px;min-height:16px}
.stage-dots{display:flex;gap:7px;margin-bottom:14px}
.sdot{width:10px;height:10px;border-radius:50%;background:var(--border);transition:all .3s}
.sdot.active{background:var(--primary);box-shadow:0 0 8px var(--primary);
  animation:dp 1s ease-in-out infinite}
.sdot.done{background:var(--success);box-shadow:none;animation:none}
@keyframes dp{0%,100%{transform:scale(1)}50%{transform:scale(1.4)}}
.c-scores{display:flex;flex-direction:column;gap:7px}
.score-row{display:flex;justify-content:space-between;align-items:center}
.score-lbl{font-size:.7rem;color:var(--muted)}
.score-val{font-size:.85rem;font-weight:700}

/* ── Results table ── */
.tbl-wrap{background:var(--surface);border-radius:16px;border:1px solid var(--border);
  overflow:auto;margin-bottom:36px}
table{width:100%;border-collapse:collapse;min-width:620px}
thead tr{background:var(--surface2);border-bottom:1px solid var(--border)}
th{padding:13px 18px;text-align:left;font-size:.75rem;font-weight:600;
  color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
td{padding:13px 18px;border-bottom:1px solid rgba(42,42,74,.5);font-size:.88rem}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(108,99,255,.04)}
.tier-badge{padding:4px 10px;border-radius:8px;font-size:.72rem;font-weight:700;text-transform:uppercase}
.tP{background:rgba(34,197,94,.14);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
.tS{background:rgba(108,99,255,.14);color:#6c63ff;border:1px solid rgba(108,99,255,.3)}
.tN{background:rgba(245,158,11,.14);color:#f59e0b;border:1px solid rgba(245,158,11,.3)}
.tA{background:rgba(100,116,139,.14);color:#94a3b8;border:1px solid rgba(100,116,139,.3)}
.sbar{display:flex;align-items:center;gap:8px}
.sbar-track{flex:1;height:5px;background:var(--border);border-radius:3px;overflow:hidden;min-width:60px}
.sbar-fill{height:100%;border-radius:3px;transition:width 1.2s ease}
.sbar-val{font-weight:700;font-size:.82rem;min-width:28px;text-align:right}

/* ── Outreach cards ── */
.outreach-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));
  gap:18px;margin-bottom:36px}
.oc{background:var(--surface);border-radius:16px;border:1px solid var(--border);overflow:hidden}
.oc-head{padding:14px 18px;background:var(--surface2);border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center}
.oc-name{font-weight:700;font-size:.92rem}
.oc-tabs{display:flex;padding:0 18px;border-bottom:1px solid var(--border)}
.oc-tab{padding:9px 14px;font-size:.78rem;cursor:pointer;color:var(--muted);
  border:none;border-bottom:2px solid transparent;background:none;transition:all .2s}
.oc-tab.active{color:var(--primary);border-bottom-color:var(--primary)}
.oc-body{padding:15px 18px;font-size:.8rem;color:var(--muted);white-space:pre-wrap;
  max-height:200px;overflow-y:auto;line-height:1.65}

/* ── Analytics ── */
.analytics-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));
  gap:18px;margin-bottom:40px}
.an-card{background:var(--surface);border-radius:16px;border:1px solid var(--border);padding:22px}
.an-title{font-size:.85rem;font-weight:600;color:var(--muted);margin-bottom:14px}
.funnel-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.stat-box{background:var(--surface2);border-radius:10px;padding:14px;text-align:center}
.stat-num{font-size:1.9rem;font-weight:900;
  background:linear-gradient(135deg,var(--primary),var(--primary-l));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-lbl{font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:2px}

/* ── Insights ── */
.insights-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
  gap:16px;margin-bottom:40px}
.insight-card{background:var(--surface);border-radius:14px;padding:20px;
  border-left:3px solid var(--primary);border-top:1px solid var(--border);
  border-right:1px solid var(--border);border-bottom:1px solid var(--border)}
.insight-icon{font-size:1.6rem;margin-bottom:8px}
.insight-title{font-size:.85rem;font-weight:600;color:var(--muted);margin-bottom:4px}
.insight-val{font-size:1.8rem;font-weight:900;margin-bottom:4px}
.insight-detail{font-size:.75rem;color:var(--muted);margin-bottom:8px;line-height:1.5}
.insight-rec{font-size:.73rem;color:var(--faint);font-style:italic;line-height:1.5}

/* ── Utils ── */
.hidden{display:none!important}
.spinner{display:inline-block;width:14px;height:14px;
  border:2px solid rgba(108,99,255,.3);border-top-color:var(--primary);
  border-radius:50%;animation:spin .75s linear infinite;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
</style>
</head>
<body>

<!-- ── Hero ──────────────────────────────────────────────────────── -->
<div class="hero">
  <div style="position:relative;z-index:1">
    <div class="logo">⚡ VelocityHire</div>
    <div class="tagline">AI-Powered Recruitment Intelligence · Complete.dev Hackathon Demo</div>
    <div class="sub">
      Identify the candidates with the highest <em>learning velocity</em> — not just years of experience
    </div>
    <div class="badges">
      <span class="badge">🤖 3 LangGraph Agents</span>
      <span class="badge">⚡ Real-time Pipeline</span>
      <span class="badge">🏢 Multi-tenant</span>
      <span class="badge">📊 Analytics Dashboard</span>
      <span class="badge">🎯 Adaptive Scoring</span>
      <span class="badge">📧 Auto Outreach Gen</span>
      <span class="badge">💾 SQLite Persistence</span>
    </div>
    <button class="run-btn" id="runBtn" onclick="runDemo()">
      ▶&nbsp; Run Full Pipeline Demo
    </button>
    <div id="statusMsg" class="status-msg hidden"></div>
  </div>
</div>

<!-- ── Main ───────────────────────────────────────────────────────── -->
<div class="container">

  <!-- Pipeline diagram -->
  <div class="pipe-flow">
    <div class="pipe-step">
      <div class="pipe-icon">🔍</div>
      <div class="pipe-label">Agent 1</div>
      <div class="pipe-sub">Profile Analyzer</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">
      <div class="pipe-icon">🎯</div>
      <div class="pipe-label">Agent 2</div>
      <div class="pipe-sub">Job Matcher</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">
      <div class="pipe-icon">📧</div>
      <div class="pipe-label">Agent 3</div>
      <div class="pipe-sub">Outreach Gen</div>
    </div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">
      <div class="pipe-icon">✅</div>
      <div class="pipe-label">Complete</div>
      <div class="pipe-sub">Campaign Ready</div>
    </div>
    <div class="pipe-divider"></div>
    <div class="pipe-meta">
      <div class="pipe-meta-title">Scoring Weights</div>
      <div class="pipe-weights">
        <div class="pw">🏆 Hackathons <span>40%</span></div>
        <div class="pw">⚡ Skills <span>25%</span></div>
        <div class="pw">📚 Certs <span>20%</span></div>
        <div class="pw">🕐 Recency <span>15%</span></div>
      </div>
    </div>
    <div class="pipe-divider"></div>
    <div class="pipe-meta">
      <div class="pipe-meta-title">Demo Role</div>
      <div class="pipe-meta-val">Senior AI Engineer</div>
      <div class="pipe-meta-sub">VelocityHire · 5 Candidates</div>
    </div>
  </div>

  <!-- Candidate cards -->
  <div class="section-title"><span class="dot"></span>Candidate Pipeline</div>
  <div class="candidates-grid" id="candidatesGrid"></div>

  <!-- Results section (hidden until done) -->
  <div id="resultsSection" class="hidden">

    <!-- Ranked results table -->
    <div class="section-title">
      <span class="dot" style="background:#22c55e"></span>Pipeline Results — Ranked by Score
    </div>
    <div class="tbl-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th><th>Candidate</th><th>Adaptability</th>
            <th>Job Match</th><th>Outreach Tier</th><th>Action</th>
          </tr>
        </thead>
        <tbody id="resultsBody"></tbody>
      </table>
    </div>

    <!-- Outreach preview -->
    <div class="section-title">
      <span class="dot" style="background:#f5a623"></span>Generated Outreach Campaigns
      <span style="font-size:.8rem;color:var(--muted);font-weight:400">(PRIORITY &amp; STANDARD)</span>
    </div>
    <div class="outreach-grid" id="outreachGrid"></div>

    <!-- Predictive insights -->
    <div class="section-title">
      <span class="dot" style="background:#a78bfa"></span>Predictive Insights
    </div>
    <div class="insights-grid" id="insightsGrid"></div>

    <!-- Analytics charts -->
    <div class="section-title">
      <span class="dot" style="background:#6c63ff"></span>Pipeline Analytics
    </div>
    <div class="analytics-grid">
      <div class="an-card">
        <div class="an-title">📊 Pipeline Funnel</div>
        <div class="funnel-grid" id="funnelStats"></div>
      </div>
      <div class="an-card">
        <div class="an-title">🏷️ Outreach Tier Breakdown</div>
        <canvas id="tierChart" height="190"></canvas>
      </div>
      <div class="an-card">
        <div class="an-title">📈 Adaptability Score Distribution</div>
        <canvas id="scoreChart" height="190"></canvas>
      </div>
    </div>

  </div><!-- /resultsSection -->
</div><!-- /container -->

<script>
const CANDIDATES=[
  {name:"Marcus Rivera",  emoji:"🏆"},
  {name:"Priya Sharma",   emoji:"⭐"},
  {name:"Alex Chen",      emoji:"✅"},
  {name:"Jordan Kim",     emoji:"📋"},
  {name:"Elena Voronova", emoji:"🚀"},
];

let currentRunId=null, pollInterval=null;
let tierChartInst=null, scoreChartInst=null;

/* ── Card init ──────────────────────────────────────────────────── */
function initCards(){
  document.getElementById('candidatesGrid').innerHTML=
    CANDIDATES.map((c,i)=>`
      <div class="c-card" id="card-${i}">
        <div class="c-emoji">${c.emoji}</div>
        <div class="c-name">${c.name}</div>
        <div class="c-stage" id="stage-${i}">Waiting to start…</div>
        <div class="stage-dots">
          <div class="sdot" id="d${i}0" title="Agent 1: Profile Analysis"></div>
          <div class="sdot" id="d${i}1" title="Agent 2: Job Matching"></div>
          <div class="sdot" id="d${i}2" title="Agent 3: Outreach Gen"></div>
        </div>
        <div class="c-scores">
          <div class="score-row"><span class="score-lbl">Adaptability</span>
            <span class="score-val" id="a${i}" style="color:var(--faint)">—</span></div>
          <div class="score-row"><span class="score-lbl">Job Match</span>
            <span class="score-val" id="m${i}" style="color:var(--faint)">—</span></div>
          <div class="score-row"><span class="score-lbl">Tier</span>
            <span class="score-val" id="t${i}" style="color:var(--faint)">—</span></div>
        </div>
      </div>`).join('');
}

/* ── Start run ──────────────────────────────────────────────────── */
async function runDemo(){
  const btn=document.getElementById('runBtn');
  const msg=document.getElementById('statusMsg');
  btn.disabled=true;
  btn.textContent='⏳ Running Pipeline…';
  msg.className='status-msg running';
  msg.innerHTML='<span class="spinner"></span>Initialising LangGraph pipeline…';
  msg.classList.remove('hidden');
  document.getElementById('resultsSection').classList.add('hidden');
  initCards();
  try{
    const r=await fetch('/demo/run',{method:'POST'});
    const d=await r.json();
    currentRunId=d.run_id;
    if(pollInterval) clearInterval(pollInterval);
    pollInterval=setInterval(pollProgress,600);
  }catch(e){
    msg.textContent='Error starting pipeline — check server logs.';
    btn.disabled=false; btn.textContent='▶ Run Full Pipeline Demo';
  }
}

/* ── Poll progress ──────────────────────────────────────────────── */
async function pollProgress(){
  if(!currentRunId) return;
  try{
    const r=await fetch(`/demo/progress/${currentRunId}`);
    const d=await r.json();
    updateCards(d);
    if(d.status==='done'){
      clearInterval(pollInterval);
      const msg=document.getElementById('statusMsg');
      msg.innerHTML='✅ Pipeline complete — all 5 candidates processed';
      msg.className='status-msg';
      const btn=document.getElementById('runBtn');
      btn.disabled=false; btn.textContent='🔄 Run Again';
      showResults(d.results);
      loadAnalytics();
    }
  }catch(e){ console.error(e); }
}

/* ── Update cards ───────────────────────────────────────────────── */
const STAGE_DOTS={
  waiting:[0,0,0], agent1:[1,0,0], agent2:[2,1,0], agent3:[2,2,1], done:[2,2,2], error:[0,0,0]
};
const STAGE_LBL={
  waiting:'Waiting…', agent1:'🔍 Analysing profile…',
  agent2:'🎯 Matching job…', agent3:'📧 Generating outreach…',
  done:'✅ Complete', error:'❌ Error',
};
const TIER_COLOR={PRIORITY:'#22c55e',STANDARD:'#6c63ff',NURTURE:'#f59e0b',ARCHIVE:'#64748b'};

function scoreColor(s){return s>=70?'#22c55e':s>=55?'#f59e0b':'#94a3b8'}

function updateCards(data){
  (data.candidates||[]).forEach((c,i)=>{
    const stage=c.stage||'waiting';
    const card=document.getElementById(`card-${i}`);
    card.className='c-card'+(stage==='done'?' done':
      (data.current_idx===i&&stage!=='waiting'&&stage!=='error')?' active':
      stage==='error'?' error':'');
    document.getElementById(`stage-${i}`).textContent=STAGE_LBL[stage]||stage;
    const dots=STAGE_DOTS[stage]||[0,0,0];
    for(let d=0;d<3;d++){
      const el=document.getElementById(`d${i}${d}`);
      el.className='sdot'+(dots[d]===2?' done':dots[d]===1?' active':'');
    }
    if(c.adaptability_score!=null){
      const el=document.getElementById(`a${i}`);
      el.textContent=`${c.adaptability_score}/100`;el.style.color=scoreColor(c.adaptability_score);
    }
    if(c.match_score!=null){
      const el=document.getElementById(`m${i}`);
      el.textContent=`${c.match_score}/100`;el.style.color=scoreColor(c.match_score);
    }
    if(c.outreach_tier){
      const el=document.getElementById(`t${i}`);
      el.textContent=c.outreach_tier;el.style.color=TIER_COLOR[c.outreach_tier]||'#94a3b8';
    }
  });
}

/* ── Show results ───────────────────────────────────────────────── */
function showResults(results){
  if(!results||!results.length) return;
  const sorted=[...results].sort((a,b)=>(b.match_score||0)-(a.match_score||0));
  window._outreachData=sorted.filter(r=>['PRIORITY','STANDARD'].includes(r.outreach_tier));

  /* table */
  const tierCls={PRIORITY:'tP',STANDARD:'tS',NURTURE:'tN',ARCHIVE:'tA'};
  document.getElementById('resultsBody').innerHTML=sorted.map((r,i)=>{
    const a=r.adaptability_score||0, m=r.match_score||0, tier=r.outreach_tier||'ARCHIVE';
    const ac=scoreColor(a), mc=scoreColor(m);
    const rec=(['PRIORITY','STANDARD'].includes(tier))?'✅ Interview':'📋 Pipeline';
    return `<tr>
      <td style="color:var(--faint);font-size:.8rem">#${i+1}</td>
      <td><span style="font-size:1.1rem;margin-right:8px">${r.emoji||'👤'}</span><strong>${r.name}</strong></td>
      <td><div class="sbar"><div class="sbar-track"><div class="sbar-fill" style="width:${a}%;background:${ac}"></div></div>
        <span class="sbar-val" style="color:${ac}">${a}</span></div></td>
      <td><div class="sbar"><div class="sbar-track"><div class="sbar-fill" style="width:${m}%;background:${mc}"></div></div>
        <span class="sbar-val" style="color:${mc}">${m}</span></div></td>
      <td><span class="tier-badge ${tierCls[tier]||'tA'}">${tier}</span></td>
      <td style="color:${['PRIORITY','STANDARD'].includes(tier)?'#22c55e':'#94a3b8'}">${rec}</td>
    </tr>`;
  }).join('');

  /* outreach cards */
  document.getElementById('outreachGrid').innerHTML=
    (window._outreachData||[]).map((r,ri)=>`
      <div class="oc">
        <div class="oc-head">
          <div><span style="font-size:1.1rem;margin-right:7px">${r.emoji}</span>
            <span class="oc-name">${r.name}</span></div>
          <span class="tier-badge ${tierCls[r.outreach_tier]||'tA'}">${r.outreach_tier}</span>
        </div>
        <div class="oc-tabs">
          <button class="oc-tab active" onclick="switchTab(${ri},'linkedin',this)">LinkedIn</button>
          <button class="oc-tab" onclick="switchTab(${ri},'email',this)">Email</button>
          <button class="oc-tab" onclick="switchTab(${ri},'followup',this)">Follow-up</button>
          <button class="oc-tab" onclick="switchTab(${ri},'note',this)">ATS Note</button>
        </div>
        <div class="oc-body" id="oc-body-${ri}">${r.linkedin_message||'(no message)'}</div>
      </div>`).join('');

  document.getElementById('resultsSection').classList.remove('hidden');
  setTimeout(()=>document.getElementById('resultsSection').scrollIntoView({behavior:'smooth'}),200);
}

function switchTab(ri,tab,btn){
  btn.closest('.oc').querySelectorAll('.oc-tab').forEach(t=>t.classList.remove('active'));
  btn.classList.add('active');
  const r=window._outreachData[ri];
  const el=document.getElementById(`oc-body-${ri}`);
  if(tab==='linkedin') el.textContent=r.linkedin_message||'(none)';
  else if(tab==='email') el.textContent=`Subject: ${r.email_subject}\n\n${r.email_body}`;
  else if(tab==='followup') el.textContent=`Subject: ${r.followup_subject}\n\n${r.followup_body}`;
  else if(tab==='note') el.textContent=r.recruiter_note||'(no note)';
}

/* ── Load analytics ─────────────────────────────────────────────── */
async function loadAnalytics(){
  try{
    const r=await fetch('/analytics/data');
    const d=await r.json();

    /* Funnel */
    const f=d.funnel||{};
    document.getElementById('funnelStats').innerHTML=[
      [f.profiles_analyzed||0,'Profiles Analysed'],
      [f.jobs_matched||0,'Jobs Matched'],
      [f.campaigns_sent||0,'Campaigns Sent'],
      [f.priority_candidates||0,'Priority Candidates'],
    ].map(([n,l])=>`<div class="stat-box"><div class="stat-num">${n}</div>
      <div class="stat-lbl">${l}</div></div>`).join('');

    /* Tier chart */
    const td=d.tier_breakdown||{};
    if(tierChartInst) tierChartInst.destroy();
    if(td.labels&&td.values){
      tierChartInst=new Chart(document.getElementById('tierChart'),{
        type:'doughnut',
        data:{labels:td.labels,datasets:[{data:td.values,
          backgroundColor:['#22c55e','#6c63ff','#f59e0b','#64748b','#94a3b8'],borderWidth:0}]},
        options:{plugins:{legend:{labels:{color:'#94a3b8',font:{size:11}}}},cutout:'62%'}
      });
    }

    /* Score distribution */
    const sd=d.score_distribution||{};
    if(scoreChartInst) scoreChartInst.destroy();
    if(sd.labels&&sd.values){
      scoreChartInst=new Chart(document.getElementById('scoreChart'),{
        type:'bar',
        data:{labels:sd.labels,datasets:[{label:'Candidates',data:sd.values,
          backgroundColor:'rgba(108,99,255,.55)',borderColor:'#6c63ff',
          borderWidth:1,borderRadius:4}]},
        options:{scales:{
          x:{ticks:{color:'#64748b',font:{size:10}},grid:{color:'#1e1e3a'}},
          y:{ticks:{color:'#64748b'},grid:{color:'#1e1e3a'},beginAtZero:true}},
          plugins:{legend:{display:false}}}
      });
    }

    /* Predictive insights */
    const ins=d.predictive_insights||[];
    document.getElementById('insightsGrid').innerHTML=ins.map(i=>`
      <div class="insight-card" style="border-left-color:${i.color||'#6c63ff'}">
        <div class="insight-icon">${i.icon||'📊'}</div>
        <div class="insight-title">${i.title}</div>
        <div class="insight-val" style="color:${i.color||'#6c63ff'}">${i.value}</div>
        <div class="insight-detail">${i.detail}</div>
        <div class="insight-rec">${i.recommendation}</div>
      </div>`).join('');

  }catch(e){ console.error('Analytics failed:',e); }
}

/* Init */
initCards();
</script>
</body>
</html>
"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(DEMO_HTML)


@app.get("/health")
async def health():
    return {
        "status":    "ok",
        "db":        DB_ENABLED,
        "analytics": ANALYTICS_ENABLED,
        "agents":    3,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/demo/run")
async def start_run():
    """Kick off a fresh background pipeline run."""
    run_id = str(uuid.uuid4())[:8]
    _runs[run_id] = {
        "status":            "initializing",
        "run_id":            run_id,
        "current_candidate": None,
        "current_idx":       -1,
        "candidates": [
            {"name": c["name"], "emoji": c["emoji"], "stage": "waiting"}
            for c in DEMO_CANDIDATES
        ],
        "results": [],
    }
    t = threading.Thread(target=_run_pipeline, args=(run_id,), daemon=True)
    t.start()
    return {"run_id": run_id, "total_candidates": len(DEMO_CANDIDATES)}


@app.get("/demo/progress/{run_id}")
async def get_progress(run_id: str):
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    return _runs[run_id]


@app.get("/analytics/data")
async def analytics_data():
    if ANALYTICS_ENABLED:
        try:
            return get_full_analytics("demo")
        except Exception as e:
            logger.warning("Analytics fetch failed: %s", e)
    return {}


@app.get("/demo/results/{run_id}")
async def get_results(run_id: str):
    if run_id not in _runs:
        raise HTTPException(status_code=404, detail="Run not found")
    run = _runs[run_id]
    return {"status": run["status"], "results": run.get("results", [])}
