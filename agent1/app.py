"""
Agent 1 — Profile Analyzer  |  FastAPI Web Application
Hackathon Prototype for VelocityHire / AdaptScore platform

Routes:
  GET  /          → UI
  POST /analyze   → JSON API (profile_text) → adaptability report
  GET  /health    → health check
"""

import json
import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# ── logging ──────────────────────────────────────────────────────────────────
LOG_DIR = Path("/mnt/efs/spaces/6f40e0fa-8a03-41a6-a37c-c728be34b83b/f99b24e1-53b1-4954-a709-a448e806bd7b/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
    handlers=[
        logging.FileHandler(LOG_DIR / "agent1.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("agent1")

# ── import agent ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))   # shared/ package
from agent_1 import analyze_profile
from profile_fetcher import fetch_linkedin_profile

# ── Phase 4: shared memory (non-fatal if sqlalchemy not installed) ────────────
try:
    from shared.db_memory import save_candidate_score, get_recent_candidates, get_db_stats
    DB_ENABLED = True
except ImportError:
    DB_ENABLED = False
    def save_candidate_score(*a, **kw): return None      # noqa: E704
    def get_recent_candidates(*a, **kw): return []       # noqa: E704
    def get_db_stats(*a, **kw): return {"db_persistence": False}  # noqa: E704

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Agent 1 — Profile Analyzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProfileRequest(BaseModel):
    profile_text: str
    client_id: str | None = None
    client_secret: str | None = None
    org_id: str | None = None


class FetchRequest(BaseModel):
    url: str


# ── HTML UI ───────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VelocityHire · Agent 1 — Profile Analyzer</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #242736;
    --accent: #6c63ff;
    --accent2: #f5a623;
    --green: #22c55e;
    --red: #ef4444;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --border: #2d3147;
    --radius: 12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
  }
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  header .logo {
    font-size: 1.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  header .badge {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.75rem;
    padding: 2px 10px;
    border-radius: 20px;
  }
  .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
  .tagline {
    text-align: center;
    margin-bottom: 36px;
  }
  .tagline h1 { font-size: 2rem; font-weight: 700; margin-bottom: 8px; }
  .tagline p { color: var(--muted); font-size: 1rem; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media(max-width:768px){ .grid { grid-template-columns: 1fr; } }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
  }
  .card h2 { font-size: 1rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 16px; }

  textarea {
    width: 100%;
    min-height: 320px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.875rem;
    line-height: 1.6;
    padding: 14px;
    resize: vertical;
    outline: none;
    transition: border-color .2s;
  }
  textarea:focus { border-color: var(--accent); }

  .examples { margin-top: 12px; }
  .examples span { font-size: 0.75rem; color: var(--muted); margin-right: 8px; }
  .ex-btn {
    font-size: 0.75rem;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--accent);
    padding: 3px 10px;
    border-radius: 20px;
    cursor: pointer;
    margin-right: 6px;
  }
  .ex-btn:hover { border-color: var(--accent); }

  .btn {
    display: block;
    width: 100%;
    margin-top: 16px;
    padding: 14px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    color: #fff;
    font-size: 1rem;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: opacity .2s;
  }
  .btn:hover { opacity: .9; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }

  /* Score display */
  .score-ring {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 24px;
  }
  .ring-wrap {
    position: relative;
    width: 160px;
    height: 160px;
    margin-bottom: 8px;
  }
  .ring-wrap svg { transform: rotate(-90deg); }
  .ring-bg { fill: none; stroke: var(--surface2); stroke-width: 14; }
  .ring-fill { fill: none; stroke-width: 14; stroke-linecap: round; transition: stroke-dashoffset .8s ease; }
  .ring-label {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .ring-num { font-size: 2.5rem; font-weight: 800; }
  .ring-max { font-size: 0.8rem; color: var(--muted); }

  .tier-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
    margin-top: 4px;
  }

  .breakdown { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
  .brow { display: flex; align-items: center; gap: 10px; }
  .brow-label { width: 130px; font-size: 0.8rem; color: var(--muted); flex-shrink: 0; }
  .brow-bar { flex: 1; height: 8px; background: var(--surface2); border-radius: 4px; overflow: hidden; }
  .brow-fill { height: 100%; border-radius: 4px; transition: width .6s ease; }
  .brow-score { width: 60px; text-align: right; font-size: 0.8rem; font-weight: 600; }

  .reasoning {
    background: var(--surface2);
    border-radius: 8px;
    padding: 16px;
    font-size: 0.85rem;
    line-height: 1.7;
    white-space: pre-wrap;
    color: var(--text);
    max-height: 220px;
    overflow-y: auto;
  }

  .verdict {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 18px;
    border-radius: 8px;
    font-weight: 600;
    margin-top: 16px;
  }
  .verdict.pass { background: rgba(34,197,94,.1); border: 1px solid rgba(34,197,94,.3); color: var(--green); }
  .verdict.fail { background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.3); color: var(--red); }

  .placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 12px;
    color: var(--muted);
    text-align: center;
    min-height: 300px;
  }
  .placeholder .icon { font-size: 3rem; }

  .spinner {
    display: none;
    width: 40px; height: 40px;
    border: 4px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .8s linear infinite;
    margin: 40px auto;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .pipeline {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-top: 20px;
    flex-wrap: wrap;
  }
  .pipe-step {
    font-size: 0.72rem;
    padding: 4px 10px;
    border-radius: 20px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--muted);
  }
  .pipe-step.active { border-color: var(--accent); color: var(--accent); }
  .pipe-arrow { color: var(--muted); font-size: 0.8rem; }

  .json-toggle {
    font-size: 0.75rem;
    color: var(--accent);
    cursor: pointer;
    text-decoration: underline;
    margin-top: 12px;
    display: inline-block;
  }
  pre.json-out {
    display: none;
    margin-top: 8px;
    background: #0a0c12;
    border-radius: 8px;
    padding: 14px;
    font-size: 0.75rem;
    overflow-x: auto;
    color: #a3e635;
    max-height: 240px;
    overflow-y: auto;
  }

  /* Tab switcher */
  .tabs { display: flex; gap: 0; margin-bottom: 16px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
  .tab-btn {
    flex: 1;
    padding: 10px;
    background: var(--surface2);
    border: none;
    color: var(--muted);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .2s, color .2s;
  }
  .tab-btn.active { background: var(--accent); color: #fff; }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  /* URL input row */
  .url-row { display: flex; gap: 8px; align-items: center; }
  .url-input {
    flex: 1;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 0.875rem;
    padding: 12px 14px;
    outline: none;
    transition: border-color .2s;
  }
  .url-input:focus { border-color: var(--accent); }
  .fetch-btn {
    padding: 12px 18px;
    background: var(--surface2);
    border: 1px solid var(--accent);
    border-radius: 8px;
    color: var(--accent);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: background .2s;
  }
  .fetch-btn:hover { background: rgba(108,99,255,.15); }
  .fetch-btn:disabled { opacity: .5; cursor: not-allowed; }

  .fetch-status {
    font-size: 0.78rem;
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 6px;
    display: none;
  }
  .fetch-status.loading { display: block; background: rgba(108,99,255,.1); color: var(--accent); }
  .fetch-status.ok   { display: block; background: rgba(34,197,94,.1); color: var(--green); }
  .fetch-status.err  { display: block; background: rgba(239,68,68,.1); color: var(--red); }
</style>
</head>
<body>

<header>
  <div class="logo">⚡ VelocityHire</div>
  <span class="badge">Agent 1 — Profile Analyzer</span>
  <span class="badge" style="margin-left:auto;">Hackathon Prototype · Feb 2026</span>
</header>

<div class="container">
  <div class="tagline">
    <h1>Learning Velocity over Static Skills</h1>
    <p>Paste a candidate's LinkedIn profile to receive an AI-powered adaptability score (0–100)</p>
  </div>

  <!-- Pipeline indicator -->
  <div class="pipeline" style="justify-content:center;margin-bottom:28px;">
    <div class="pipe-step active">① Profile Analyzer</div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">② Job Matcher</div>
    <div class="pipe-arrow">→</div>
    <div class="pipe-step">③ Outreach Coordinator</div>
  </div>

  <div class="grid">
    <!-- INPUT -->
    <div class="card">
      <h2>Candidate Profile Input</h2>

      <!-- Tab switcher -->
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('url')">🔗 LinkedIn URL</button>
        <button class="tab-btn" onclick="switchTab('paste')">📋 Paste Profile</button>
      </div>

      <!-- TAB: LinkedIn URL -->
      <div class="tab-panel active" id="tab-url">
        <div class="url-row">
          <input id="linkedinUrl" class="url-input"
            type="url"
            placeholder="https://www.linkedin.com/in/username/"
            autocomplete="off"/>
          <button class="fetch-btn" id="fetchBtn" onclick="fetchProfile()">
            ⬇ Fetch
          </button>
        </div>
        <div class="fetch-status" id="fetchStatus"></div>
        <p style="font-size:0.75rem;color:var(--muted);margin-top:10px;line-height:1.5;">
          ℹ️ Works on public profiles. If LinkedIn blocks the request, switch to <strong>Paste Profile</strong> and copy-paste the profile text directly.
        </p>
      </div>

      <!-- TAB: Paste -->
      <div class="tab-panel" id="tab-paste">
        <textarea id="profileInput" placeholder="Paste LinkedIn profile text here…

Example:
Sarah Chen — Full Stack Developer
Skills: React, TypeScript, Python, Next.js
Hackathons:
  - AI Buildathon (2 weeks ago) — Winner
  - Junction Helsinki (5 months ago) — Finalist
Certifications:
  - AWS Solutions Architect (1 month ago)
GitHub: 60 commits last month exploring LLMs...
"></textarea>
        <div class="examples" style="margin-top:10px;">
          <span>Load sample:</span>
          <button class="ex-btn" onclick="loadSample('high')">🏆 High Performer</button>
          <button class="ex-btn" onclick="loadSample('mid')">⭐ Promising</button>
          <button class="ex-btn" onclick="loadSample('low')">📋 Static Skills</button>
        </div>
      </div>

      <!-- Fetched profile preview (shown after URL fetch) -->
      <div id="fetchedPreview" style="display:none;margin-top:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
          <span style="font-size:0.78rem;color:var(--muted);">📄 Fetched profile text (used for analysis)</span>
          <button onclick="clearFetch()" style="font-size:0.72rem;color:var(--red);background:none;border:none;cursor:pointer;">✕ Clear</button>
        </div>
        <textarea id="fetchedText" rows="6"
          style="width:100%;background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--muted);font-size:0.75rem;padding:10px;resize:vertical;outline:none;"
          readonly></textarea>
      </div>

      <details style="margin-top:16px;">
        <summary style="cursor:pointer;font-size:0.8rem;color:var(--muted);padding:8px 0;">⚙️ Deploy AI Credentials (pre-configured)</summary>
        <div style="margin-top:10px;display:flex;flex-direction:column;gap:8px;">
          <label style="font-size:0.72rem;color:var(--muted);">API Key ID</label>
          <input id="clientId" type="text" placeholder="sk_ API Key ID"
            value="sk_0OWou3RCtje5aPRisLUMVj0wQAAgON_x9VdvyEF_u8A"
            style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:8px 12px;font-size:0.8rem;outline:none;"/>
          <label style="font-size:0.72rem;color:var(--muted);">API Key Secret</label>
          <input id="clientSecret" type="password" placeholder="sk_ API Key Secret"
            value="sk_aXUDvegSCPvq3eVtCNMvXd5jWEV7g4aePJh8MQkDaEM"
            style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:8px 12px;font-size:0.8rem;outline:none;"/>
          <label style="font-size:0.72rem;color:var(--muted);">Organisation ID</label>
          <input id="orgId" type="text" placeholder="ORG_ID"
            value="133081f3-32d9-4fe5-8ee6-9a190624c1cc"
            style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--text);padding:8px 12px;font-size:0.8rem;outline:none;"/>
        </div>
      </details>

      <button class="btn" id="analyzeBtn" onclick="analyze()">
        🔍 Analyze Adaptability Score
      </button>
    </div>

    <!-- OUTPUT -->
    <div class="card" id="outputCard">
      <h2>Adaptability Report</h2>
      <div id="placeholder" class="placeholder">
        <div class="icon">🤖</div>
        <p>Submit a profile to generate an<br>AI-powered adaptability report</p>
      </div>
      <div id="spinner" class="spinner"></div>
      <div id="result" style="display:none;">
        <div class="score-ring">
          <div class="ring-wrap">
            <svg viewBox="0 0 160 160" width="160" height="160">
              <circle class="ring-bg" cx="80" cy="80" r="66"/>
              <circle class="ring-fill" id="ringFill" cx="80" cy="80" r="66"
                stroke-dasharray="414.69" stroke-dashoffset="414.69"/>
            </svg>
            <div class="ring-label">
              <span class="ring-num" id="scoreNum">0</span>
              <span class="ring-max">/100</span>
            </div>
          </div>
          <span class="tier-badge" id="tierBadge">—</span>
        </div>

        <div class="breakdown" id="breakdown"></div>

        <div class="reasoning" id="reasoning"></div>

        <div id="verdict" class="verdict"></div>

        <span class="json-toggle" onclick="toggleJson()">Show raw JSON ↓</span>
        <pre class="json-out" id="jsonOut"></pre>
      </div>
    </div>
  </div>
</div>

<script>
// ── Tab switching ─────────────────────────────────────────────────────────
let activeTab = 'url';
function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach((b, i) => {
    b.classList.toggle('active', (i === 0 && tab === 'url') || (i === 1 && tab === 'paste'));
  });
  document.getElementById('tab-url').classList.toggle('active', tab === 'url');
  document.getElementById('tab-paste').classList.toggle('active', tab === 'paste');
}

// ── LinkedIn URL fetch ─────────────────────────────────────────────────────
async function fetchProfile() {
  const url = document.getElementById('linkedinUrl').value.trim();
  if (!url) { alert('Please enter a LinkedIn URL.'); return; }
  const status = document.getElementById('fetchStatus');
  const fetchBtn = document.getElementById('fetchBtn');
  status.className = 'fetch-status loading';
  status.textContent = '⏳ Fetching LinkedIn profile…';
  fetchBtn.disabled = true;
  document.getElementById('fetchedPreview').style.display = 'none';

  try {
    const resp = await fetch('/fetch-profile', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
    const data = await resp.json();
    if (data.success) {
      status.className = 'fetch-status ok';
      status.textContent = '✅ Profile fetched — ready to analyze!';
      document.getElementById('fetchedText').value = data.profile_text;
      document.getElementById('fetchedPreview').style.display = 'block';
    } else {
      status.className = 'fetch-status err';
      status.textContent = '⚠️ ' + data.error;
      // Auto-switch to paste tab so user can enter manually
      switchTab('paste');
    }
  } catch(e) {
    status.className = 'fetch-status err';
    status.textContent = '⚠️ Fetch failed — please paste the profile text manually.';
    switchTab('paste');
  } finally {
    fetchBtn.disabled = false;
  }
}

function clearFetch() {
  document.getElementById('fetchedText').value = '';
  document.getElementById('fetchedPreview').style.display = 'none';
  document.getElementById('fetchStatus').className = 'fetch-status';
  document.getElementById('linkedinUrl').value = '';
}

// ── Resolve profile text from whichever input mode is active ───────────────
function getProfileText() {
  // If a fetched profile is available, use that regardless of active tab
  const fetched = document.getElementById('fetchedText').value.trim();
  if (fetched) return fetched;
  // Otherwise use pasted text
  return document.getElementById('profileInput').value.trim();
}

const SAMPLES = {
  high: `Marcus Rivera — Senior Software Engineer
Skills: React, Node.js, TypeScript, Next.js, Python, FastAPI, PostgreSQL, Svelte, Rust
Experience:
  - TechStartup (2021-present): Full-stack engineer. Built AI-powered analytics dashboard.
  - Acme Corp (2019-2021): Backend developer, microservices, AWS.
Hackathons:
  - React Summit Hackathon (1 month ago) — WINNER, built AI code-review bot in 24 hrs.
  - Junction Helsinki (4 months ago) — Finalist, GenAI travel planner. Led team of 4.
  - HackMIT (14 months ago) — Participant.
Certifications:
  - AWS Certified Developer (2 months ago)
  - LangChain & LangGraph Bootcamp (3 months ago)
GitHub: 45 commits last month, exploring Svelte and Rust. Contributor to open-source LLM library.
Recent activity: Blog post on vector databases (2 weeks ago). Speaker at local AI meetup (1 month ago).`,

  mid: `Sarah Chen — Full Stack Developer
Skills: React, Vue.js, Node.js, Python, Docker, AWS basics
Experience:
  - FinTech Co (2022-present): Frontend developer. Delivered 3 major product features.
  - Agency (2020-2022): Web developer, various client sites.
Hackathons:
  - Local AI Hackathon (6 months ago) — Participant. Built a chatbot prototype.
Certifications:
  - Google Cloud Fundamentals (5 months ago)
  - Scrum Master Certification (8 months ago)
GitHub: 12 commits last month. Started exploring LangChain in side project.
Recent activity: LinkedIn post on AI trends (1 month ago).`,

  low: `James Wilson — Senior Java Developer
Skills: Java, Spring Boot, Hibernate, Oracle DB, Maven, SVN
Experience:
  - Bank Corp (2015-present): Maintains legacy payment processing system.
  - Insurance Co (2010-2015): Java backend developer.
Hackathons: None listed.
Certifications:
  - Oracle Certified Professional Java (2016)
  - Project Management Professional (2018)
GitHub: Last commit 2 years ago. Mostly Java utility scripts.
Recent activity: No recent public activity found.`
};

function loadSample(type) {
  switchTab('paste');
  document.getElementById('profileInput').value = SAMPLES[type];
  clearFetch();
}

async function analyze() {
  const text = getProfileText();
  if (!text) { alert('Please enter a LinkedIn URL or paste a profile first.'); return; }

  document.getElementById('placeholder').style.display = 'none';
  document.getElementById('result').style.display = 'none';
  document.getElementById('spinner').style.display = 'block';
  document.getElementById('analyzeBtn').disabled = true;

  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        profile_text: text,
        client_id: document.getElementById('clientId').value || null,
        client_secret: document.getElementById('clientSecret').value || null,
        org_id: document.getElementById('orgId').value || null,
      })
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Analysis failed');
    }
    const data = await resp.json();
    renderResult(data);
  } catch(e) {
    document.getElementById('spinner').style.display = 'none';
    document.getElementById('placeholder').style.display = 'flex';
    document.getElementById('placeholder').innerHTML =
      '<div class="icon">⚠️</div><p>' + e.message + '</p>';
  } finally {
    document.getElementById('analyzeBtn').disabled = false;
  }
}

function renderResult(data) {
  document.getElementById('spinner').style.display = 'none';
  document.getElementById('result').style.display = 'block';

  const score = data.adaptability_score || 0;

  // Ring
  const circumference = 414.69;
  const offset = circumference - (score / 100) * circumference;
  const fill = document.getElementById('ringFill');
  fill.style.strokeDashoffset = offset;
  fill.style.stroke = score >= 70 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444';
  document.getElementById('scoreNum').textContent = score;
  document.getElementById('scoreNum').style.color = score >= 70 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444';

  // Tier badge
  const tierEl = document.getElementById('tierBadge');
  tierEl.textContent = data.tier || '—';
  tierEl.style.background = score >= 70 ? 'rgba(34,197,94,.15)' : 'rgba(239,68,68,.1)';
  tierEl.style.color = score >= 70 ? '#22c55e' : '#f59e0b';

  // Breakdown bars
  const bd = data.score_breakdown || {};
  const dims = [
    {key:'hackathons',     label:'Hackathons',     color:'#6c63ff', max:40},
    {key:'skills',         label:'Skills',         color:'#f5a623', max:25},
    {key:'certifications', label:'Certifications', color:'#3b82f6', max:20},
    {key:'recency',        label:'Recency',        color:'#22c55e', max:15},
  ];
  const bdEl = document.getElementById('breakdown');
  bdEl.innerHTML = dims.map(d => {
    const val = bd[d.key]?.score || 0;
    const pct = Math.round((val/d.max)*100);
    return `
      <div class="brow">
        <span class="brow-label">${d.label}</span>
        <div class="brow-bar">
          <div class="brow-fill" style="width:${pct}%;background:${d.color};"></div>
        </div>
        <span class="brow-score" style="color:${d.color}">${val}/${d.max}</span>
      </div>`;
  }).join('');

  // Reasoning
  document.getElementById('reasoning').textContent = data.reasoning || '';

  // Verdict
  const v = document.getElementById('verdict');
  if (data.recommend_interview) {
    v.className = 'verdict pass';
    v.innerHTML = '✅ &nbsp;Recommend for Interview — above 70+ threshold';
  } else {
    v.className = 'verdict fail';
    v.innerHTML = '📋 &nbsp;Keep in pipeline — below interview threshold';
  }

  // Raw JSON
  document.getElementById('jsonOut').textContent = JSON.stringify(data, null, 2);
}

function toggleJson() {
  const el = document.getElementById('jsonOut');
  const tog = document.querySelector('.json-toggle');
  if (el.style.display === 'none' || !el.style.display) {
    el.style.display = 'block';
    tog.textContent = 'Hide raw JSON ↑';
  } else {
    el.style.display = 'none';
    tog.textContent = 'Show raw JSON ↓';
  }
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
    return {"status": "ok", "agent": "Profile Analyzer", "version": "1.0.0", "db": db}


@app.post("/fetch-profile")
async def fetch_profile(req: FetchRequest):
    """Attempt to fetch and extract text from a public LinkedIn profile URL."""
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="url cannot be empty")
    logger.info("Fetching LinkedIn profile: %s", req.url)
    result = fetch_linkedin_profile(req.url)
    logger.info("Fetch result: success=%s", result.get("success"))
    return JSONResponse(content=result)


@app.post("/analyze")
async def analyze(req: ProfileRequest):
    if not req.profile_text.strip():
        raise HTTPException(status_code=400, detail="profile_text cannot be empty")
    logger.info("Received analysis request (%d chars)", len(req.profile_text))
    try:
        result = analyze_profile(
            req.profile_text,
            client_id=req.client_id,
            client_secret=req.client_secret,
            org_id=req.org_id,
        )
        logger.info("Analysis complete — score=%s tier=%s",
                    result.get("adaptability_score"), result.get("tier"))
        # Phase 4 — persist to shared memory (non-blocking)
        try:
            save_candidate_score(req.profile_text, result)
        except Exception as db_err:
            logger.warning("DB persist (non-critical): %s", str(db_err))
        return JSONResponse(content=result)
    except Exception as e:
        logger.error("Analysis failed: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def history(limit: int = 20):
    """Phase 4 — Return recent adaptability scores from shared memory."""
    try:
        records = get_recent_candidates(limit)
        return JSONResponse(content={"count": len(records), "records": records})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
