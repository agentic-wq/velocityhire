"""VelocityHire Quiz Hub — Streamlit edition.

Three 40-question quizzes hosted as a single Streamlit app.
Run with:  streamlit run quiz/streamlit_app.py
"""

import streamlit as st

# ── QUIZ DATA ─────────────────────────────────────────────────────────────────

QUIZZES = {
    "docs": {
        "title": "📋 Project Docs Quiz",
        "subtitle": "Project Documentation",
        "description": (
            "Test your mastery of the VelocityHire project documentation — "
            "from the core value proposition and scoring system through to the "
            "BRD, user stories, market research, and product roadmap."
        ),
        "accent": "#00d4aa",
        "sections": [
            "Core Value Proposition & Vision",
            "Adaptability Scoring System",
            "Agent Architecture & Data Flow",
            "Demo Simulations & Candidates",
            "Business Requirements & Pricing",
            "User Stories & Personas",
            "Market Research & Validation",
            "Roadmap & Hackathon Requirements",
        ],
        "questions": [
            # Section 1: Core Value Proposition & Vision (Q1–Q5)
            {
                "s": 0,
                "q": "What is VelocityHire's primary value proposition as stated in the Core Value Proposition document?",
                "choices": [
                    "Credentials beat experience",
                    "Learning Velocity over Static Skills",
                    "Years of experience predict performance",
                    "AI replaces human recruiters",
                ],
                "a": 1,
            },
            {
                "s": 0,
                "q": "According to the Core Value Proposition document, what does VelocityHire prioritize candidates on?",
                "choices": [
                    "Degree from prestigious universities",
                    "Years of experience in specific technologies",
                    "Demonstrated ability to continuously learn and adapt",
                    "Technical assessment test scores",
                ],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What is VelocityHire's primary target problem according to the marketing value proposition document?",
                "choices": [
                    "Companies can't find enough developers",
                    "Companies waste resources hiring developers with outdated skills who can't adapt, while missing hungry learners",
                    "Remote work increases hiring costs",
                    "AI is replacing software developers",
                ],
                "a": 1,
            },
            {
                "s": 0,
                "q": "According to the VelocityHire demo script, by what percentage do adaptable candidates outperform traditional hires in retention?",
                "choices": ["40%", "60%", "73%", "80%"],
                "a": 0,
            },
            {
                "s": 0,
                "q": "According to the demo script opening hook, what percentage of successful hires share adaptability as their defining trait?",
                "choices": ["57%", "63%", "73%", "85%"],
                "a": 2,
            },
            # Section 2: Adaptability Scoring System (Q6–Q11)
            {
                "s": 1,
                "q": "What is the maximum total score in the Hackathon Enhanced Scoring rubric?",
                "choices": ["50 points", "75 points", "100 points", "150 points"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "What is the total point allocation for 'Learning Velocity Priority' in the Hackathon Enhanced Scoring rubric?",
                "choices": ["25 points", "35 points", "45 points", "60 points"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "How many points is 'Recent Skill Acquisition' worth within the Learning Velocity Priority category?",
                "choices": ["10 points", "25 points", "35 points", "45 points"],
                "a": 1,
            },
            {
                "s": 1,
                "q": "What recency multiplier is applied to hackathon participation within the last 3 months?",
                "choices": ["2x", "3x", "4x", "5x"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "According to Agent 1's hackathon extraction logic, what is the total score a recent win (last 6 months) generates including the 4x recency multiplier?",
                "choices": ["6 points", "12 points", "24 points", "40 points"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "What are the three main scoring categories in the Hackathon Enhanced Scoring rubric?",
                "choices": [
                    "Skills, Experience, Education",
                    "Learning Velocity Priority, Technical Foundation, Startup Experience",
                    "Adaptability, Culture Fit, Role Requirements",
                    "Hackathons, Certifications, GitHub Activity",
                ],
                "a": 1,
            },
            # Section 3: Agent Architecture & Data Flow (Q12–Q16)
            {
                "s": 2,
                "q": "What percentage weight does adaptability carry in Agent 2's job matching algorithm?",
                "choices": ["25%", "40%", "60%", "75%"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "What are the correct weights in Agent 2's matching algorithm across all three dimensions?",
                "choices": [
                    "Adaptability 50%, Role requirements 30%, Culture fit 20%",
                    "Adaptability 60%, Role requirements 25%, Culture fit 15%",
                    "Adaptability 70%, Role requirements 20%, Culture fit 10%",
                    "Adaptability 40%, Role requirements 40%, Culture fit 20%",
                ],
                "a": 1,
            },
            {
                "s": 2,
                "q": "What is Agent 1's primary input according to the system architecture overview?",
                "choices": [
                    "Job descriptions from hiring managers",
                    "LinkedIn profile URLs",
                    "GitHub repository links",
                    "Candidate resumes in PDF format",
                ],
                "a": 1,
            },
            {
                "s": 2,
                "q": "What technologies does Agent 1 use for processing according to the system architecture?",
                "choices": [
                    "Deep learning neural networks and transformers",
                    "Blockchain and distributed ledger",
                    "Web scraping, NLP processing, and pattern recognition",
                    "Computer vision and OCR",
                ],
                "a": 2,
            },
            {
                "s": 2,
                "q": "What success metrics does the system architecture document specify for measuring platform effectiveness?",
                "choices": [
                    "Revenue per customer, churn rate, and LTV",
                    "Adaptability score accuracy vs. actual performance, response rates by score tier, hire success rate for 70+ scored candidates",
                    "Time to hire, cost per hire, number of applications",
                    "Server uptime, API response time, and error rate",
                ],
                "a": 1,
            },
            # Section 4: Demo Simulations & Candidates (Q17–Q22)
            {
                "s": 3,
                "q": "In the three-agent demo simulation, what adaptability score does Candidate A (Sarah Chen, 8 years React) receive?",
                "choices": ["25/100", "35/100", "50/100", "65/100"],
                "a": 1,
            },
            {
                "s": 3,
                "q": "In the three-agent demo simulation, what adaptability score does Candidate B (Marcus Rodriguez) receive?",
                "choices": ["75/100", "80/100", "87/100", "95/100"],
                "a": 2,
            },
            {
                "s": 3,
                "q": "In the demo simulation, which hackathon did Marcus Rodriguez recently win?",
                "choices": [
                    "TechCrunch Disrupt",
                    "AngelHack Global",
                    "React Summit Hackathon",
                    "GitHub Universe",
                ],
                "a": 2,
            },
            {
                "s": 3,
                "q": "What is Candidate A's total job match score in Agent 2 of the demo simulation?",
                "choices": ["35/100", "42/100", "54/100", "68/100"],
                "a": 2,
            },
            {
                "s": 3,
                "q": "In the three-agent simulation demo (Sarah Chen scenario), what is Sarah Chen's total match score from Agent 2?",
                "choices": ["75.2/100", "80.5/100", "85.7/100", "92.3/100"],
                "a": 2,
            },
            {
                "s": 3,
                "q": "What action does Agent 3 take for a candidate with a low adaptability score (below threshold) in the demo simulation?",
                "choices": [
                    "Send a standard template outreach email",
                    "Schedule a technical screening call",
                    "Skip outreach and add to passive pipeline for future roles",
                    "Request updated portfolio materials",
                ],
                "a": 2,
            },
            # Section 5: Business Requirements & Pricing (Q23–Q27)
            {
                "s": 4,
                "q": "What is the monthly price for the Starter subscription tier?",
                "choices": ["$99/month", "$199/month", "$299/month", "$499/month"],
                "a": 2,
            },
            {
                "s": 4,
                "q": "What is the monthly price for the Enterprise subscription tier?",
                "choices": ["$999/month", "$1,499/month", "$1,999/month", "$2,999/month"],
                "a": 2,
            },
            {
                "s": 4,
                "q": "What is VelocityHire's Year 2 ARR revenue target according to the Business Requirements Document?",
                "choices": ["$500K", "$1M", "$2M", "$5M"],
                "a": 2,
            },
            {
                "s": 4,
                "q": "According to the Business Requirements Document, what is the SAM (Serviceable Addressable Market) for the technical recruiting segment?",
                "choices": ["$150M", "$1.5B", "$3.2B", "$15B"],
                "a": 2,
            },
            {
                "s": 4,
                "q": "What are VelocityHire's three target market segments according to the BRD?",
                "choices": [
                    "Startups, SMBs, and Enterprises",
                    "Mid-size tech companies (100–1000 employees), technical recruiting agencies, and enterprise companies (1000+ employees)",
                    "US companies, EU companies, and Asia-Pacific companies",
                    "Engineering, Product, and Marketing teams",
                ],
                "a": 1,
            },
            # Section 6: User Stories & Personas (Q28–Q32)
            {
                "s": 5,
                "q": "What is the name and title of the Hiring Manager persona defined in the user stories?",
                "choices": [
                    "Jennifer Park — VP People Operations",
                    "Mike Rodriguez — Senior Recruiter",
                    "Sarah Chen — Engineering Manager",
                    "Marcus Rodriguez — Team Lead",
                ],
                "a": 2,
            },
            {
                "s": 5,
                "q": "What is the name and title of the HR Director persona in the user stories?",
                "choices": [
                    "Sarah Chen — Engineering Manager",
                    "Mike Rodriguez — Senior Recruiter",
                    "Jennifer Park — VP People Operations",
                    "Alex Thompson — Senior Technical Recruiter",
                ],
                "a": 2,
            },
            {
                "s": 5,
                "q": "According to User Story 5 (Outreach Prioritization), what are the three outreach tiers and their score thresholds?",
                "choices": [
                    "Tier 1: 90+, Tier 2: 80–89, Tier 3: 70–79",
                    "Tier 1: 80+, Tier 2: 70–79, Tier 3: 60–69",
                    "Tier 1: 75+, Tier 2: 65–74, Tier 3: 55–64",
                    "Tier 1: 85+, Tier 2: 75–84, Tier 3: 65–74",
                ],
                "a": 1,
            },
            {
                "s": 5,
                "q": "According to the user stories success metrics, what screening time reduction is targeted for Stories 4–6 (Recruiter Workflow)?",
                "choices": ["30% reduction", "45% reduction", "60% reduction", "75% reduction"],
                "a": 2,
            },
            {
                "s": 5,
                "q": "According to the user stories success metrics, what improvement in hire success rate is expected for Stories 1–3 (Hiring Manager)?",
                "choices": ["20% improvement", "30% improvement", "40% improvement", "50% improvement"],
                "a": 2,
            },
            # Section 7: Market Research & Validation (Q33–Q37)
            {
                "s": 6,
                "q": "What is the validated cost of a senior developer mis-hire targeted in the market research framework?",
                "choices": ["$100K+", "$150K+", "$200K+", "$240K+"],
                "a": 3,
            },
            {
                "s": 6,
                "q": "According to the market research framework, what percentage of 'required skills' in job posts become outdated within 18 months?",
                "choices": ["20%+", "30%+", "40%+", "50%+"],
                "a": 2,
            },
            {
                "s": 6,
                "q": "What retention advantage do adaptable learners have according to the market research framework's target metrics?",
                "choices": [
                    "15%+ higher retention",
                    "25%+ higher retention",
                    "35%+ higher retention",
                    "45%+ higher retention",
                ],
                "a": 1,
            },
            {
                "s": 6,
                "q": "How many tech hiring managers should be interviewed in Phase 2 (Primary Research) of the market research plan?",
                "choices": ["10", "20", "50", "100"],
                "a": 1,
            },
            {
                "s": 6,
                "q": "What statistical confidence level is required for the market research success criteria?",
                "choices": ["80%", "90%", "95%", "99%"],
                "a": 2,
            },
            # Section 8: Roadmap & Hackathon Requirements (Q38–Q40)
            {
                "s": 7,
                "q": "What is the hackathon submission deadline according to the AI Recruitment Platform Master Roadmap?",
                "choices": [
                    "Monday, February 24th",
                    "Wednesday, February 26th, 6:00 PM",
                    "Friday, February 27th, 6:00 PM",
                    "Sunday, March 1st",
                ],
                "a": 2,
            },
            {
                "s": 7,
                "q": "What was the overall project completion percentage at the time the master roadmap was written?",
                "choices": ["20%", "35%", "50%", "65%"],
                "a": 1,
            },
            {
                "s": 7,
                "q": "According to the hackathon requirements analysis, what is the minimum number of AI agents required by the Complete.dev challenge?",
                "choices": ["1", "2", "3", "5"],
                "a": 1,
            },
        ],
    },
    "arch": {
        "title": "🏗 Architecture & Full-Stack Quiz",
        "subtitle": "Architecture & Full-Stack",
        "description": (
            "Test your understanding of the full VelocityHire system — "
            "from the LangGraph agent pipeline and FastAPI server to ATS integrations, "
            "the analytics bug fix, security hardening, and the production roadmap."
        ),
        "accent": "#f59e0b",
        "sections": [
            "Architecture & Core Concepts",
            "The Three Agents",
            "Demo Features & UI",
            "API Endpoints",
            "ATS Integrations",
            "Security Fixes",
            "Database & Analytics",
            "Production Roadmap",
        ],
        "questions": [
            # Section 1: Architecture & Core Concepts (Q1–Q8)
            {
                "s": 0,
                "q": "What is the core thesis VelocityHire was built to prove?",
                "choices": [
                    "Credentials beat experience",
                    "Learning velocity beats credentials",
                    "Years of experience predict performance",
                    "Certifications are the best hiring signal",
                ],
                "a": 1,
            },
            {
                "s": 0,
                "q": "How many LangGraph agents does VelocityHire use in its pipeline?",
                "choices": ["1", "2", "3", "5"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What Python framework powers VelocityHire's API server?",
                "choices": ["Django", "Flask", "FastAPI", "Tornado"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What LangGraph class is used to define the agent orchestration graph?",
                "choices": ["AgentGraph", "StateGraph", "WorkflowGraph", "PipelineGraph"],
                "a": 1,
            },
            {
                "s": 0,
                "q": "What database does VelocityHire use in the demo/hackathon version?",
                "choices": ["PostgreSQL", "MongoDB", "SQLite", "Redis"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What is the name of the in-memory dictionary used to cache pipeline results for re-runs?",
                "choices": ["_RUN_CACHE", "_RESULT_STORE", "_PIPELINE_CACHE", "_DEMO_CACHE"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What replay delay (seconds per stage) is used during cached pipeline re-runs to keep the animation alive?",
                "choices": ["0.1 s", "0.35 s", "1.0 s", "2.0 s"],
                "a": 1,
            },
            {
                "s": 0,
                "q": "What is the per-agent hard timeout (in seconds) to prevent demo hangs?",
                "choices": ["10 s", "20 s", "30 s", "60 s"],
                "a": 2,
            },
            # Section 2: The Three Agents (Q9–Q18)
            {
                "s": 1,
                "q": "What does Agent 1 produce?",
                "choices": [
                    "Job match score",
                    "LinkedIn outreach message",
                    "Adaptability score and tier",
                    "ATS webhook payload",
                ],
                "a": 2,
            },
            {
                "s": 1,
                "q": "What does Agent 2 produce?",
                "choices": [
                    "Outreach campaign",
                    "Total match score, match tier, and interview recommendation",
                    "Candidate profile summary",
                    "Analytics dashboard data",
                ],
                "a": 1,
            },
            {
                "s": 1,
                "q": "What does Agent 3 produce?",
                "choices": [
                    "Adaptability score",
                    "Job description analysis",
                    "Outreach campaign: LinkedIn message, email, follow-up, recruiter note",
                    "Database schema",
                ],
                "a": 2,
            },
            {
                "s": 1,
                "q": "What are the four outreach tiers produced by Agent 3?",
                "choices": [
                    "HOT / WARM / COLD / DEAD",
                    "PRIORITY / STANDARD / NURTURE / ARCHIVE",
                    "A / B / C / D",
                    "FAST / NORMAL / SLOW / SKIP",
                ],
                "a": 1,
            },
            {
                "s": 1,
                "q": "What does Agent 1 look for when scoring adaptability? (Best answer)",
                "choices": [
                    "Only years of experience",
                    "Only education level",
                    "Hackathon wins, recent certifications, GitHub commits, startup experience, learning signals",
                    "Salary expectations",
                ],
                "a": 2,
            },
            {
                "s": 1,
                "q": "Which Python function name in agent1 runs the full profile analysis?",
                "choices": ["run_agent", "score_profile", "analyze_profile", "process_candidate"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "Which function in agent2 performs job matching?",
                "choices": ["run_matching", "match_candidate", "score_job_fit", "evaluate_candidate"],
                "a": 1,
            },
            {
                "s": 1,
                "q": "Which function in agent3 generates outreach?",
                "choices": ["create_campaign", "write_outreach", "generate_outreach", "build_message"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "In MOCK_MODE, what drives the scoring logic?",
                "choices": [
                    "OpenAI GPT-4o API calls",
                    "Deploy AI OAuth2 endpoint",
                    "Rule-based deterministic scoring",
                    "Random number generation",
                ],
                "a": 2,
            },
            {
                "s": 1,
                "q": "Why is MOCK_MODE hard-locked to true in the demo?",
                "choices": [
                    "GPT-4o is too expensive",
                    "The Deploy AI /openai/chat/completions endpoint returns 403 and direct sk- auth returns 401 without OAuth2 provisioning",
                    "The agents are too slow with real LLMs",
                    "The hackathon rules prohibit real API calls",
                ],
                "a": 1,
            },
            # Section 3: Demo Features & UI (Q19–Q24)
            {
                "s": 2,
                "q": "What is the name of the demo feature that shows how traditional ATS rankings differ from VelocityHire's?",
                "choices": [
                    "The Talent Gap",
                    "The Ranking Flip",
                    "The Score Reversal",
                    "The Credential Check",
                ],
                "a": 1,
            },
            {
                "s": 2,
                "q": "How many demo candidates does VelocityHire process in the main pipeline run?",
                "choices": ["3", "4", "5", "10"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "Which demo candidate typically ranks lowest in traditional ATS but higher in VelocityHire?",
                "choices": ["Marcus Rivera", "Jordan Kim", "Elena Voronova", "Alex Chen"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "What is the polling interval (in milliseconds) used by the front-end to check pipeline progress?",
                "choices": ["100 ms", "300 ms", "600 ms", "1000 ms"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "What chart library does the VelocityHire UI use for analytics visualizations?",
                "choices": ["D3.js", "Highcharts", "Chart.js v4.4.0", "ApexCharts"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "What CSS breakpoints are used for mobile responsiveness?",
                "choices": ["480px / 320px", "768px / 480px", "720px / 440px", "1024px / 768px"],
                "a": 2,
            },
            # Section 4: API Endpoints (Q25–Q28)
            {
                "s": 3,
                "q": "Which endpoint starts a background pipeline run and returns a run_id?",
                "choices": [
                    "GET /demo/start",
                    "POST /demo/run",
                    "POST /pipeline/execute",
                    "GET /demo/run",
                ],
                "a": 1,
            },
            {
                "s": 3,
                "q": "Which endpoint allows scoring a single custom profile through all 3 agents?",
                "choices": [
                    "POST /demo/analyze",
                    "POST /score/profile",
                    "POST /demo/score-one",
                    "GET /demo/score",
                ],
                "a": 2,
            },
            {
                "s": 3,
                "q": "What HTTP status code is returned when an invalid run_id is requested from /demo/progress/{run_id}?",
                "choices": ["400", "401", "403", "404"],
                "a": 3,
            },
            {
                "s": 3,
                "q": "Which endpoint returns the full analytics JSON for the dashboard?",
                "choices": [
                    "GET /dashboard",
                    "GET /analytics/data",
                    "GET /stats",
                    "GET /metrics",
                ],
                "a": 1,
            },
            # Section 5: ATS Integrations (Q29–Q31)
            {
                "s": 4,
                "q": "Which three ATS platforms does VelocityHire integrate with?",
                "choices": [
                    "Workday, SAP, Oracle",
                    "Greenhouse, Lever, BambooHR",
                    "Taleo, iCIMS, SmartRecruiters",
                    "Jobvite, Workable, Recruitee",
                ],
                "a": 1,
            },
            {
                "s": 4,
                "q": "What technique does VelocityHire use to normalize payloads from different ATS platforms?",
                "choices": [
                    "API gateway transformation",
                    "Webhook normalizers",
                    "GraphQL resolvers",
                    "ETL pipelines",
                ],
                "a": 1,
            },
            {
                "s": 4,
                "q": "What is the name of the shared module that handles ATS integrations?",
                "choices": [
                    "shared/connectors.py",
                    "shared/ats_webhooks.py",
                    "shared/ats_integrations.py",
                    "shared/integrations.py",
                ],
                "a": 2,
            },
            # Section 6: Security Fixes (Q32–Q36)
            {
                "s": 5,
                "q": "What XSS attack vector was identified in the security audit?",
                "choices": [
                    "SQL injection via candidate name",
                    "Script tags reflected verbatim through profile_text into innerHTML in the live scorer UI",
                    "Cookie theft via CSRF",
                    "Path traversal via file upload",
                ],
                "a": 1,
            },
            {
                "s": 5,
                "q": "What server-side function was added to sanitize profile_text input?",
                "choices": ["sanitize_input()", "clean_html()", "_strip_html()", "remove_tags()"],
                "a": 2,
            },
            {
                "s": 5,
                "q": "What maximum character limit was enforced on profile_text in ScoreOneRequest?",
                "choices": ["10,000", "25,000", "50,000", "100,000"],
                "a": 2,
            },
            {
                "s": 5,
                "q": "What JavaScript helper function was added to the UI to escape HTML before inserting into innerHTML?",
                "choices": ["sanitize()", "escHtml()", "encodeHtml()", "htmlEscape()"],
                "a": 1,
            },
            {
                "s": 5,
                "q": "After the CORS fix, what HTTP methods are explicitly allowed?",
                "choices": ["GET, POST, PUT, DELETE", "GET only", "GET, POST", "POST, PUT, PATCH"],
                "a": 2,
            },
            # Section 7: Database & Analytics (Q37–Q38)
            {
                "s": 6,
                "q": "What critical bug in shared/analytics.py was fixed during Phase 2?",
                "choices": [
                    "Missing index on candidate_id",
                    "_fetch_all() used positional zip() against metadata columns, causing misalignment because ALTER TABLE appended company_id at the end",
                    "Analytics query returned duplicate rows",
                    "Date formatting was incorrect",
                ],
                "a": 1,
            },
            {
                "s": 6,
                "q": "What method is used to correctly map SQLAlchemy row results after the analytics fix?",
                "choices": ["dict(row)", "row.to_dict()", "dict(row._mapping)", "row.as_dict()"],
                "a": 2,
            },
            # Section 8: Production Roadmap (Q39–Q40)
            {
                "s": 7,
                "q": "What is the planned database migration path from the hackathon version to production?",
                "choices": [
                    "SQLite → MySQL → Oracle",
                    "SQLite → PostgreSQL with Redis caching",
                    "SQLite → MongoDB",
                    "SQLite → DynamoDB",
                ],
                "a": 1,
            },
            {
                "s": 7,
                "q": "What feature is identified in the production roadmap to replace the in-memory _PIPELINE_CACHE?",
                "choices": ["Memcached", "Varnish", "Redis", "CDN edge caching"],
                "a": 2,
            },
        ],
    },
    "demo": {
        "title": "⚡ demo/app.py Quiz",
        "subtitle": "Codebase Deep-Dive",
        "description": (
            "Deep-dive into the VelocityHire FastAPI application. Questions cover config constants, "
            "pipeline mechanics, API endpoints, scoring tiers, security implementation, "
            "ATS integrations, and the inline frontend."
        ),
        "accent": "#6c63ff",
        "sections": [
            "Configuration & Constants",
            "Demo Data — Candidates & Job",
            "Pipeline Mechanics",
            "API Endpoints",
            "Scoring Logic & Tiers",
            "Security Implementation",
            "ATS Integration",
            "Frontend & Analytics",
        ],
        "questions": [
            # Section 1: Configuration & Constants (Q1–Q5)
            {
                "s": 0,
                "q": "What is the value of `_CACHE_REPLAY_DELAY` (per-stage delay for cached pipeline re-runs) in demo/app.py?",
                "choices": ["0.1 seconds", "0.35 seconds", "1.0 second", "2.0 seconds"],
                "a": 1,
            },
            {
                "s": 0,
                "q": "What is the value of `_AGENT_TIMEOUT_SECS` (per-agent hard timeout) in demo/app.py?",
                "choices": ["10 seconds", "20 seconds", "30 seconds", "60 seconds"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What is `MOCK_MODE` hard-locked to in demo/app.py?",
                "choices": ['False', '"false"', '"true"', "True"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What is the name of the in-memory dict that caches completed pipeline results for re-runs?",
                "choices": ["_RUN_CACHE", "_RESULT_STORE", "_PIPELINE_CACHE", "_DEMO_CACHE"],
                "a": 2,
            },
            {
                "s": 0,
                "q": "What Python concurrency primitive is used to run the VelocityHire pipeline in the background?",
                "choices": [
                    "asyncio.Task",
                    "multiprocessing.Process",
                    "threading.Thread",
                    "concurrent.futures.ProcessPoolExecutor",
                ],
                "a": 2,
            },
            # Section 2: Demo Data — Candidates & Job (Q6–Q10)
            {
                "s": 1,
                "q": "How many demo candidates are defined in `DEMO_CANDIDATES` in demo/app.py?",
                "choices": ["3", "4", "5", "10"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "Which demo candidate typically ranks lowest in traditional ATS scoring but higher in VelocityHire?",
                "choices": ["Marcus Rivera", "Jordan Kim", "Elena Voronova", "Alex Chen"],
                "a": 2,
            },
            {
                "s": 1,
                "q": "What is the demo job title used for all pipeline runs in demo/app.py?",
                "choices": [
                    "Lead Machine Learning Engineer",
                    "Senior AI Engineer",
                    "Principal Data Scientist",
                    "AI Platform Architect",
                ],
                "a": 1,
            },
            {
                "s": 1,
                "q": "What initial `status` value is written to `_runs` when `POST /demo/run` creates a new run?",
                "choices": ['"pending"', '"starting"', '"initializing"', '"running"'],
                "a": 2,
            },
            {
                "s": 1,
                "q": "How many characters of the UUID4 value are used as the `run_id` in `POST /demo/run`?",
                "choices": ["4", "6", "8", "12"],
                "a": 2,
            },
            # Section 3: Pipeline Mechanics (Q11–Q15)
            {
                "s": 2,
                "q": "Which function in demo/app.py wraps every agent call to enforce the timeout limit?",
                "choices": ["_agent_call()", "_timeout_call()", "_call_with_timeout()", "_run_with_limit()"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "When Agent 1 times out during a `score_one` request, what default `adaptability_score` is returned?",
                "choices": ["0", "25", "50", "75"],
                "a": 2,
            },
            {
                "s": 2,
                "q": "The background pipeline thread is started with `daemon=True`. What is the effect of this flag?",
                "choices": [
                    "Thread runs with elevated privileges",
                    "Thread is automatically killed when the main process exits",
                    "Thread cannot be interrupted by signals",
                    "Thread runs at a lower CPU scheduling priority",
                ],
                "a": 1,
            },
            {
                "s": 2,
                "q": "What value does `POST /demo/run` return alongside `run_id`?",
                "choices": ["candidate_count", "total_candidates", "num_agents", "pipeline_id"],
                "a": 1,
            },
            {
                "s": 2,
                "q": "Which function contains the full pipeline logic that executes in the background thread?",
                "choices": [
                    "_start_pipeline()",
                    "_execute_pipeline()",
                    "_run_pipeline()",
                    "_process_pipeline()",
                ],
                "a": 2,
            },
            # Section 4: API Endpoints (Q16–Q20)
            {
                "s": 3,
                "q": "What fields does `GET /health` include in its JSON response?",
                "choices": [
                    "CPU usage, memory, and uptime",
                    "status, db, analytics, agents count, and UTC timestamp",
                    "version number and build info",
                    "Total runs and candidate count",
                ],
                "a": 1,
            },
            {
                "s": 3,
                "q": "What HTTP status code does `GET /demo/progress/{run_id}` return when the run_id is not found?",
                "choices": ["400", "401", "403", "404"],
                "a": 3,
            },
            {
                "s": 3,
                "q": "What does `GET /analytics/data` return when `ANALYTICS_ENABLED` is False?",
                "choices": ['{"error": "disabled"}', "[]", "{}", "HTTP 503"],
                "a": 2,
            },
            {
                "s": 3,
                "q": "What argument is passed to `get_full_analytics()` in the `/analytics/data` route handler?",
                "choices": ['"velocityhire"', '"test"', '"demo"', '"prod"'],
                "a": 2,
            },
            {
                "s": 3,
                "q": 'What does `GET /demo/results/{run_id}` return in its JSON response?',
                "choices": [
                    '{"results": [...]}',
                    '{"status": ..., "results": [...]}',
                    '{"run_id": ..., "data": [...]}',
                    "The full _runs entry",
                ],
                "a": 1,
            },
            # Section 5: Scoring Logic & Tiers (Q21–Q25)
            {
                "s": 4,
                "q": 'What minimum match score triggers the "PRIORITY" outreach tier in the `score_one` route?',
                "choices": ["≥70", "≥75", "≥80", "≥85"],
                "a": 3,
            },
            {
                "s": 4,
                "q": "What is the `velocityhire_action` string returned when `match_score` is 85 or above?",
                "choices": [
                    '"✅ Add to interview pipeline"',
                    '"🚀 Fast-track to interview"',
                    '"⚡ Priority candidate"',
                    '"🌟 Top performer"',
                ],
                "a": 1,
            },
            {
                "s": 4,
                "q": "In the `scoreColor()` JavaScript function, what score threshold returns the green colour `#22c55e`?",
                "choices": ["≥60", "≥65", "≥70", "≥75"],
                "a": 2,
            },
            {
                "s": 4,
                "q": "What colour does `scoreColor()` return for scores between 55 and 69?",
                "choices": [
                    "#3b82f6 (blue)",
                    "#f59e0b (amber)",
                    "#ef4444 (red)",
                    "#8b5cf6 (purple)",
                ],
                "a": 1,
            },
            {
                "s": 4,
                "q": "What score breakdown weight is assigned to hackathons in Agent 1's adaptability scoring?",
                "choices": ["25%", "30%", "40%", "50%"],
                "a": 2,
            },
            # Section 6: Security Implementation (Q26–Q30)
            {
                "s": 5,
                "q": "What regex pattern does the server-side `_strip_html()` function use to remove HTML tags?",
                "choices": ["<[^>]+>", "<[^>]{0,200}>", "<.*?>", "<\\w+[^>]*>"],
                "a": 1,
            },
            {
                "s": 5,
                "q": "What maximum character limit is enforced on `profile_text` in the `ScoreOneRequest` Pydantic model?",
                "choices": ["10,000", "25,000", "50,000", "100,000"],
                "a": 2,
            },
            {
                "s": 5,
                "q": "Which JavaScript function escapes HTML before inserting content into `innerHTML` in the live scorer UI?",
                "choices": ["sanitize()", "escHtml()", "encodeHtml()", "htmlEscape()"],
                "a": 1,
            },
            {
                "s": 5,
                "q": "What HTTP methods are explicitly allowed by the CORS middleware configuration in demo/app.py?",
                "choices": ["GET, POST, PUT, DELETE", "GET only", "GET, POST", "POST, PUT, PATCH"],
                "a": 2,
            },
            {
                "s": 5,
                "q": "Which Pydantic decorator is used to validate the `profile_text` field in `ScoreOneRequest`?",
                "choices": ["@field_validator", "@validator", "@validates", "@check_field"],
                "a": 1,
            },
            # Section 7: ATS Integration (Q31–Q35)
            {
                "s": 6,
                "q": "Which three ATS platforms are supported in the demo/app.py ATS integration routes?",
                "choices": [
                    "Workday, SAP, Oracle",
                    "Greenhouse, Lever, BambooHR",
                    "Taleo, iCIMS, SmartRecruiters",
                    "Jobvite, Workable, Recruitee",
                ],
                "a": 1,
            },
            {
                "s": 6,
                "q": "Which function normalises raw ATS webhook payloads into a standard format in demo/app.py?",
                "choices": ["ats_transform()", "normalize_webhook()", "ats_normalise()", "process_webhook()"],
                "a": 2,
            },
            {
                "s": 6,
                "q": "What HTTP status does `POST /ats/{provider}/test` return when the ATS module is unavailable?",
                "choices": ["400", "404", "503", "501"],
                "a": 2,
            },
            {
                "s": 6,
                "q": "How many recent ATS events does `GET /ats/integrations` return in its `recent_events` field?",
                "choices": ["5", "10", "25", "50"],
                "a": 1,
            },
            {
                "s": 6,
                "q": "What is the maximum number of entries retained in the `_ats_demo_log` list?",
                "choices": ["10", "20", "50", "100"],
                "a": 2,
            },
            # Section 8: Frontend & Analytics (Q36–Q40)
            {
                "s": 7,
                "q": "What is the frontend polling interval (in milliseconds) used to check pipeline progress via `/demo/progress/{run_id}`?",
                "choices": ["100ms", "300ms", "600ms", "1000ms"],
                "a": 2,
            },
            {
                "s": 7,
                "q": "What chart library version is loaded by the VelocityHire demo UI for analytics visualisations?",
                "choices": ["Chart.js v3.9.1", "Chart.js v4.2.0", "Chart.js v4.4.0", "D3.js v7"],
                "a": 2,
            },
            {
                "s": 7,
                "q": "What CSS breakpoints are defined for mobile responsiveness in the inline DEMO_HTML?",
                "choices": ["480px / 320px", "768px / 480px", "720px / 440px", "1024px / 768px"],
                "a": 2,
            },
            {
                "s": 7,
                "q": "Which JavaScript function appends a new scored-candidate row to the ATS integration activity log in the UI?",
                "choices": ["updateATSLog()", "appendATSLog()", "addATSEntry()", "logATSResult()"],
                "a": 1,
            },
            {
                "s": 7,
                "q": 'What `company_id` string is passed to `save_candidate_score()` in the demo pipeline and ATS routes?',
                "choices": ['"velocityhire"', '"test"', '"demo"', '"prod"'],
                "a": 2,
            },
        ],
    },
}

# ── SCORING HELPERS ───────────────────────────────────────────────────────────

LETTERS = ["A", "B", "C", "D"]


def score_tier(score: int, total: int) -> tuple[str, str]:
    """Return (tier label, colour) for a given score."""
    pct = score / total if total else 0
    if pct >= 0.95:
        return "Expert 🏆", "#f59e0b"
    if pct >= 0.75:
        return "Proficient ✅", "#00d4aa"
    if pct >= 0.50:
        return "Familiar 📖", "#6c63ff"
    return "Review the codebase 🔍", "#ff6b6b"


# ── SESSION STATE HELPERS ─────────────────────────────────────────────────────


def _state_key(quiz_id: str, suffix: str) -> str:
    return f"quiz_{quiz_id}_{suffix}"


def init_quiz_state(quiz_id: str) -> None:
    n = len(QUIZZES[quiz_id]["questions"])
    for key, default in [
        ("started", False),
        ("current", 0),
        ("answers", [-1] * n),
        ("answered", [False] * n),
        ("finished", False),
    ]:
        k = _state_key(quiz_id, key)
        if k not in st.session_state:
            st.session_state[k] = default


def get_s(quiz_id: str, key: str):
    return st.session_state[_state_key(quiz_id, key)]


def set_s(quiz_id: str, key: str, value) -> None:
    st.session_state[_state_key(quiz_id, key)] = value


# ── PAGE CONFIG ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="VelocityHire Quiz Hub",
    page_icon="⚡",
    layout="centered",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
/* Global dark theme */
[data-testid="stAppViewContainer"] {
    background-color: #0d0f1a;
    color: #e8eaf6;
}
[data-testid="stHeader"] { background-color: #0d0f1a; }

/* Hide default Streamlit menu and footer */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Card styles */
.quiz-card {
    background: #1e2235;
    border: 1.5px solid #2a2f4a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}
.quiz-card h3 { margin: 0 0 6px 0; }
.quiz-card p  { color: #8892b0; font-size: 0.9rem; margin: 0 0 12px 0; }

/* Section badge */
.section-badge {
    display: inline-block;
    background: #161928;
    border: 1px solid #2a2f4a;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #8892b0;
    margin: 2px 2px;
}

/* Feedback boxes */
.fb-correct {
    background: #0d2b25;
    border: 1px solid #00d4aa;
    border-radius: 8px;
    padding: 12px 16px;
    color: #00d4aa;
    font-weight: 600;
    margin-top: 12px;
}
.fb-wrong {
    background: #2b1515;
    border: 1px solid #ff6b6b;
    border-radius: 8px;
    padding: 12px 16px;
    color: #ff6b6b;
    font-weight: 600;
    margin-top: 12px;
}

/* Results screen */
.results-hero {
    text-align: center;
    padding: 24px 0 16px;
}
.score-big {
    font-size: 4rem;
    font-weight: 800;
    line-height: 1;
}
.tier-pill {
    display: inline-block;
    padding: 8px 24px;
    border-radius: 99px;
    font-size: 1.1rem;
    font-weight: 700;
    margin: 12px 0;
}

/* Streamlit native widget overrides for dark theme */
[data-testid="stMainBlockContainer"] {
    background-color: #0d0f1a;
    color: #e8eaf6;
}

/* Answer choice buttons */
[data-testid="stBaseButton-secondary"] {
    background-color: #1e2235;
    color: #e8eaf6;
    border: 1px solid #2a2f4a;
}
[data-testid="stBaseButton-secondary"]:hover {
    background-color: #252840;
    border-color: #5a6290;
    color: #e8eaf6;
}

/* Markdown text */
[data-testid="stMarkdown"] p,
[data-testid="stMarkdown"] h1,
[data-testid="stMarkdown"] h2,
[data-testid="stMarkdown"] h3 {
    color: #e8eaf6;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── ROUTING ───────────────────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state["page"] = "hub"
if "active_quiz" not in st.session_state:
    st.session_state["active_quiz"] = None


def go_hub():
    st.session_state["page"] = "hub"
    st.session_state["active_quiz"] = None


def go_quiz(quiz_id: str):
    st.session_state["page"] = "quiz"
    st.session_state["active_quiz"] = quiz_id
    init_quiz_state(quiz_id)


# ── HUB PAGE ──────────────────────────────────────────────────────────────────


def render_hub():
    st.markdown(
        """
<div style="text-align:center; padding: 32px 0 24px;">
  <div style="font-size:3rem; margin-bottom:12px;">⚡</div>
  <h1 style="font-size:2.2rem; font-weight:800; margin:0 0 8px;">VelocityHire Quiz Hub</h1>
  <p style="color:#8892b0; max-width:480px; margin:0 auto; line-height:1.6;">
    Test your knowledge of the VelocityHire recruitment platform.<br>
    Choose a quiz below to get started.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    for quiz_id, quiz in QUIZZES.items():
        accent = quiz["accent"]
        sections_html = "".join(
            f'<span class="section-badge">S{i + 1} · {s}</span>'
            for i, s in enumerate(quiz["sections"])
        )
        st.markdown(
            f"""
<div class="quiz-card" style="border-color:{accent}22;">
  <h3 style="color:{accent};">{quiz['title']}</h3>
  <p>{quiz['description']}</p>
  <div style="margin-bottom:12px;">
    {sections_html}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button(f"Start {quiz['subtitle']} →", key=f"start_{quiz_id}", use_container_width=True):
            go_quiz(quiz_id)
            st.rerun()

    st.markdown(
        "<p style='text-align:center; color:#8892b0; margin-top:32px; font-size:0.85rem;'>"
        "VelocityHire Quiz Hub · 120 questions across 3 quizzes</p>",
        unsafe_allow_html=True,
    )


# ── QUIZ PAGE ─────────────────────────────────────────────────────────────────


def render_quiz(quiz_id: str):
    quiz = QUIZZES[quiz_id]
    accent = quiz["accent"]
    questions = quiz["questions"]
    sections = quiz["sections"]
    total = len(questions)

    init_quiz_state(quiz_id)

    # ── Back button ──
    if st.button("← Back to Hub", key="back_btn"):
        go_hub()
        st.rerun()

    st.markdown(
        f"""
<div style="text-align:center; padding: 16px 0 8px;">
  <h2 style="color:{accent}; margin:0 0 4px;">{quiz['title']}</h2>
  <p style="color:#8892b0; font-size:0.88rem; margin:0;">{quiz['description']}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Splash / start screen ──
    if not get_s(quiz_id, "started"):
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"""
<div style="text-align:center; padding:24px 0;">
  <div style="font-size:3rem; margin-bottom:16px;">{quiz['title'].split()[0]}</div>
  <h3 style="margin:0 0 8px;">Ready to be tested?</h3>
  <p style="color:#8892b0; line-height:1.6;">{quiz['description']}</p>
  <div style="margin:20px 0; display:flex; justify-content:center; gap:12px; flex-wrap:wrap;">
    <span style="background:#1e2235;border:1px solid #2a2f4a;border-radius:99px;padding:5px 14px;font-size:0.82rem;color:#8892b0;">📋 <strong style="color:{accent};">{total}</strong> Questions</span>
    <span style="background:#1e2235;border:1px solid #2a2f4a;border-radius:99px;padding:5px 14px;font-size:0.82rem;color:#8892b0;">🗂 <strong style="color:{accent};">8</strong> Sections</span>
    <span style="background:#1e2235;border:1px solid #2a2f4a;border-radius:99px;padding:5px 14px;font-size:0.82rem;color:#8892b0;">⏱ Self-paced</span>
    <span style="background:#1e2235;border:1px solid #2a2f4a;border-radius:99px;padding:5px 14px;font-size:0.82rem;color:#8892b0;">🎯 Instant feedback</span>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button("Start Quiz →", key=f"begin_{quiz_id}", use_container_width=True):
                set_s(quiz_id, "started", True)
                st.rerun()
        return

    # ── Results screen ──
    if get_s(quiz_id, "finished"):
        answers = get_s(quiz_id, "answers")
        answered = get_s(quiz_id, "answered")
        score = sum(
            1
            for i, q in enumerate(questions)
            if answered[i] and answers[i] == q["a"]
        )
        tier_label, tier_color = score_tier(score, total)

        st.markdown(
            f"""
<div class="results-hero">
  <div class="score-big" style="color:{accent};">{score}<span style="font-size:1.5rem;color:#8892b0;">/{total}</span></div>
  <div class="tier-pill" style="background:{tier_color}22; color:{tier_color}; border:1px solid {tier_color}44;">{tier_label}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Per-section breakdown
        st.markdown("#### Section Breakdown")
        for si, sname in enumerate(sections):
            qs = [(i, q) for i, q in enumerate(questions) if q["s"] == si]
            sec_score = sum(1 for i, q in qs if answered[i] and answers[i] == q["a"])
            sec_total = len(qs)
            pct = int(sec_score / sec_total * 100) if sec_total else 0
            st.markdown(
                f"**S{si + 1} · {sname}** — {sec_score}/{sec_total} ({pct}%)"
            )
            st.progress(pct / 100)

        st.markdown("---")

        # Review table
        with st.expander("📋 Review all answers"):
            for i, q in enumerate(questions):
                if answered[i]:
                    user_a = answers[i]
                    correct = user_a == q["a"]
                    icon = "✅" if correct else "❌"
                    correct_text = f"{LETTERS[q['a']]}) {q['choices'][q['a']]}"
                    user_text = f"{LETTERS[user_a]}) {q['choices'][user_a]}" if user_a >= 0 else "Skipped"
                    st.markdown(
                        f"**Q{i + 1}.** {icon} {q['q']}  \n"
                        f"Your answer: `{user_text}`  \n"
                        f"Correct: `{correct_text}`"
                    )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Restart this quiz", use_container_width=True):
                n = len(questions)
                set_s(quiz_id, "current", 0)
                set_s(quiz_id, "answers", [-1] * n)
                set_s(quiz_id, "answered", [False] * n)
                set_s(quiz_id, "finished", False)
                set_s(quiz_id, "started", False)
                st.rerun()
        with col_b:
            if st.button("🏠 Back to Hub", use_container_width=True):
                go_hub()
                st.rerun()
        return

    # ── Active quiz ──
    current = get_s(quiz_id, "current")
    answers = get_s(quiz_id, "answers")
    answered = get_s(quiz_id, "answered")
    q = questions[current]

    # Progress bar
    progress_pct = current / total
    st.progress(progress_pct)
    st.markdown(
        f"<p style='color:#8892b0; font-size:0.82rem; text-align:right; margin-top:-8px;'>"
        f"Question {current + 1} of {total}"
        f"</p>",
        unsafe_allow_html=True,
    )

    # Section tabs (clickable)
    st.markdown("**Jump to section:**")
    tab_cols = st.columns(len(sections))
    for si, sname in enumerate(sections):
        with tab_cols[si]:
            # Determine status colour
            qs_in_sec = [(i, qx) for i, qx in enumerate(questions) if qx["s"] == si]
            all_done = all(answered[i] for i, _ in qs_in_sec)
            is_current = q["s"] == si
            btn_style = f"color:{accent}; font-weight:700;" if is_current else ""
            label = f"S{si + 1}" + (" ✓" if all_done else "")
            if st.button(label, key=f"{quiz_id}_tab_{si}", help=sname):
                first_idx = next((i for i, qx in enumerate(questions) if qx["s"] == si), current)
                set_s(quiz_id, "current", first_idx)
                st.rerun()

    # Question card
    st.markdown("---")
    st.markdown(
        f"<p style='color:{accent}; font-size:0.82rem; font-weight:600; margin-bottom:6px;'>"
        f"Section {q['s'] + 1}: {sections[q['s']]}"
        f"</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f"### Q{current + 1}. {q['q']}")

    # Answer choices
    is_answered = answered[current]
    user_choice = answers[current]

    if not is_answered:
        for i, choice_text in enumerate(q["choices"]):
            label = f"{LETTERS[i]}) {choice_text}"
            if st.button(label, key=f"{quiz_id}_choice_{current}_{i}", use_container_width=True):
                answers[current] = i
                answered[current] = True
                set_s(quiz_id, "answers", answers)
                set_s(quiz_id, "answered", answered)
                st.rerun()
    else:
        for i, choice_text in enumerate(q["choices"]):
            label = f"{LETTERS[i]}) {choice_text}"
            correct_ans = q["a"]
            if i == correct_ans:
                st.success(f"✓ {label}")
            elif i == user_choice and user_choice != correct_ans:
                st.error(f"✗ {label}")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;{label}")

        # Feedback
        if user_choice == q["a"]:
            st.markdown('<div class="fb-correct">✅ Correct!</div>', unsafe_allow_html=True)
        else:
            correct_text = f"{LETTERS[q['a']]}) {q['choices'][q['a']]}"
            st.markdown(
                f'<div class="fb-wrong">❌ Incorrect — Correct answer: {correct_text}</div>',
                unsafe_allow_html=True,
            )

    # Navigation row
    st.markdown("")
    nav_left, nav_mid, nav_right = st.columns([1, 2, 1])

    with nav_left:
        if current > 0:
            if st.button("← Prev", key=f"{quiz_id}_prev"):
                set_s(quiz_id, "current", current - 1)
                st.rerun()

    with nav_mid:
        # Skip button (only when not yet answered)
        if not is_answered:
            if st.button("⏭ Skip", key=f"{quiz_id}_skip", use_container_width=True):
                answered[current] = True
                answers[current] = -1
                set_s(quiz_id, "answers", answers)
                set_s(quiz_id, "answered", answered)
                if current < total - 1:
                    set_s(quiz_id, "current", current + 1)
                else:
                    set_s(quiz_id, "finished", True)
                st.rerun()

    with nav_right:
        if is_answered:
            if current < total - 1:
                if st.button("Next →", key=f"{quiz_id}_next"):
                    set_s(quiz_id, "current", current + 1)
                    st.rerun()
            else:
                if st.button("Finish 🎉", key=f"{quiz_id}_finish"):
                    set_s(quiz_id, "finished", True)
                    st.rerun()

    # Question mini-map
    st.markdown("---")
    st.markdown("**Question map:**")
    map_cols = st.columns(10)
    for idx in range(total):
        col = map_cols[idx % 10]
        if answered[idx]:
            icon = "✅" if answers[idx] == questions[idx]["a"] else "❌"
        else:
            icon = "·"
        marker = f"**{icon}**" if idx == current else icon
        col.markdown(marker, unsafe_allow_html=True)


# ── MAIN ROUTER ───────────────────────────────────────────────────────────────

page = st.session_state["page"]

if page == "hub":
    render_hub()
elif page == "quiz" and st.session_state["active_quiz"]:
    render_quiz(st.session_state["active_quiz"])
else:
    go_hub()
    st.rerun()
