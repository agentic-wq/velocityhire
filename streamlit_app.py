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
import time
import html
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any

# -- Path setup (must happen before agent imports) ----------------------------
ROOT = Path(__file__).parent
os.environ.setdefault("MOCK_MODE", "true")
for _sub in ("agent1", "agent2", "agent3"):
    _p = str(ROOT / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
_root_str = str(ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

import streamlit as st  # noqa: E402

# -- Page config --------------------------------------------------------------
st.set_page_config(
    page_title="VelocityHire — AI Recruitment Demo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -- CSS: hide Streamlit chrome, match Cloud Run visual design ----------------
st.markdown("""
<style>
/* Hide Streamlit UI chrome */
#MainMenu {visibility: hidden !important;}
header[data-testid="stHeader"] {display: none !important;}
footer {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
button[kind="header"] {display: none !important;}
[data-testid="collapsedControl"] {display: none !important;}

/* Remove default padding, make full-width */
.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    max-width: 100% !important;
}
section[data-testid="stMain"] > div:first-child {padding-top: 0 !important;}
.stApp > header {display: none !important;}

/* CSS Variables (mirror Cloud Run) */
:root {
  --bg: #080812;
  --surface: #10101e;
  --surface2: #16162a;
  --border: #2a2a4a;
  --primary: #6c63ff;
  --primary-l: #a78bfa;
  --success: #22c55e;
  --warn: #f59e0b;
  --danger: #ef4444;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --faint: #64748b;
}

/* Base */
.stApp {background: var(--bg) !important;}
*{box-sizing:border-box;}

/* Hero */
.vh-hero {
  background: linear-gradient(135deg, #060610 0%, #12082a 50%, #061220 100%);
  padding: 56px 24px 48px;
  text-align: center;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-hero::before {
  content: '';
  position: absolute;
  inset: -50%;
  background: radial-gradient(circle at 50% 50%, rgba(108,99,255,.08) 0%, transparent 60%);
  animation: hpulse 5s ease-in-out infinite;
}
@keyframes hpulse {
  0%,100% {transform: scale(1); opacity: 1;}
  50% {transform: scale(1.12); opacity: .6;}
}
.vh-logo {
  font-size: 2.6rem;
  font-weight: 900;
  position: relative;
  background: linear-gradient(135deg, #6c63ff, #a78bfa 45%, #22c55e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 8px;
}
.vh-tagline {color: var(--muted); font-size: 1.05rem; margin-bottom: 4px; position: relative;}
.vh-sub {color: var(--faint); font-size: .83rem; position: relative; margin-bottom: 20px;}
.vh-badges {
  display: flex; gap: 8px; justify-content: center;
  flex-wrap: wrap; margin: 16px 0; position: relative;
}
.vh-badge {
  background: rgba(108,99,255,.12);
  border: 1px solid rgba(108,99,255,.35);
  color: #a78bfa;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: .78rem;
  font-weight: 500;
}

/* Run button wrapper — continues hero gradient */
.vh-btn-wrap {
  background: linear-gradient(135deg, #060610 0%, #12082a 50%, #061220 100%);
  padding: 0 24px 48px;
  text-align: center;
}

/* Eliminate Streamlit inter-element gaps (handled by our own CSS margins) */
[data-testid="stVerticalBlock"] {gap: 0 !important;}

/* Container */
.vh-container {
  max-width: 1380px;
  margin: 0 auto;
  padding: 36px 20px;
  font-family: 'Inter', -apple-system, sans-serif;
}

/* Section title */
.vh-section-title {
  font-size: 1.15rem; font-weight: 700; margin-bottom: 18px;
  display: flex; align-items: center; gap: 10px; color: var(--text);
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--primary); flex-shrink: 0; display: inline-block;
}

/* Innovation cards */
.vh-innovation-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px; margin-bottom: 32px;
}
.vh-inno-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 20px;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-inno-title {font-weight: 700; font-size: .92rem; margin-bottom: 6px; color: var(--text);}
.vh-inno-desc {font-size: .78rem; color: var(--muted); line-height: 1.6;}

/* Pipeline diagram */
.vh-pipe-flow {
  display: flex; align-items: center; justify-content: center;
  flex-wrap: wrap; gap: 0; margin-bottom: 36px; padding: 20px 24px;
  background: var(--surface); border-radius: 16px; border: 1px solid var(--border);
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-pipe-step {display: flex; flex-direction: column; align-items: center; gap: 5px; padding: 12px 20px;}
.vh-pipe-icon {
  width: 50px; height: 50px; border-radius: 13px;
  display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
  background: rgba(108,99,255,.12); border: 1px solid rgba(108,99,255,.28);
}
.vh-pipe-label {font-size: .78rem; color: var(--muted); font-weight: 600; text-align: center;}
.vh-pipe-sub {font-size: .7rem; color: var(--faint); text-align: center;}
.vh-pipe-arrow {color: var(--border); font-size: 1.3rem; padding: 0 6px;}
.vh-pipe-divider {width: 1px; height: 60px; background: var(--border); margin: 0 24px;}
.vh-pipe-meta {padding: 0 20px; text-align: left;}
.vh-pipe-meta-title {
  font-size: .72rem; color: var(--faint); text-transform: uppercase;
  letter-spacing: .05em; margin-bottom: 5px;
}
.vh-pipe-meta-val {font-size: .9rem; font-weight: 700; color: var(--text);}
.vh-pipe-meta-sub {font-size: .75rem; color: var(--muted); margin-top: 2px;}
.vh-pipe-weights {display: grid; grid-template-columns: 1fr 1fr; gap: 3px 16px; margin-top: 4px;}
.vh-pw {font-size: .75rem; color: var(--text);}
.vh-pw span {color: var(--primary); font-weight: 700;}

/* Candidate grid */
.vh-candidates-grid {
  display: grid; grid-template-columns: repeat(5, 1fr);
  gap: 16px; margin-bottom: 36px;
}
@media(max-width:1100px){.vh-candidates-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:680px){.vh-candidates-grid{grid-template-columns:repeat(2,1fr)}}
.vh-c-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 16px; padding: 20px; transition: all .35s;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-c-card.active {border-color: var(--primary); box-shadow: 0 0 22px rgba(108,99,255,.25);}
.vh-c-card.done {border-color: var(--success); box-shadow: 0 0 16px rgba(34,197,94,.15);}
.vh-c-emoji {font-size: 2rem; margin-bottom: 8px;}
.vh-c-name {font-weight: 700; font-size: .92rem; margin-bottom: 4px; color: var(--text); line-height: 1.2;}
.vh-c-stage {font-size: .73rem; color: var(--muted); margin-bottom: 12px; min-height: 16px;}
.vh-stage-dots {display: flex; gap: 7px; margin-bottom: 14px;}
.vh-sdot {width: 10px; height: 10px; border-radius: 50%; background: var(--border); transition: all .3s;}
.vh-sdot.active {
  background: var(--primary); box-shadow: 0 0 8px var(--primary);
  animation: dp 1s ease-in-out infinite;
}
.vh-sdot.done {background: var(--success); box-shadow: none; animation: none;}
@keyframes dp {0%,100%{transform:scale(1)} 50%{transform:scale(1.4)}}
.vh-c-scores {display: flex; flex-direction: column; gap: 7px;}
.vh-score-row {display: flex; justify-content: space-between; align-items: center;}
.vh-score-lbl {font-size: .7rem; color: var(--muted);}
.vh-score-val {font-size: .85rem; font-weight: 700;}

/* Score bar */
.vh-sbar {display: flex; align-items: center; gap: 8px;}
.vh-sbar-track {flex: 1; height: 5px; background: var(--border); border-radius: 3px; overflow: hidden; min-width: 60px;}
.vh-sbar-fill {height: 100%; border-radius: 3px;}
.vh-sbar-val {font-weight: 700; font-size: .82rem; min-width: 28px; text-align: right;}

/* Tier badges */
.vh-tier-badge {
  padding: 4px 10px; border-radius: 8px; font-size: .72rem;
  font-weight: 700; text-transform: uppercase; display: inline-block;
}
.vh-tP {background: rgba(34,197,94,.14); color: #22c55e; border: 1px solid rgba(34,197,94,.3);}
.vh-tS {background: rgba(108,99,255,.14); color: #6c63ff; border: 1px solid rgba(108,99,255,.3);}
.vh-tN {background: rgba(245,158,11,.14); color: #f59e0b; border: 1px solid rgba(245,158,11,.3);}
.vh-tA {background: rgba(100,116,139,.14); color: #94a3b8; border: 1px solid rgba(100,116,139,.3);}

/* Comparison */
.vh-comparison-outer {
  display: grid; grid-template-columns: 1fr 56px 1fr;
  background: var(--surface); border-radius: 16px;
  border: 1px solid var(--border); overflow: hidden; margin-bottom: 32px;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-comp-col {min-width: 0;}
.vh-comp-header {
  padding: 13px 18px; text-align: center; font-size: .75rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .06em;
  border-bottom: 1px solid var(--border); line-height: 1.5;
}
.vh-comp-header.trad {background: rgba(100,116,139,.1); color: #94a3b8;}
.vh-comp-header.vhh {background: rgba(108,99,255,.1); color: #a78bfa;}
.vh-comp-arrow-col {
  background: var(--surface2);
  border-left: 1px solid var(--border); border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
}
.vh-comp-arrow-header {
  padding: 13px 6px; border-bottom: 1px solid var(--border);
  font-size: .65rem; text-align: center; color: var(--faint); line-height: 1.5;
}
.vh-comp-row {
  padding: 11px 16px; border-bottom: 1px solid rgba(42,42,74,.4);
  display: flex; align-items: center; gap: 10px; font-size: .83rem; color: var(--text);
}
.vh-comp-row:last-child {border-bottom: none;}
.vh-comp-rank {
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: .7rem; font-weight: 700; flex-shrink: 0;
}
.vh-comp-row.trad .vh-comp-rank {background: rgba(100,116,139,.18); color: #94a3b8;}
.vh-comp-row.vhh .vh-comp-rank {background: rgba(108,99,255,.18); color: #a78bfa;}
.vh-comp-row.vhh-top .vh-comp-rank {background: rgba(34,197,94,.18); color: #22c55e;}
.vh-comp-row.vhh-last .vh-comp-rank {background: rgba(100,116,139,.14); color: #64748b;}
.vh-comp-exp {font-size: .69rem; color: var(--faint); margin-top: 1px;}
.vh-comp-arrow-row {
  padding: 11px 6px; border-bottom: 1px solid rgba(42,42,74,.4);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: .82rem;
}
.vh-comp-arrow-row:last-child {border-bottom: none;}
.arr-up {color: #22c55e;} .arr-dn {color: #ef4444;} .arr-eq {color: var(--faint);}
.vh-comp-callout {
  background: linear-gradient(135deg, rgba(108,99,255,.08), rgba(34,197,94,.06));
  border: 1px solid rgba(108,99,255,.2); border-radius: 12px;
  padding: 16px 20px; display: flex; align-items: flex-start; gap: 14px; margin-bottom: 32px;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-comp-callout-icon {font-size: 1.8rem; flex-shrink: 0; margin-top: 2px;}
.vh-comp-callout-text {font-size: .82rem; color: var(--text); line-height: 1.65;}

/* Results table */
.vh-tbl-wrap {
  background: var(--surface); border-radius: 16px;
  border: 1px solid var(--border); overflow: auto; margin-bottom: 36px;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-tbl-wrap table {width: 100%; border-collapse: collapse; min-width: 620px;}
.vh-tbl-wrap thead tr {background: var(--surface2); border-bottom: 1px solid var(--border);}
.vh-tbl-wrap th {
  padding: 13px 18px; text-align: left; font-size: .75rem; font-weight: 600;
  color: var(--muted); text-transform: uppercase; letter-spacing: .05em;
}
.vh-tbl-wrap td {
  padding: 13px 18px; border-bottom: 1px solid rgba(42,42,74,.5);
  font-size: .88rem; color: var(--text);
}
.vh-tbl-wrap tr:last-child td {border-bottom: none;}

/* Insights */
.vh-insights-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px; margin-bottom: 40px;
}
.vh-insight-card {
  background: var(--surface); border-radius: 14px; padding: 20px;
  border-left: 3px solid var(--primary); border-top: 1px solid var(--border);
  border-right: 1px solid var(--border); border-bottom: 1px solid var(--border);
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-insight-icon {font-size: 1.6rem; margin-bottom: 8px;}
.vh-insight-title {font-size: .85rem; font-weight: 600; color: var(--muted); margin-bottom: 4px;}
.vh-insight-val {font-size: 1.8rem; font-weight: 900; margin-bottom: 4px;}
.vh-insight-detail {font-size: .75rem; color: var(--muted); margin-bottom: 8px; line-height: 1.5;}
.vh-insight-rec {font-size: .73rem; color: var(--faint); font-style: italic; line-height: 1.5;}

/* Analytics */
.vh-analytics-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 18px; margin-bottom: 40px;
}
.vh-an-card {
  background: var(--surface); border-radius: 16px;
  border: 1px solid var(--border); padding: 22px;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-an-title {font-size: .85rem; font-weight: 600; color: var(--muted); margin-bottom: 14px;}
.vh-funnel-grid {display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;}
.vh-stat-box {background: var(--surface2); border-radius: 10px; padding: 14px; text-align: center;}
.vh-stat-num {
  font-size: 1.9rem; font-weight: 900;
  background: linear-gradient(135deg, var(--primary), var(--primary-l));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.vh-stat-lbl {
  font-size: .68rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: .06em; margin-top: 2px;
}

/* Scorer */
/* The vh-scorer-wrap div is a marker only — it cannot wrap Streamlit columns
   because st.markdown() calls are isolated. Card styling is applied instead
   to the stLayoutWrapper that immediately follows the marker element. */
.vh-scorer-wrap { display: none; }
[data-testid="stElementContainer"]:has(.vh-scorer-wrap) + [data-testid="stLayoutWrapper"] {
  background: var(--surface); border-radius: 16px;
  border: 1px solid var(--border); padding: 28px; margin-bottom: 36px;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-scorer-label {
  font-size: .8rem; font-weight: 600; color: var(--muted);
  text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px;
}
.vh-scorer-result {
  background: var(--surface2); border-radius: 12px;
  padding: 20px; border-left: 4px solid var(--primary);
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-dim-row {display: flex; align-items: center; gap: 10px; margin-bottom: 6px;}
.vh-dim-lbl {font-size: .72rem; color: var(--muted); width: 90px; flex-shrink: 0; text-align: right;}
.vh-dim-track {flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden;}
.vh-dim-fill {height: 100%; border-radius: 3px;}
.vh-dim-val {font-size: .75rem; font-weight: 700; min-width: 36px; text-align: right;}

/* ATS */
.vh-ats-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px; margin-bottom: 36px;
}
.vh-ats-card {
  background: var(--surface); border-radius: 16px;
  border: 1px solid var(--border); overflow: hidden;
  font-family: 'Inter', -apple-system, sans-serif;
}
.vh-ats-head {
  padding: 16px 20px; display: flex; align-items: center; gap: 12px;
  border-bottom: 1px solid var(--border);
}
.vh-ats-logo {font-size: 1.8rem;}
.vh-ats-info {flex: 1;}
.vh-ats-name {font-weight: 700; font-size: .95rem; color: var(--text);}
.vh-ats-event {font-size: .73rem; color: var(--muted); margin-top: 2px;}
.vh-ats-status {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--success); box-shadow: 0 0 6px var(--success);
}
.vh-ats-body {padding: 16px 20px;}
.vh-ats-webhook {
  font-size: .73rem; color: var(--faint); font-family: monospace;
  background: var(--surface2); padding: 6px 10px; border-radius: 6px;
  margin-bottom: 12px; word-break: break-all;
}
.vh-ats-result {
  margin-top: 12px; padding: 10px; background: var(--surface2);
  border-radius: 8px; font-size: .78rem;
}
.vh-ats-log-wrap {
  background: var(--surface); border-radius: 16px; border: 1px solid var(--border);
  margin-bottom: 36px; overflow: hidden; font-family: 'Inter', -apple-system, sans-serif;
}
.vh-ats-log-head {
  padding: 14px 20px; background: var(--surface2); border-bottom: 1px solid var(--border);
  font-size: .85rem; font-weight: 600;
}
.vh-ats-log-row {
  display: grid; grid-template-columns: 1fr 1.2fr .8fr .8fr .8fr;
  gap: 12px; padding: 12px 20px; border-bottom: 1px solid rgba(42,42,74,.4);
  font-size: .8rem; align-items: center;
}
.vh-ats-log-header {
  background: var(--surface2); font-weight: 600; font-size: .72rem;
  color: var(--muted); text-transform: uppercase; letter-spacing: .05em;
}
/* Score ring for scorer section */
.vh-score-ring-wrap {display: flex; align-items: center; gap: 20px; margin-bottom: 16px;}
.vh-score-ring-info .name {font-size: 1.05rem; font-weight: 700; margin-bottom: 4px;}
.vh-score-ring-info .tier {font-size: .8rem; color: var(--muted);}
.vh-score-ring-info .action {font-size: .82rem; margin-top: 6px; font-weight: 600;}

/* Scrollbar */
::-webkit-scrollbar {width: 5px; height: 5px;}
::-webkit-scrollbar-track {background: var(--bg);}
::-webkit-scrollbar-thumb {background: var(--border); border-radius: 3px;}

/* Streamlit button overrides — primary (action) buttons */
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #6c63ff, #a78bfa) !important;
  color: #fff !important;
  border: none !important;
  padding: 14px 52px !important;
  border-radius: 12px !important;
  font-size: 1.05rem !important;
  font-weight: 700 !important;
  box-shadow: 0 0 32px rgba(108,99,255,.45) !important;
  transition: all .2s !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
}
.stButton > button[data-testid="baseButton-primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 0 55px rgba(108,99,255,.65) !important;
  background: linear-gradient(135deg, #6c63ff, #a78bfa) !important;
  color: #fff !important;
}
.stButton > button[data-testid="baseButton-primary"]:disabled {
  opacity: .55 !important; cursor: not-allowed !important; transform: none !important;
}
/* Streamlit button overrides — secondary (sample/utility) buttons */
.stButton > button[data-testid="baseButton-secondary"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  color: var(--muted) !important;
  font-size: .78rem !important;
  font-weight: 600 !important;
  padding: 7px 14px !important;
  box-shadow: none !important;
  border-radius: 6px !important;
  transition: border-color .2s, color .2s !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
}
.stButton > button[data-testid="baseButton-secondary"]:hover {
  border-color: var(--primary) !important;
  color: var(--primary) !important;
}

/* Streamlit expander override */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}
[data-testid="stExpander"] summary {color: var(--text) !important;}

/* Streamlit tabs override */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface2) !important;
  border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {color: var(--muted) !important; background: transparent !important;}
.stTabs [aria-selected="true"] {
  color: var(--primary) !important;
  border-bottom: 2px solid var(--primary) !important;
}
.stTabs [data-baseweb="tab-panel"] {background: var(--surface) !important; padding: 14px !important;}
.stTextArea textarea {
  background: var(--surface2) !important; border: 1px solid var(--border) !important;
  color: var(--muted) !important; font-size: .82rem !important; border-radius: 8px !important;
}
.stTextInput input {
  background: var(--surface2) !important; border: 1px solid var(--border) !important;
  color: var(--muted) !important; border-radius: 8px !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
  background: linear-gradient(135deg, #6c63ff, #a78bfa) !important;
}

/* Button wrapper: make Streamlit column internals inherit the hero gradient */
.vh-btn-wrap [data-testid="stHorizontalBlock"],
.vh-btn-wrap [data-testid="stColumn"],
.vh-btn-wrap [data-testid="stVerticalBlock"],
.vh-btn-wrap > div,
.vh-btn-wrap > div > div {
  background: transparent !important;
}
/* Single-line button text */
.vh-btn-wrap .stButton > button[data-testid="baseButton-primary"] {
  white-space: nowrap !important;
  padding: 14px 36px !important;
}

/* Mobile */
@media(max-width:720px){
  .vh-hero{padding:36px 16px 32px;}
  .vh-logo{font-size:2rem;}
  .vh-tagline{font-size:.9rem;}
  .vh-container{padding:24px 14px;}
  .vh-pipe-flow{flex-direction:column;align-items:flex-start;gap:8px;padding:16px;}
  .vh-pipe-divider{width:100%;height:1px;margin:8px 0;}
  .vh-comparison-outer{grid-template-columns:1fr;}
  .vh-comp-arrow-col{display:none;}
}
</style>
""", unsafe_allow_html=True)


# -- Agent imports (cached so they only load once) ----------------------------
@st.cache_resource(show_spinner="Loading AI agents…")
def _load_agents():
    from agent_1 import analyze_profile
    from agent_2 import match_candidate
    from agent_3 import generate_outreach
    return analyze_profile, match_candidate, generate_outreach


analyze_profile, match_candidate, generate_outreach = _load_agents()

# -- ATS integration helpers (optional) --------------------------------------
try:
    from shared.ats_integrations import normalise as _ats_normalise, get_mock_payload as _get_mock_payload
    _ATS_ENABLED = True
except Exception:
    _ATS_ENABLED = False

    def _ats_normalise(*a, **kw):  # noqa: E302
        return None

    def _get_mock_payload(*a, **kw):  # noqa: E302
        return {}

# -- LinkedIn profile fetcher (optional) -------------------------------------
try:
    from profile_fetcher import fetch_linkedin_profile as _fetch_linkedin_profile
    _PROFILE_FETCHER_ENABLED = True
except Exception:
    _PROFILE_FETCHER_ENABLED = False

    def _fetch_linkedin_profile(url: str) -> dict:  # noqa: E302
        return {"success": False, "profile_text": "", "error": "profile_fetcher not available"}

# -- Demo data ----------------------------------------------------------------
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

# Traditional ATS baseline (rank by years of experience)
_TRAD_DATA = {
    "Marcus Rivera":  {"trad_rank": 4, "exp": "3 yr exp · AI startup"},
    "Priya Sharma":   {"trad_rank": 2, "exp": "5 yr exp · ML/DeepMind"},
    "Alex Chen":      {"trad_rank": 3, "exp": "4 yr exp · Full-Stack"},
    "Jordan Kim":     {"trad_rank": 1, "exp": "8 yr exp · Java/Banking"},
    "Elena Voronova": {"trad_rank": 5, "exp": "6 mo exp · Bootcamp grad"},
}

_AGENT_TIMEOUT_SECS = 30
_STAGE_ANIM_DELAY_SECS = 0.35  # pause per stage so animation is visible in mock mode

# -- Colour helpers -----------------------------------------------------------
_TIER_COLOURS = {
    "PRIORITY": "#22c55e",
    "STANDARD": "#6c63ff",
    "NURTURE": "#f59e0b",
    "ARCHIVE": "#94a3b8",
}
_TIER_CLS = {
    "PRIORITY": "vh-tP",
    "STANDARD": "vh-tS",
    "NURTURE": "vh-tN",
    "ARCHIVE": "vh-tA",
}


def _score_colour(score: int) -> str:
    return "#22c55e" if score >= 70 else "#f59e0b" if score >= 55 else "#94a3b8"


def _sbar(score: int, colour: str) -> str:
    pct = max(0, min(100, score))
    return (
        f'<div class="vh-sbar">'
        f'<div class="vh-sbar-track"><div class="vh-sbar-fill" '
        f'style="width:{pct}%;background:{colour}"></div></div>'
        f'<span class="vh-sbar-val" style="color:{colour}">{score}</span>'
        f'</div>'
    )


def _tier_badge(tier: str) -> str:
    cls = _TIER_CLS.get(tier, "vh-tA")
    return f'<span class="vh-tier-badge {cls}">{tier}</span>'


# -- Pipeline execution -------------------------------------------------------
def _call_with_timeout(fn, timeout, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(fn, *args, **kwargs)
        return fut.result(timeout=timeout)


def _render_candidate_grid(states: List[Dict]) -> str:
    """Render the 5-column candidate grid HTML given per-candidate state."""
    cards = []
    for cand, state in zip(DEMO_CANDIDATES, states):
        stage = state.get("stage", "waiting")
        adapt_score = state.get("adapt_score")
        match_score = state.get("match_score")
        outreach_tier = state.get("outreach_tier")

        stage_labels = {
            "waiting": "<span style='color:var(--faint)'>Waiting to start…</span>",
            "agent1":  "<span style='color:var(--primary)'>\U0001f50d Analysing profile…</span>",
            "agent2":  "<span style='color:var(--primary)'>\U0001f3af Matching job…</span>",
            "agent3":  "<span style='color:var(--primary)'>\U0001f4e7 Generating outreach…</span>",
            "done":    "<span style='color:#22c55e'>✅ Complete</span>",
        }
        stage_lbl = stage_labels.get(stage, "")

        card_extra = ""
        if stage == "done":
            card_extra = " done"
        elif stage in ("agent1", "agent2", "agent3"):
            card_extra = " active"

        dot_states = {
            "waiting": [0, 0, 0], "agent1": [1, 0, 0],
            "agent2": [2, 1, 0], "agent3": [2, 2, 1], "done": [2, 2, 2],
        }
        dots_data = dot_states.get(stage, [0, 0, 0])
        dots_html = ""
        for ds in dots_data:
            cls = ""
            if ds == 1:
                cls = " active"
            elif ds == 2:
                cls = " done"
            dots_html += f'<div class="vh-sdot{cls}"></div>'

        scores_html = ""
        if adapt_score is not None:
            ac = _score_colour(adapt_score)
            scores_html += (
                f'<div class="vh-score-row">'
                f'<span class="vh-score-lbl">Adaptability</span>'
                f'<span class="vh-score-val" style="color:{ac}">{adapt_score}/100</span>'
                f'</div>'
            )
        if match_score is not None:
            mc = _score_colour(match_score)
            scores_html += (
                f'<div class="vh-score-row">'
                f'<span class="vh-score-lbl">Job Match</span>'
                f'<span class="vh-score-val" style="color:{mc}">{match_score}/100</span>'
                f'</div>'
            )
        if outreach_tier:
            scores_html += (
                f'<div class="vh-score-row" style="margin-top:6px">'
                f'{_tier_badge(outreach_tier)}'
                f'</div>'
            )

        cards.append(
            f'<div class="vh-c-card{card_extra}">'
            f'<div class="vh-c-emoji">{cand["emoji"]}</div>'
            f'<div class="vh-c-name">{cand["name"]}</div>'
            f'<div class="vh-c-stage">{stage_lbl}</div>'
            f'<div class="vh-stage-dots">{dots_html}</div>'
            f'<div class="vh-c-scores">{scores_html}</div>'
            f'</div>'
        )

    return f'<div class="vh-candidates-grid">{"".join(cards)}</div>'


def run_pipeline(grid_placeholder, progress_bar, status_text) -> List[Dict[str, Any]]:
    """Run all 3 agents for all 5 demo candidates, updating the grid live."""
    results = []
    total = len(DEMO_CANDIDATES)
    states = [{"stage": "waiting"} for _ in DEMO_CANDIDATES]

    # Ensure waiting state is visible before processing starts (important on re-runs)
    grid_placeholder.markdown(_render_candidate_grid(states), unsafe_allow_html=True)

    for idx, cand in enumerate(DEMO_CANDIDATES):
        name = cand["name"]
        profile = cand["profile"]

        # Agent 1
        states[idx]["stage"] = "agent1"
        grid_placeholder.markdown(_render_candidate_grid(states), unsafe_allow_html=True)
        status_text.markdown(
            f"<span style='color:var(--primary)'>"
            f"**{cand['emoji']} {name}** — \U0001f52c Agent 1: Analysing adaptability…</span>",
            unsafe_allow_html=True,
        )
        time.sleep(_STAGE_ANIM_DELAY_SECS)
        try:
            a1 = _call_with_timeout(analyze_profile, _AGENT_TIMEOUT_SECS, profile)
        except concurrent.futures.TimeoutError:
            a1 = {"adaptability_score": 50, "tier": "Standard",
                  "recommend_interview": False, "reasoning": "Timeout", "score_breakdown": {}}
        adapt_score = int(a1.get("adaptability_score") or 50)
        adapt_tier = a1.get("tier") or "Standard"
        states[idx]["adapt_score"] = adapt_score

        # Agent 2
        states[idx]["stage"] = "agent2"
        grid_placeholder.markdown(_render_candidate_grid(states), unsafe_allow_html=True)
        status_text.markdown(
            f"<span style='color:var(--primary)'>"
            f"**{cand['emoji']} {name}** — \U0001f3af Agent 2: Matching to job…</span>",
            unsafe_allow_html=True,
        )
        time.sleep(_STAGE_ANIM_DELAY_SECS)
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
        states[idx]["match_score"] = match_score

        # Agent 3
        states[idx]["stage"] = "agent3"
        grid_placeholder.markdown(_render_candidate_grid(states), unsafe_allow_html=True)
        status_text.markdown(
            f"<span style='color:var(--primary)'>"
            f"**{cand['emoji']} {name}** — \u2709\ufe0f Agent 3: Generating outreach…</span>",
            unsafe_allow_html=True,
        )
        time.sleep(_STAGE_ANIM_DELAY_SECS)
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
                      "email": {"subject": "Opportunity at VelocityHire", "body": "We'd love to connect."},
                      "followup": {"subject": "", "body": ""},
                      "recruiter_note": f"Timeout — manual review recommended for {name}"}}

        outreach_tier = a3.get("outreach_tier") or "ARCHIVE"
        campaign = a3.get("campaign") or {}

        states[idx]["stage"] = "done"
        states[idx]["outreach_tier"] = outreach_tier
        grid_placeholder.markdown(_render_candidate_grid(states), unsafe_allow_html=True)

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


# -- HTML fragments -----------------------------------------------------------

_HERO_HTML = """
<div class="vh-hero">
  <div style="position:relative;z-index:1">
    <div class="vh-logo">⚡ VelocityHire</div>
    <div class="vh-tagline">AI-Powered Recruitment Intelligence · Complete.dev Hackathon Demo</div>
    <div class="vh-sub">
      Identify the candidates with the highest <em>learning velocity</em> — not just years of experience
    </div>
    <div class="vh-badges">
      <span class="vh-badge">🤖 3 LangGraph Agents</span>
      <span class="vh-badge">⚡ Real-time Pipeline</span>
      <span class="vh-badge">🏢 Multi-tenant</span>
      <span class="vh-badge">📊 Analytics Dashboard</span>
      <span class="vh-badge">🎯 Adaptive Scoring</span>
      <span class="vh-badge">📧 Auto Outreach Gen</span>
      <span class="vh-badge">💾 SQLite Persistence</span>
    </div>
  </div>
</div>
"""

_INNOVATION_HTML = """
<div class="vh-innovation-grid">
  <div class="vh-inno-card" style="border-left:3px solid #6c63ff">
    <div style="font-size:1.5rem;margin-bottom:8px">🎯</div>
    <div class="vh-inno-title">Learning Velocity, Not Credentials</div>
    <div class="vh-inno-desc">
      A bootcamp grad who won 2 hackathons last month and shipped an LLM tool used by 500 people
      scores <strong style="color:#22c55e">higher</strong> than a 10-year Java developer with no recent activity.
    </div>
  </div>
  <div class="vh-inno-card" style="border-left:3px solid #22c55e">
    <div style="font-size:1.5rem;margin-bottom:8px">🤖</div>
    <div class="vh-inno-title">3 LangGraph Agents in Sequence</div>
    <div class="vh-inno-desc">
      Profile Analyzer → Job Matcher → Outreach Coordinator. Each is a separate
      <strong style="color:#a78bfa">StateGraph</strong> with typed state, conditional edges, and
      shared SQLite memory across all agents.
    </div>
  </div>
  <div class="vh-inno-card" style="border-left:3px solid #f59e0b">
    <div style="font-size:1.5rem;margin-bottom:8px">🏢</div>
    <div class="vh-inno-title">Enterprise-Ready from Day One</div>
    <div class="vh-inno-desc">
      Multi-tenant data isolation, ATS webhooks (Greenhouse · Lever · BambooHR),
      hiring outcome tracking, and predictive analytics — all included.
    </div>
  </div>
</div>
"""

_PIPELINE_HTML = """
<div class="vh-pipe-flow">
  <div class="vh-pipe-step">
    <div class="vh-pipe-icon">🔍</div>
    <div class="vh-pipe-label">Agent 1</div>
    <div class="vh-pipe-sub">Profile Analyzer</div>
  </div>
  <div class="vh-pipe-arrow">→</div>
  <div class="vh-pipe-step">
    <div class="vh-pipe-icon">🎯</div>
    <div class="vh-pipe-label">Agent 2</div>
    <div class="vh-pipe-sub">Job Matcher</div>
  </div>
  <div class="vh-pipe-arrow">→</div>
  <div class="vh-pipe-step">
    <div class="vh-pipe-icon">📧</div>
    <div class="vh-pipe-label">Agent 3</div>
    <div class="vh-pipe-sub">Outreach Gen</div>
  </div>
  <div class="vh-pipe-arrow">→</div>
  <div class="vh-pipe-step">
    <div class="vh-pipe-icon">✅</div>
    <div class="vh-pipe-label">Complete</div>
    <div class="vh-pipe-sub">Campaign Ready</div>
  </div>
  <div class="vh-pipe-divider"></div>
  <div class="vh-pipe-meta">
    <div class="vh-pipe-meta-title">Scoring Weights</div>
    <div class="vh-pipe-weights">
      <div class="vh-pw">🏆 Hackathons <span>40%</span></div>
      <div class="vh-pw">⚡ Skills <span>25%</span></div>
      <div class="vh-pw">📚 Certs <span>20%</span></div>
      <div class="vh-pw">🕐 Recency <span>15%</span></div>
    </div>
  </div>
  <div class="vh-pipe-divider"></div>
  <div class="vh-pipe-meta">
    <div class="vh-pipe-meta-title">Demo Role</div>
    <div class="vh-pipe-meta-val">Senior AI Engineer</div>
    <div class="vh-pipe-meta-sub">VelocityHire · 5 Candidates</div>
  </div>
</div>
"""

_ATS_HTML = """
<div class="vh-section-title" style="margin-top:8px">
  <span class="vh-dot" style="background:#22c55e"></span>
  Enterprise ATS Integrations
  <span style="font-size:.78rem;color:var(--muted);font-weight:400">
    — click Test to fire a live mock webhook
  </span>
</div>
"""

_FOOTER_HTML = """
<div style="text-align:center;padding:32px 0 24px;border-top:1px solid var(--border);
            font-family:'Inter',-apple-system,sans-serif;">
  <p style="color:#64748b;font-size:.8rem;margin:0">
    ⚡ VelocityHire · Complete.dev Hackathon 2026 · Built with LangGraph ·
    <a href="https://velocityhire-868513859116.us-central1.run.app/" target="_blank"
       style="color:#a78bfa;text-decoration:none;">Primary Demo (Cloud Run)</a>
  </p>
</div>
"""


def _build_comparison_html(sorted_results: List[Dict]) -> str:
    trad_sorted = sorted(
        sorted_results,
        key=lambda r: _TRAD_DATA.get(r["name"], {}).get("trad_rank", 3)
    )
    trad_rows = "".join(
        f'<div class="vh-comp-row trad">'
        f'<div class="vh-comp-rank">{i + 1}</div>'
        f'<div style="flex:1;min-width:0">'
        f'<div style="font-weight:600">{r["emoji"]} {r["name"]}</div>'
        f'<div class="vh-comp-exp">{_TRAD_DATA.get(r["name"], {}).get("exp", "")}</div>'
        f'</div></div>'
        for i, r in enumerate(trad_sorted)
    )

    vh_rows = ""
    for i, r in enumerate(sorted_results):
        sc = r.get("match_score", 0)
        sc_color = _score_colour(sc)
        row_cls = "vhh vhh-top" if i == 0 else (
            "vhh vhh-last" if i == len(sorted_results) - 1 else "vhh"
        )
        vh_rows += (
            f'<div class="vh-comp-row {row_cls}">'
            f'<div class="vh-comp-rank">{i + 1}</div>'
            f'<div style="flex:1;min-width:0">'
            f'<div style="font-weight:600">{r["emoji"]} {r["name"]}</div>'
            f'<div class="vh-comp-exp" style="color:{sc_color}">{sc}/100 · {r.get("outreach_tier", "")}</div>'
            f'</div></div>'
        )

    arrow_rows = ""
    for i, r in enumerate(sorted_results):
        trad_rank = _TRAD_DATA.get(r["name"], {}).get("trad_rank", i + 1)
        delta = trad_rank - (i + 1)
        if delta > 0:
            arrow_html = f'<span class="arr-up">↑{delta}</span>'
        elif delta < 0:
            arrow_html = f'<span class="arr-dn">↓{abs(delta)}</span>'
        else:
            arrow_html = '<span class="arr-eq">→</span>'
        arrow_rows += f'<div class="vh-comp-arrow-row">{arrow_html}</div>'

    elena_rank = next((i + 1 for i, r in enumerate(sorted_results) if r["name"] == "Elena Voronova"), 5)
    jordan_rank = next((i + 1 for i, r in enumerate(sorted_results) if r["name"] == "Jordan Kim"), 5)

    comparison = (
        f'<div class="vh-comparison-outer">'
        f'<div class="vh-comp-col">'
        f'<div class="vh-comp-header trad">❌ Traditional ATS<br>'
        f'<span style="font-weight:400;font-size:.68rem">Ranked by years of experience</span></div>'
        f'{trad_rows}</div>'
        f'<div class="vh-comp-arrow-col">'
        f'<div class="vh-comp-arrow-header">Rank<br>shift</div>'
        f'{arrow_rows}</div>'
        f'<div class="vh-comp-col">'
        f'<div class="vh-comp-header vhh">✅ VelocityHire AI<br>'
        f'<span style="font-weight:400;font-size:.68rem">Ranked by learning velocity</span></div>'
        f'{vh_rows}</div></div>'
    )

    callout = (
        f'<div class="vh-comp-callout">'
        f'<div class="vh-comp-callout-icon">💡</div>'
        f'<div class="vh-comp-callout-text">'
        f'<strong>The key insight:</strong> '
        f'<span style="color:#22c55e;font-weight:700"> Elena Voronova</span> — bootcamp grad, '
        f'<span style="color:#22c55e;font-weight:700">6 months experience</span> — ranks '
        f'<span style="color:#22c55e;font-weight:700">#{elena_rank} by learning velocity.</span> '
        f'<span style="color:#ef4444;font-weight:700"> Jordan Kim</span> — '
        f'<span style="color:#ef4444;font-weight:700">8 years Java experience</span> — '
        f'ranks <span style="color:#ef4444;font-weight:700">#{jordan_rank}.</span> '
        f'Traditional ATS shortlists Jordan and auto-rejects Elena. '
        f'VelocityHire sees who is <em>actually learning the fastest</em> — '
        f'and that is the only signal that matters for AI-first hiring.'
        f'</div></div>'
    )

    return comparison + callout


def _build_results_table_html(sorted_results: List[Dict]) -> str:
    rows = ""
    for i, r in enumerate(sorted_results):
        a = r.get("adaptability_score", 0)
        m = r.get("match_score", 0)
        tier = r.get("outreach_tier", "ARCHIVE")
        ac = _score_colour(a)
        mc = _score_colour(m)
        rec = "✅ Interview" if tier in ("PRIORITY", "STANDARD") else "📋 Pipeline"
        rec_color = "#22c55e" if tier in ("PRIORITY", "STANDARD") else "#94a3b8"
        rows += (
            f'<tr>'
            f'<td style="color:var(--faint);font-size:.8rem">#{i + 1}</td>'
            f'<td><span style="font-size:1.1rem;margin-right:8px">{r["emoji"]}</span>'
            f'<strong>{r["name"]}</strong></td>'
            f'<td>{_sbar(a, ac)}</td>'
            f'<td>{_sbar(m, mc)}</td>'
            f'<td>{_tier_badge(tier)}</td>'
            f'<td style="color:{rec_color}">{rec}</td>'
            f'</tr>'
        )
    return (
        f'<div class="vh-tbl-wrap">'
        f'<table><thead><tr>'
        f'<th>#</th><th>Candidate</th><th>Adaptability</th>'
        f'<th>Job Match</th><th>Outreach Tier</th><th>Action</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _build_insights_html(results: List[Dict]) -> str:
    if not results:
        return ""
    sorted_r = sorted(results, key=lambda r: r.get("match_score", 0), reverse=True)
    top = sorted_r[0]
    priority_count = sum(1 for r in results if r.get("outreach_tier") == "PRIORITY")
    avg_adapt = int(sum(r.get("adaptability_score", 0) for r in results) / len(results))
    recommend_count = sum(1 for r in results if r.get("recommend"))

    insights = [
        {
            "icon": "🏆", "color": "#22c55e",
            "title": "Top Candidate",
            "value": top["name"],
            "detail": f'Score: {top.get("match_score", 0)}/100 · {top.get("outreach_tier", "")}',
            "rec": "Fast-track to hiring manager — high velocity signal.",
        },
        {
            "icon": "⚡", "color": "#6c63ff",
            "title": "Priority Candidates",
            "value": str(priority_count),
            "detail": f'{priority_count} of {len(results)} candidates ready for same-day outreach.',
            "rec": "Send PRIORITY LinkedIn messages within 24 hours.",
        },
        {
            "icon": "📈", "color": "#a78bfa",
            "title": "Avg Adaptability",
            "value": f"{avg_adapt}/100",
            "detail": f'Pipeline average across all {len(results)} candidates.',
            "rec": "Candidates above 70 are recommended for interview.",
        },
        {
            "icon": "✅", "color": "#f59e0b",
            "title": "Interview Recommendations",
            "value": str(recommend_count),
            "detail": f'{recommend_count} candidates flagged for interview pipeline.',
            "rec": "Begin scheduling within 48 hours for best conversion.",
        },
    ]

    cards = "".join(
        f'<div class="vh-insight-card" style="border-left-color:{ins["color"]}">'
        f'<div class="vh-insight-icon">{ins["icon"]}</div>'
        f'<div class="vh-insight-title">{ins["title"]}</div>'
        f'<div class="vh-insight-val" style="color:{ins["color"]}">{ins["value"]}</div>'
        f'<div class="vh-insight-detail">{ins["detail"]}</div>'
        f'<div class="vh-insight-rec">{ins["rec"]}</div>'
        f'</div>'
        for ins in insights
    )
    return f'<div class="vh-insights-grid">{cards}</div>'


def _build_analytics_html(results: List[Dict]) -> str:
    if not results:
        return ""
    priority = sum(1 for r in results if r.get("outreach_tier") == "PRIORITY")
    standard = sum(1 for r in results if r.get("outreach_tier") == "STANDARD")
    nurture = sum(1 for r in results if r.get("outreach_tier") == "NURTURE")
    archive = sum(1 for r in results if r.get("outreach_tier") == "ARCHIVE")

    funnel_items = [
        (len(results), "Profiles Analysed"),
        (len(results), "Jobs Matched"),
        (priority + standard, "Campaigns Sent"),
        (priority, "Priority Candidates"),
    ]
    funnel_html = "".join(
        f'<div class="vh-stat-box">'
        f'<div class="vh-stat-num">{n}</div>'
        f'<div class="vh-stat-lbl">{lbl}</div>'
        f'</div>'
        for n, lbl in funnel_items
    )

    tier_rows = [
        (priority, "PRIORITY", "#22c55e", "vh-tP"),
        (standard, "STANDARD", "#6c63ff", "vh-tS"),
        (nurture, "NURTURE", "#f59e0b", "vh-tN"),
        (archive, "ARCHIVE", "#94a3b8", "vh-tA"),
    ]
    tier_bars = ""
    for count, label, color, cls in tier_rows:
        pct = int((count / len(results)) * 100) if results else 0
        tier_bars += (
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
            f'<span class="vh-tier-badge {cls}" style="min-width:80px;text-align:center">{label}</span>'
            f'<div style="flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden">'
            f'<div style="width:{pct}%;height:8px;background:{color};border-radius:4px"></div></div>'
            f'<span style="font-size:.82rem;font-weight:700;color:{color};min-width:16px">{count}</span>'
            f'</div>'
        )

    adapt_scores = [r.get("adaptability_score", 0) for r in results]
    high = sum(1 for s in adapt_scores if s >= 70)
    mid = sum(1 for s in adapt_scores if 55 <= s < 70)
    low = sum(1 for s in adapt_scores if s < 55)
    dist_bars = ""
    for count, label, color in [
        (high, "High (70+)", "#22c55e"),
        (mid, "Mid (55—69)", "#f59e0b"),
        (low, "Low (<55)", "#94a3b8"),
    ]:
        pct = int((count / len(results)) * 100) if results else 0
        dist_bars += (
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
            f'<span style="font-size:.75rem;color:var(--muted);width:80px;flex-shrink:0">{label}</span>'
            f'<div style="flex:1;height:8px;background:var(--border);border-radius:4px;overflow:hidden">'
            f'<div style="width:{pct}%;height:8px;background:{color};border-radius:4px"></div></div>'
            f'<span style="font-size:.82rem;font-weight:700;color:{color};min-width:16px">{count}</span>'
            f'</div>'
        )

    return (
        f'<div class="vh-analytics-grid">'
        f'<div class="vh-an-card">'
        f'<div class="vh-an-title">📊 Pipeline Funnel</div>'
        f'<div class="vh-funnel-grid">{funnel_html}</div>'
        f'</div>'
        f'<div class="vh-an-card">'
        f'<div class="vh-an-title">🏷️ Outreach Tier Breakdown</div>'
        f'{tier_bars}'
        f'</div>'
        f'<div class="vh-an-card">'
        f'<div class="vh-an-title">📈 Adaptability Score Distribution</div>'
        f'{dist_bars}'
        f'</div>'
        f'</div>'
    )


# -- UI -----------------------------------------------------------------------

# Hero
st.markdown(_HERO_HTML, unsafe_allow_html=True)

# Run button (continues the hero gradient visually)
st.markdown('<div class="vh-btn-wrap">', unsafe_allow_html=True)
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    run_clicked = st.button("▶  Run Full Pipeline Demo", use_container_width=True, type="primary")
st.markdown('</div>', unsafe_allow_html=True)

# Main container
st.markdown('<div class="vh-container">', unsafe_allow_html=True)

# Innovation panel
st.markdown(_INNOVATION_HTML, unsafe_allow_html=True)

# Pipeline diagram
st.markdown(_PIPELINE_HTML, unsafe_allow_html=True)

# Job description expander
with st.expander("\U0001f4cb Target Role — Senior AI Engineer @ VelocityHire", expanded=False):
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(
            f'<span style="font-size:.88rem;color:var(--muted);line-height:1.6">'
            f'<strong style="color:var(--text)">Description:</strong> {DEMO_JOB["job_description"]}'
            f'</span>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            '<strong style="color:var(--text)">Required Skills:</strong><br>'
            f'<span style="font-size:.85rem;color:var(--muted)">'
            f'{", ".join(DEMO_JOB["required_skills"])}</span>',
            unsafe_allow_html=True,
        )

# Candidate pipeline section title
st.markdown(
    '<div class="vh-section-title" style="margin-top:24px">'
    '<span class="vh-dot"></span>Candidate Pipeline</div>',
    unsafe_allow_html=True,
)

# Candidate grid placeholder (live-updates during pipeline run)
grid_placeholder = st.empty()

if "results" not in st.session_state:
    initial_states = [{"stage": "waiting"} for _ in DEMO_CANDIDATES]
    grid_placeholder.markdown(_render_candidate_grid(initial_states), unsafe_allow_html=True)

# -- Pipeline execution -------------------------------------------------------
if run_clicked:
    st.session_state.pop("results", None)

if "results" not in st.session_state and run_clicked:
    progress_bar = st.progress(0)
    status_text = st.empty()
    # Scroll to the candidate grid so the per-stage animation is visible
    st.html(
        "<script>setTimeout(function(){"
        "var el=document.querySelector('.vh-candidates-grid');"
        "if(el)el.scrollIntoView({behavior:'smooth',block:'start'});"
        "},100);</script>",
        unsafe_allow_javascript=True,
    )
    with st.spinner("Running LangGraph pipeline…"):
        st.session_state["results"] = run_pipeline(grid_placeholder, progress_bar, status_text)
    status_text.empty()
    progress_bar.empty()
    st.success("✅ Pipeline complete — all 5 candidates processed")

# -- Results ------------------------------------------------------------------
if "results" in st.session_state:
    results: List[Dict] = st.session_state["results"]
    sorted_results = sorted(results, key=lambda r: r.get("match_score", 0), reverse=True)

    # Show final done-state grid
    done_states = [
        {
            "stage": "done",
            "adapt_score": r["adaptability_score"],
            "match_score": r["match_score"],
            "outreach_tier": r["outreach_tier"],
        }
        for r in results
    ]
    grid_placeholder.markdown(_render_candidate_grid(done_states), unsafe_allow_html=True)

    # Ranking Flip comparison
    st.markdown(
        '<div class="vh-section-title">'
        '<span class="vh-dot" style="background:#ef4444"></span>'
        'The Ranking Flip'
        '<span style="font-size:.78rem;color:var(--muted);font-weight:400"> '
        '— traditional ATS (experience) vs VelocityHire (learning velocity)</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_build_comparison_html(sorted_results), unsafe_allow_html=True)

    # Results table
    st.markdown(
        '<div class="vh-section-title">'
        '<span class="vh-dot" style="background:#22c55e"></span>'
        'Pipeline Results — Ranked by Score</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_build_results_table_html(sorted_results), unsafe_allow_html=True)

    # Outreach campaigns
    priority_standard = [r for r in sorted_results if r.get("outreach_tier") in ("PRIORITY", "STANDARD")]
    st.markdown(
        '<div class="vh-section-title">'
        '<span class="vh-dot" style="background:#f5a623"></span>'
        'Generated Outreach Campaigns'
        '<span style="font-size:.8rem;color:var(--muted);font-weight:400"> (PRIORITY &amp; STANDARD)</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    if priority_standard:
        cols = st.columns(min(len(priority_standard), 2))
        for i, r in enumerate(priority_standard):
            with cols[i % 2]:
                st.markdown(
                    f'<div class="vh-oc">'
                    f'<div class="vh-oc-head">'
                    f'<div><span style="font-size:1.1rem;margin-right:7px">{r["emoji"]}</span>'
                    f'<span style="font-weight:700;font-size:.92rem;color:var(--text)">{r["name"]}</span></div>'
                    f'{_tier_badge(r.get("outreach_tier", "ARCHIVE"))}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                tab1, tab2, tab3, tab4 = st.tabs(["LinkedIn", "Email", "Follow-up", "ATS Note"])
                with tab1:
                    st.text_area(
                        "LinkedIn Message", value=r.get("linkedin_message", ""),
                        height=140, disabled=True, key=f"li_{r['name']}",
                    )
                with tab2:
                    st.text_input(
                        "Subject", value=r.get("email_subject", ""),
                        disabled=True, key=f"es_{r['name']}",
                    )
                    st.text_area(
                        "Body", value=r.get("email_body", ""),
                        height=160, disabled=True, key=f"eb_{r['name']}",
                    )
                with tab3:
                    st.text_input(
                        "Subject", value=r.get("followup_subject", ""),
                        disabled=True, key=f"fs_{r['name']}",
                    )
                    st.text_area(
                        "Body", value=r.get("followup_body", ""),
                        height=120, disabled=True, key=f"fb_{r['name']}",
                    )
                with tab4:
                    st.text_area(
                        "ATS Note", value=r.get("recruiter_note", ""),
                        height=120, disabled=True, key=f"rn_{r['name']}",
                    )
    else:
        st.markdown(
            '<p style="color:var(--muted);font-size:.88rem">No PRIORITY or STANDARD candidates generated.</p>',
            unsafe_allow_html=True,
        )

    # Predictive Insights
    st.markdown(
        '<div class="vh-section-title" style="margin-top:8px">'
        '<span class="vh-dot" style="background:#a78bfa"></span>'
        'Predictive Insights</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_build_insights_html(results), unsafe_allow_html=True)

    # Analytics
    st.markdown(
        '<div class="vh-section-title">'
        '<span class="vh-dot" style="background:#6c63ff"></span>'
        'Pipeline Analytics</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_build_analytics_html(results), unsafe_allow_html=True)

# -- Live scorer --------------------------------------------------------------
st.markdown(
    '<div class="vh-section-title" style="margin-top:8px">'
    '<span class="vh-dot" style="background:#a78bfa"></span>'
    'Try Your Own Candidate'
    '<span style="font-size:.78rem;color:var(--muted);font-weight:400"> '
    '— paste any profile, score through all 3 agents live</span>'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="vh-scorer-wrap">', unsafe_allow_html=True)

col_in, col_out = st.columns(2)

_SAMPLES = {
    "high": (
        "Kenji Watanabe — AI Engineer\n"
        "Skills: Python, LangGraph, LangChain, FastAPI, React, AWS, Rust, Svelte\n"
        "Experience:\n  - NeuralStack startup (2022-present): Lead AI engineer.\n"
        "  - SeedCo (2020-2022): Founding engineer, shipped 3 products.\n"
        "Hackathons:\n  - Global AI Hack (3 weeks ago) — WINNER, best LLM integration.\n"
        "  - Junction Helsinki (2 months ago) — WINNER, led team of 4.\n"
        "Certifications:\n  - AWS Certified ML Specialty (1 month ago)\n"
        "GitHub: 72 commits last month. LangGraph OSS contributor."
    ),
    "mid": (
        "Fatima Al-Hassan — Full Stack Developer\n"
        "Skills: React, Node.js, Python, PostgreSQL, Docker, GCP\n"
        "Experience:\n  - TechCorp (2021-present): Senior developer.\n"
        "Hackathons:\n  - Local Startup Weekend (5 months ago) — Finalist.\n"
        "Certifications:\n  - GCP Professional Developer (4 months ago)\n"
        "GitHub: 15 commits last month."
    ),
    "low": (
        "Robert Chen — Senior Java Developer\n"
        "Skills: Java, Spring Boot, Oracle DB, Maven, Hibernate\n"
        "Experience:\n  - BankCorp (2014-present): Legacy core banking system.\n"
        "Hackathons: None.\n"
        "Certifications:\n  - Oracle Java SE 8 (2016)\n"
        "GitHub: 3 commits last month."
    ),
}

with col_in:
    st.markdown('<div class="vh-scorer-label">Candidate Profile</div>', unsafe_allow_html=True)
    if "scorer_profile" not in st.session_state:
        st.session_state["scorer_profile"] = ""

    scorer_tab_url, scorer_tab_paste = st.tabs(["🔗 LinkedIn URL", "📋 Paste Profile"])

    with scorer_tab_url:
        scorer_url = st.text_input(
            "LinkedIn URL",
            placeholder="https://www.linkedin.com/in/username/",
            label_visibility="collapsed",
            key="scorer_url",
        )
        fetch_col, _ = st.columns([1, 3])
        with fetch_col:
            fetch_btn = st.button("⬇ Fetch", key="scorer_fetch_btn", type="primary")
        st.caption("ℹ️ Works on public profiles. Switch to Paste Profile if blocked.")
        if fetch_btn:
            if scorer_url:
                with st.spinner("Fetching LinkedIn profile…"):
                    _fetch_result = _fetch_linkedin_profile(scorer_url)
                    if _fetch_result.get("success"):
                        st.session_state["scorer_profile"] = _fetch_result["profile_text"]
                        st.success("✅ Profile fetched! Click ⚡ Score below.")
                    else:
                        st.warning(
                            f"⚠️ {_fetch_result.get('error', 'Could not fetch profile')}. "
                            "Try the Paste Profile tab."
                        )
            else:
                st.warning("Please enter a LinkedIn URL.")

    with scorer_tab_paste:
        st.text_area(
            "Profile",
            value=st.session_state.get("scorer_profile", ""),
            height=200,
            placeholder=(
                "Paste a LinkedIn-style profile here…\n\nExample:\n"
                "Jane Smith — Senior ML Engineer\n"
                "Skills: Python, LangChain, FastAPI, AWS\n"
                "Hackathons: AI Builders (1 month ago) — WINNER\n"
                "Certs: AWS ML Specialty (2 months ago)\n"
                "GitHub: 55 commits last month"
            ),
            label_visibility="collapsed",
            key="scorer_text",
        )
        st.markdown(
            '<span style="font-size:.72rem;color:var(--faint)">Load sample:</span>',
            unsafe_allow_html=True,
        )
        s1, s2, s3 = st.columns(3)
        with s1:
            if st.button("\U0001f3c6 High velocity", key="s_high"):
                st.session_state["scorer_profile"] = _SAMPLES["high"]
        with s2:
            if st.button("\u2705 Mid tier", key="s_mid"):
                st.session_state["scorer_profile"] = _SAMPLES["mid"]
        with s3:
            if st.button("\U0001f4cb Low velocity", key="s_low"):
                st.session_state["scorer_profile"] = _SAMPLES["low"]

    score_btn = st.button("\u26a1 Score This Candidate (3 Agents)", use_container_width=True, key="score_btn", type="primary")

with col_out:
    st.markdown('<div class="vh-scorer-label">Live Result</div>', unsafe_allow_html=True)
    scorer_result_ph = st.empty()
    scorer_result_ph.markdown(
        '<div style="color:var(--faint);font-size:.85rem;padding:20px 0;text-align:center">'
        'Results will appear here after scoring</div>',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

if score_btn:
    profile_text = (
        st.session_state.get("scorer_text", "").strip()
        or st.session_state.get("scorer_profile", "").strip()
    )
    if not profile_text:
        st.warning("Please paste a candidate profile or fetch one via LinkedIn URL before scoring.")
    else:
        with st.spinner("\u26a1 Running 3 agents…"):
            try:
                first_line = profile_text.split("\n")[0].strip()
                cname = first_line.split(" — ")[0][:80] if " — " in first_line else first_line[:80]

                try:
                    sa1 = _call_with_timeout(analyze_profile, _AGENT_TIMEOUT_SECS, profile_text)
                except concurrent.futures.TimeoutError:
                    sa1 = {"adaptability_score": 50, "tier": "Standard",
                           "recommend_interview": False, "score_breakdown": {}}

                s_adapt = int(sa1.get("adaptability_score") or 50)
                s_tier = sa1.get("tier") or "Standard"

                try:
                    sa2 = _call_with_timeout(
                        match_candidate, _AGENT_TIMEOUT_SECS,
                        job_title=DEMO_JOB["job_title"],
                        job_description=DEMO_JOB["job_description"],
                        required_skills=DEMO_JOB["required_skills"],
                        candidate_name=cname,
                        candidate_profile=profile_text,
                        adaptability_score=s_adapt,
                        adaptability_tier=s_tier,
                    )
                except concurrent.futures.TimeoutError:
                    sa2 = {
                        "total_match_score": int((s_adapt / 100) * 60 + 10),
                        "match_tier": "Unknown",
                        "recommend_interview": s_adapt >= 70,
                        "score_breakdown": {
                            "role_fit": {"matched_skills": []},
                            "culture_fit": {"startup_experience": False},
                        },
                    }

                s_match = int(sa2.get("total_match_score") or 0)
                s_match_tier = sa2.get("match_tier") or "Unknown"
                s_bd2 = sa2.get("score_breakdown") or {}
                s_skills = s_bd2.get("role_fit", {}).get("matched_skills", []) or []
                s_startup = s_bd2.get("culture_fit", {}).get("startup_experience", False)
                s_recommend = bool(sa2.get("recommend_interview"))

                try:
                    sa3 = _call_with_timeout(
                        generate_outreach, _AGENT_TIMEOUT_SECS,
                        candidate_name=cname,
                        candidate_profile=profile_text,
                        job_title=DEMO_JOB["job_title"],
                        company_name=DEMO_JOB["company_name"],
                        recruiter_name=DEMO_JOB["recruiter_name"],
                        total_match_score=s_match,
                        match_tier=s_match_tier,
                        adaptability_score=s_adapt,
                        adaptability_tier=s_tier,
                        matched_skills=s_skills,
                        startup_experience=s_startup,
                        recommend_interview=s_recommend,
                        reasoning=sa1.get("reasoning", ""),
                    )
                except concurrent.futures.TimeoutError:
                    t = ("PRIORITY" if s_match >= 85 else "STANDARD" if s_match >= 70
                         else "NURTURE" if s_match >= 55 else "ARCHIVE")
                    sa3 = {"outreach_tier": t, "campaign": {
                        "linkedin_message": f"Hi {cname.split()[0]}, great profile!"}}

                s_outreach = sa3.get("outreach_tier") or "ARCHIVE"
                s_li = (sa3.get("campaign") or {}).get("linkedin_message", "")
                s_adapt_color = _score_colour(s_adapt)
                s_bd = sa1.get("score_breakdown") or {}

                action_map = {
                    "PRIORITY": "\U0001f680 Fast-track to interview",
                    "STANDARD": "\u2705 Add to interview pipeline",
                    "NURTURE":  "\U0001f4cb Add to nurture pipeline",
                    "ARCHIVE":  "\U0001f5c4\ufe0f Archive for now",
                }
                action = action_map.get(s_outreach, "")

                dim_rows = ""
                for label, key, max_val, color in [
                    ("Hackathons", "hackathons", 40, "#6c63ff"),
                    ("Skills", "skills", 25, "#f5a623"),
                    ("Certs", "certifications", 20, "#3b82f6"),
                    ("Recency", "recency", 15, "#22c55e"),
                ]:
                    val = (s_bd.get(key) or {}).get("score", 0)
                    pct = int((val / max_val) * 100)
                    dim_rows += (
                        f'<div class="vh-dim-row">'
                        f'<span class="vh-dim-lbl">{label}</span>'
                        f'<div class="vh-dim-track"><div class="vh-dim-fill" '
                        f'style="width:{pct}%;background:{color}"></div></div>'
                        f'<span class="vh-dim-val" style="color:{color}">{val}/{max_val}</span>'
                        f'</div>'
                    )
                dim_rows += (
                    '<div class="vh-dim-row" style="margin-top:8px;border-top:1px solid var(--border);padding-top:8px">'
                    '<span class="vh-dim-lbl">Job Match</span>'
                    f'<div class="vh-dim-track"><div class="vh-dim-fill" '
                    f'style="width:{s_match}%;background:#a78bfa"></div></div>'
                    f'<span class="vh-dim-val" style="color:#a78bfa">{s_match}/100</span>'
                    '</div>'
                )

                li_block = ""
                if s_li:
                    li_block = (
                        f'<div style="margin-top:12px;background:var(--surface);border-radius:8px;'
                        f'padding:10px 12px;font-size:.78rem;color:var(--muted);line-height:1.6">'
                        f'<span style="font-size:.7rem;color:var(--primary);font-weight:600;'
                        f'display:block;margin-bottom:4px">\U0001f4e8 Generated LinkedIn Message</span>'
                        f'{html.escape(s_li)}</div>'
                    )

                _circumference = 213.6
                _ring_offset = round(_circumference - (s_adapt / 100) * _circumference, 1)
                scorer_result_ph.markdown(
                    f'<div class="vh-scorer-result">'
                    f'<div class="vh-score-ring-wrap">'
                    f'<svg width="80" height="80" viewBox="0 0 80 80" style="flex-shrink:0">'
                    f'<circle cx="40" cy="40" r="34" fill="none" stroke="#1e1e3a" stroke-width="8"/>'
                    f'<circle cx="40" cy="40" r="34" fill="none" stroke="{s_adapt_color}" '
                    f'stroke-width="8" stroke-linecap="round" stroke-dasharray="{_circumference}" '
                    f'stroke-dashoffset="{_ring_offset}" transform="rotate(-90 40 40)"/>'
                    f'<text x="40" y="45" text-anchor="middle" font-size="18" font-weight="900" '
                    f'fill="{s_adapt_color}">{s_adapt}</text>'
                    f'</svg>'
                    f'<div class="vh-score-ring-info">'
                    f'<div class="name" style="color:var(--text)">{html.escape(cname)}</div>'
                    f'<div class="tier">Adaptability: {html.escape(s_tier)}</div>'
                    f'<div class="action" style="color:{_TIER_COLOURS.get(s_outreach, "#94a3b8")}">{action}</div>'
                    f'</div></div>'
                    f'{dim_rows}'
                    f'<div style="margin-top:12px">{_tier_badge(s_outreach)}'
                    f'<span style="color:var(--faint);font-size:.75rem;margin-left:8px">'
                    f'Job Match: {s_match}/100</span></div>'
                    f'{li_block}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            except Exception as exc:
                scorer_result_ph.error(f"Scoring failed: {exc}")

# -- ATS integrations ---------------------------------------------------------
st.markdown(_ATS_HTML, unsafe_allow_html=True)

# ATS provider definitions
_ATS_PROVIDERS = [
    {
        "key": "greenhouse",
        "logo": "🌿",
        "name": "Greenhouse",
        "event": "candidate.created webhook",
        "webhook": "POST /ats/greenhouse/webhook",
        "color": "#3db639",
    },
    {
        "key": "lever",
        "logo": "⚙️",
        "name": "Lever",
        "event": "candidateCreated webhook",
        "webhook": "POST /ats/lever/webhook",
        "color": "#006dff",
    },
    {
        "key": "bamboohr",
        "logo": "🎋",
        "name": "BambooHR",
        "event": "employee.hired webhook",
        "webhook": "POST /ats/bamboohr/webhook",
        "color": "#74a318",
    },
]

# Build a label lookup from _ATS_PROVIDERS to avoid duplication
_ATS_PROVIDER_LABELS = {p["key"]: f'{p["logo"]} {p["name"]}' for p in _ATS_PROVIDERS}

if "ats_log" not in st.session_state:
    st.session_state["ats_log"] = []

# Render ATS cards as a single HTML grid (compact layout matching Cloud Run)
_ats_cards_html = '<div class="vh-ats-grid">'
for _provider in _ATS_PROVIDERS:
    _ats_cards_html += (
        f'<div class="vh-ats-card">'
        f'<div class="vh-ats-head">'
        f'<div class="vh-ats-logo">{_provider["logo"]}</div>'
        f'<div class="vh-ats-info">'
        f'<div class="vh-ats-name">{_provider["name"]}</div>'
        f'<div class="vh-ats-event">{_provider["event"]}</div>'
        f'</div>'
        f'<div class="vh-ats-status" title="Active"></div>'
        f'</div>'
        f'<div class="vh-ats-body">'
        f'<div class="vh-ats-webhook">{_provider["webhook"]}</div>'
        f'</div></div>'
    )
_ats_cards_html += '</div>'
st.markdown(_ats_cards_html, unsafe_allow_html=True)

# Render test buttons and results in columns below the grid
ats_cols = st.columns(len(_ATS_PROVIDERS))
for col, provider in zip(ats_cols, _ATS_PROVIDERS):
    with col:
        btn_key = f"ats_test_{provider['key']}"
        last_result_key = f"ats_result_{provider['key']}"
        last_result = st.session_state.get(last_result_key)
        btn_label = f"✅ {provider['name']} — run again" if last_result else f"{provider['logo']} Test {provider['name']} Webhook"
        if st.button(btn_label, key=btn_key, use_container_width=True, type="primary"):
            with st.spinner(f"⏳ Running Agent 1 for {provider['name']}…"):
                try:
                    mock = _get_mock_payload(provider["key"])
                    normalised = _ats_normalise(provider["key"], mock) if mock else None
                    if normalised:
                        profile_text = normalised["profile_text"]
                        candidate_name = normalised["candidate_name"]
                        job_title = normalised.get("job_title", "Unknown Role")
                        result = analyze_profile(profile_text)
                        sc = int(result.get("adaptability_score") or 0)
                        tier = result.get("tier") or "Standard"
                        recommend = result.get("recommend_interview", False)
                        action_str = (
                            "🚀 Fast-track to interview" if sc >= 85 else
                            "✅ Add to interview pipeline" if recommend else
                            "📋 Add to nurture pipeline"
                        )
                        res_data = {
                            "provider": provider["key"],
                            "provider_color": provider["color"],
                            "candidate_name": candidate_name,
                            "job_title": job_title,
                            "adaptability_score": sc,
                            "tier": tier,
                            "action": action_str,
                        }
                        st.session_state[last_result_key] = res_data
                        st.session_state["ats_log"].insert(0, res_data)
                        st.rerun()
                    else:
                        st.error("ATS normalisation failed — module unavailable")
                except Exception as exc:
                    st.error(f"⚠️ Error: {exc}")
        if last_result:
            sc = last_result["adaptability_score"]
            sc_color = "#22c55e" if sc >= 70 else "#f59e0b" if sc >= 55 else "#94a3b8"
            st.markdown(
                f'<div class="vh-ats-result" style="border-left:3px solid {last_result["provider_color"]}">'
                f'<div style="font-weight:700;margin-bottom:6px">'
                f'{html.escape(last_result["candidate_name"])}'
                f'<span style="font-size:.7rem;color:var(--muted);margin-left:6px">{html.escape(last_result["job_title"])}</span>'
                f'</div>'
                f'<div style="display:flex;gap:16px;margin-bottom:6px">'
                f'<span>Adaptability: <strong style="color:{sc_color}">{sc}/100</strong></span>'
                f'<span>Tier: <strong style="color:{sc_color}">{html.escape(last_result["tier"])}</strong></span>'
                f'</div>'
                f'<div style="color:#22c55e;font-size:.75rem">{last_result["action"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ATS Event Log
if st.session_state.get("ats_log"):
    header_row = (
        '<div class="vh-ats-log-row vh-ats-log-header">'
        '<span>Provider</span><span>Candidate</span>'
        '<span>Adaptability</span><span>Tier</span><span>Action</span>'
        '</div>'
    )
    log_rows = ""
    for entry in st.session_state["ats_log"]:
        sc = entry["adaptability_score"]
        sc_color = "#22c55e" if sc >= 70 else "#f59e0b" if sc >= 55 else "#94a3b8"
        prov_label = _ATS_PROVIDER_LABELS.get(entry["provider"], entry["provider"])
        log_rows += (
            f'<div class="vh-ats-log-row">'
            f'<span style="color:{entry["provider_color"]}">{prov_label}</span>'
            f'<span style="font-weight:600">{html.escape(entry["candidate_name"])}</span>'
            f'<span style="color:{sc_color};font-weight:700">{sc}/100</span>'
            f'<span style="color:{sc_color}">{html.escape(entry["tier"])}</span>'
            f'<span style="color:#22c55e;font-size:.72rem">{entry["action"]}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="vh-ats-log-wrap">'
        f'<div class="vh-ats-log-head">📋 ATS Event Log</div>'
        f'{header_row}{log_rows}'
        f'</div>',
        unsafe_allow_html=True,
    )

# -- Footer -------------------------------------------------------------------
st.markdown(_FOOTER_HTML, unsafe_allow_html=True)

# Main container close
st.markdown('</div>', unsafe_allow_html=True)
