"""
Agent 3: Outreach Coordinator
LangGraph-powered personalised recruitment campaign generator.

Outreach Strategy (based on combined Agent 1 + Agent 2 scores):
  - 85+  Exceptional  → Priority Fast-Track  (same-day reach-out, exec referral)
  - 70+  Strong       → Standard Interview   (personal note, highlight achievements)
  - 55+  Promising    → Pipeline Nurture     (warm hold, future-role framing)
  - <55  Weak Match   → Passive Archive      (generic acknowledgement only)

Each campaign includes:
  1. LinkedIn connection request  (≤300 chars — platform limit)
  2. Initial outreach email       (personalised, references learning velocity)
  3. Follow-up email              (sent if no reply in 5 days)
  4. Internal recruiter note      (for ATS / hiring manager handoff)
"""

from typing import TypedDict, List
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

class OutreachState(TypedDict):
    # Inputs (from Agent 2 output)
    candidate_name: str
    candidate_profile: str
    job_title: str
    company_name: str
    recruiter_name: str
    total_match_score: int
    match_tier: str
    adaptability_score: int
    adaptability_tier: str
    matched_skills: List[str]
    startup_experience: bool
    recommend_interview: bool
    reasoning: str

    # Computed
    outreach_tier: str          # PRIORITY / STANDARD / NURTURE / ARCHIVE
    tone: str                   # enthusiastic / professional / warm / neutral
    key_highlights: List[str]   # personalisation bullets

    # Generated messages
    linkedin_message: str
    email_subject: str
    email_body: str
    followup_subject: str
    followup_body: str
    recruiter_note: str

    final_output: dict


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _first_name(full_name: str) -> str:
    return full_name.strip().split()[0] if full_name.strip() else "there"


def _extract_highlights(profile: str, matched_skills: List[str]) -> List[str]:
    """Pull the most compelling personalisation signals from the profile text."""
    text = profile.lower()
    highlights = []

    # Hackathon wins
    if any(w in text for w in ["winner", "won", "1st place", "best hack"]):
        for kw in ["hackathon", "buildathon", "coding competition", "hack day"]:
            if kw in text:
                highlights.append(f"hackathon winner ({kw})")
                break

    # Recent learning signals
    recent = [t for t in ["langchain", "langgraph", "llm", "genai", "vector", "next.js", "svelte", "rust", "fastapi"]
              if t in text]
    if recent:
        highlights.append(f"recently adopted {', '.join(recent[:3])}")

    # Startup experience
    if any(w in text for w in ["startup", "seed", "series a", "founding"]):
        highlights.append("startup / early-stage experience")

    # Certifications
    if any(w in text for w in ["certified", "certification", "aws cert", "gcp cert"]):
        highlights.append("recently certified")

    # Matched skills
    if matched_skills:
        highlights.append(f"strong match on {', '.join(matched_skills[:3])}")

    return highlights[:4]  # cap at 4 bullets


# ─────────────────────────────────────────────
# Node 1 — Classify outreach tier
# ─────────────────────────────────────────────

def classify_tier(state: OutreachState) -> OutreachState:
    score = state["total_match_score"]
    if score >= 85:
        tier, tone = "PRIORITY", "enthusiastic"
    elif score >= 70:
        tier, tone = "STANDARD", "professional"
    elif score >= 55:
        tier, tone = "NURTURE", "warm"
    else:
        tier, tone = "ARCHIVE", "neutral"

    highlights = _extract_highlights(state["candidate_profile"], state["matched_skills"])
    return {**state, "outreach_tier": tier, "tone": tone, "key_highlights": highlights}


# ─────────────────────────────────────────────
# Node 2 — LinkedIn message (≤300 chars)
# ─────────────────────────────────────────────

def generate_linkedin(state: OutreachState) -> OutreachState:
    first = _first_name(state["candidate_name"])
    tier = state["outreach_tier"]
    job = state["job_title"]
    co = state["company_name"]

    highlight = state["key_highlights"][0] if state["key_highlights"] else "your impressive profile"

    templates = {
        "PRIORITY": (
            f"Hi {first}! Noticed your {highlight} — exactly the learning velocity "
            f"we look for at {co}. Would love to connect about our {job} role. 🚀"
        ),
        "STANDARD": (
            f"Hi {first}, your {highlight} caught my eye while sourcing for a {job} "
            f"at {co}. Would love to tell you more — happy to connect!"
        ),
        "NURTURE": (
            f"Hi {first}, came across your profile and thought {co}'s {job} opening "
            f"could be a great fit down the line. Worth connecting to stay in touch?"
        ),
        "ARCHIVE": (
            f"Hi {first}, I came across your profile and wanted to connect for future opportunities at {co}."
        ),
    }
    msg = templates[tier]
    # Hard-enforce LinkedIn 300-char limit
    if len(msg) > 300:
        msg = msg[:297] + "…"
    return {**state, "linkedin_message": msg}


# ─────────────────────────────────────────────
# Node 3 — Initial outreach email
# ─────────────────────────────────────────────

def generate_email(state: OutreachState) -> OutreachState:
    first = _first_name(state["candidate_name"])
    tier = state["outreach_tier"]
    job = state["job_title"]
    co = state["company_name"]
    recruiter = state["recruiter_name"]
    score = state["total_match_score"]
    highlights = state["key_highlights"]
    adapt = state["adaptability_score"]

    bullets = "\n".join(f"  • {h.capitalize()}" for h in highlights) if highlights else "  • Strong technical profile"

    subjects = {
        "PRIORITY": f"🚀 Fast-track opportunity: {job} at {co} — made for someone like you",
        "STANDARD": f"Exciting {job} opportunity at {co} — your profile stands out",
        "NURTURE": f"Keeping you in mind for future roles at {co}",
        "ARCHIVE": f"Connecting for future opportunities at {co}",
    }

    intros = {
        "PRIORITY": (
            f"I'll be direct — your profile is one of the strongest I've seen this month. "
            f"At {co} we score candidates on *learning velocity* rather than just years of experience, "
            f"and you scored {adapt}/100 on adaptability with a {score}/100 overall match for our {job} role."
        ),
        "STANDARD": (
            f"I came across your profile while sourcing for a {job} at {co} and was genuinely impressed. "
            f"We evaluate candidates on learning velocity — your ability to adopt new technologies quickly — "
            f"and you scored {adapt}/100 on adaptability, placing you firmly in our top tier."
        ),
        "NURTURE": (
            f"I came across your profile while building our talent pipeline for future {job} roles at {co}. "
            f"While the timing may not be perfect right now, your adaptability signals ({adapt}/100) "
            f"suggest you'd be a strong fit as we grow."
        ),
        "ARCHIVE": (
            f"I wanted to reach out to connect and keep you in mind for future opportunities at {co}. "
            f"We regularly look for talented engineers and your profile is worth keeping on our radar."
        ),
    }

    ctas = {
        "PRIORITY": "I'd love to schedule a 20-minute call this week to tell you more. Does Thursday or Friday work?",
        "STANDARD": "Would you be open to a 20-minute exploratory call this week?",
        "NURTURE": "Would you be open to staying connected so I can reach out when the right role opens up?",
        "ARCHIVE": "Feel free to reach out if you're ever exploring new opportunities.",
    }

    body = f"""Hi {first},

{intros[tier]}

Here's what caught my eye:
{bullets}

This is exactly the profile we're looking for — someone who keeps learning and ships fast, not just someone with a long list of credentials.

{ctas[tier]}

Best,
{recruiter}
{co} Talent Team

---
P.S. We don't use traditional "years of experience" filters. Your adaptability score of {adapt}/100 tells us more than a 10-year résumé. 🎯
"""

    return {**state, "email_subject": subjects[tier], "email_body": body}


# ─────────────────────────────────────────────
# Node 4 — Follow-up email (sent after 5 days)
# ─────────────────────────────────────────────

def generate_followup(state: OutreachState) -> OutreachState:
    first = _first_name(state["candidate_name"])
    job = state["job_title"]
    co = state["company_name"]
    recruiter = state["recruiter_name"]
    tier = state["outreach_tier"]

    if tier == "ARCHIVE":
        return {**state, "followup_subject": "", "followup_body": ""}

    subject = f"Re: {state['email_subject']}"

    bodies = {
        "PRIORITY": f"""Hi {first},

Just following up on my note from earlier this week about the {job} role at {co}.

Given your profile, I wanted to make sure this didn't get buried — our hiring team specifically flagged you as a priority candidate based on your learning velocity signals.

If you're happy where you are, that's completely fine — but if you have 15 minutes, I think you'd find the conversation genuinely interesting.

{recruiter}
{co} Talent Team
""",
        "STANDARD": f"""Hi {first},

Just circling back on the {job} opportunity at {co} I mentioned earlier.

No pressure at all — I just wanted to make sure my previous note didn't get lost. If you're curious, I'm happy to share more about the role and why we think you'd be a great fit.

{recruiter}
{co} Talent Team
""",
        "NURTURE": f"""Hi {first},

Just wanted to stay on your radar! We're continuing to grow the team at {co} and I'd love to keep you in the loop as new {job}-style roles open up.

{recruiter}
{co} Talent Team
""",
    }

    return {**state, "followup_subject": subject, "followup_body": bodies.get(tier, "")}


# ─────────────────────────────────────────────
# Node 5 — Internal recruiter note (for ATS)
# ─────────────────────────────────────────────

def generate_recruiter_note(state: OutreachState) -> OutreachState:
    note = (
        f"CANDIDATE: {state['candidate_name']}\n"
        f"ROLE: {state['job_title']}\n"
        f"DATE: {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
        f"SCORES\n"
        f"  Adaptability (Agent 1): {state['adaptability_score']}/100 — {state['adaptability_tier']}\n"
        f"  Job Match    (Agent 2): {state['total_match_score']}/100 — {state['match_tier']}\n"
        f"  Outreach Tier        : {state['outreach_tier']}\n\n"
        f"KEY SIGNALS\n"
        + "\n".join(f"  • {h}" for h in state["key_highlights"]) + "\n\n"
        f"MATCHED SKILLS: {', '.join(state['matched_skills']) or 'None'}\n"
        f"STARTUP EXP: {'Yes' if state['startup_experience'] else 'No'}\n\n"
        f"AGENT REASONING\n{state['reasoning']}\n\n"
        f"ACTION: {'Schedule interview immediately' if state['outreach_tier'] == 'PRIORITY' else 'Send outreach sequence'}"
    )
    return {**state, "recruiter_note": note}


# ─────────────────────────────────────────────
# Node 6 — Build final output
# ─────────────────────────────────────────────

def build_output(state: OutreachState) -> OutreachState:
    final = {
        "agent": "Agent 3 — Outreach Coordinator",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "candidate_name": state["candidate_name"],
        "job_title": state["job_title"],
        "outreach_tier": state["outreach_tier"],
        "tone": state["tone"],
        "total_match_score": state["total_match_score"],
        "adaptability_score": state["adaptability_score"],
        "key_highlights": state["key_highlights"],
        "campaign": {
            "linkedin_message": state["linkedin_message"],
            "email": {
                "subject": state["email_subject"],
                "body": state["email_body"],
            },
            "followup": {
                "subject": state["followup_subject"],
                "body": state["followup_body"],
                "send_after_days": 5,
            },
            "recruiter_note": state["recruiter_note"],
        },
        "pipeline_complete": True,
    }
    return {**state, "final_output": final}


# ─────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────

def build_agent_3():
    graph = StateGraph(OutreachState)

    graph.add_node("classify_tier", classify_tier)
    graph.add_node("generate_linkedin", generate_linkedin)
    graph.add_node("generate_email", generate_email)
    graph.add_node("generate_followup", generate_followup)
    graph.add_node("generate_recruiter_note", generate_recruiter_note)
    graph.add_node("build_output", build_output)

    graph.set_entry_point("classify_tier")
    graph.add_edge("classify_tier", "generate_linkedin")
    graph.add_edge("generate_linkedin", "generate_email")
    graph.add_edge("generate_email", "generate_followup")
    graph.add_edge("generate_followup", "generate_recruiter_note")
    graph.add_edge("generate_recruiter_note", "build_output")
    graph.add_edge("build_output", END)

    return graph.compile()


agent_3_graph = build_agent_3()


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def generate_outreach(
    candidate_name: str,
    candidate_profile: str,
    job_title: str,
    company_name: str,
    recruiter_name: str,
    total_match_score: int,
    match_tier: str,
    adaptability_score: int,
    adaptability_tier: str,
    matched_skills: list,
    startup_experience: bool,
    recommend_interview: bool,
    reasoning: str,
) -> dict:
    initial: OutreachState = {
        "candidate_name": candidate_name,
        "candidate_profile": candidate_profile,
        "job_title": job_title,
        "company_name": company_name,
        "recruiter_name": recruiter_name,
        "total_match_score": total_match_score,
        "match_tier": match_tier,
        "adaptability_score": adaptability_score,
        "adaptability_tier": adaptability_tier,
        "matched_skills": matched_skills,
        "startup_experience": startup_experience,
        "recommend_interview": recommend_interview,
        "reasoning": reasoning,
        "outreach_tier": "",
        "tone": "",
        "key_highlights": [],
        "linkedin_message": "",
        "email_subject": "",
        "email_body": "",
        "followup_subject": "",
        "followup_body": "",
        "recruiter_note": "",
        "final_output": {},
    }
    result = agent_3_graph.invoke(initial)
    return result["final_output"]
