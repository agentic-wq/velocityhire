"""
VelocityHire — Shared Memory Module (Phase 4 · Multi-Tenant)
=============================================================
SQLite-backed persistent store shared across all three agents.

Tables:
  companies            — Tenant registry
  candidates           — Agent 1 adaptability scores  (per company)
  job_matches          — Agent 2 job match results    (per company)
  outreach_campaigns   — Agent 3 outreach campaigns   (per company)

All agents write to the same database file; every row is scoped to a
company_id so data is fully isolated between tenants.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger("velocityhire.db")

# ── Graceful import of sqlalchemy ──────────────────────────────────────────────
try:
    from sqlalchemy import (
        create_engine, text, MetaData, Table, Column,
        Integer, String, Float, Boolean, Text,
    )
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("sqlalchemy not installed — DB persistence disabled.")

# ── DB path ────────────────────────────────────────────────────────────────────
WORKSPACE = "/mnt/efs/spaces/6f40e0fa-8a03-41a6-a37c-c728be34b83b/f99b24e1-53b1-4954-a709-a448e806bd7b"
DB_PATH   = os.getenv("DB_PATH", f"{WORKSPACE}/velocityhire.db")
DB_URL    = f"sqlite:///{DB_PATH}"

DEFAULT_COMPANY = "demo"

_engine = None
_meta: Any = None


# ── Engine + schema bootstrap ──────────────────────────────────────────────────

def _get_engine():
    global _engine, _meta
    if not SQLALCHEMY_AVAILABLE:
        return None
    if _engine is None:
        _engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
        _init_tables()
        _migrate_tables()
    return _engine


def _init_tables():
    """Create all tables if they don't already exist."""
    global _meta
    _meta = MetaData()

    # ── Tenant registry ─────────────────────────────────────────────────────
    Table("companies", _meta,
        Column("id",           Integer, primary_key=True, autoincrement=True),
        Column("created_at",   String(50)),
        Column("company_id",   String(100), unique=True),   # slug e.g. "acme-corp"
        Column("company_name", String(255)),
        Column("api_key",      String(255), nullable=True), # optional per-tenant key
        Column("plan",         String(50),  default="starter"),  # starter / pro / enterprise
        Column("is_active",    String(10),  default="True"),
    )

    # ── Agent 1 results ───────────────────────────────────────────────────────
    Table("candidates", _meta,
        Column("id",                 Integer, primary_key=True, autoincrement=True),
        Column("created_at",         String(50)),
        Column("company_id",         String(100), default=DEFAULT_COMPANY),
        Column("candidate_name",     String(255)),
        Column("adaptability_score", Integer),
        Column("adaptability_tier",  String(100)),
        Column("recommend_interview",String(10)),
        Column("score_breakdown",    Text),
        Column("reasoning",          Text),
        Column("profile_snippet",    Text),
    )

    # ── Agent 2 results ───────────────────────────────────────────────────────
    Table("job_matches", _meta,
        Column("id",                    Integer, primary_key=True, autoincrement=True),
        Column("created_at",            String(50)),
        Column("company_id",            String(100), default=DEFAULT_COMPANY),
        Column("candidate_name",        String(255)),
        Column("job_title",             String(255)),
        Column("adaptability_score",    Integer),
        Column("total_match_score",     Integer),
        Column("match_tier",            String(100)),
        Column("role_fit_score",        Float),
        Column("culture_fit_score",     Float),
        Column("adaptability_weighted", Float),
        Column("matched_skills",        Text),
        Column("startup_experience",    String(10)),
        Column("recommend_interview",   String(10)),
        Column("reasoning",             Text),
        Column("score_breakdown",       Text),
    )

    # ── Hiring outcomes (success tracking) ───────────────────────────────────
    Table("outcomes", _meta,
        Column("id",             Integer, primary_key=True, autoincrement=True),
        Column("created_at",     String(50)),
        Column("company_id",     String(100), default=DEFAULT_COMPANY),
        Column("candidate_name", String(255)),
        Column("job_title",      String(255)),
        Column("outcome",        String(50)),   # hired / rejected / no_response / offer_declined
        Column("adaptability_score", Integer, nullable=True),
        Column("match_score",    Integer, nullable=True),
        Column("time_to_hire_days", Integer, nullable=True),
        Column("notes",          Text, nullable=True),
    )

    # ── Agent 3 results ───────────────────────────────────────────────────────
    Table("outreach_campaigns", _meta,
        Column("id",                Integer, primary_key=True, autoincrement=True),
        Column("created_at",        String(50)),
        Column("company_id",        String(100), default=DEFAULT_COMPANY),
        Column("candidate_name",    String(255)),
        Column("job_title",         String(255)),
        Column("company_name",      String(255)),
        Column("recruiter_name",    String(255)),
        Column("total_match_score", Integer),
        Column("adaptability_score",Integer),
        Column("outreach_tier",     String(50)),
        Column("tone",              String(50)),
        Column("key_highlights",    Text),
        Column("linkedin_message",  Text),
        Column("email_subject",     Text),
        Column("email_body",        Text),
        Column("followup_subject",  Text),
        Column("followup_body",     Text),
        Column("recruiter_note",    Text),
    )

    _meta.create_all(_engine)
    logger.info("VelocityHire DB tables ready at %s", DB_PATH)

    # Ensure the demo company exists
    _ensure_demo_company()


def _migrate_tables():
    """
    Add company_id to existing tables that predate multi-tenancy.
    SQLite does not support IF NOT EXISTS on ALTER TABLE so we use try/except.
    """
    if not SQLALCHEMY_AVAILABLE or _engine is None:
        return
    with _engine.begin() as conn:
        for tbl in ("candidates", "job_matches", "outreach_campaigns"):
            try:
                conn.execute(text(
                    f"ALTER TABLE {tbl} ADD COLUMN company_id TEXT DEFAULT '{DEFAULT_COMPANY}'"
                ))
                logger.info("Migrated table %s: added company_id column", tbl)
            except Exception:
                pass  # Column already exists — safe to ignore
        # outcomes table migration (add company_id if missing)
        try:
            conn.execute(text(
                f"ALTER TABLE outcomes ADD COLUMN company_id TEXT DEFAULT '{DEFAULT_COMPANY}'"
            ))
        except Exception:
            pass


def _ensure_demo_company():
    """Seed the demo tenant if not present."""
    try:
        engine = _get_engine()
        if engine is None:
            return
        tbl = _meta.tables["companies"]
        with engine.connect() as conn:
            row = conn.execute(
                tbl.select().where(tbl.c.company_id == DEFAULT_COMPANY)
            ).fetchone()
        if not row:
            with engine.begin() as conn:
                conn.execute(tbl.insert().values(
                    created_at   = datetime.utcnow().isoformat(),
                    company_id   = DEFAULT_COMPANY,
                    company_name = "VelocityHire Demo",
                    api_key      = None,
                    plan         = "starter",
                    is_active    = "True",
                ))
            logger.info("Seeded demo company tenant")
    except Exception as exc:
        logger.warning("_ensure_demo_company failed (non-fatal): %s", exc)


# ── Name extraction helper ─────────────────────────────────────────────────────

def _extract_name_from_profile(profile_text: str) -> str:
    if not profile_text:
        return "Unknown"
    first_line = profile_text.strip().split("\n")[0].strip()
    for prefix in ("Name:", "Profile:", "Candidate:", "About:"):
        if first_line.lower().startswith(prefix.lower()):
            first_line = first_line[len(prefix):].strip()
    if " — " in first_line:
        first_line = first_line.split(" — ")[0].strip()
    return first_line[:80] if first_line else "Unknown"


def _row_to_dict(row, table) -> Dict:
    d = dict(zip([c.name for c in table.columns], row))
    for key in ("score_breakdown", "matched_skills", "key_highlights"):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    return d


# ── Company (tenant) management ───────────────────────────────────────────────

def register_company(
    company_id: str,
    company_name: str,
    plan: str = "starter",
    api_key: Optional[str] = None,
) -> Optional[int]:
    """Create a new tenant company. Returns inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        tbl = _meta.tables["companies"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at   = datetime.utcnow().isoformat(),
                company_id   = company_id.lower().replace(" ", "-"),
                company_name = company_name,
                api_key      = api_key,
                plan         = plan,
                is_active    = "True",
            ))
            row_id = res.lastrowid
        logger.info("Company registered: %s (id=%s)", company_id, row_id)
        return row_id
    except Exception as exc:
        logger.error("register_company failed: %s", exc)
        return None


def get_company(company_id: str) -> Optional[Dict]:
    """Return company record or None."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        tbl = _meta.tables["companies"]
        with engine.connect() as conn:
            row = conn.execute(
                tbl.select().where(tbl.c.company_id == company_id)
            ).fetchone()
        return _row_to_dict(row, tbl) if row else None
    except Exception as exc:
        logger.error("get_company failed: %s", exc)
        return None


def list_companies() -> List[Dict]:
    """Return all registered tenant companies."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["companies"]
        with engine.connect() as conn:
            rows = conn.execute(tbl.select().order_by(tbl.c.id.desc())).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("list_companies failed: %s", exc)
        return []


# ── Write helpers ──────────────────────────────────────────────────────────────

def save_candidate_score(
    profile_text: str,
    result: dict,
    candidate_name: Optional[str] = None,
    company_id: str = DEFAULT_COMPANY,
) -> Optional[int]:
    """Persist an Agent 1 adaptability result. Returns inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        name = candidate_name or _extract_name_from_profile(profile_text)
        tbl  = _meta.tables["candidates"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at          = datetime.utcnow().isoformat(),
                company_id          = company_id or DEFAULT_COMPANY,
                candidate_name      = name,
                adaptability_score  = result.get("adaptability_score", 0),
                adaptability_tier   = result.get("tier", ""),
                recommend_interview = str(result.get("recommend_interview", False)),
                score_breakdown     = json.dumps(result.get("score_breakdown", {})),
                reasoning           = result.get("reasoning", ""),
                profile_snippet     = (profile_text or "")[:500],
            ))
            row_id = res.lastrowid
        logger.info("DB [candidates] company=%s id=%s name=%s score=%s",
                    company_id, row_id, name, result.get("adaptability_score"))
        return row_id
    except Exception as exc:
        logger.error("save_candidate_score failed: %s", exc)
        return None


def save_job_match(
    result: dict,
    company_id: str = DEFAULT_COMPANY,
) -> Optional[int]:
    """Persist an Agent 2 job-match result. Returns inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        bd  = result.get("score_breakdown", {})
        tbl = _meta.tables["job_matches"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at            = datetime.utcnow().isoformat(),
                company_id            = company_id or DEFAULT_COMPANY,
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
        logger.info("DB [job_matches] company=%s id=%s candidate=%s score=%s",
                    company_id, row_id, result.get("candidate_name"), result.get("total_match_score"))
        return row_id
    except Exception as exc:
        logger.error("save_job_match failed: %s", exc)
        return None


def save_outreach(
    result: dict,
    company_id: str = DEFAULT_COMPANY,
) -> Optional[int]:
    """Persist an Agent 3 outreach campaign. Returns inserted row id."""
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
                company_id        = company_id or DEFAULT_COMPANY,
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
        logger.info("DB [outreach_campaigns] company=%s id=%s candidate=%s tier=%s",
                    company_id, row_id, result.get("candidate_name"), result.get("outreach_tier"))
        return row_id
    except Exception as exc:
        logger.error("save_outreach failed: %s", exc)
        return None


# ── Read helpers ───────────────────────────────────────────────────────────────

def get_recent_candidates(
    limit: int = 20,
    company_id: Optional[str] = None,
) -> List[Dict]:
    """Return the N most recent Agent 1 records, optionally filtered by company."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["candidates"]
        q   = tbl.select().order_by(tbl.c.id.desc()).limit(limit)
        if company_id:
            q = q.where(tbl.c.company_id == company_id)
        with engine.connect() as conn:
            rows = conn.execute(q).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_recent_candidates failed: %s", exc)
        return []


def get_recent_matches(
    limit: int = 20,
    company_id: Optional[str] = None,
) -> List[Dict]:
    """Return the N most recent Agent 2 records, optionally filtered by company."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["job_matches"]
        q   = tbl.select().order_by(tbl.c.id.desc()).limit(limit)
        if company_id:
            q = q.where(tbl.c.company_id == company_id)
        with engine.connect() as conn:
            rows = conn.execute(q).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_recent_matches failed: %s", exc)
        return []


def get_recent_campaigns(
    limit: int = 20,
    company_id: Optional[str] = None,
) -> List[Dict]:
    """Return the N most recent Agent 3 records, optionally filtered by company."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["outreach_campaigns"]
        q   = tbl.select().order_by(tbl.c.id.desc()).limit(limit)
        if company_id:
            q = q.where(tbl.c.company_id == company_id)
        with engine.connect() as conn:
            rows = conn.execute(q).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_recent_campaigns failed: %s", exc)
        return []


def get_pipeline_summary(
    candidate_name: str,
    company_id: Optional[str] = None,
) -> Dict:
    """Cross-agent view for a candidate, optionally scoped to a company."""
    if not SQLALCHEMY_AVAILABLE:
        return {"error": "sqlalchemy not installed"}
    try:
        engine = _get_engine()
        if engine is None:
            return {}
        cands = _meta.tables["candidates"]
        jm    = _meta.tables["job_matches"]
        camps = _meta.tables["outreach_campaigns"]

        def _q(tbl):
            q = tbl.select().where(
                tbl.c.candidate_name.ilike(f"%{candidate_name}%")
            ).order_by(tbl.c.id.desc()).limit(5)
            if company_id:
                q = q.where(tbl.c.company_id == company_id)
            return q

        with engine.connect() as conn:
            c_rows    = conn.execute(_q(cands)).fetchall()
            jm_rows   = conn.execute(_q(jm)).fetchall()
            camp_rows = conn.execute(_q(camps)).fetchall()

        return {
            "candidate_name":     candidate_name,
            "company_id":         company_id,
            "profile_analyses":   [_row_to_dict(r, cands) for r in c_rows],
            "job_matches":        [_row_to_dict(r, jm)    for r in jm_rows],
            "outreach_campaigns": [_row_to_dict(r, camps) for r in camp_rows],
        }
    except Exception as exc:
        logger.error("get_pipeline_summary failed: %s", exc)
        return {"error": str(exc)}


def save_outcome(
    candidate_name: str,
    outcome: str,
    job_title: str = "",
    adaptability_score: Optional[int] = None,
    match_score: Optional[int] = None,
    time_to_hire_days: Optional[int] = None,
    notes: str = "",
    company_id: str = DEFAULT_COMPANY,
) -> Optional[int]:
    """Record a hiring outcome for a candidate. Returns inserted row id."""
    if not SQLALCHEMY_AVAILABLE:
        return None
    try:
        engine = _get_engine()
        if engine is None:
            return None
        tbl = _meta.tables["outcomes"]
        with engine.begin() as conn:
            res = conn.execute(tbl.insert().values(
                created_at         = datetime.utcnow().isoformat(),
                company_id         = company_id or DEFAULT_COMPANY,
                candidate_name     = candidate_name,
                job_title          = job_title,
                outcome            = outcome,
                adaptability_score = adaptability_score,
                match_score        = match_score,
                time_to_hire_days  = time_to_hire_days,
                notes              = notes,
            ))
            row_id = res.lastrowid
        logger.info("DB [outcomes] company=%s candidate=%s outcome=%s",
                    company_id, candidate_name, outcome)
        return row_id
    except Exception as exc:
        logger.error("save_outcome failed: %s", exc)
        return None


def get_outcomes(
    limit: int = 50,
    company_id: Optional[str] = None,
) -> List[Dict]:
    """Return hiring outcomes, optionally scoped to a company."""
    if not SQLALCHEMY_AVAILABLE:
        return []
    try:
        engine = _get_engine()
        if engine is None:
            return []
        tbl = _meta.tables["outcomes"]
        q   = tbl.select().order_by(tbl.c.id.desc()).limit(limit)
        if company_id:
            q = q.where(tbl.c.company_id == company_id)
        with engine.connect() as conn:
            rows = conn.execute(q).fetchall()
        return [_row_to_dict(r, tbl) for r in rows]
    except Exception as exc:
        logger.error("get_outcomes failed: %s", exc)
        return []


def get_company_stats(company_id: str) -> Dict:
    """Return pipeline statistics scoped to a single tenant."""
    if not SQLALCHEMY_AVAILABLE:
        return {"db_persistence": False}
    try:
        engine = _get_engine()
        if engine is None:
            return {}
        with engine.connect() as conn:
            n_c  = conn.execute(text(
                f"SELECT COUNT(*) FROM candidates WHERE company_id=:cid"
            ), {"cid": company_id}).scalar()
            n_jm = conn.execute(text(
                f"SELECT COUNT(*) FROM job_matches WHERE company_id=:cid"
            ), {"cid": company_id}).scalar()
            n_oc = conn.execute(text(
                f"SELECT COUNT(*) FROM outreach_campaigns WHERE company_id=:cid"
            ), {"cid": company_id}).scalar()
        return {
            "company_id":          company_id,
            "candidates":          n_c,
            "job_matches":         n_jm,
            "outreach_campaigns":  n_oc,
            "total_pipeline_runs": min(n_c, n_jm, n_oc),
        }
    except Exception as exc:
        return {"error": str(exc)}


def get_db_stats() -> Dict:
    """Global row counts across all tenants — used by /health endpoints."""
    if not SQLALCHEMY_AVAILABLE:
        return {"sqlalchemy": "not_installed", "db_persistence": False}
    try:
        engine = _get_engine()
        if engine is None:
            return {"db_persistence": False}
        with engine.connect() as conn:
            n_companies = conn.execute(text("SELECT COUNT(*) FROM companies")).scalar()
            n_c  = conn.execute(text("SELECT COUNT(*) FROM candidates")).scalar()
            n_jm = conn.execute(text("SELECT COUNT(*) FROM job_matches")).scalar()
            n_oc = conn.execute(text("SELECT COUNT(*) FROM outreach_campaigns")).scalar()
            n_out= conn.execute(text("SELECT COUNT(*) FROM outcomes")).scalar()
        return {
            "db_path":             DB_PATH,
            "db_persistence":      True,
            "multi_tenant":        True,
            "companies":           n_companies,
            "candidates":          n_c,
            "job_matches":         n_jm,
            "outreach_campaigns":  n_oc,
            "outcomes":            n_out,
            "total_pipeline_runs": min(n_c, n_jm, n_oc),
        }
    except Exception as exc:
        return {"error": str(exc), "db_persistence": False}
