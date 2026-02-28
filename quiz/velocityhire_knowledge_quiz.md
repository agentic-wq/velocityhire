# 🎯 VelocityHire Knowledge Quiz — 40 Questions

## Section 1: Architecture & Core Concept (Q1–8)

**Q1. What is the core thesis VelocityHire was built to prove?**
A) Credentials beat experience  
B) Learning velocity beats credentials  
C) Years of experience predict performance  
D) Certifications are the best hiring signal  

**Q2. How many LangGraph agents does VelocityHire use in its pipeline?**
A) 1  
B) 2  
C) 3  
D) 5  

**Q3. What Python framework powers VelocityHire's API server?**
A) Django  
B) Flask  
C) FastAPI  
D) Tornado  

**Q4. What LangGraph class is used to define the agent orchestration graph?**
A) AgentGraph  
B) StateGraph  
C) WorkflowGraph  
D) PipelineGraph  

**Q5. What database does VelocityHire use in the demo/hackathon version?**
A) PostgreSQL  
B) MongoDB  
C) SQLite  
D) Redis  

**Q6. What is the name of the in-memory dictionary used to cache pipeline results for re-runs?**
A) _RUN_CACHE  
B) _RESULT_STORE  
C) _PIPELINE_CACHE  
D) _DEMO_CACHE  

**Q7. What replay delay (in seconds per stage) is used during cached pipeline re-runs to keep the animation alive?**
A) 0.1s  
B) 0.35s  
C) 1.0s  
D) 2.0s  

**Q8. What is the per-agent hard timeout (in seconds) to prevent demo hangs?**
A) 10s  
B) 20s  
C) 30s  
D) 60s  

## Section 2: The Three Agents (Q9–18)

**Q9. What does Agent 1 produce?**
A) Job match score  
B) LinkedIn outreach message  
C) Adaptability score and tier  
D) ATS webhook payload  

**Q10. What does Agent 2 produce?**
A) Outreach campaign  
B) Total match score, match tier, and interview recommendation  
C) Candidate profile summary  
D) Analytics dashboard data  

**Q11. What does Agent 3 produce?**
A) Adaptability score  
B) Job description analysis  
C) Outreach campaign: LinkedIn message, email, follow-up, recruiter note  
D) Database schema  

**Q12. What are the four outreach tiers produced by Agent 3? (Select the correct set)**
A) HOT / WARM / COLD / DEAD  
B) PRIORITY / STANDARD / NURTURE / ARCHIVE  
C) A / B / C / D  
D) FAST / NORMAL / SLOW / SKIP  

**Q13. What does Agent 1 look for when scoring adaptability? (Best answer)**
A) Only years of experience  
B) Only education level  
C) Hackathon wins, recent certifications, GitHub commits, startup experience, learning signals  
D) Salary expectations  

**Q14. Which Python function name in agent1 runs the full profile analysis?**
A) run_agent  
B) score_profile  
C) analyze_profile  
D) process_candidate  

**Q15. Which function in agent2 performs job matching?**
A) run_matching  
B) match_candidate  
C) score_job_fit  
D) evaluate_candidate  

**Q16. Which function in agent3 generates outreach?**
A) create_campaign  
B) write_outreach  
C) generate_outreach  
D) build_message  

**Q17. In MOCK_MODE, what drives the scoring logic?**
A) OpenAI GPT-4o API calls  
B) Deploy AI OAuth2 endpoint  
C) Rule-based deterministic scoring  
D) Random number generation  

**Q18. Why is MOCK_MODE hard-locked to true in the demo?**
A) GPT-4o is too expensive  
B) The Deploy AI /openai/chat/completions endpoint returns 403 and direct sk_ auth returns 401 without OAuth2 provisioning  
C) The agents are too slow with real LLMs  
D) The hackathon rules prohibit real API calls  

## Section 3: Demo Features & UI (Q19–24)

**Q19. What is the name of the demo feature that shows how traditional ATS rankings differ from VelocityHire's rankings?**
A) The Talent Gap  
B) The Ranking Flip  
C) The Score Reversal  
D) The Credential Check  

**Q20. How many demo candidates does VelocityHire process in the main pipeline run?**
A) 3  
B) 4  
C) 5  
D) 10  

**Q21. Which demo candidate typically ranks lowest in traditional ATS but higher in VelocityHire?**
A) Marcus Rivera  
B) Jordan Kim  
C) Elena Voronova  
D) Alex Chen  

**Q22. What is the polling interval (in milliseconds) used by the front-end to check pipeline progress?**
A) 100ms  
B) 300ms  
C) 600ms  
D) 1000ms  

**Q23. What chart library does the VelocityHire UI use for analytics visualizations?**
A) D3.js  
B) Highcharts  
C) Chart.js v4.4.0  
D) ApexCharts  

**Q24. What CSS breakpoints are used for mobile responsiveness?**
A) 480px / 320px  
B) 768px / 480px  
C) 720px / 440px  
D) 1024px / 768px  

## Section 4: API Endpoints (Q25–28)

**Q25. Which endpoint starts a background pipeline run and returns a run_id?**
A) GET /demo/start  
B) POST /demo/run  
C) POST /pipeline/execute  
D) GET /demo/run  

**Q26. Which endpoint allows scoring a single custom profile through all 3 agents?**
A) POST /demo/analyze  
B) POST /score/profile  
C) POST /demo/score-one  
D) GET /demo/score  

**Q27. What HTTP status code is returned when an invalid run_id is requested from /demo/progress/{run_id}?**
A) 400  
B) 401  
C) 403  
D) 404  

**Q28. Which endpoint returns the full analytics JSON for the dashboard?**
A) GET /dashboard  
B) GET /analytics/data  
C) GET /stats  
D) GET /metrics  

## Section 5: ATS Integrations (Q29–31)

**Q29. Which three ATS platforms does VelocityHire integrate with?**
A) Workday, SAP, Oracle  
B) Greenhouse, Lever, BambooHR  
C) Taleo, iCIMS, SmartRecruiters  
D) Jobvite, Workable, Recruitee  

**Q30. What technique does VelocityHire use to normalize payloads from different ATS platforms?**
A) API gateway transformation  
B) Webhook normalizers  
C) GraphQL resolvers  
D) ETL pipelines  

**Q31. What is the name of the shared module that handles ATS integrations?**
A) shared/connectors.py  
B) shared/ats_webhooks.py  
C) shared/ats_integrations.py  
D) shared/integrations.py  

## Section 6: Security Fixes (Q32–36)

**Q32. What XSS attack vector was identified in the security audit?**
A) SQL injection via candidate name  
B) Script tags reflected verbatim through profile_text into innerHTML in the live scorer UI  
C) Cookie theft via CSRF  
D) Path traversal via file upload  

**Q33. What server-side function was added to sanitize profile_text input?**
A) sanitize_input()  
B) clean_html()  
C) _strip_html()  
D) remove_tags()  

**Q34. What maximum character limit was enforced on profile_text in ScoreOneRequest?**
A) 10,000  
B) 25,000  
C) 50,000  
D) 100,000  

**Q35. What JavaScript helper function was added to the UI to escape HTML before inserting into innerHTML?**
A) sanitize()  
B) escHtml()  
C) encodeHtml()  
D) htmlEscape()  

**Q36. After the CORS fix, what HTTP methods are explicitly allowed?**
A) GET, POST, PUT, DELETE  
B) GET only  
C) GET, POST  
D) POST, PUT, PATCH  

## Section 7: Database & Analytics (Q37–38)

**Q37. What critical bug in shared/analytics.py was fixed during Phase 2?**
A) Missing index on candidate_id  
B) _fetch_all() used positional zip() against metadata columns, causing misalignment because ALTER TABLE appended company_id at the end  
C) Analytics query returned duplicate rows  
D) Date formatting was incorrect  

**Q38. What method is used to correctly map SQLAlchemy row results after the analytics fix?**
A) dict(row)  
B) row.to_dict()  
C) dict(row._mapping)  
D) row.as_dict()  

## Section 8: Production Roadmap (Q39–40)

**Q39. What is the planned database migration path from the hackathon version to production?**
A) SQLite → MySQL → Oracle  
B) SQLite → PostgreSQL with Redis caching  
C) SQLite → MongoDB  
D) SQLite → DynamoDB  

**Q40. What feature is identified in the production roadmap to replace the in-memory _PIPELINE_CACHE?**
A) Memcached  
B) Varnish  
C) Redis  
D) CDN edge caching  

## 📋 Answer Key

| Q | A | Q | A | Q | A | Q | A |
|---|---|---|---|---|---|---|---|
| 1 | B | 11| C | 21| C | 31| C |
| 2 | C | 12| B | 22| C | 32| B |
| 3 | C | 13| C | 23| C | 33| C |
| 4 | B | 14| C | 24| C | 34| C |
| 5 | C | 15| B | 25| B | 35| B |
| 6 | C | 16| C | 26| C | 36| C |
| 7 | B | 17| C | 27| D | 37| B |
| 8 | C | 18| B | 28| B | 38| C |
| 9 | C | 19| B | 29| B | 39| B |
| 10| B | 20| C | 30| B | 40| C |

**Scoring:** 38-40 = Expert | 30-37 = Proficient | 20-29 = Familiar | <20 = Review the codebase