"""
Agent 1: Profile Analyzer
LangGraph-powered adaptability scoring engine.

Scoring Algorithm:
  - Hackathons (40%)        → Execution under pressure
  - Frameworks/Skills (25%) → Technical breadth
  - Certifications (20%)    → Structured learning
  - Recency (15%)           → Current engagement
    - 4x multiplier for last 3 months
    - 2x multiplier for last 6 months

Adaptability threshold: 70+ = high-potential candidate
"""

import os
import json
import re
import requests
from datetime import datetime, timedelta
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

# ─────────────────────────────────────────────
# Deploy AI helpers — OpenAI-compatible proxy
# ─────────────────────────────────────────────
# Deploy AI exposes /openai/chat/completions which is a standard
# OpenAI-format endpoint, accepting a Bearer API key directly.

API_BASE = os.getenv("API_URL", "https://core-api.deploy.ai")
OPENAI_COMPAT_URL = f"{API_BASE}/openai/chat/completions"
MODEL = os.getenv("DEPLOY_AI_MODEL", "gpt-4o")


def _get_api_key() -> str:
    """Return the best available API key from environment."""
    return (
        os.getenv("API_KEY")
        or os.getenv("CLIENT_SECRET")
        or os.getenv("CLIENT_ID")
        or ""
    )


def _mock_llm(prompt: str) -> str:
    """
    Rule-based mock LLM — no API calls needed.
    Scans the prompt for keywords and returns realistic JSON.
    Used when MOCK_MODE=true or no API key is configured.
    """
    text = prompt.lower()

    # ── Hackathon detection ────────────────────────────────────────────────
    hack_events = []
    hack_score = 0.0
    hack_keywords = ["hackathon", "hack day", "buildathon", "coding competition",
                     "junction", "hackmit", "angelhack", "innovation challenge"]
    win_keywords  = ["winner", "won", "1st place", "first place", "best hack"]
    fin_keywords  = ["finalist", "runner-up", "2nd place", "top 3"]

    for kw in hack_keywords:
        if kw in text:
            role = "winner" if any(w in text for w in win_keywords) else \
                   "finalist" if any(f in text for f in fin_keywords) else "participant"
            ai_ml = any(w in text for w in ["ai", "ml", "llm", "genai", "gpt", "vector", "langchain"])
            # Recency heuristic
            months_ago = 1 if any(w in text for w in ["1 month", "2 month", "last month", "week ago", "weeks ago"]) \
                          else 5 if any(w in text for w in ["3 month", "4 month", "5 month", "6 month"]) else 14
            multiplier = 4 if months_ago <= 3 else 2 if months_ago <= 6 else 1
            base = 6 if role == "winner" else 4 if role == "finalist" else 2
            if ai_ml: base *= 1.5
            pts = min(base * multiplier, 40)
            hack_events.append({"name": kw.title(), "role": role, "ai_ml": ai_ml,
                                 "months_ago": months_ago, "raw_points": base,
                                 "multiplied_points": pts})
            hack_score = min(hack_score + pts, 40)
            break  # one event per pass to avoid over-counting

    summary_h = f"{len(hack_events)} hackathon event(s) detected; score {hack_score:.1f}/40." \
                if hack_events else "No hackathon participation detected."

    # ── Skills detection ───────────────────────────────────────────────────
    trending = {"llm_genai": any(w in text for w in ["llm", "genai", "gpt", "langchain", "langgraph"]),
                "vector_db": any(w in text for w in ["vector", "pinecone", "weaviate", "chroma"]),
                "ai_agents": any(w in text for w in ["agent", "multi-agent", "autonomous"])}
    langs = [l for l in ["python","typescript","rust","go","java","c++","kotlin","swift","scala"] if l in text]
    clouds = [c for c in ["aws","gcp","azure","vercel","railway","fly.io"] if c in text]
    new_tech_count = sum(1 for w in ["next.js","svelte","fastapi","langchain","langgraph",
                                      "htmx","bun","deno","astro","drizzle"] if w in text)
    skills_score = min(new_tech_count * 4 + len(langs) * 1.5 + sum(trending.values()) * 3 + len(clouds), 25)
    summary_s = f"{new_tech_count} new technologies, {len(langs)} languages, trending AI skills: {sum(trending.values())}/3."

    # ── Certifications ─────────────────────────────────────────────────────
    cert_keywords = ["certified","certification","aws cert","gcp cert","azure cert",
                     "bootcamp","course","udemy","coursera","pluralsight","langchain cert"]
    certs = [c for c in cert_keywords if c in text]
    recent_cert = any(w in text for w in ["1 month","2 month","3 month","last month"])
    certs_score = min(len(certs) * (5 if recent_cert else 2), 20)
    summary_c = f"{len(certs)} certification/course signal(s) found; recent={recent_cert}."

    # ── Recency ────────────────────────────────────────────────────────────
    high_recency = any(w in text for w in ["last month","this month","week ago","weeks ago",
                                            "1 month","2 month","3 month"])
    med_recency  = any(w in text for w in ["4 month","5 month","6 month","recent","recently"])
    recency_score = 13 if high_recency else 8 if med_recency else 3
    velocity = "high" if high_recency else "medium" if med_recency else "low"
    summary_r = f"Velocity level: {velocity}; score {recency_score}/15."

    # ── Build JSON response matching the exact format the node expects ─────
    node = _detect_node(prompt)

    if node == "hackathon":
        return json.dumps({
            "events": hack_events,
            "total_hackathon_score": round(hack_score, 1),
            "summary": summary_h,
        })
    elif node == "skills":
        return json.dumps({
            "new_technologies": [{"name": t, "months_ago": 2, "ai_ml": True, "points": 4}
                                  for t in ["Next.js","LangChain","FastAPI"] if t.lower() in text][:3],
            "languages": langs[:5],
            "cloud_platforms": clouds[:3],
            "trending_skills": trending,
            "total_skills_score": round(skills_score, 1),
            "summary": summary_s,
        })
    elif node == "certs":
        return json.dumps({
            "certifications": [{"name": c.title(), "provider": "Online", "months_ago": 2 if recent_cert else 8,
                                 "ai_ml": "ai" in c or "ml" in c, "points": 5 if recent_cert else 2}
                                for c in certs[:3]],
            "total_certs_score": round(certs_score, 1),
            "summary": summary_c,
        })
    else:  # recency
        return json.dumps({
            "recent_signals": [{"type": "GitHub", "description": "Active commits", "months_ago": 1}]
                               if high_recency else [],
            "velocity_level": velocity,
            "total_recency_score": recency_score,
            "summary": summary_r,
        })


def _detect_node(prompt: str) -> str:
    """Identify which LangGraph node is calling based on prompt keywords."""
    p = prompt.lower()
    if "hackathon" in p and "total_hackathon_score" in p: return "hackathon"
    if "total_skills_score" in p: return "skills"
    if "total_certs_score" in p: return "certs"
    return "recency"


def call_llm_openai(prompt: str) -> str:
    """
    Call Deploy AI's OpenAI-compatible proxy.
    Falls back to mock mode when MOCK_MODE=true or no API key is available.
    """
    if os.getenv("MOCK_MODE", "false").lower() == "true":
        return _mock_llm(prompt)

    api_key = _get_api_key()
    if not api_key:
        return _mock_llm(prompt)   # no key → use mock silently

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Org": os.getenv("ORG_ID", ""),
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a talent intelligence engine that analyses candidate profiles and returns structured JSON."},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1500,
    }
    try:
        resp = requests.post(OPENAI_COMPAT_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        pass

    # Any failure → mock fallback
    return _mock_llm(prompt)


def _call_llm_legacy(api_key: str, prompt: str) -> str:
    """Legacy Deploy AI chat flow kept as fallback."""
    # Step 1 – get token (sk_ keys are used directly; others need OAuth2)
    if api_key.startswith("sk_"):
        token = api_key
    else:
        data = {
            "grant_type": "client_credentials",
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
        }
        r = requests.post(
            os.getenv("AUTH_URL", "https://api-auth.deploy.ai/oauth2/token"),
            data=data, timeout=30,
        )
        r.raise_for_status()
        token = r.json()["access_token"]

    org_id = os.getenv("ORG_ID", "")
    hdrs = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Org": org_id,
    }

    # Step 2 – create chat
    r = requests.post(f"{API_BASE}/chats", headers=hdrs,
                      json={"agentId": "GPT_4O", "stream": False}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"create_chat failed: {r.status_code} {r.text}")
    chat_id = r.json()["id"]

    # Step 3 – send message
    r = requests.post(f"{API_BASE}/messages", headers=hdrs,
                      json={"chatId": chat_id, "stream": False,
                            "content": [{"type": "text", "value": prompt}]},
                      timeout=60)
    if r.status_code == 200:
        return r.json()["content"][0]["value"]
    raise RuntimeError(f"call_llm failed: {r.status_code} {r.text}")


# Keep old signatures for compatibility
def get_access_token() -> str:
    return _get_api_key()

def create_chat(access_token: str) -> str:
    return "openai-compat"   # not used in new flow

def call_llm(access_token: str, chat_id: str, prompt: str) -> str:
    return call_llm_openai(prompt)


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

class ProfileState(TypedDict):
    profile_text: str           # Raw candidate profile pasted by user
    access_token: str
    chat_id: str
    hackathon_raw: str          # LLM output – hackathon signals
    skills_raw: str             # LLM output – skills/frameworks
    certs_raw: str              # LLM output – certifications/courses
    recency_raw: str            # LLM output – recency analysis
    score_breakdown: dict       # Numeric scores per dimension
    adaptability_score: int     # Final 0-100 score
    reasoning: str              # Plain-English reasoning
    final_output: dict          # Structured result returned to caller


# ─────────────────────────────────────────────
# Helper – extract JSON from LLM response
# ─────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    """Extract the first JSON object from an LLM response string."""
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


# ─────────────────────────────────────────────
# Node 1 – Bootstrap Deploy AI session
# ─────────────────────────────────────────────

def bootstrap_session(state: ProfileState) -> ProfileState:
    token = _get_api_key()
    return {**state, "access_token": token, "chat_id": "openai-compat"}


# ─────────────────────────────────────────────
# Node 2 – Extract hackathon signals  (40 pts)
# ─────────────────────────────────────────────

HACKATHON_PROMPT = """
You are a talent intelligence engine specialising in hackathon detection.

Analyse the candidate profile below and extract ALL hackathon signals.

SCORING RULES
• Participation:  2 pts
• Finalist:       4 pts
• Winner:         6 pts
• AI/ML solution: ×2 technical-complexity multiplier
• Team leadership: ×1.5 multiplier
• Recency:        last 3 months → ×4 multiplier
                  last 4-6 months → ×2 multiplier
                  older than 6 months → ×1 multiplier
• Max category score: 40 pts (scale down proportionally if over)

KEYWORDS TO DETECT
hackathon, hack day, coding competition, 48-hour build, weekend hack,
innovation challenge, AngelHack, TechCrunch Disrupt, Junction, HackMIT,
winner, finalist, best hack, people's choice, demo day

Return ONLY valid JSON (no markdown, no prose outside JSON):
{{
  "events": [
    {{
      "name": "<event name or 'Unnamed hackathon'>",
      "role": "winner | finalist | participant",
      "ai_ml": true | false,
      "leadership": true | false,
      "months_ago": <integer or null if unknown>,
      "raw_points": <float>,
      "multiplied_points": <float>
    }}
  ],
  "total_hackathon_score": <float, max 40>,
  "summary": "<1-sentence summary>"
}}

CANDIDATE PROFILE:
{profile}
"""


def extract_hackathons(state: ProfileState) -> ProfileState:
    prompt = HACKATHON_PROMPT.format(profile=state["profile_text"])
    raw = call_llm(state["access_token"], state["chat_id"], prompt)
    return {**state, "hackathon_raw": raw}


# ─────────────────────────────────────────────
# Node 3 – Analyse skills / frameworks  (25 pts)
# ─────────────────────────────────────────────

SKILLS_PROMPT = """
You are a talent intelligence engine specialising in technical skills analysis.

Analyse the candidate profile and evaluate learning breadth across frameworks,
tools, and technologies — focusing on NOVELTY and RECENCY of adoption.

SCORING RULES (max 25 pts)
• Each genuinely new technology adopted in last 6 months:  up to 5 pts
  – AI/ML/GenAI/Vector DB/LLM agent tools:  ×1.5 bonus
• Programming versatility (number of languages at production level): up to 8 pts
• Cloud platform depth (multi-cloud or advanced IaC): up to 4 pts
• Trending skills bonus:
  – LLM / GenAI implementation: 4 pts
  – Vector database:            3 pts
  – AI agent development:       3 pts
  (these sub-totals count toward the 25-pt max)

Return ONLY valid JSON:
{{
  "new_technologies": [
    {{"name": "<tech>", "months_ago": <int or null>, "ai_ml": true|false, "points": <float>}}
  ],
  "languages": ["<lang>"],
  "cloud_platforms": ["<cloud>"],
  "trending_skills": {{"llm_genai": true|false, "vector_db": true|false, "ai_agents": true|false}},
  "total_skills_score": <float, max 25>,
  "summary": "<1-sentence summary>"
}}

CANDIDATE PROFILE:
{profile}
"""


def analyze_skills(state: ProfileState) -> ProfileState:
    prompt = SKILLS_PROMPT.format(profile=state["profile_text"])
    raw = call_llm(state["access_token"], state["chat_id"], prompt)
    return {**state, "skills_raw": raw}


# ─────────────────────────────────────────────
# Node 4 – Certifications / courses  (20 pts)
# ─────────────────────────────────────────────

CERTS_PROMPT = """
You are a talent intelligence engine specialising in continuous learning analysis.

Analyse the candidate profile for formal learning signals (certifications,
online courses, bootcamps, degrees, workshops).

SCORING RULES (max 20 pts)
• Each relevant certification/course completed in last 12 months: up to 6 pts
• AI/ML/Cloud certifications: ×1.5 bonus
• Recency: last 3 months → ×4 multiplier
           4-6 months   → ×2 multiplier
           6-12 months  → ×1 multiplier
           older        → 0.5 pts each (diminishing)

Return ONLY valid JSON:
{{
  "certifications": [
    {{"name": "<cert/course>", "provider": "<provider>", "months_ago": <int or null>, "ai_ml": true|false, "points": <float>}}
  ],
  "total_certs_score": <float, max 20>,
  "summary": "<1-sentence summary>"
}}

CANDIDATE PROFILE:
{profile}
"""


def analyze_certifications(state: ProfileState) -> ProfileState:
    prompt = CERTS_PROMPT.format(profile=state["profile_text"])
    raw = call_llm(state["access_token"], state["chat_id"], prompt)
    return {**state, "certs_raw": raw}


# ─────────────────────────────────────────────
# Node 5 – Recency / overall velocity  (15 pts)
# ─────────────────────────────────────────────

RECENCY_PROMPT = """
You are a talent intelligence engine specialising in learning-velocity signals.

Analyse the candidate profile for RECENCY and PACE of learning activity.
Look for GitHub activity timestamps, post dates, job-change cadence,
open-source contributions, blog posts, and community engagement.

SCORING RULES (max 15 pts)
• High-frequency recent activity (multiple signals in last 3 months): 12-15 pts
• Moderate recent activity (1-2 signals in last 3 months):            7-11 pts
• Activity in last 6 months only:                                     4-6 pts
• Activity older than 6 months:                                       1-3 pts
• No discernible recent activity:                                     0 pts

Return ONLY valid JSON:
{{
  "recent_signals": [
    {{"type": "<GitHub|blog|job change|open-source|community>", "description": "<brief>", "months_ago": <int or null>}}
  ],
  "velocity_level": "high | medium | low | stale",
  "total_recency_score": <float, max 15>,
  "summary": "<1-sentence summary>"
}}

CANDIDATE PROFILE:
{profile}
"""


def analyze_recency(state: ProfileState) -> ProfileState:
    prompt = RECENCY_PROMPT.format(profile=state["profile_text"])
    raw = call_llm(state["access_token"], state["chat_id"], prompt)
    return {**state, "recency_raw": raw}


# ─────────────────────────────────────────────
# Node 6 – Aggregate score + reasoning
# ─────────────────────────────────────────────

def aggregate_score(state: ProfileState) -> ProfileState:
    hackathon_data = _parse_json(state.get("hackathon_raw", "{}"))
    skills_data    = _parse_json(state.get("skills_raw", "{}"))
    certs_data     = _parse_json(state.get("certs_raw", "{}"))
    recency_data   = _parse_json(state.get("recency_raw", "{}"))

    h_score = min(float(hackathon_data.get("total_hackathon_score", 0)), 40)
    s_score = min(float(skills_data.get("total_skills_score", 0)), 25)
    c_score = min(float(certs_data.get("total_certs_score", 0)), 20)
    r_score = min(float(recency_data.get("total_recency_score", 0)), 15)

    total = round(h_score + s_score + c_score + r_score)
    total = max(0, min(100, total))

    breakdown = {
        "hackathons":     {"score": round(h_score, 1), "max": 40, "weight": "40%",
                           "summary": hackathon_data.get("summary", "")},
        "skills":         {"score": round(s_score, 1), "max": 25, "weight": "25%",
                           "summary": skills_data.get("summary", "")},
        "certifications": {"score": round(c_score, 1), "max": 20, "weight": "20%",
                           "summary": certs_data.get("summary", "")},
        "recency":        {"score": round(r_score, 1), "max": 15, "weight": "15%",
                           "summary": recency_data.get("summary", "")},
    }

    tier = (
        "🏆 Top Performer"    if total >= 85 else
        "⭐ High Potential"   if total >= 70 else
        "✅ Promising"        if total >= 55 else
        "📋 Standard"        if total >= 40 else
        "🔍 Needs Review"
    )

    reasoning = (
        f"Adaptability Score: {total}/100 — {tier}\n\n"
        f"• Hackathons ({h_score:.1f}/40): {hackathon_data.get('summary', 'No data')}\n"
        f"• Skills ({s_score:.1f}/25): {skills_data.get('summary', 'No data')}\n"
        f"• Certifications ({c_score:.1f}/20): {certs_data.get('summary', 'No data')}\n"
        f"• Recency ({r_score:.1f}/15): {recency_data.get('summary', 'No data')}\n\n"
        f"{'✅ ABOVE threshold — recommend for interview' if total >= 70 else '❌ BELOW threshold — keep in pipeline for future roles'}"
    )

    return {
        **state,
        "score_breakdown": breakdown,
        "adaptability_score": total,
        "reasoning": reasoning,
    }


# ─────────────────────────────────────────────
# Node 7 – Build final output
# ─────────────────────────────────────────────

def build_output(state: ProfileState) -> ProfileState:
    final = {
        "agent": "Agent 1 — Profile Analyzer",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "adaptability_score": state["adaptability_score"],
        "tier": (
            "Top Performer"  if state["adaptability_score"] >= 85 else
            "High Potential" if state["adaptability_score"] >= 70 else
            "Promising"      if state["adaptability_score"] >= 55 else
            "Standard"       if state["adaptability_score"] >= 40 else
            "Needs Review"
        ),
        "recommend_interview": state["adaptability_score"] >= 70,
        "score_breakdown": state["score_breakdown"],
        "reasoning": state["reasoning"],
        "ready_for_agent_2": True,
    }
    return {**state, "final_output": final}


# ─────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────

def build_agent_1() -> StateGraph:
    graph = StateGraph(ProfileState)

    graph.add_node("bootstrap",          bootstrap_session)
    graph.add_node("extract_hackathons", extract_hackathons)
    graph.add_node("analyze_skills",     analyze_skills)
    graph.add_node("analyze_certs",      analyze_certifications)
    graph.add_node("analyze_recency",    analyze_recency)
    graph.add_node("aggregate_score",    aggregate_score)
    graph.add_node("build_output",       build_output)

    graph.set_entry_point("bootstrap")
    graph.add_edge("bootstrap",          "extract_hackathons")
    graph.add_edge("extract_hackathons", "analyze_skills")
    graph.add_edge("analyze_skills",     "analyze_certs")
    graph.add_edge("analyze_certs",      "analyze_recency")
    graph.add_edge("analyze_recency",    "aggregate_score")
    graph.add_edge("aggregate_score",    "build_output")
    graph.add_edge("build_output",       END)

    return graph.compile()


agent_1_graph = build_agent_1()


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def analyze_profile(
    profile_text: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    org_id: Optional[str] = None,
) -> dict:
    """
    Entry point.  Pass raw LinkedIn profile text; receive adaptability report.
    Credentials can be supplied directly or via environment variables.
    Returns the `final_output` dict.
    """
    # Allow runtime credential injection (useful when .env is not configured)
    if client_id:
        os.environ["CLIENT_ID"] = client_id
    if client_secret:
        os.environ["CLIENT_SECRET"] = client_secret
    if org_id:
        os.environ["ORG_ID"] = org_id

    initial_state: ProfileState = {
        "profile_text":      profile_text,
        "access_token":      "",
        "chat_id":           "",
        "hackathon_raw":     "",
        "skills_raw":        "",
        "certs_raw":         "",
        "recency_raw":       "",
        "score_breakdown":   {},
        "adaptability_score": 0,
        "reasoning":         "",
        "final_output":      {},
    }
    result = agent_1_graph.invoke(initial_state)
    return result["final_output"]


# ─────────────────────────────────────────────
# CLI smoke-test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    sample = """
    Marcus Rivera — Senior Software Engineer
    Skills: React, Node.js, TypeScript, Next.js, Python, FastAPI, PostgreSQL
    Experience:
      - TechStartup (2021-present): Full-stack engineer. Built AI-powered analytics dashboard.
      - Acme Corp (2019-2021): Backend developer, microservices, AWS.
    Hackathons:
      - React Summit Hackathon (1 month ago) — WINNER, built AI code-review bot in 24 hrs.
      - Junction Helsinki (4 months ago) — Finalist, GenAI travel planner.
      - HackMIT (14 months ago) — Participant.
    Certifications:
      - AWS Certified Developer (2 months ago)
      - LangChain & LangGraph Bootcamp (3 months ago)
    GitHub: 45 commits last month, exploring Svelte and Rust.
    Recent activity: Blog post on vector databases (2 weeks ago).
    """
    output = analyze_profile(sample)
    print(json.dumps(output, indent=2))
