"""
Agent 2: Job Matcher
LangGraph-powered candidate-to-job matching engine.

Scoring Algorithm:
  - Adaptability Weight (60%) → Score from Agent 1
  - Role Fit           (25%) → Skills vs job requirements
  - Culture Fit        (15%) → Startup exp, collaboration, prototyping

Match threshold: 70+ = recommend for interview
"""

import os
import re
from typing import TypedDict, List
from datetime import datetime
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

class MatchState(TypedDict):
    # Inputs
    job_title: str
    job_description: str
    required_skills: List[str]
    candidate_name: str
    candidate_profile: str
    adaptability_score: int        # From Agent 1 (0-100)
    adaptability_tier: str         # From Agent 1

    # Intermediate
    role_fit_raw: dict
    culture_fit_raw: dict

    # Outputs
    role_fit_score: float          # 0-25
    culture_fit_score: float       # 0-15
    adaptability_weighted: float   # 0-60
    total_match_score: int         # 0-100
    match_tier: str
    recommend_interview: bool
    reasoning: str
    final_output: dict


# ─────────────────────────────────────────────
# Mock scoring engine (used when MOCK_MODE=true)
# ─────────────────────────────────────────────

def _score_role_fit(profile: str, job_desc: str, required_skills: List[str]) -> dict:
    """Rule-based role fit scoring (max 25 pts)."""
    text = profile.lower()
    jd = job_desc.lower()

    # Skills overlap
    matched = [s for s in required_skills if s.lower() in text]
    coverage = len(matched) / max(len(required_skills), 1)
    skills_pts = round(coverage * 15, 1)

    # Experience level signals
    senior_signals = ["senior", "lead", "principal", "staff", "architect", "head of", "vp", "cto"]
    exp_pts = 5.0 if any(s in text for s in senior_signals) else \
        3.0 if any(s in text for s in ["mid", "intermediate", "3 year", "4 year", "5 year"]) else 1.5

    # Domain relevance — check if job keywords appear in profile
    jd_keywords = set(re.findall(r'\b[a-z]{4,}\b', jd)) - {"with", "that", "this",
                                                           "have", "from", "will", "your", "they", "their", "been", "also", "more"}
    domain_overlap = len(jd_keywords & set(re.findall(r'\b[a-z]{4,}\b', text))) / max(len(jd_keywords), 1)
    domain_pts = min(domain_overlap * 10, 5.0)

    total = min(skills_pts + exp_pts + domain_pts, 25.0)
    return {
        "matched_skills": matched,
        "skills_coverage_pct": round(coverage * 100),
        "skills_points": skills_pts,
        "experience_points": exp_pts,
        "domain_points": round(domain_pts, 1),
        "total_role_fit_score": round(total, 1),
        "summary": f"{len(matched)}/{len(required_skills)} required skills matched; {round(coverage * 100)}% coverage.",
    }


def _score_culture_fit(profile: str) -> dict:
    """Rule-based culture fit scoring (max 15 pts)."""
    text = profile.lower()

    # Startup experience
    startup_signals = [
        "startup",
        "early-stage",
        "seed",
        "series a",
        "series b",
        "founding",
        "pre-launch",
        "0 to 1",
        "greenfield"]
    startup_pts = 6.0 if any(s in text for s in startup_signals) else 2.0

    # Cross-functional collaboration
    collab_signals = [
        "cross-functional",
        "collaborated",
        "team of",
        "led team",
        "worked with",
        "partnership",
        "stakeholder"]
    collab_pts = min(sum(1 for s in collab_signals if s in text) * 1.5, 5.0)

    # Rapid prototyping / shipping
    ship_signals = [
        "shipped",
        "launched",
        "prototype",
        "mvp",
        "rapid",
        "hackathon",
        "built in",
        "24 hour",
        "48 hour",
        "weekend"]
    ship_pts = min(sum(1 for s in ship_signals if s in text) * 1.0, 4.0)

    total = min(startup_pts + collab_pts + ship_pts, 15.0)
    return {
        "startup_experience": any(s in text for s in startup_signals),
        "collaboration_signals": [s for s in collab_signals if s in text],
        "shipping_signals": [s for s in ship_signals if s in text],
        "startup_points": startup_pts,
        "collaboration_points": round(collab_pts, 1),
        "shipping_points": round(ship_pts, 1),
        "total_culture_fit_score": round(total, 1),
        "summary": f"Startup exp: {any(s in text for s in startup_signals)}; shipping signals: {len([s for s in ship_signals if s in text])}.",
    }


# ─────────────────────────────────────────────
# LangGraph nodes
# ─────────────────────────────────────────────

def analyze_role_fit(state: MatchState) -> MatchState:
    """Node 1 — Score candidate against job requirements (25 pts)."""
    result = _score_role_fit(
        state["candidate_profile"],
        state["job_description"],
        state["required_skills"],
    )
    return {**state, "role_fit_raw": result, "role_fit_score": result["total_role_fit_score"]}


def analyze_culture_fit(state: MatchState) -> MatchState:
    """Node 2 — Score culture fit (15 pts)."""
    result = _score_culture_fit(state["candidate_profile"])
    return {**state, "culture_fit_raw": result, "culture_fit_score": result["total_culture_fit_score"]}


def apply_adaptability_weight(state: MatchState) -> MatchState:
    """Node 3 — Apply Agent 1 adaptability score at 60% weight."""
    weighted = round((state["adaptability_score"] / 100) * 60, 1)
    return {**state, "adaptability_weighted": weighted}


def aggregate_match_score(state: MatchState) -> MatchState:
    """Node 4 — Combine all dimensions into final match score."""
    total = round(
        state["adaptability_weighted"] +
        state["role_fit_score"] +
        state["culture_fit_score"]
    )
    total = max(0, min(100, total))

    tier = (
        "🏆 Exceptional Match" if total >= 85 else
        "⭐ Strong Match" if total >= 70 else
        "✅ Good Potential" if total >= 55 else
        "📋 Partial Match" if total >= 40 else
        "🔍 Weak Match"
    )

    reasoning = (
        f"Job Match Score: {total}/100 — {tier}\n\n"
        f"• Adaptability (60%): {state['adaptability_weighted']:.1f}/60 "
        f"[Agent 1 score: {state['adaptability_score']}/100, tier: {state['adaptability_tier']}]\n"
        f"• Role Fit (25%): {state['role_fit_score']:.1f}/25 "
        f"[{state['role_fit_raw'].get('summary', '')}]\n"
        f"• Culture Fit (15%): {state['culture_fit_score']:.1f}/15 "
        f"[{state['culture_fit_raw'].get('summary', '')}]\n\n"
        f"{'✅ RECOMMEND for interview — above 70 threshold' if total >= 70 else '📋 Hold — below interview threshold; keep for future roles'}"
    )

    return {
        **state,
        "total_match_score": total,
        "match_tier": tier,
        "recommend_interview": total >= 70,
        "reasoning": reasoning,
    }


def build_output(state: MatchState) -> MatchState:
    """Node 5 — Package final structured output for Agent 3."""
    final = {
        "agent": "Agent 2 — Job Matcher",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "candidate_name": state["candidate_name"],
        "job_title": state["job_title"],
        "total_match_score": state["total_match_score"],
        "match_tier": state["match_tier"],
        "recommend_interview": state["recommend_interview"],
        "score_breakdown": {
            "adaptability": {
                "weighted_score": state["adaptability_weighted"],
                "max": 60,
                "weight": "60%",
                "agent1_raw": state["adaptability_score"],
                "tier": state["adaptability_tier"],
            },
            "role_fit": {
                "score": state["role_fit_score"],
                "max": 25,
                "weight": "25%",
                "matched_skills": state["role_fit_raw"].get("matched_skills", []),
                "coverage_pct": state["role_fit_raw"].get("skills_coverage_pct", 0),
                "summary": state["role_fit_raw"].get("summary", ""),
            },
            "culture_fit": {
                "score": state["culture_fit_score"],
                "max": 15,
                "weight": "15%",
                "startup_experience": state["culture_fit_raw"].get("startup_experience", False),
                "summary": state["culture_fit_raw"].get("summary", ""),
            },
        },
        "reasoning": state["reasoning"],
        "ready_for_agent_3": state["recommend_interview"],
    }
    return {**state, "final_output": final}


# ─────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────

def build_agent_2() -> StateGraph:
    graph = StateGraph(MatchState)

    graph.add_node("analyze_role_fit", analyze_role_fit)
    graph.add_node("analyze_culture_fit", analyze_culture_fit)
    graph.add_node("apply_adaptability_weight", apply_adaptability_weight)
    graph.add_node("aggregate_match_score", aggregate_match_score)
    graph.add_node("build_output", build_output)

    graph.set_entry_point("analyze_role_fit")
    graph.add_edge("analyze_role_fit", "analyze_culture_fit")
    graph.add_edge("analyze_culture_fit", "apply_adaptability_weight")
    graph.add_edge("apply_adaptability_weight", "aggregate_match_score")
    graph.add_edge("aggregate_match_score", "build_output")
    graph.add_edge("build_output", END)

    return graph.compile()


agent_2_graph = build_agent_2()


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def match_candidate(
    job_title: str,
    job_description: str,
    required_skills: List[str],
    candidate_name: str,
    candidate_profile: str,
    adaptability_score: int,
    adaptability_tier: str = "Unknown",
) -> dict:
    """
    Entry point. Accepts job + candidate data including Agent 1 score.
    Returns job match report (final_output dict).
    """
    initial: MatchState = {
        "job_title": job_title,
        "job_description": job_description,
        "required_skills": required_skills,
        "candidate_name": candidate_name,
        "candidate_profile": candidate_profile,
        "adaptability_score": adaptability_score,
        "adaptability_tier": adaptability_tier,
        "role_fit_raw": {},
        "culture_fit_raw": {},
        "role_fit_score": 0.0,
        "culture_fit_score": 0.0,
        "adaptability_weighted": 0.0,
        "total_match_score": 0,
        "match_tier": "",
        "recommend_interview": False,
        "reasoning": "",
        "final_output": {},
    }
    result = agent_2_graph.invoke(initial)
    return result["final_output"]
