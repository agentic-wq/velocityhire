"""
VelocityHire — Analytics Module (Phase 4)
==========================================
Computes hiring intelligence from the shared SQLite database.

Functions:
  get_pipeline_funnel()      — stage-by-stage candidate counts
  get_score_distribution()   — adaptability score histogram
  get_tier_breakdown()       — outreach tier counts
  get_daily_activity()       — time-series candidates per day (last 30d)
  get_top_skills()           — most frequently matched skills
  get_avg_scores()           — average scores across all dimensions
  get_predictive_insights()  — heuristic success patterns from historical data
  get_full_analytics()       — all of the above in one call
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("velocityhire.analytics")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_db():
    """Lazy import to avoid circular deps."""
    try:
        from shared.db_memory import _get_engine, _meta
        return _get_engine(), _meta
    except Exception:
        return None, None


def _cid_clause(company_id: Optional[str]) -> tuple:
    """Return (sql_fragment, params) for optional tenant scoping."""
    if company_id:
        return "company_id = :cid", {"cid": company_id}
    return "1=1", {}


def _fetch_all(engine, meta, table_name: str, company_id: Optional[str] = None) -> List[Dict]:
    """Fetch all rows from a table, optionally scoped to a company.

    Uses row._mapping (actual DB column names) rather than positional zip
    against metadata columns — this avoids mis-mapping when company_id was
    added via ALTER TABLE (appended at end) while metadata has it at position 3.
    """
    try:
        from sqlalchemy import text
        clause, params = _cid_clause(company_id)
        with engine.connect() as conn:
            result_proxy = conn.execute(
                text(f"SELECT * FROM {table_name} WHERE {clause} ORDER BY id DESC"),
                params,
            )
            result = []
            for row in result_proxy:
                # Use actual DB column names via _mapping, not metadata order
                d = dict(row._mapping)
                for key in ("score_breakdown", "matched_skills", "key_highlights"):
                    if key in d and d[key]:
                        try:
                            d[key] = json.loads(d[key])
                        except Exception:
                            pass
                result.append(d)
        return result
    except Exception as exc:
        logger.error("_fetch_all(%s) failed: %s", table_name, exc)
        return []


# ── Analytics functions ───────────────────────────────────────────────────────

def get_pipeline_funnel(company_id: Optional[str] = None) -> Dict:
    """Stage-by-stage conversion counts."""
    engine, meta = _get_db()
    if not engine:
        return {}
    try:
        from sqlalchemy import text
        clause, params = _cid_clause(company_id)
        with engine.connect() as conn:
            n_c = conn.execute(text(f"SELECT COUNT(*) FROM candidates WHERE {clause}"), params).scalar() or 0
            n_jm = conn.execute(text(f"SELECT COUNT(*) FROM job_matches WHERE {clause}"), params).scalar() or 0
            n_oc = conn.execute(text(f"SELECT COUNT(*) FROM outreach_campaigns WHERE {clause}"), params).scalar() or 0

            # Priority tier (fast-track candidates)
            priority_params = {**params, "tier": "PRIORITY"}
            priority_clause = f"{clause} AND outreach_tier = :tier"
            n_priority = conn.execute(
                text(f"SELECT COUNT(*) FROM outreach_campaigns WHERE {priority_clause}"),
                priority_params,
            ).scalar() or 0

            # Interview recommendations
            rec_params = {**params, "rec": "True"}
            n_rec = conn.execute(
                text(f"SELECT COUNT(*) FROM candidates WHERE {clause} AND recommend_interview = :rec"),
                rec_params,
            ).scalar() or 0

        return {
            "profiles_analyzed": n_c,
            "jobs_matched": n_jm,
            "campaigns_sent": n_oc,
            "priority_candidates": n_priority,
            "interview_recommended": n_rec,
            "match_rate_pct": round(n_jm / n_c * 100) if n_c else 0,
            "outreach_rate_pct": round(n_oc / n_c * 100) if n_c else 0,
            "priority_rate_pct": round(n_priority / n_oc * 100) if n_oc else 0,
            "interview_rate_pct": round(n_rec / n_c * 100) if n_c else 0,
        }
    except Exception as exc:
        logger.error("get_pipeline_funnel: %s", exc)
        return {}


def get_score_distribution(company_id: Optional[str] = None) -> Dict:
    """Histogram of adaptability scores in 10-point buckets."""
    engine, meta = _get_db()
    if not engine:
        return {}
    try:
        rows = _fetch_all(engine, meta, "candidates", company_id)
        buckets = {f"{i}-{i + 9}": 0 for i in range(0, 100, 10)}
        buckets["100"] = 0

        scores = []
        for r in rows:
            s = r.get("adaptability_score") or 0
            try:
                s = int(s)
                scores.append(s)
                if s == 100:
                    buckets["100"] += 1
                else:
                    key = f"{(s // 10) * 10}-{(s // 10) * 10 + 9}"
                    buckets[key] = buckets.get(key, 0) + 1
            except Exception:
                pass

        avg = round(sum(scores) / len(scores), 1) if scores else 0
        return {
            "buckets": buckets,
            "labels": list(buckets.keys()),
            "values": list(buckets.values()),
            "average": avg,
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "count": len(scores),
        }
    except Exception as exc:
        logger.error("get_score_distribution: %s", exc)
        return {}


def get_tier_breakdown(company_id: Optional[str] = None) -> Dict:
    """Outreach tier distribution across all campaigns."""
    engine, meta = _get_db()
    if not engine:
        return {}
    try:
        rows = _fetch_all(engine, meta, "outreach_campaigns", company_id)
        tier_counts = Counter(r.get("outreach_tier", "UNKNOWN") for r in rows)
        order = ["PRIORITY", "STANDARD", "NURTURE", "ARCHIVE"]
        labels = order + [t for t in tier_counts if t not in order]
        values = [tier_counts.get(t, 0) for t in labels]
        return {
            "labels": labels,
            "values": values,
            "counts": dict(zip(labels, values)),
            "total": sum(values),
        }
    except Exception as exc:
        logger.error("get_tier_breakdown: %s", exc)
        return {}


def get_daily_activity(
    company_id: Optional[str] = None,
    days: int = 14,
) -> Dict:
    """Candidates analyzed per day for the last N days."""
    engine, meta = _get_db()
    if not engine:
        return {}
    try:
        rows = _fetch_all(engine, meta, "candidates", company_id)
        today = datetime.utcnow().date()
        date_counts: Dict[str, int] = defaultdict(int)

        for r in rows:
            raw = r.get("created_at", "")[:10]
            try:
                d = datetime.strptime(raw, "%Y-%m-%d").date()
                if (today - d).days < days:
                    date_counts[raw] += 1
            except Exception:
                pass

        # Build complete date range (fill gaps with 0)
        labels, values = [], []
        for i in range(days - 1, -1, -1):
            day = (today - timedelta(days=i)).isoformat()
            labels.append(day[5:])   # MM-DD
            values.append(date_counts.get(day, 0))

        return {"labels": labels, "values": values, "days": days}
    except Exception as exc:
        logger.error("get_daily_activity: %s", exc)
        return {}


def get_top_skills(
    company_id: Optional[str] = None,
    top_n: int = 10,
) -> Dict:
    """Most frequently matched skills across all job-match runs."""
    engine, meta = _get_db()
    if not engine:
        return {}
    try:
        rows = _fetch_all(engine, meta, "job_matches", company_id)
        skill_counter: Counter = Counter()
        for r in rows:
            skills = r.get("matched_skills") or []
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except Exception:
                    skills = []
            skill_counter.update(s.lower() for s in skills if s)

        top = skill_counter.most_common(top_n)
        return {
            "labels": [s for s, _ in top],
            "values": [c for _, c in top],
            "total_unique": len(skill_counter),
        }
    except Exception as exc:
        logger.error("get_top_skills: %s", exc)
        return {}


def get_avg_scores(company_id: Optional[str] = None) -> Dict:
    """Average scores across all three agents' dimensions."""
    engine, meta = _get_db()
    if not engine:
        return {}
    try:
        from sqlalchemy import text
        clause, params = _cid_clause(company_id)

        with engine.connect() as conn:
            avg_adapt = conn.execute(text(
                f"SELECT AVG(adaptability_score) FROM candidates WHERE {clause}"
            ), params).scalar() or 0

            avg_match = conn.execute(text(
                f"SELECT AVG(total_match_score) FROM job_matches WHERE {clause}"
            ), params).scalar() or 0

            avg_role = conn.execute(text(
                f"SELECT AVG(role_fit_score) FROM job_matches WHERE {clause}"
            ), params).scalar() or 0

            avg_culture = conn.execute(text(
                f"SELECT AVG(culture_fit_score) FROM job_matches WHERE {clause}"
            ), params).scalar() or 0

        return {
            "avg_adaptability": round(float(avg_adapt), 1),
            "avg_job_match": round(float(avg_match), 1),
            "avg_role_fit": round(float(avg_role), 1),
            "avg_culture_fit": round(float(avg_culture), 1),
        }
    except Exception as exc:
        logger.error("get_avg_scores: %s", exc)
        return {}


def get_predictive_insights(company_id: Optional[str] = None) -> List[Dict]:
    """
    Heuristic insights derived from historical pipeline data.
    Returns a list of insight cards with title, value, and recommendation.
    """
    engine, meta = _get_db()
    if not engine:
        return []
    try:
        from sqlalchemy import text
        clause, params = _cid_clause(company_id)

        with engine.connect() as conn:
            # High adaptability (80+) → interview rate
            high_adapt_params = {**params, "min": 80, "rec": "True"}
            high_adapt_total = conn.execute(text(
                f"SELECT COUNT(*) FROM candidates WHERE {clause} AND adaptability_score >= :min"
            ), high_adapt_params).scalar() or 0
            high_adapt_rec = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM candidates WHERE {clause} AND adaptability_score >= :min AND recommend_interview = :rec"),
                high_adapt_params).scalar() or 0

            # PRIORITY tier → outreach conversion
            priority_total = conn.execute(text(
                f"SELECT COUNT(*) FROM outreach_campaigns WHERE {clause} AND outreach_tier='PRIORITY'"
            ), params).scalar() or 0

            # Average days between first analysis and outreach (proxy: not calculable
            # without timestamps gap, use counts ratio)
            total_cands = conn.execute(text(f"SELECT COUNT(*) FROM candidates WHERE {clause}"), params).scalar() or 0
            total_outreach = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM outreach_campaigns WHERE {clause}"),
                params).scalar() or 0

            # Startup experience correlation with high match
            startup_high_params = {**params, "rec": "True", "su": "True"}
            startup_high = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM job_matches WHERE {clause} AND startup_experience = :su AND recommend_interview = :rec"),
                startup_high_params).scalar() or 0
            startup_total = conn.execute(text(
                f"SELECT COUNT(*) FROM job_matches WHERE {clause} AND startup_experience = :su"
            ), {**params, "su": "True"}).scalar() or 0

        insights = []

        # Insight 1 — High adaptability success rate
        if high_adapt_total > 0:
            rate = round(high_adapt_rec / high_adapt_total * 100)
            insights.append({
                "icon": "🎯",
                "title": "High Adaptability → Interview Rate",
                "value": f"{rate}%",
                "detail": f"{high_adapt_rec} of {high_adapt_total} candidates with score ≥80 recommended for interview",
                "recommendation": "Prioritise candidates with adaptability score ≥80 — they pass the interview bar at a significantly higher rate.",
                "color": "#22c55e" if rate >= 70 else "#f59e0b",
            })

        # Insight 2 — Pipeline conversion rate
        if total_cands > 0:
            conv = round(total_outreach / total_cands * 100)
            insights.append({
                "icon": "⚡",
                "title": "End-to-End Pipeline Conversion",
                "value": f"{conv}%",
                "detail": f"{total_outreach} of {total_cands} analysed candidates reached outreach stage",
                "recommendation": "A conversion rate above 30% indicates a well-calibrated pipeline. Below 20% suggests criteria may be too strict.",
                "color": "#6c63ff",
            })

        # Insight 3 — Startup experience correlation
        if startup_total > 0:
            su_rate = round(startup_high / startup_total * 100)
            insights.append({
                "icon": "🚀",
                "title": "Startup Experience → Match Rate",
                "value": f"{su_rate}%",
                "detail": f"{startup_high} of {startup_total} candidates with startup exp recommended",
                "recommendation": "Startup experience is a strong culture-fit signal. These candidates score higher on adaptability and rapid-shipping dimensions.",
                "color": "#f5a623",
            })

        # Insight 4 — Priority tier volume
        if priority_total > 0 and total_outreach > 0:
            pct = round(priority_total / total_outreach * 100)
            insights.append({
                "icon": "🏆",
                "title": "Priority Tier Ratio",
                "value": f"{pct}%",
                "detail": f"{priority_total} of {total_outreach} outreach campaigns are Priority tier",
                "recommendation": "Priority candidates should be contacted within 24 hours. Ratios above 30% indicate a strong talent pipeline for the role.",
                "color": "#6c63ff",
            })

        # Fallback if no data yet
        if not insights:
            insights.append({
                "icon": "📊",
                "title": "Insights Available Soon",
                "value": "—",
                "detail": "Run candidates through the pipeline to unlock predictive insights.",
                "recommendation": "Score at least 5 candidates to generate meaningful analytics.",
                "color": "#94a3b8",
            })

        return insights
    except Exception as exc:
        logger.error("get_predictive_insights: %s", exc)
        return []


def get_full_analytics(company_id: Optional[str] = None) -> Dict:
    """Aggregate all analytics in a single call."""
    return {
        "company_id": company_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "funnel": get_pipeline_funnel(company_id),
        "score_distribution": get_score_distribution(company_id),
        "tier_breakdown": get_tier_breakdown(company_id),
        "daily_activity": get_daily_activity(company_id),
        "top_skills": get_top_skills(company_id),
        "avg_scores": get_avg_scores(company_id),
        "predictive_insights": get_predictive_insights(company_id),
    }
