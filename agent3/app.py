"""
Agent 3 — Outreach Coordinator  |  FastAPI Web Application
VelocityHire Hackathon Prototype
"""

import json, logging, os, sys
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
    handlers=[logging.FileHandler(LOG_DIR / "agent3.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("agent3")

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))   # shared/ package
from agent_3 import generate_outreach

# ── Phase 4: shared memory ────────────────────────────────────────────────────
try:
    from shared.db_memory import (
        save_outreach, get_recent_campaigns, get_pipeline_summary,
        get_recent_candidates, get_recent_matches, get_db_stats,
        get_company_stats, list_companies,
    )
    DB_ENABLED = True
except ImportError:
    DB_ENABLED = False
    def save_outreach(*a, **kw): return None                       # noqa: E704
    def get_recent_campaigns(*a, **kw): return []                  # noqa: E704
    def get_pipeline_summary(*a, **kw): return {}                  # noqa: E704
    def get_recent_candidates(*a, **kw): return []                 # noqa: E704
    def get_recent_matches(*a, **kw): return []                    # noqa: E704
    def get_db_stats(*a, **kw): return {"db_persistence": False}   # noqa: E704
    def get_company_stats(*a, **kw): return {}                     # noqa: E704
    def list_companies(*a, **kw): return []                        # noqa: E704

app = FastAPI(title="Agent 3 — Outreach Coordinator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AGENT1_URL = os.getenv("AGENT1_URL", "https://p8j7jjz1.run.complete.dev")
AGENT2_URL = os.getenv("AGENT2_URL", "https://xztqf3sj.run.complete.dev")


class OutreachRequest(BaseModel):
    candidate_name: str
    candidate_profile: str
    job_title: str
    company_name: Optional[str] = "VelocityHire Client"
    recruiter_name: Optional[str] = "The Recruiting Team"
    total_match_score: Optional[int] = None
    match_tier: Optional[str] = "Unknown"
    adaptability_score: Optional[int] = None
    adaptability_tier: Optional[str] = "Unknown"
    matched_skills: Optional[List[str]] = []
    startup_experience: Optional[bool] = False
    recommend_interview: Optional[bool] = True
    reasoning: Optional[str] = ""
    required_skills: Optional[List[str]] = []
    job_description: Optional[str] = ""


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VelocityHire · Agent 3 — Outreach Coordinator</title>
<style>
  :root{--bg:#0f1117;--surface:#1a1d27;--surface2:#242736;--accent:#6c63ff;--accent2:#f5a623;--green:#22c55e;--red:#ef4444;--amber:#f59e0b;--text:#e2e8f0;--muted:#94a3b8;--border:#2d3147;--radius:12px;}
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;}
  header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;align-items:center;gap:12px;}
  .logo{font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .badge{background:var(--surface2);border:1px solid var(--border);color:var(--muted);font-size:.75rem;padding:2px 10px;border-radius:20px;}
  .container{max-width:1300px;margin:0 auto;padding:28px 20px;}
  .tagline{text-align:center;margin-bottom:24px;}
  .tagline h1{font-size:1.8rem;font-weight:700;margin-bottom:6px;}
  .tagline p{color:var(--muted);}
  .pipeline{display:flex;gap:8px;align-items:center;justify-content:center;margin-bottom:28px;flex-wrap:wrap;}
  .pipe-step{font-size:.72rem;padding:4px 12px;border-radius:20px;background:var(--surface2);border:1px solid var(--border);color:var(--muted);}
  .pipe-step.done{border-color:var(--green);color:var(--green);}
  .pipe-step.active{border-color:var(--accent);color:var(--accent);}
  .pipe-arrow{color:var(--muted);font-size:.8rem;}
  .layout{display:grid;grid-template-columns:360px 1fr;gap:20px;}
  @media(max-width:900px){.layout{grid-template-columns:1fr;}}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px;}
  .card h2{font-size:.82rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px;}
  label{display:block;font-size:.76rem;color:var(--muted);margin-bottom:3px;margin-top:10px;}
  input,textarea{width:100%;background:var(--surface2);border:1px solid var(--border);border-radius:7px;color:var(--text);font-size:.85rem;padding:9px 12px;outline:none;transition:border-color .2s;}
  input:focus,textarea:focus{border-color:var(--accent);}
  textarea{min-height:100px;resize:vertical;line-height:1.5;}
  .btn{display:block;width:100%;margin-top:14px;padding:13px;background:linear-gradient(135deg,var(--accent),#8b5cf6);color:#fff;font-size:.95rem;font-weight:700;border:none;border-radius:8px;cursor:pointer;transition:opacity .2s;}
  .btn:hover{opacity:.9;}
  .btn:disabled{opacity:.5;cursor:not-allowed;}
  .auto-btn{width:100%;margin-top:8px;padding:9px;background:var(--surface2);border:1px solid var(--border);border-radius:7px;color:var(--muted);font-size:.76rem;cursor:pointer;transition:all .2s;}
  .auto-btn:hover{border-color:var(--accent);color:var(--accent);}
  .auto-btn.done{border-color:var(--green);color:var(--green);}
  .score-row{display:flex;gap:10px;margin-top:8px;}
  .score-box{flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:10px;text-align:center;}
  .score-box .num{font-size:1.6rem;font-weight:800;}
  .score-box .lbl{font-size:.7rem;color:var(--muted);}

  /* Right panel */
  .placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:12px;color:var(--muted);text-align:center;min-height:400px;}
  .placeholder .icon{font-size:3rem;}
  .spinner{display:none;width:40px;height:40px;border:4px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:80px auto;}
  @keyframes spin{to{transform:rotate(360deg)}}

  /* Tier badge */
  .tier-header{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding:14px 18px;border-radius:10px;}
  .tier-header.PRIORITY{background:rgba(108,99,255,.15);border:1px solid rgba(108,99,255,.4);}
  .tier-header.STANDARD{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);}
  .tier-header.NURTURE{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);}
  .tier-header.ARCHIVE{background:rgba(148,163,184,.1);border:1px solid rgba(148,163,184,.3);}
  .tier-icon{font-size:2rem;}
  .tier-title{font-size:1.1rem;font-weight:700;}
  .tier-sub{font-size:.8rem;color:var(--muted);}

  /* Tabs */
  .msg-tabs{display:flex;gap:0;margin-bottom:14px;border-radius:8px;overflow:hidden;border:1px solid var(--border);}
  .msg-tab{flex:1;padding:9px;background:var(--surface2);border:none;color:var(--muted);font-size:.78rem;font-weight:600;cursor:pointer;transition:all .2s;}
  .msg-tab.active{background:var(--accent);color:#fff;}
  .msg-panel{display:none;}
  .msg-panel.active{display:block;}

  .msg-box{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px;font-size:.82rem;line-height:1.7;white-space:pre-wrap;position:relative;min-height:120px;}
  .copy-btn{position:absolute;top:8px;right:8px;padding:4px 10px;background:var(--surface);border:1px solid var(--border);border-radius:6px;color:var(--muted);font-size:.7rem;cursor:pointer;}
  .copy-btn:hover{border-color:var(--accent);color:var(--accent);}
  .char-count{font-size:.68rem;color:var(--muted);margin-top:4px;}
  .subj-box{background:rgba(108,99,255,.1);border:1px solid rgba(108,99,255,.3);border-radius:6px;padding:8px 12px;font-size:.8rem;font-weight:600;color:var(--accent);margin-bottom:8px;}

  .highlights{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
  .hl-tag{background:rgba(245,166,35,.1);border:1px solid rgba(245,166,35,.3);color:var(--accent2);font-size:.7rem;padding:3px 10px;border-radius:20px;}

  .json-toggle{font-size:.7rem;color:var(--accent);cursor:pointer;text-decoration:underline;margin-top:10px;display:inline-block;}
  pre.json-out{display:none;margin-top:6px;background:#0a0c12;border-radius:8px;padding:12px;font-size:.7rem;overflow-x:auto;color:#a3e635;max-height:200px;overflow-y:auto;}
</style>
</head>
<body>
<header>
  <div class="logo">⚡ VelocityHire</div>
  <span class="badge">Agent 3 — Outreach Coordinator</span>
  <span class="badge" style="margin-left:auto;">Hackathon Prototype · Feb 2026</span>
</header>

<div class="container">
  <div class="tagline">
    <h1>Personalised Outreach Campaigns</h1>
    <p>Agent 3 generates LinkedIn messages, emails, follow-ups & recruiter notes — personalised around learning velocity</p>
  </div>

  <div class="pipeline">
    <div class="pipe-step done">① Profile Analyzer ✓</div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step done">② Job Matcher ✓</div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step active">③ Outreach Coordinator ◀</div>
  </div>

  <div class="layout">
    <!-- INPUT -->
    <div>
      <div class="card">
        <h2>Candidate & Role</h2>
        <label>Candidate Name</label>
        <input id="candName" value="Marcus Rivera" placeholder="Full name"/>
        <label>Job Title</label>
        <input id="jobTitle" value="Senior AI Engineer" placeholder="Role being hired for"/>
        <label>Company Name</label>
        <input id="companyName" value="TechVentures" placeholder="Your company"/>
        <label>Recruiter Name</label>
        <input id="recruiterName" value="Alex" placeholder="Your first name"/>
        <label>Candidate Profile</label>
        <textarea id="candProfile" rows="5">Marcus Rivera — Senior Software Engineer. Skills: React, Python, LangChain, FastAPI. Hackathon winner last month (AI Summit). AWS certified 2 months ago. Startup experience. Led cross-functional team. Shipped MVP in 48 hours. Active on GitHub with LLM projects.</textarea>

        <button class="auto-btn" id="autoBtn" onclick="runPipeline()">
          ⚡ Auto-run Agents 1 + 2 to fetch scores
        </button>
        <div id="pipelineStatus" style="font-size:.72rem;color:var(--muted);margin-top:6px;min-height:16px;"></div>

        <div class="score-row">
          <div class="score-box">
            <div class="num" id="adaptNum" style="color:var(--accent);">—</div>
            <div class="lbl">Adaptability<br>(Agent 1)</div>
          </div>
          <div class="score-box">
            <div class="num" id="matchNum" style="color:var(--green);">—</div>
            <div class="lbl">Job Match<br>(Agent 2)</div>
          </div>
        </div>

        <button class="btn" id="outreachBtn" onclick="generate()">✉️ Generate Outreach Campaign</button>
      </div>
    </div>

    <!-- OUTPUT -->
    <div class="card" id="resultCard">
      <h2>Outreach Campaign</h2>
      <div id="placeholder" class="placeholder">
        <div class="icon">✉️</div>
        <p>Fill in the candidate details and click<br><strong>Generate Outreach Campaign</strong></p>
      </div>
      <div id="spinner" class="spinner"></div>
      <div id="result" style="display:none;">

        <div class="tier-header" id="tierHeader">
          <div class="tier-icon" id="tierIcon">🏆</div>
          <div>
            <div class="tier-title" id="tierTitle">—</div>
            <div class="tier-sub" id="tierSub">—</div>
          </div>
        </div>

        <div style="margin-bottom:14px;">
          <div style="font-size:.76rem;color:var(--muted);margin-bottom:6px;">Key Personalisation Signals</div>
          <div class="highlights" id="highlights"></div>
        </div>

        <!-- Message tabs -->
        <div class="msg-tabs">
          <button class="msg-tab active" onclick="showTab('linkedin')">LinkedIn</button>
          <button class="msg-tab" onclick="showTab('email')">Email</button>
          <button class="msg-tab" onclick="showTab('followup')">Follow-up</button>
          <button class="msg-tab" onclick="showTab('recruiter')">ATS Note</button>
        </div>

        <!-- LinkedIn -->
        <div class="msg-panel active" id="tab-linkedin">
          <div class="msg-box" id="linkedinMsg">
            <button class="copy-btn" onclick="copyMsg('linkedinMsg')">Copy</button>
          </div>
          <div class="char-count" id="linkedinChars"></div>
        </div>

        <!-- Email -->
        <div class="msg-panel" id="tab-email">
          <div class="subj-box" id="emailSubj"></div>
          <div class="msg-box" id="emailBody">
            <button class="copy-btn" onclick="copyMsg('emailBody')">Copy</button>
          </div>
        </div>

        <!-- Follow-up -->
        <div class="msg-panel" id="tab-followup">
          <div style="font-size:.72rem;color:var(--amber);margin-bottom:8px;">⏰ Send automatically after 5 days if no reply</div>
          <div class="subj-box" id="followupSubj"></div>
          <div class="msg-box" id="followupBody">
            <button class="copy-btn" onclick="copyMsg('followupBody')">Copy</button>
          </div>
        </div>

        <!-- Recruiter note -->
        <div class="msg-panel" id="tab-recruiter">
          <div style="font-size:.72rem;color:var(--muted);margin-bottom:8px;">📋 Internal ATS note — not sent to candidate</div>
          <div class="msg-box" id="recruiterNote">
            <button class="copy-btn" onclick="copyMsg('recruiterNote')">Copy</button>
          </div>
        </div>

        <span class="json-toggle" onclick="toggleJson()">Show raw JSON ↓</span>
        <pre class="json-out" id="jsonOut"></pre>
      </div>
    </div>
  </div>
</div>

<script>
let _cachedScores = {adapt: null, match: null, tier: null, adaptTier: null,
                    matched_skills: [], startup: false, reasoning: '', matchTier: ''};

// ── Auto-run pipeline ─────────────────────────────────────────────────────
async function runPipeline() {
  const profile = document.getElementById('candProfile').value.trim();
  if (!profile) { alert('Please enter a candidate profile.'); return; }
  const btn    = document.getElementById('autoBtn');
  const status = document.getElementById('pipelineStatus');
  btn.disabled = true;
  status.textContent = '⏳ Running Agent 1 — scoring adaptability…';

  try {
    // Step 1 — Agent 1
    const r1 = await fetch('/pipeline/agent1', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({profile_text: profile})
    });
    const d1 = await r1.json();
    document.getElementById('adaptNum').textContent = d1.adaptability_score;
    _cachedScores.adapt     = d1.adaptability_score;
    _cachedScores.adaptTier = d1.tier;
    status.textContent = `✅ Agent 1: ${d1.adaptability_score}/100 (${d1.tier}) — running Agent 2…`;

    // Step 2 — Agent 2
    const jobTitle = document.getElementById('jobTitle').value.trim();
    const r2 = await fetch('/pipeline/agent2', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        profile_text:       profile,
        adaptability_score: d1.adaptability_score,
        adaptability_tier:  d1.tier,
        job_title:          jobTitle,
      })
    });
    const d2 = await r2.json();
    document.getElementById('matchNum').textContent = d2.total_match_score;
    _cachedScores.match        = d2.total_match_score;
    _cachedScores.matchTier    = d2.match_tier || '';
    _cachedScores.matched_skills = d2.score_breakdown?.role_fit?.matched_skills || [];
    _cachedScores.startup      = d2.score_breakdown?.culture_fit?.startup_experience || false;
    _cachedScores.reasoning    = d2.reasoning || '';
    status.textContent = `✅ Agent 2: ${d2.total_match_score}/100 (${d2.match_tier}) — ready to generate campaign!`;
    btn.className = 'auto-btn done';
    btn.textContent = '✅ Scores fetched — click Generate';
  } catch(e) {
    status.textContent = '⚠️ Pipeline failed — enter scores manually or retry.';
  } finally {
    btn.disabled = false;
  }
}

// ── Generate outreach ─────────────────────────────────────────────────────
async function generate() {
  const candName    = document.getElementById('candName').value.trim();
  const profile     = document.getElementById('candProfile').value.trim();
  const jobTitle    = document.getElementById('jobTitle').value.trim();
  const companyName = document.getElementById('companyName').value.trim();
  const recruiter   = document.getElementById('recruiterName').value.trim();
  if (!candName || !profile || !jobTitle) { alert('Please fill in Candidate Name, Job Title, and Profile.'); return; }

  document.getElementById('placeholder').style.display = 'none';
  document.getElementById('result').style.display = 'none';
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('outreachBtn').disabled = true;

  try {
    const resp = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        candidate_name:     candName,
        candidate_profile:  profile,
        job_title:          jobTitle,
        company_name:       companyName || 'VelocityHire Client',
        recruiter_name:     recruiter || 'The Recruiting Team',
        total_match_score:  _cachedScores.match,
        match_tier:         _cachedScores.matchTier,
        adaptability_score: _cachedScores.adapt,
        adaptability_tier:  _cachedScores.adaptTier,
        matched_skills:     _cachedScores.matched_skills,
        startup_experience: _cachedScores.startup,
        recommend_interview: (_cachedScores.match || 0) >= 70,
        reasoning:          _cachedScores.reasoning,
      })
    });
    if (!resp.ok) { const e = await resp.json(); throw new Error(e.detail); }
    renderResult(await resp.json());
  } catch(e) {
    document.getElementById('spinner').style.display = 'none';
    document.getElementById('placeholder').style.display = 'flex';
    document.getElementById('placeholder').innerHTML = '<div class="icon">⚠️</div><p>' + e.message + '</p>';
  } finally {
    document.getElementById('outreachBtn').disabled = false;
  }
}

function renderResult(d) {
  document.getElementById('spinner').style.display = 'none';
  document.getElementById('result').style.display = 'block';

  const tier = d.outreach_tier || 'STANDARD';
  const tierMeta = {
    PRIORITY: {icon:'🚀', title:'Priority Fast-Track', sub:'Same-day outreach — top priority candidate', color:'var(--accent)'},
    STANDARD: {icon:'⭐', title:'Standard Interview Track', sub:'Strong match — proceed with interview invite', color:'var(--green)'},
    NURTURE:  {icon:'🌱', title:'Pipeline Nurture', sub:'Promising — warm hold for future roles', color:'var(--amber)'},
    ARCHIVE:  {icon:'📁', title:'Passive Archive', sub:'Keep on file for future consideration', color:'var(--muted)'},
  }[tier] || {};

  const hdr = document.getElementById('tierHeader');
  hdr.className = 'tier-header ' + tier;
  document.getElementById('tierIcon').textContent = tierMeta.icon || '✉️';
  document.getElementById('tierTitle').textContent = tierMeta.title || tier;
  document.getElementById('tierSub').textContent = tierMeta.sub || '';

  // Highlights
  const hl = d.key_highlights || [];
  document.getElementById('highlights').innerHTML = hl.map(h =>
    `<span class="hl-tag">✨ ${h}</span>`).join('') || '<span style="color:var(--muted);font-size:.8rem;">No highlights extracted</span>';

  // Messages
  const c = d.campaign || {};
  setMsg('linkedinMsg', c.linkedin_message || '');
  document.getElementById('linkedinChars').textContent =
    `${(c.linkedin_message||'').length}/300 characters (LinkedIn limit)`;
  document.getElementById('emailSubj').textContent = c.email?.subject || '';
  setMsg('emailBody', c.email?.body || '');
  document.getElementById('followupSubj').textContent = c.followup?.subject || '';
  setMsg('followupBody', c.followup?.body || '(No follow-up for this tier)');
  setMsg('recruiterNote', c.recruiter_note || '');

  document.getElementById('jsonOut').textContent = JSON.stringify(d, null, 2);
}

function setMsg(id, text) {
  const el = document.getElementById(id);
  // Keep the copy button, replace text
  const btn = el.querySelector('.copy-btn');
  el.textContent = text;
  if (btn) el.appendChild(btn);
}

function showTab(name) {
  document.querySelectorAll('.msg-tab').forEach((b,i) => {
    b.classList.toggle('active', ['linkedin','email','followup','recruiter'][i] === name);
  });
  ['linkedin','email','followup','recruiter'].forEach(n => {
    document.getElementById('tab-'+n).classList.toggle('active', n === name);
  });
}

function copyMsg(id) {
  const el = document.getElementById(id);
  const text = el.textContent.replace('Copy','').trim();
  navigator.clipboard.writeText(text).then(() => {
    const btn = el.querySelector('.copy-btn');
    if (btn) { btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = 'Copy', 2000); }
  });
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


# ── Routes ────────────────────────────────────────────────────────────────────

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
    return {"status": "ok", "agent": "Outreach Coordinator", "version": "1.0.0", "db": db}


@app.post("/pipeline/agent1")
async def proxy_agent1(body: dict):
    """Proxy → Agent 1."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{AGENT1_URL}/analyze", json={"profile_text": body.get("profile_text", "")})
        r.raise_for_status()
        return r.json()


@app.post("/pipeline/agent2")
async def proxy_agent2(body: dict):
    """Proxy → Agent 2 using adaptability score from Agent 1."""
    payload = {
        "job_title":          body.get("job_title", "Engineer"),
        "job_description":    body.get("job_description", ""),
        "required_skills":    body.get("required_skills", []),
        "candidate_name":     body.get("candidate_name", "Candidate"),
        "candidate_profile":  body.get("profile_text", ""),
        "adaptability_score": body.get("adaptability_score", 50),
        "adaptability_tier":  body.get("adaptability_tier", "Unknown"),
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{AGENT2_URL}/match", json=payload)
        r.raise_for_status()
        return r.json()


@app.post("/generate")
async def generate(
    req: OutreachRequest,
    x_company_id: Optional[str] = Header(default="demo"),
):
    company_id = (x_company_id or "demo").strip()
    # Auto-fetch scores from Agent 1 + 2 if not provided
    adapt_score = req.adaptability_score
    adapt_tier  = req.adaptability_tier or "Unknown"
    match_score = req.total_match_score
    match_tier  = req.match_tier or "Unknown"
    matched     = req.matched_skills or []
    startup     = req.startup_experience or False
    reasoning   = req.reasoning or ""

    if adapt_score is None or match_score is None:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Agent 1
                r1 = await client.post(f"{AGENT1_URL}/analyze",
                                       json={"profile_text": req.candidate_profile})
                if r1.status_code == 200:
                    d1 = r1.json()
                    adapt_score = d1.get("adaptability_score", 50)
                    adapt_tier  = d1.get("tier", "Unknown")
                # Agent 2
                r2 = await client.post(f"{AGENT2_URL}/match", json={
                    "job_title":          req.job_title,
                    "job_description":    req.job_description or "",
                    "required_skills":    req.required_skills or [],
                    "candidate_name":     req.candidate_name,
                    "candidate_profile":  req.candidate_profile,
                    "adaptability_score": adapt_score,
                    "adaptability_tier":  adapt_tier,
                })
                if r2.status_code == 200:
                    d2 = r2.json()
                    match_score = d2.get("total_match_score", 60)
                    match_tier  = d2.get("match_tier", "Unknown")
                    bd          = d2.get("score_breakdown", {})
                    matched     = bd.get("role_fit", {}).get("matched_skills", [])
                    startup     = bd.get("culture_fit", {}).get("startup_experience", False)
                    reasoning   = d2.get("reasoning", "")
        except Exception as e:
            logger.warning("Pipeline proxy failed: %s", str(e))
            adapt_score = adapt_score or 60
            match_score = match_score or 60

    result = generate_outreach(
        candidate_name=req.candidate_name,
        candidate_profile=req.candidate_profile,
        job_title=req.job_title,
        company_name=req.company_name or "VelocityHire Client",
        recruiter_name=req.recruiter_name or "The Recruiting Team",
        total_match_score=match_score,
        match_tier=match_tier,
        adaptability_score=adapt_score,
        adaptability_tier=adapt_tier,
        matched_skills=matched,
        startup_experience=startup,
        recommend_interview=req.recommend_interview,
        reasoning=reasoning,
    )
    logger.info("Outreach generated: tier=%s candidate=%s", result.get("outreach_tier"), req.candidate_name)
    # Phase 4 — persist to shared memory (tenant-scoped, non-blocking)
    try:
        save_outreach(result, company_id=company_id)
    except Exception as db_err:
        logger.warning("DB persist (non-critical): %s", str(db_err))
    return JSONResponse(content=result)


# ── Phase 4 endpoints ────────────────────────────────────────────────────────

@app.get("/history")
async def history(
    limit: int = 20,
    x_company_id: Optional[str] = Header(default=None),
):
    """Phase 4 — Return recent outreach campaigns, scoped to tenant if header provided."""
    try:
        records = get_recent_campaigns(limit, company_id=x_company_id or None)
        return JSONResponse(content={"count": len(records), "company_id": x_company_id, "records": records})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline", response_class=HTMLResponse)
async def pipeline_dashboard(
    company: Optional[str] = None,
    x_company_id: Optional[str] = Header(default=None),
):
    """Phase 4 — Full cross-agent pipeline dashboard (HTML), tenant-scoped."""
    # company param from query string takes priority, then header
    tenant = company or x_company_id or None
    try:
        candidates  = get_recent_candidates(50, company_id=tenant)
        matches     = get_recent_matches(50,     company_id=tenant)
        campaigns   = get_recent_campaigns(50,   company_id=tenant)
        db_stats    = get_db_stats()
        all_tenants = list_companies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Build lookup maps keyed by candidate_name (latest entry wins)
    cand_map = {r["candidate_name"]: r for r in reversed(candidates)}
    match_map = {r["candidate_name"]: r for r in reversed(matches)}
    camp_map  = {r["candidate_name"]: r for r in reversed(campaigns)}

    all_names = list(dict.fromkeys(
        [r["candidate_name"] for r in campaigns] +
        [r["candidate_name"] for r in matches] +
        [r["candidate_name"] for r in candidates]
    ))

    def tier_color(tier: str) -> str:
        return {"PRIORITY": "#6c63ff", "STANDARD": "#22c55e",
                "NURTURE": "#f59e0b", "ARCHIVE": "#94a3b8"}.get(tier, "#94a3b8")

    def score_color(s) -> str:
        try:
            s = int(s)
            return "#22c55e" if s >= 70 else "#f59e0b" if s >= 55 else "#ef4444"
        except Exception:
            return "#94a3b8"

    rows_html = ""
    for name in all_names:
        c  = cand_map.get(name, {})
        m  = match_map.get(name, {})
        oc = camp_map.get(name, {})
        a_score = c.get("adaptability_score", "—")
        m_score = m.get("total_match_score", "—")
        tier    = oc.get("outreach_tier", "—")
        date    = (oc.get("created_at") or m.get("created_at") or c.get("created_at") or "")[:10]
        job     = m.get("job_title") or oc.get("job_title") or "—"
        recommend = c.get("recommend_interview", "—")
        rows_html += f"""
        <tr>
          <td style="font-weight:600;color:#e2e8f0;">{name}</td>
          <td>{job}</td>
          <td style="color:{score_color(a_score)};font-weight:700;">{a_score}</td>
          <td style="color:{score_color(m_score)};font-weight:700;">{m_score}</td>
          <td><span style="background:{tier_color(tier)}22;color:{tier_color(tier)};border:1px solid {tier_color(tier)}55;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:700;">{tier}</span></td>
          <td style="color:{'#22c55e' if 'True' in str(recommend) else '#ef4444'}">{recommend}</td>
          <td style="color:#94a3b8;font-size:.78rem;">{date}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VelocityHire · Pipeline Dashboard</title>
<style>
  :root{{--bg:#0f1117;--surface:#1a1d27;--surface2:#242736;--accent:#6c63ff;--accent2:#f5a623;
        --text:#e2e8f0;--muted:#94a3b8;--border:#2d3147;--radius:12px;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;}}
  header{{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 32px;display:flex;align-items:center;gap:12px;}}
  .logo{{font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
  .badge{{background:var(--surface2);border:1px solid var(--border);color:var(--muted);font-size:.75rem;padding:2px 10px;border-radius:20px;}}
  .container{{max-width:1300px;margin:0 auto;padding:28px 20px;}}
  h1{{font-size:1.6rem;font-weight:700;margin-bottom:6px;}}
  .stats{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px;}}
  .stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 22px;min-width:150px;}}
  .stat-card .num{{font-size:2rem;font-weight:900;color:var(--accent);}}
  .stat-card .lbl{{font-size:.75rem;color:var(--muted);margin-top:2px;}}
  table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:var(--radius);overflow:hidden;}}
  th{{background:var(--surface2);color:var(--muted);font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;padding:12px 16px;text-align:left;}}
  td{{padding:12px 16px;border-top:1px solid var(--border);font-size:.85rem;color:var(--muted);}}
  tr:hover td{{background:var(--surface2);}}
  .empty{{text-align:center;padding:48px;color:var(--muted);}}
</style>
</head>
<body>
<header>
  <div class="logo">⚡ VelocityHire</div>
  <span class="badge">Phase 4 · Pipeline Dashboard</span>
  <span class="badge" style="margin-left:auto;">Shared Memory · {db_stats.get("db_path","SQLite")[-30:]}</span>
</header>
<div class="container">
  <div style="margin-bottom:20px;display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;">
    <div>
      <h1>Cross-Agent Pipeline Dashboard</h1>
      <p style="color:var(--muted);margin-top:4px;">All candidates scored by Agents 1, 2 &amp; 3 — persisted to shared SQLite memory</p>
    </div>
    <form method="get" action="/pipeline" style="display:flex;gap:8px;align-items:center;">
      <label style="font-size:.75rem;color:var(--muted);">Company:</label>
      <select name="company" onchange="this.form.submit()" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:7px;padding:6px 10px;font-size:.8rem;cursor:pointer;">
        <option value="">All companies</option>
        {"".join(f'<option value="{c["company_id"]}" {"selected" if c["company_id"]==tenant else ""}>{c["company_name"]} ({c["company_id"]})</option>' for c in all_tenants)}
      </select>
    </form>
  </div>
  <div class="stats">
    <div class="stat-card"><div class="num">{db_stats.get("candidates",0)}</div><div class="lbl">Profiles Analyzed<br>(Agent 1)</div></div>
    <div class="stat-card"><div class="num">{db_stats.get("job_matches",0)}</div><div class="lbl">Jobs Matched<br>(Agent 2)</div></div>
    <div class="stat-card"><div class="num">{db_stats.get("outreach_campaigns",0)}</div><div class="lbl">Campaigns Sent<br>(Agent 3)</div></div>
    <div class="stat-card"><div class="num">{len(all_names)}</div><div class="lbl">Unique<br>Candidates</div></div>
  </div>
  {"<table><thead><tr><th>Candidate</th><th>Role</th><th>Adaptability</th><th>Job Match</th><th>Outreach Tier</th><th>Interview?</th><th>Date</th></tr></thead><tbody>" + rows_html + "</tbody></table>" if all_names else '<div class="empty"><div style="font-size:3rem;">📭</div><p style="margin-top:12px;">No pipeline data yet — run some candidates through the agents!</p></div>'}
</div>
</body>
</html>"""


@app.get("/pipeline/candidate/{candidate_name}")
async def pipeline_candidate(candidate_name: str):
    """Phase 4 — Cross-agent JSON view for a specific candidate."""
    try:
        data = get_pipeline_summary(candidate_name)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
