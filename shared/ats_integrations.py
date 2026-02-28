"""
VelocityHire — ATS Integration Module
======================================
Normalises inbound webhook payloads from major ATS providers into
VelocityHire's internal candidate profile format, then routes them
through the 3-agent scoring pipeline.

Supported providers (mock / webhook simulation):
  • Greenhouse  — POST /ats/greenhouse/webhook
  • Lever       — POST /ats/lever/webhook
  • BambooHR    — POST /ats/bamboohr/webhook

Each normaliser returns a dict with keys:
  candidate_name  str
  profile_text    str   (formatted for Agent 1)
  job_title       str
  source          str   (provider slug)
  raw             dict  (original payload, for audit)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("velocityhire.ats")

# ── Mock test candidates (one per provider) ───────────────────────────────────
MOCK_PAYLOADS: Dict[str, Dict] = {

    "greenhouse": {
        "action": "candidate_created",
        "payload": {
            "candidate": {
                "id": 88412,
                "first_name": "Aisha",
                "last_name": "Nakamura",
                "headline": "Staff ML Engineer · ex-Stripe · LangGraph contributor",
                "emails": [{"value": "aisha.nakamura@example.com", "type": "work"}],
                "notes": (
                    "Aisha Nakamura — Staff ML Engineer\n"
                    "Skills: Python, LangGraph, LangChain, PyTorch, FastAPI, AWS, Kubernetes, Rust\n"
                    "Experience:\n"
                    "  - Stripe (2021-present): Staff ML engineer, built fraud-detection "
                    "agent with LangGraph. Team of 8.\n"
                    "  - SeedAI startup (2019-2021): Founding engineer, shipped ML platform "
                    "from zero. Series A achieved.\n"
                    "Hackathons:\n"
                    "  - NeurIPS ML4Code (1 month ago) — WINNER, best agent design, "
                    "multi-modal code assistant.\n"
                    "  - AI SF Buildathon (3 months ago) — WINNER, built Rust + LLM "
                    "debugger in 36 hours.\n"
                    "Certifications:\n"
                    "  - AWS Certified ML Specialty (6 weeks ago)\n"
                    "  - LangGraph Advanced (1 month ago)\n"
                    "GitHub: 94 commits last month. Core contributor to LangGraph OSS.\n"
                    "Startup experience: founding engineer at SeedAI."
                ),
                "applications": [
                    {"job": {"id": 5001, "name": "Senior AI Engineer"}}
                ],
                "tags": ["ml", "langgraph", "startup", "hackathon-winner"],
                "source": {"public_name": "LinkedIn"},
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        },
    },

    "lever": {
        "triggeredAt": int(datetime.utcnow().timestamp() * 1000),
        "event": "candidateCreated",
        "data": {
            "candidate": {
                "id": "lv-77201-cc",
                "name": "Diego Fernandez",
                "headline": "Senior Full-Stack Engineer | React + Python | Startup Veteran",
                "location": "Barcelona, Spain",
                "emails": ["diego.fernandez@example.com"],
                "links": ["https://github.com/diego-builds", "https://diegoblog.dev"],
                "tags": ["python", "react", "fastapi", "startup", "hackathon"],
                "summary": (
                    "Diego Fernandez — Senior Full-Stack Engineer\n"
                    "Skills: Python, React, TypeScript, FastAPI, PostgreSQL, AWS, Docker, "
                    "LangChain, Next.js\n"
                    "Experience:\n"
                    "  - Cabify (2022-present): Senior engineer, real-time geo-routing with ML.\n"
                    "  - TechNova startup (2019-2022): Co-founder and CTO, shipped "
                    "SaaS product from MVP to 10k users.\n"
                    "Hackathons:\n"
                    "  - Barcelona Hack Day (2 months ago) — WINNER, built AI travel "
                    "planner using LangChain + vector search.\n"
                    "  - HackUPC (5 months ago) — Finalist.\n"
                    "Certifications:\n"
                    "  - AWS Solutions Architect (3 months ago)\n"
                    "GitHub: 51 commits last month. Active in OSS.\n"
                    "Startup experience: co-founded TechNova, 0-to-1 product build."
                ),
            },
            "opportunity": {
                "id": "opp-99123",
                "posting": {"text": "Senior AI Engineer", "state": "published"},
                "stage": {"text": "New Applicant"},
            },
        },
    },

    "bamboohr": {
        "employeeId": 3821,
        "action": "hired",
        "employee": {
            "firstName": "Yuki",
            "lastName": "Tanaka",
            "jobTitle": "AI/ML Engineer",
            "department": "Engineering",
            "location": "Tokyo, Japan",
            "customFields": {
                "linkedinProfile": "https://linkedin.com/in/yuki-tanaka",
                "githubProfile": "https://github.com/yuki-ai",
                "skills": "Python, TensorFlow, LLM fine-tuning, FastAPI, GCP, LangChain",
                "notes": (
                    "Yuki Tanaka — AI/ML Engineer\n"
                    "Skills: Python, TensorFlow, LangChain, FastAPI, GCP, Docker, "
                    "Kubernetes, vector databases\n"
                    "Experience:\n"
                    "  - Sony AI (2022-present): ML engineer, LLM applications and "
                    "fine-tuning pipelines.\n"
                    "  - DeepTech startup (2020-2022): Early engineer, built "
                    "recommendation engine from scratch.\n"
                    "Hackathons:\n"
                    "  - Tokyo AI Fest (2 months ago) — WINNER, best use of LLMs.\n"
                    "Certifications:\n"
                    "  - GCP Professional ML Engineer (2 months ago)\n"
                    "GitHub: 38 commits last month.\n"
                    "Startup experience: early-stage at DeepTech."
                ),
            },
        },
    },
}

# ── Normalisers ───────────────────────────────────────────────────────────────


def normalise_greenhouse(payload: Dict[str, Any]) -> Optional[Dict]:
    """
    Convert a Greenhouse candidate.created webhook into VelocityHire format.
    https://developers.greenhouse.io/webhooks.html
    """
    try:
        cand = payload.get("payload", {}).get("candidate", {})
        if not cand:
            cand = payload.get("candidate", {})

        first = cand.get("first_name", "")
        last = cand.get("last_name", "")
        name = f"{first} {last}".strip() or "Unknown"
        headline = cand.get("headline", "")
        notes = cand.get("notes", "") or cand.get("summary", "")
        apps = cand.get("applications", [{}])
        job = apps[0].get("job", {}).get("name", "Unknown Role") if apps else "Unknown Role"
        tags = cand.get("tags", [])
        emails = cand.get("emails", [])
        email = emails[0].get("value", "") if emails else ""

        # Build profile text for Agent 1
        profile = f"{name}"
        if headline:
            profile += f" — {headline}"
        profile += "\n"
        if email:
            profile += f"Email: {email}\n"
        if tags:
            profile += f"Tags: {', '.join(tags)}\n"
        if notes:
            profile += f"\n{notes}"

        return {
            "candidate_name": name,
            "profile_text": profile.strip(),
            "job_title": job,
            "source": "greenhouse",
            "raw": payload,
        }
    except Exception as exc:
        logger.error("normalise_greenhouse failed: %s", exc)
        return None


def normalise_lever(payload: Dict[str, Any]) -> Optional[Dict]:
    """
    Convert a Lever candidateCreated webhook into VelocityHire format.
    https://hire.lever.co/developer/webhooks
    """
    try:
        data = payload.get("data", {})
        cand = data.get("candidate", {})
        opp = data.get("opportunity", {})
        name = cand.get("name", "Unknown")
        headline = cand.get("headline", "")
        location = cand.get("location", "")
        tags = cand.get("tags", [])
        links = cand.get("links", [])
        summary = cand.get("summary", "") or cand.get("notes", "")
        job = opp.get("posting", {}).get("text", "Unknown Role")

        profile = f"{name}"
        if headline:
            profile += f" — {headline}"
        profile += "\n"
        if location:
            profile += f"Location: {location}\n"
        if links:
            profile += f"Links: {', '.join(links)}\n"
        if tags:
            profile += f"Tags: {', '.join(tags)}\n"
        if summary:
            profile += f"\n{summary}"

        return {
            "candidate_name": name,
            "profile_text": profile.strip(),
            "job_title": job,
            "source": "lever",
            "raw": payload,
        }
    except Exception as exc:
        logger.error("normalise_lever failed: %s", exc)
        return None


def normalise_bamboohr(payload: Dict[str, Any]) -> Optional[Dict]:
    """
    Convert a BambooHR employee.hired webhook into VelocityHire format.
    https://documentation.bamboohr.com/docs/webhooks
    """
    try:
        emp = payload.get("employee", {})
        custom = emp.get("customFields", {})
        first = emp.get("firstName", "")
        last = emp.get("lastName", "")
        name = f"{first} {last}".strip() or "Unknown"
        title = emp.get("jobTitle", "Unknown Role")
        dept = emp.get("department", "")
        location = emp.get("location", "")
        skills = custom.get("skills", "")
        notes = custom.get("notes", "")

        profile = f"{name} — {title}\n"
        if dept:
            profile += f"Department: {dept}\n"
        if location:
            profile += f"Location: {location}\n"
        if skills:
            profile += f"Skills: {skills}\n"
        if notes:
            profile += f"\n{notes}"

        return {
            "candidate_name": name,
            "profile_text": profile.strip(),
            "job_title": title,
            "source": "bamboohr",
            "raw": payload,
        }
    except Exception as exc:
        logger.error("normalise_bamboohr failed: %s", exc)
        return None


# ── Dispatcher ────────────────────────────────────────────────────────────────

NORMALISERS = {
    "greenhouse": normalise_greenhouse,
    "lever": normalise_lever,
    "bamboohr": normalise_bamboohr,
}

PROVIDER_META = {
    "greenhouse": {
        "name": "Greenhouse",
        "logo": "🌿",
        "color": "#3db639",
        "docs": "https://developers.greenhouse.io/webhooks.html",
        "event": "candidate.created",
        "status": "active",
    },
    "lever": {
        "name": "Lever",
        "logo": "⚙️",
        "color": "#006dff",
        "docs": "https://hire.lever.co/developer/webhooks",
        "event": "candidateCreated",
        "status": "active",
    },
    "bamboohr": {
        "name": "BambooHR",
        "logo": "🎋",
        "color": "#74a318",
        "docs": "https://documentation.bamboohr.com/docs/webhooks",
        "event": "employee.hired",
        "status": "active",
    },
}


def normalise(provider: str, payload: Dict[str, Any]) -> Optional[Dict]:
    """Route payload to the correct normaliser."""
    fn = NORMALISERS.get(provider.lower())
    if not fn:
        logger.warning("Unknown ATS provider: %s", provider)
        return None
    return fn(payload)


def get_mock_payload(provider: str) -> Optional[Dict]:
    """Return the built-in test payload for a provider."""
    return MOCK_PAYLOADS.get(provider.lower())


def list_integrations() -> Dict:
    """Return metadata for all supported integrations."""
    return {
        provider: {
            **meta,
            "webhook_url": f"/ats/{provider}/webhook",
            "test_url": f"/ats/{provider}/test",
            "mock_payload": MOCK_PAYLOADS.get(provider, {}),
        }
        for provider, meta in PROVIDER_META.items()
    }
