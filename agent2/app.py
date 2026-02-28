"""
Agent 2 — Job Matcher  |  FastAPI Web Application
VelocityHire Hackathon Prototype
"""

from agent_2 import match_candidate
import logging
import os
import sys
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

LOG_DIR = Path("/mnt/efs/spaces/6f40e0fa-8a03-41a6-a37c-c728be34b83b/f99b24e1-53b1-4954-a709-a448e806bd7b/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    handlers=[logging.FileHandler(LOG_DIR / "agent2.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("agent2")

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))   # shared/ package

# ── Phase 4: shared memory ────────────────────────────────────────────────────
try:
    from shared.db_memory import save_job_match, get_recent_matches, get_db_stats, get_company_stats
    DB_ENABLED = True
except ImportError:
    DB_ENABLED = False
    def save_job_match(*a, **kw): return None            # noqa: E704
    def get_recent_matches(*a, **kw): return []          # noqa: E704
    def get_db_stats(*a, **kw): return {"db_persistence": False}  # noqa: E704
    def get_company_stats(*a, **kw): return {}           # noqa: E704

app = FastAPI(title="Agent 2 — Job Matcher", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AGENT1_URL = os.getenv("AGENT1_URL", "https://p8j7jjz1.run.complete.dev")


class MatchRequest(BaseModel):
    job_title: str
    job_description: str
    required_skills: List[str]
    candidate_name: str
    candidate_profile: str
    adaptability_score: Optional[int] = None     # If None → call Agent 1 first
    adaptability_tier: Optional[str] = "Unknown"


class Agent1Request(BaseModel):
    profile_text: str


# ── HTML ─────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VelocityHire · Agent 2 — Job Matcher</title>
<style>
  :root {
    --bg:#0f1117;--surface:#1a1d27;--surface2:#242736;
    --accent:#6c63ff;--accent2:#f5a623;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;
    --text:#e2e8f0;--muted:#94a3b8;--border:#2d3147;--radius:12px;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;}
  header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;align-items:center;gap:12px;}
  .logo{font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .badge{background:var(--surface2);border:1px solid var(--border);color:var(--muted);font-size:.75rem;padding:2px 10px;border-radius:20px;}
  .container{max-width:1200px;margin:0 auto;padding:28px 20px;}
  .tagline{text-align:center;margin-bottom:28px;}
  .tagline h1{font-size:1.8rem;font-weight:700;margin-bottom:6px;}
  .tagline p{color:var(--muted);}
  .pipeline{display:flex;gap:8px;align-items:center;justify-content:center;margin-bottom:28px;flex-wrap:wrap;}
  .pipe-step{font-size:.72rem;padding:4px 12px;border-radius:20px;background:var(--surface2);border:1px solid var(--border);color:var(--muted);}
  .pipe-step.done{border-color:var(--green);color:var(--green);}
  .pipe-step.active{border-color:var(--accent);color:var(--accent);}
  .pipe-arrow{color:var(--muted);font-size:.8rem;}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
  @media(max-width:800px){.grid{grid-template-columns:1fr;}}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:22px;}
  .card h2{font-size:.85rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px;}
  label{display:block;font-size:.78rem;color:var(--muted);margin-bottom:4px;margin-top:12px;}
  input,textarea,select{width:100%;background:var(--surface2);border:1px solid var(--border);border-radius:7px;color:var(--text);font-size:.875rem;padding:10px 12px;outline:none;transition:border-color .2s;}
  input:focus,textarea:focus{border-color:var(--accent);}
  textarea{min-height:120px;resize:vertical;line-height:1.55;}
  .skills-input{display:flex;gap:8px;margin-top:4px;}
  .skills-input input{flex:1;}
  .add-btn{padding:10px 14px;background:var(--surface2);border:1px solid var(--accent);border-radius:7px;color:var(--accent);font-size:.8rem;font-weight:600;cursor:pointer;white-space:nowrap;}
  .add-btn:hover{background:rgba(108,99,255,.15);}
  .skill-tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;min-height:28px;}
  .skill-tag{background:rgba(108,99,255,.15);border:1px solid var(--accent);color:var(--accent);font-size:.72rem;padding:3px 10px;border-radius:20px;display:flex;align-items:center;gap:5px;}
  .skill-tag button{background:none;border:none;color:var(--accent);cursor:pointer;font-size:.85rem;line-height:1;padding:0;}
  .adaptability-row{display:flex;gap:10px;align-items:flex-end;}
  .adaptability-row .score-input{width:80px;text-align:center;font-size:1.2rem;font-weight:700;}
  .auto-btn{flex:1;padding:10px;background:var(--surface2);border:1px solid var(--border);border-radius:7px;color:var(--muted);font-size:.78rem;cursor:pointer;transition:all .2s;}
  .auto-btn:hover{border-color:var(--accent);color:var(--accent);}
  .auto-btn.fetched{border-color:var(--green);color:var(--green);}
  .btn{display:block;width:100%;margin-top:16px;padding:14px;background:linear-gradient(135deg,var(--accent),#8b5cf6);color:#fff;font-size:1rem;font-weight:700;border:none;border-radius:8px;cursor:pointer;transition:opacity .2s;}
  .btn:hover{opacity:.9;}
  .btn:disabled{opacity:.5;cursor:not-allowed;}

  /* Result panel */
  .placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:12px;color:var(--muted);text-align:center;min-height:340px;}
  .placeholder .icon{font-size:3rem;}
  .spinner{display:none;width:40px;height:40px;border:4px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:60px auto;}
  @keyframes spin{to{transform:rotate(360deg)}}

  .score-hero{text-align:center;margin-bottom:20px;}
  .score-big{font-size:4rem;font-weight:900;line-height:1;}
  .score-label{font-size:.85rem;color:var(--muted);margin-top:2px;}
  .tier-pill{display:inline-block;padding:6px 20px;border-radius:20px;font-weight:700;font-size:.9rem;margin-top:8px;}

  .dim-bars{display:flex;flex-direction:column;gap:10px;margin-bottom:16px;}
  .dim-row{display:flex;align-items:center;gap:10px;}
  .dim-label{width:120px;font-size:.78rem;color:var(--muted);flex-shrink:0;}
  .dim-bar{flex:1;height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;}
  .dim-fill{height:100%;border-radius:4px;transition:width .6s ease;}
  .dim-score{width:55px;text-align:right;font-size:.78rem;font-weight:600;}

  .skills-grid{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0 14px;}
  .skill-match{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:var(--green);font-size:.7rem;padding:2px 8px;border-radius:12px;}
  .skill-miss{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:var(--red);font-size:.7rem;padding:2px 8px;border-radius:12px;}

  .reasoning-box{background:var(--surface2);border-radius:8px;padding:14px;font-size:.82rem;line-height:1.7;white-space:pre-wrap;max-height:200px;overflow-y:auto;}
  .verdict{display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:8px;font-weight:600;margin-top:12px;}
  .verdict.pass{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:var(--green);}
  .verdict.hold{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:var(--red);}

  .agent3-btn{display:block;width:100%;margin-top:10px;padding:12px;background:rgba(245,166,35,.1);border:1px solid var(--accent2);border-radius:8px;color:var(--accent2);font-size:.85rem;font-weight:700;cursor:pointer;text-align:center;text-decoration:none;}
  .agent3-btn:hover{background:rgba(245,166,35,.2);}

  .json-toggle{font-size:.72rem;color:var(--accent);cursor:pointer;text-decoration:underline;margin-top:10px;display:inline-block;}
  pre.json-out{display:none;margin-top:6px;background:#0a0c12;border-radius:8px;padding:12px;font-size:.72rem;overflow-x:auto;color:#a3e635;max-height:200px;overflow-y:auto;}
</style>
</head>
<body>
<header>
  <div class="logo">⚡ VelocityHire</div>
  <span class="badge">Agent 2 — Job Matcher</span>
  <span class="badge" style="margin-left:auto;">Hackathon Prototype · Feb 2026</span>
</header>

<div class="container">
  <div class="tagline">
    <h1>Adaptability-Weighted Job Matching</h1>
    <p>Enter a job + candidate — Agent 2 scores the match at 60% adaptability, 25% role fit, 15% culture fit</p>
  </div>

  <div class="pipeline">
    <div class="pipe-step done">① Profile Analyzer ✓</div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step active">② Job Matcher ◀</div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">③ Outreach Coordinator</div>
  </div>

  <div class="grid">
    <!-- INPUT -->
    <div>
      <!-- Job Card -->
      <div class="card" style="margin-bottom:16px;">
        <h2>Job Requirements</h2>
        <label>Job Title</label>
        <input id="jobTitle" type="text" placeholder="e.g. Senior AI Engineer" value="Senior AI Engineer"/>
        <label>Job Description</label>
        <textarea id="jobDesc" placeholder="Paste the job description here…">We are looking for a Senior AI Engineer to build production-grade LLM applications. You will design multi-agent systems, integrate vector databases, and ship rapid prototypes. Ideal candidate thrives in a fast-paced startup environment and can learn new frameworks quickly.</textarea>
        <label>Required Skills</label>
        <div class="skills-input">
          <input id="skillInput" type="text" placeholder="Add a required skill…" onkeydown="if(event.key==='Enter'){addSkill();}"/>
          <button class="add-btn" onclick="addSkill()">+ Add</button>
        </div>
        <div class="skill-tags" id="skillTags"></div>
      </div>

      <!-- Candidate Card -->
      <div class="card">
        <h2>Candidate</h2>
        <label>Candidate Name</label>
        <input id="candidateName" type="text" placeholder="e.g. Marcus Rivera" value="Marcus Rivera"/>
        <label>Profile Text</label>
        <textarea id="candidateProfile" placeholder="Paste candidate profile text…">Marcus Rivera — Senior Software Engineer. Skills: React, Node.js, TypeScript, Next.js, Python, FastAPI, LangChain. Experience: TechStartup (2021-present) built AI analytics dashboard. Hackathons: React Summit winner 1 month ago, Junction Helsinki finalist 4 months ago. AWS certified 2 months ago. 45 commits last month exploring LLMs and vector databases. Worked cross-functionally with product and design teams. Rapid prototype experience shipping MVPs.</textarea>
        <label>Adaptability Score (from Agent 1)</label>
        <div class="adaptability-row">
          <input id="adaptScore" class="score-input" type="number" min="0" max="100" value="87" placeholder="0-100"/>
          <button class="auto-btn" id="autoBtn" onclick="runAgent1()">⚡ Auto-score via Agent 1</button>
        </div>
        <div id="agent1Status" style="font-size:.72rem;color:var(--muted);margin-top:6px;"></div>

        <button class="btn" id="matchBtn" onclick="runMatch()">🎯 Calculate Job Match</button>
      </div>
    </div>

    <!-- OUTPUT -->
    <div class="card" id="resultCard">
      <h2>Match Report</h2>
      <div id="placeholder" class="placeholder">
        <div class="icon">🎯</div>
        <p>Add job details and candidate profile<br>then click <strong>Calculate Job Match</strong></p>
      </div>
      <div id="spinner" class="spinner"></div>
      <div id="result" style="display:none;">

        <div class="score-hero">
          <div class="score-big" id="scoreBig">—</div>
          <div class="score-label">/100 match score</div>
          <div class="tier-pill" id="tierPill">—</div>
        </div>

        <div class="dim-bars" id="dimBars"></div>

        <div style="font-size:.78rem;color:var(--muted);margin-bottom:4px;">Skills Coverage</div>
        <div class="skills-grid" id="skillsGrid"></div>

        <div class="reasoning-box" id="reasoningBox"></div>
        <div class="verdict" id="verdict"></div>

        <a id="agent3Link" class="agent3-btn" href="#" style="display:none;">
          ✉️ Send to Agent 3 — Outreach Coordinator →
        </a>

        <span class="json-toggle" onclick="toggleJson()">Show raw JSON ↓</span>
        <pre class="json-out" id="jsonOut"></pre>
      </div>
    </div>
  </div>
</div>

<script>
// ── Default required skills ───────────────────────────────────────────────
const defaultSkills = ["Python","LangChain","LLM","FastAPI","Vector DB","TypeScript"];
let skills = [...defaultSkills];

function renderSkills() {
  document.getElementById('skillTags').innerHTML = skills.map(s =>
    `<span class="skill-tag">${s}<button onclick="removeSkill('${s}')">×</button></span>`
  ).join('');
}
function addSkill() {
  const v = document.getElementById('skillInput').value.trim();
  if (v && !skills.includes(v)) { skills.push(v); renderSkills(); }
  document.getElementById('skillInput').value = '';
}
function removeSkill(s) { skills = skills.filter(x => x !== s); renderSkills(); }
renderSkills();

// ── Auto-score via Agent 1 ────────────────────────────────────────────────
async function runAgent1() {
  const profile = document.getElementById('candidateProfile').value.trim();
  if (!profile) { alert('Please paste a candidate profile first.'); return; }
  const btn = document.getElementById('autoBtn');
  const status = document.getElementById('agent1Status');
  btn.disabled = true;
  btn.textContent = '⏳ Scoring…';
  status.textContent = 'Calling Agent 1 — Profile Analyzer…';
  try {
    const resp = await fetch('/agent1-score', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({profile_text: profile})
    });
    const data = await resp.json();
    document.getElementById('adaptScore').value = data.adaptability_score;
    btn.className = 'auto-btn fetched';
    btn.textContent = '✅ Score fetched from Agent 1';
    status.textContent = `Agent 1 result: ${data.adaptability_score}/100 — ${data.tier}`;
  } catch(e) {
    status.textContent = 'Agent 1 unavailable — enter score manually.';
    btn.textContent = '⚡ Auto-score via Agent 1';
  } finally {
    btn.disabled = false;
  }
}

// ── Run match ─────────────────────────────────────────────────────────────
async function runMatch() {
  const jobTitle    = document.getElementById('jobTitle').value.trim();
  const jobDesc     = document.getElementById('jobDesc').value.trim();
  const candName    = document.getElementById('candidateName').value.trim();
  const candProfile = document.getElementById('candidateProfile').value.trim();
  const adaptScore  = parseInt(document.getElementById('adaptScore').value) || 0;
  if (!jobTitle || !jobDesc || !candName || !candProfile) {
    alert('Please fill in all fields.'); return;
  }
  document.getElementById('placeholder').style.display = 'none';
  document.getElementById('result').style.display = 'none';
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('matchBtn').disabled = true;
  try {
    const resp = await fetch('/match', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        job_title: jobTitle,
        job_description: jobDesc,
        required_skills: skills,
        candidate_name: candName,
        candidate_profile: candProfile,
        adaptability_score: adaptScore,
        adaptability_tier: 'From Agent 1',
      })
    });
    if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail); }
    renderResult(await resp.json());
  } catch(e) {
    document.getElementById('spinner').style.display = 'none';
    document.getElementById('placeholder').style.display = 'flex';
    document.getElementById('placeholder').innerHTML = '<div class="icon">⚠️</div><p>' + e.message + '</p>';
  } finally {
    document.getElementById('matchBtn').disabled = false;
  }
}

function renderResult(d) {
  document.getElementById('spinner').style.display = 'none';
  document.getElementById('result').style.display = 'block';

  const score = d.total_match_score || 0;
  const color = score >= 70 ? 'var(--green)' : score >= 55 ? 'var(--amber)' : 'var(--red)';

  document.getElementById('scoreBig').textContent = score;
  document.getElementById('scoreBig').style.color = color;

  const pill = document.getElementById('tierPill');
  pill.textContent = d.match_tier || '—';
  pill.style.background = score >= 70 ? 'rgba(34,197,94,.15)' : 'rgba(245,158,11,.15)';
  pill.style.color = color;

  // Dimension bars
  const bd = d.score_breakdown || {};
  const dims = [
    {key:'adaptability', label:'Adaptability', color:'#6c63ff', max:60, score: bd.adaptability?.weighted_score || 0},
    {key:'role_fit',     label:'Role Fit',     color:'#f5a623', max:25, score: bd.role_fit?.score || 0},
    {key:'culture_fit',  label:'Culture Fit',  color:'#22c55e', max:15, score: bd.culture_fit?.score || 0},
  ];
  document.getElementById('dimBars').innerHTML = dims.map(d => {
    const pct = Math.round((d.score / d.max) * 100);
    return `<div class="dim-row">
      <span class="dim-label">${d.label}</span>
      <div class="dim-bar"><div class="dim-fill" style="width:${pct}%;background:${d.color};"></div></div>
      <span class="dim-score" style="color:${d.color}">${d.score.toFixed ? d.score.toFixed(1) : d.score}/${d.max}</span>
    </div>`;
  }).join('');

  // Skills grid
  const matched = bd.role_fit?.matched_skills || [];
  const allSkills = skills;
  document.getElementById('skillsGrid').innerHTML = allSkills.map(s =>
    matched.some(m => m.toLowerCase() === s.toLowerCase())
      ? `<span class="skill-match">✓ ${s}</span>`
      : `<span class="skill-miss">✗ ${s}</span>`
  ).join('');

  document.getElementById('reasoningBox').textContent = d.reasoning || '';

  const v = document.getElementById('verdict');
  if (d.recommend_interview) {
    v.className = 'verdict pass';
    v.innerHTML = '✅ &nbsp;Recommend for Interview — passes 70+ threshold';
    const lnk = document.getElementById('agent3Link');
    lnk.style.display = 'block';
    lnk.href = '#';  // Will link to Agent 3 when built
  } else {
    v.className = 'verdict hold';
    v.innerHTML = '📋 &nbsp;Hold — below threshold; flag for future roles';
    document.getElementById('agent3Link').style.display = 'none';
  }

  document.getElementById('jsonOut').textContent = JSON.stringify(d, null, 2);
}

function toggleJson() {
  const el = document.getElementById('jsonOut');
  const tog = document.querySelector('.json-toggle');
  el.style.display = el.style.display === 'block' ? 'none' : 'block';
  tog.textContent = el.style.display === 'block' ? 'Hide raw JSON ↑' : 'Show raw JSON ↓';
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.get("/health")
async def health():
    db = {}
    try:
        db = get_db_stats()
    except Exception:
        pass
    return {"status": "ok", "agent": "Job Matcher", "version": "1.0.0", "db": db}


@app.post("/agent1-score")
async def proxy_agent1(req: Agent1Request):
    """Proxy to Agent 1 — Profile Analyzer to auto-fetch adaptability score."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{AGENT1_URL}/analyze",
                json={"profile_text": req.profile_text},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"adaptability_score": data.get("adaptability_score", 0),
                    "tier": data.get("tier", "Unknown"),
                    "recommend_interview": data.get("recommend_interview", False)}
    except Exception as e:
        logger.warning("Agent 1 proxy failed: %s", str(e))
        raise HTTPException(status_code=503, detail=f"Agent 1 unavailable: {str(e)}")


@app.post("/match")
async def match(
    req: MatchRequest,
    x_company_id: Optional[str] = Header(default="demo"),
):
    company_id = (x_company_id or "demo").strip()
    if not req.job_title.strip() or not req.candidate_profile.strip():
        raise HTTPException(status_code=400, detail="job_title and candidate_profile are required")
    logger.info("Match request: %s → %s", req.candidate_name, req.job_title)

    # If no adaptability score provided, attempt to get it from Agent 1
    adapt_score = req.adaptability_score
    adapt_tier = req.adaptability_tier or "Unknown"
    if adapt_score is None:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(f"{AGENT1_URL}/analyze",
                                      json={"profile_text": req.candidate_profile})
                if r.status_code == 200:
                    a1 = r.json()
                    adapt_score = a1.get("adaptability_score", 50)
                    adapt_tier = a1.get("tier", "Unknown")
        except Exception:
            adapt_score = 50  # neutral fallback

    result = match_candidate(
        job_title=req.job_title,
        job_description=req.job_description,
        required_skills=req.required_skills,
        candidate_name=req.candidate_name,
        candidate_profile=req.candidate_profile,
        adaptability_score=adapt_score,
        adaptability_tier=adapt_tier,
    )
    logger.info("Match complete: score=%s tier=%s", result.get("total_match_score"), result.get("match_tier"))
    # Phase 4 — persist to shared memory (tenant-scoped, non-blocking)
    try:
        save_job_match(result, company_id=company_id)
    except Exception as db_err:
        logger.warning("DB persist (non-critical): %s", str(db_err))
    return JSONResponse(content=result)


@app.get("/history")
async def history(
    limit: int = 20,
    x_company_id: Optional[str] = Header(default=None),
):
    """Phase 4 — Return recent job-match results, scoped to tenant if header provided."""
    try:
        records = get_recent_matches(limit, company_id=x_company_id or None)
        return JSONResponse(content={"count": len(records), "company_id": x_company_id, "records": records})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
