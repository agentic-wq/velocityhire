"""
VelocityHire — Shared Memory Module (Phase 4)
===============================================
SQLite-backed persistent store shared across all three agents.

Tables:
  candidates           — Agent 1 adaptability scores
  job_matches          — Agent 2 job match results
  outreach_campaigns   — Agent 3 outreach campaigns

All agents write to the same database file, enabling cross-agent
pipeline queries and historical analytics.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger("velocityhire.db")

# ── Graceful import of sqlalchemy ─────────────────────────────────────────────
try:
    from sqlalchemy import (
        create_engine, text, MetaData, Table, Column,
        Integer, String, Float, Boolean, DateTime, Text,
    )
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("sqlalchemy not installed — DB persistence disabled. Run: pip install sqlalchemy")

# ── DB path ───────────────────────────────────────────────────────────────────
WORKSPACE = "/mnt/efs/spaces/6f40e0fa-8a03-41a6-a37c-c728be34b83b/f99b24e1-53b1-4954-a709-a448e806bd7b"
DB_PATH   = os.getenv("DB_PATH", f"{WORKSPACE}/velocityhire.db")
DB_URL    = f"sqlite:///{DB_PATH}"

_engine = None
_meta: Any = None   # MetaData instance, populated on first use


# ── Engine + schema bootstrap ─────────────────────────────────────────────────

def _get_engine():
    global _engine, _meta
    if not SQLALCHEMY_AVAILABLE:
        return None
    if _engine is None:
        _engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
        _init_tables()
    return _engine


def _init_tables():
    """Create all tables if they don't already exist."""
    global _meta
    _meta = MetaData()

    # ── Agent 1 results ───────────────────────────────────────────────────────
    Table("candidates", _meta,
        Column("id",                 Integer, primary_key=True, autoincrement=True),
        Column("created_at",         String(50)),
        Column("candidate_name",     String(255)),
        Column("adaptability_score", Integer),
        Column("adaptability_tier",  String(100)),
        Column("recommend_interview",String(10)),   # "True" / "False"
        Column("score_breakdown",    Text),          # JSON string
        Column("reasoning",          Text),
        Column("profile_snippet",    Text),          # first 500 chars
    )

    # ── Agent 2 results ───────────────────────────────────────────────────────
    Table("job_matches", _meta,
        Column("id",                    Integer, primary_key=True, autoincrement=True),
        Column("created_at",            String(50)),
        Column("candidate_name",        String(255)),
        Column("job_title",             String(255)),
        Column("adaptability_score",    Integer),
        Column("total_match_score",     Integer),
        Column("match_tier",            String(100)),
        Column("role_fit_score",        Float),
        Column("culture_fit_score",     Float),
        Column("adaptability_weighted", Float),
        Column("matched_skills",        Text),   # JSON array string
        Column("startup_experience",    String(10)),
        Column("recommend_interview",   String(10)),
        Column("reasoning",             Text),
        Column("score_breakdown",       Text),   # JSON string
    )

    # ── Agent 3 results ───────────────────────────────────────────────────────
    Table("outreach_campaigns", _meta,
        Column("id",                Integer, primary_key=True, autoincrement=True),
        Column("created_at",        String(50)),
        Column("candidate_name",    String(255)),
        Column("job_title",         String(255)),
        Column("company_name",      String(255)),
        Column("recruiter_name",    String(255)),
        Column("total_match_score", Integer),
        Column("adaptability_score",Integer),
        Column("outreach_tier",     String(50)),
        Column("tone",              String(50)),
        Column("key_highlights",    Text),   # JSON array string
        Column("linkedin_message",  Text),
        Column("email_subject",     Text),
        Column("email_body",        Text),
        Column("followup_subject",  Text),
        Column("followup_body",     Text),
        Column("recruiter_note",    Text),
    )

    _meta.create_all(_engine)
    logger.info("VelocityHire DB tables ready at %s", DB_PATH)


# ── Name extraction helper ─────────────────────────────────────────────────────

def _extract_name_from_profile(profile_text: str) -> str:
    """Best-effort extraction of a candidate name from the profile text's first line."""
    if not profile_text:
        return "Unknown"
    first_line = profile_text.strip().split("\n")[0].strip()
    for prefix in ("Name:", "Profile:", "Candidate:", "About:"):
        if first_line.lower().startswith(prefix.lower()):
            first_line = first_line[len(prefix):].strip()
    # Take up to first ' — ' separator which many profiles use (e.g. "Marcus Rivera — SWE")
    if " — " in first_line:
        first_line = first_line.split(" — ")[0].strip()
    return first_line[:80] if first_line else "Unknown"


def _row_to_dict(row, table) -> Dict:
    """Convert a SQLAlchemy row-tuple to a plain dict, deserializing JSON fields."""
    d = dict(zip([c.name for c in table.columns], row))
    for key in ("score_breakdown", "matched_skills", "key_highlights"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    return d


# ── Write helpers ─────────────────────────────────────────────────────────────

def save_candidate_score(
    profile_text: str,
    result: dict,
    candidate_name: Optional[str] = None,
) -> Optional[int]:
    """Persist an Agent 1 adaptability result. Returns the inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        name = candidate_name or _extract_name_from_profile(profile_text)
        tbl = _meta.tables["candidates"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at          = datetime.utcnow().isoformat(),
                candidate_name      = name,
                adaptability_score  = result.get("adaptability_score", 0),
                adaptability_tier   = result.get("tier", ""),
                recommend_interview = str(result.get("recommend_interview", False)),
                score_breakdown     = json.dumps(result.get("score_breakdown", {})),
                reasoning           = result.get("reasoning", ""),
                profile_snippet     = (profile_text or "")[:500],
            ))
            row_id = res.lastrowid
        logger.info("DB [candidates] saved id=%s name=%s score=%s", row_id, name, result.get("adaptability_score"))
        return row_id
    except Exception as exc:
        logger.error("save_candidate_score failed: %s", exc)
        return None


def save_job_match(result: dict) -> Optional[int]:
    """Persist an Agent 2 job-match result. Returns the inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        bd   = result.get("score_breakdown", {})
        tbl  = _meta.tables["job_matches"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at            = datetime.utcnow().isoformat(),
                candidate_name        = result.get("candidate_name", "Unknown"),
                job_title             = result.get("job_title", ""),
                adaptability_score    = bd.get("adaptability", {}).get("agent1_raw", 0),
                total_match_score     = result.get("total_match_score", 0),
                match_tier            = result.get("match_tier", ""),
                role_fit_score        = bd.get("role_fit", {}).get("score", 0.0),
                culture_fit_score     = bd.get("culture_fit", {}).get("score", 0.0),
                adaptability_weighted = bd.get("adaptability", {}).get("weighted_score", 0.0),
                matched_skills        = json.dumps(bd.get("role_fit", {}).get("matched_skills", [])),
                startup_experience    = str(bd.get("culture_fit", {}).get("startup_experience", False)),
                recommend_interview   = str(result.get("recommend_interview", False)),
                reasoning             = result.get("reasoning", ""),
                score_breakdown       = json.dumps(bd),
            ))
            row_id = res.lastrowid
        logger.info("DB [job_matches] saved id=%s candidate=%s score=%s",
                    row_id, result.get("candidate_name"), result.get("total_match_score"))
        return row_id
    except Exception as exc:
        logger.error("save_job_match failed: %s", exc)
        return None


def save_outreach(result: dict) -> Optional[int]:
    """Persist an Agent 3 outreach campaign. Returns the inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        camp = result.get("campaign", {})
        tbl  = _meta.tables["outreach_campaigns"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at        = datetime.utcnow().isoformat(),
                candidate_name    = result.get("candidate_name", "Unknown"),
                job_title         = result.get("job_title", ""),
                company_name      = result.get("company_name", ""),
                recruiter_name    = result.get("recruiter_name", ""),
                total_match_score = result.get("total_match_score", 0),
                adaptability_score= result.get("adaptability_score", 0),
                outreach_tier     = result.get("outreach_tier", ""),
                tone              = result.get("tone", ""),
                key_highlights    = json.dumps(result.get("key_highlights", [])),
                linkedin_message  = camp.get("linkedin_message", ""),
                email_subject     = camp.get("email", {}).get("subject", ""),
                email_body        = camp.get("email", {}).get("body", ""),
                followup_subject  = camp.get("followup", {}).get("subject", ""),
                followup_body     = camp.get("followup", {}).get("body", ""),
                recruiter_note    = camp.get("recruiter_note", ""),
            ))
            row_id = res.lastrowid
        logger.info("DB [outreach_campaigns] saved id=%s candidate=%s tier=%s",
                    row_id, result.get("candidate_name"), result.get("outreach_tier"))
        return row_id
    except Exception as exc:
        logger.error("save_outreach failed: %s", exc)
        return None


# ── Read helpers ──────────────────────────────────────────────────────────────

def get_recent_candidates(limit: int = 20) -> List[Dict]:
    """Return the N most recent Agent 1 records."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["candidates"]
        with engine.connect() as conn:
            rows = conn.execute(
                tbl.select().order_by(tbl.c.id.desc()).limit(limit)
            ).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_recent_candidates failed: %s", exc)
        return []


def get_recent_matches(limit: int = 20) -> List[Dict]:
    """Return the N most recent Agent 2 records."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["job_matches"]
        with engine.connect() as conn:
            rows = conn.execute(
                tbl.select().order_by(tbl.c.id.desc()).limit(limit)
            ).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_recent_matches failed: %s", exc)
        return []


def get_recent_campaigns(limit: int = 20) -> List[Dict]:
    """Return the N most recent Agent 3 records."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["outreach_campaigns"]
        with engine.connect() as conn:
            rows = conn.execute(
                tbl.select().order_by(tbl.c.id.desc()).limit(limit)
            ).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_recent_campaigns failed: %s", exc)
        return []


def get_pipeline_summary(candidate_name: str) -> Dict:
    """Cross-agent view: all data for a candidate across Agents 1, 2, and 3."""
    if not SQLALCHEMY_AVAILABLE:
        return {"error": "sqlalchemy not installed"}
    try:
        engine = _get_engine()
        if engine is None:
            return {}
        cands = _meta.tables["candidates"]
        jm    = _meta.tables["job_matches"]
        camps = _meta.tables["outreach_campaigns"]
        with engine.connect() as conn:
            c_rows = conn.execute(
                cands.select()
                     .where(cands.c.candidate_name.ilike(f"%{candidate_name}%"))
                     .order_by(cands.c.id.desc()).limit(5)
            ).fetchall()
            jm_rows = conn.execute(
                jm.select()
                  .where(jm.c.candidate_name.ilike(f"%{candidate_name}%"))
                  .order_by(jm.c.id.desc()).limit(5)
            ).fetchall()
            camp_rows = conn.execute(
                camps.select()
                     .where(camps.c.candidate_name.ilike(f"%{candidate_name}%"))
                     .order_by(camps.c.id.desc()).limit(5)
            ).fetchall()
        return {
            "candidate_name":     candidate_name,
            "profile_analyses":   [_row_to_dict(r, cands) for r in c_rows],
            "job_matches":        [_row_to_dict(r, jm)    for r in jm_rows],
            "outreach_campaigns": [_row_to_dict(r, camps) for r in camp_rows],
        }
    except Exception as exc:
        logger.error("get_pipeline_summary failed: %s", exc)
        return {"error": str(exc)}


def get_db_stats() -> Dict:
    """Row counts from all tables — used by /health endpoints."""
    if not SQLALCHEMY_AVAILABLE:
        return {"sqlalchemy": "not_installed", "db_persistence": False}
    try:
        engine = _get_engine()
        if engine is None:
            return {"db_persistence": False}
        with engine.connect() as conn:
            n_c  = conn.execute(text("SELECT COUNT(*) FROM candidates")).scalar()
            n_jm = conn.execute(text("SELECT COUNT(*) FROM job_matches")).scalar()
            n_oc = conn.execute(text("SELECT COUNT(*) FROM outreach_campaigns")).scalar()
        return {
            "db_path":             DB_PATH,
            "db_persistence":      True,
            "candidates":          n_c,
            "job_matches":         n_jm,
            "outreach_campaigns":  n_oc,
            "total_pipeline_runs": min(n_c, n_jm, n_oc),
        }
    except Exception as exc:
        return {"error": str(exc), "db_persistence": False}
