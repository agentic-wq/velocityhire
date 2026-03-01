"""
VelocityHire — Streamlit Demo
==============================
Backup live demo hosted on Streamlit Community Cloud.
Runs the same 3 LangGraph agents as the primary Cloud Run deployment.

Run locally:
    streamlit run streamlit_app.py
"""

import os
import sys
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any

# ── Path setup (must happen before agent imports) ─────────────────────────────
ROOT = Path(__file__).parent
os.environ.setdefault("MOCK_MODE", "true")
for _sub in ("agent1", "agent2", "agent3"):
    _p = str(ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st  # noqa: E402

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VelocityHire — AI Recruitment Demo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Agent imports (cached so they only load once) ─────────────────────────────


@st.cache_resource(show_spinner="Loading AI agents…")
def _load_agents():
    from agent_1 import analyze_profile
    from agent_2 import match_candidate
    from agent_3 import generate_outreach
    return analyze_profile, match_candidate, generate_outreach


analyze_profile, match_candidate, generate_outreach = _load_agents()

# ── Demo data (mirrors demo/app.py) ──────────────────────────────────────────
DEMO_JOB: Dict[str, Any] = {
    "job_title": "Senior AI Engineer",
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
    "company_name": "VelocityHire",
    "recruiter_name": "Sarah Chen",
}

DEMO_CANDIDATES: List[Dict[str, Any]] = [
    {
        "name": "Marcus Rivera",
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
        "name": "Priya Sharma",
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
        "name": "Alex Chen",
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
        "name": "Jordan Kim",
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
        "name": "Elena Voronova",
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

_AGENT_TIMEOUT_SECS = 30

# ── Tier colour helpers ───────────────────────────────────────────────────────
_TIER_COLOURS = {
    "PRIORITY": "#00d4aa",
    "STANDARD": "#3b82f6",
    "NURTURE": "#f59e0b",
    "ARCHIVE": "#6b7280",
}
_ADAPT_COLOURS = {
    "Elite": "#00d4aa",
    "High": "#3b82f6",
    "Standard": "#f59e0b",
    "Low": "#6b7280",
}


def _tier_badge(tier: str, colours: dict) -> str:
    colour = colours.get(tier, "#6b7280")
    return (
        f'<span style="background:{colour};color:#000;padding:2px 10px;'
        f'border-radius:12px;font-size:0.78rem;font-weight:700;">{tier}</span>'
    )


def _score_bar(score: int, colour: str) -> str:
    """Return an HTML progress bar for a 0-100 score."""
    pct = max(0, min(100, score))
    return (
        f'<div style="background:#374151;border-radius:4px;height:8px;margin-top:4px;">'
        f'<div style="background:{colour};width:{pct}%;height:8px;border-radius:4px;"></div>'
        f"</div>"
    )


# ── Pipeline execution ────────────────────────────────────────────────────────
def _call_with_timeout(fn, timeout, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn, *args, **kwargs)
        return fut.result(timeout=timeout)


def run_pipeline(progress_bar, status_text) -> List[Dict[str, Any]]:
    """Run all 3 agents for all 5 demo candidates and return result list."""
    results = []
    total = len(DEMO_CANDIDATES)

    for idx, cand in enumerate(DEMO_CANDIDATES):
        name = cand["name"]
        profile = cand["profile"]

        # Agent 1
        status_text.markdown(
            f"**{cand['emoji']} {name}** — 🔬 Agent 1: Analysing adaptability…"
        )
        try:
            a1 = _call_with_timeout(analyze_profile, _AGENT_TIMEOUT_SECS, profile)
        except concurrent.futures.TimeoutError:
            a1 = {"adaptability_score": 50, "tier": "Standard",
                  "recommend_interview": False, "reasoning": "Timeout",
                  "score_breakdown": {}}
        adapt_score = int(a1.get("adaptability_score") or 50)
        adapt_tier = a1.get("tier") or "Standard"

        # Agent 2
        status_text.markdown(
            f"**{cand['emoji']} {name}** — 🎯 Agent 2: Matching to job…"
        )
        try:
            a2 = _call_with_timeout(
                match_candidate, _AGENT_TIMEOUT_SECS,
                job_title=DEMO_JOB["job_title"],
                job_description=DEMO_JOB["job_description"],
                required_skills=DEMO_JOB["required_skills"],
                candidate_name=name,
                candidate_profile=profile,
                adaptability_score=adapt_score,
                adaptability_tier=adapt_tier,
            )
        except concurrent.futures.TimeoutError:
            weighted = round((adapt_score / 100) * 60, 1)
            a2 = {"total_match_score": int(weighted + 10), "match_tier": "Unknown",
                  "recommend_interview": adapt_score >= 70, "reasoning": "Timeout",
                  "score_breakdown": {"role_fit": {"matched_skills": []},
                                      "culture_fit": {"startup_experience": False}}}
        match_score = int(a2.get("total_match_score") or 0)
        match_tier = a2.get("match_tier") or "Unknown"
        breakdown = a2.get("score_breakdown") or {}
        matched_skills = breakdown.get("role_fit", {}).get("matched_skills", []) or []
        startup_exp = breakdown.get("culture_fit", {}).get("startup_experience", False)
        recommend = bool(a2.get("recommend_interview"))
        reasoning = a2.get("reasoning") or ""

        # Agent 3
        status_text.markdown(
            f"**{cand['emoji']} {name}** — ✉️ Agent 3: Generating outreach…"
        )
        try:
            a3 = _call_with_timeout(
                generate_outreach, _AGENT_TIMEOUT_SECS,
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
        except concurrent.futures.TimeoutError:
            tier = ("PRIORITY" if match_score >= 85 else
                    "STANDARD" if match_score >= 70 else
                    "NURTURE" if match_score >= 55 else "ARCHIVE")
            a3 = {"outreach_tier": tier, "tone": "professional", "key_highlights": [],
                  "campaign": {
                      "linkedin_message": f"Hi {name.split()[0]}, great profile!",
                      "email": {"subject": "Opportunity at VelocityHire",
                                "body": "We'd love to connect."},
                      "followup": {"subject": "", "body": ""},
                      "recruiter_note": f"Timeout — manual review recommended for {name}"}}

        outreach_tier = a3.get("outreach_tier") or "ARCHIVE"
        campaign = a3.get("campaign") or {}

        results.append({
            "name": name,
            "emoji": cand["emoji"],
            "adaptability_score": adapt_score,
            "adaptability_tier": adapt_tier,
            "match_score": match_score,
            "match_tier": match_tier,
            "outreach_tier": outreach_tier,
            "recommend": recommend,
            "key_highlights": a3.get("key_highlights") or [],
            "linkedin_message": campaign.get("linkedin_message", ""),
            "email_subject": campaign.get("email", {}).get("subject", ""),
            "email_body": campaign.get("email", {}).get("body", ""),
            "followup_subject": campaign.get("followup", {}).get("subject", ""),
            "followup_body": campaign.get("followup", {}).get("body", ""),
            "recruiter_note": campaign.get("recruiter_note", ""),
        })

        progress_bar.progress((idx + 1) / total)

    return results


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align:center;padding:2rem 0 1rem;">
      <h1 style="font-size:2.8rem;font-weight:900;margin:0;">
        ⚡ VelocityHire
      </h1>
      <p style="font-size:1.15rem;color:#9ca3af;margin-top:0.4rem;">
        AI-Powered Recruitment Intelligence &nbsp;·&nbsp; 3 LangGraph Agents
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Job description card
with st.expander("📋 Target Role — Senior AI Engineer @ VelocityHire", expanded=False):
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(f"**Description:** {DEMO_JOB['job_description']}")
    with col_b:
        st.markdown("**Required Skills:**")
        st.markdown(", ".join(DEMO_JOB["required_skills"]))

st.markdown("---")

# Run button
col_btn, col_info = st.columns([1, 3])
with col_btn:
    run_clicked = st.button("🚀 Run Demo Pipeline", type="primary", use_container_width=True)
with col_info:
    st.markdown(
        "<small style='color:#9ca3af;'>Runs 3 LangGraph agents on 5 demo candidates "
        "in mock mode — no API key required.</small>",
        unsafe_allow_html=True,
    )

# ── Pipeline execution & results ──────────────────────────────────────────────
if run_clicked:
    st.session_state.pop("results", None)  # clear previous run

if "results" not in st.session_state:
    if run_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()
        with st.spinner("Running pipeline…"):
            st.session_state["results"] = run_pipeline(progress_bar, status_text)
        status_text.empty()
        progress_bar.empty()
        st.success("✅ Pipeline complete — all 5 candidates processed")
    else:
        st.info(
            "👆 Click **Run Demo Pipeline** above to process the 5 demo candidates "
            "through the full AI pipeline."
        )

if "results" in st.session_state:
    results: List[Dict] = st.session_state["results"]

    st.markdown("## 📊 Results")

    # Summary row
    priority = sum(1 for r in results if r.get("outreach_tier") == "PRIORITY")
    standard = sum(1 for r in results if r.get("outreach_tier") == "STANDARD")
    nurture = sum(1 for r in results if r.get("outreach_tier") == "NURTURE")
    archive = sum(1 for r in results if r.get("outreach_tier") == "ARCHIVE")
    avg_adapt = int(sum(r.get("adaptability_score", 0) for r in results) / len(results))
    avg_match = int(sum(r.get("match_score", 0) for r in results) / len(results))

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("🏆 Priority", priority)
    m2.metric("✅ Standard", standard)
    m3.metric("🌱 Nurture", nurture)
    m4.metric("📂 Archive", archive)
    m5.metric("Avg Adaptability", f"{avg_adapt}/100")
    m6.metric("Avg Match", f"{avg_match}/100")

    st.markdown("---")

    # Per-candidate cards
    for r in results:
        adapt_colour = _ADAPT_COLOURS.get(r.get("adaptability_tier", ""), "#6b7280")
        tier_colour = _TIER_COLOURS.get(r.get("outreach_tier", "ARCHIVE"), "#6b7280")
        recommend_badge = (
            '<span style="background:#00d4aa;color:#000;padding:2px 8px;'
            'border-radius:10px;font-size:0.75rem;font-weight:700;">✓ Interview</span>'
            if r.get("recommend") else
            '<span style="background:#374151;color:#9ca3af;padding:2px 8px;'
            'border-radius:10px;font-size:0.75rem;">✗ Skip</span>'
        )

        with st.container():
            st.markdown(
                f"""
                <div style="border:1px solid #374151;border-radius:12px;
                            padding:1.2rem 1.4rem;margin-bottom:1rem;
                            background:#161b22;">
                  <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem;">
                    <span style="font-size:1.6rem;">{r['emoji']}</span>
                    <span style="font-size:1.2rem;font-weight:700;">{r['name']}</span>
                    &nbsp;
                    {_tier_badge(r.get('outreach_tier', 'ARCHIVE'), _TIER_COLOURS)}
                    &nbsp;{recommend_badge}
                  </div>
                  <div style="display:flex;gap:2.5rem;">
                    <div style="min-width:160px;">
                      <div style="font-size:0.78rem;color:#9ca3af;">Adaptability Score</div>
                      <div style="font-size:1.5rem;font-weight:800;color:{adapt_colour};">
                        {r.get('adaptability_score', 0)}<span style="font-size:0.85rem;color:#9ca3af;">/100</span>
                      </div>
                      {_score_bar(r.get('adaptability_score', 0), adapt_colour)}
                      <div style="font-size:0.72rem;color:#9ca3af;margin-top:2px;">
                        {r.get('adaptability_tier', '')}
                      </div>
                    </div>
                    <div style="min-width:160px;">
                      <div style="font-size:0.78rem;color:#9ca3af;">Job Match Score</div>
                      <div style="font-size:1.5rem;font-weight:800;color:{tier_colour};">
                        {r.get('match_score', 0)}<span style="font-size:0.85rem;color:#9ca3af;">/100</span>
                      </div>
                      {_score_bar(r.get('match_score', 0), tier_colour)}
                      <div style="font-size:0.72rem;color:#9ca3af;margin-top:2px;">
                        {r.get('match_tier', '')}
                      </div>
                    </div>
                    <div>
                      <div style="font-size:0.78rem;color:#9ca3af;">Key Highlights</div>
                      <div style="font-size:0.82rem;margin-top:4px;">
                        {"<br>".join(f"• {h}" for h in (r.get('key_highlights') or [])[:3])
                         or "<em style='color:#6b7280;'>—</em>"}
                      </div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Outreach details expander
            with st.expander(f"✉️ View outreach for {r['name']}", expanded=False):
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["LinkedIn", "Email", "Follow-up", "Recruiter Note"]
                )
                with tab1:
                    st.text_area(
                        "LinkedIn Message",
                        value=r.get("linkedin_message", ""),
                        height=140,
                        disabled=True,
                        key=f"li_{r['name']}",
                    )
                with tab2:
                    st.text_input(
                        "Subject",
                        value=r.get("email_subject", ""),
                        disabled=True,
                        key=f"es_{r['name']}",
                    )
                    st.text_area(
                        "Body",
                        value=r.get("email_body", ""),
                        height=180,
                        disabled=True,
                        key=f"eb_{r['name']}",
                    )
                with tab3:
                    st.text_input(
                        "Subject",
                        value=r.get("followup_subject", ""),
                        disabled=True,
                        key=f"fs_{r['name']}",
                    )
                    st.text_area(
                        "Body",
                        value=r.get("followup_body", ""),
                        height=140,
                        disabled=True,
                        key=f"fb_{r['name']}",
                    )
                with tab4:
                    st.text_area(
                        "ATS Note",
                        value=r.get("recruiter_note", ""),
                        height=140,
                        disabled=True,
                        key=f"rn_{r['name']}",
                    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#6b7280;font-size:0.8rem;'>"
    "⚡ VelocityHire · Complete.dev Hackathon 2026 · "
    "Built with LangGraph · "
    "<a href='https://q1inyxqs.run.complete.dev' target='_blank' "
    "style='color:#00d4aa;'>Primary Demo (Cloud Run)</a>"
    "</p>",
    unsafe_allow_html=True,
)
