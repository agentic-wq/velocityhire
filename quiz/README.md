# VelocityHire Quiz System

A self-contained, browser-based knowledge-validation tool for the VelocityHire recruitment platform. Three interactive quizzes cover the project documentation, system architecture, and demo application code — 40 questions each, all client-side.

---

## Files

| File | Purpose |
|------|---------|
| `server.py` | Lightweight Python HTTP server (port 3004) that serves the quiz directory as static files |
| `index.html` | Hub page — displays the three quiz cards and links to each quiz |
| `docs-quiz.html` | 40-question quiz on project documentation (BRD, personas, roadmap, scoring system) |
| `arch-quiz.html` | 40-question quiz on architecture and full-stack implementation |
| `demo-quiz.html` | 40-question deep-dive into `demo/app.py` |
| `velocityhire_knowledge_quiz.md` | Knowledge-base / answer key used to author the questions |

---

## Running the Quiz Server

```bash
cd quiz
python server.py
# Serving on port 3004
```

Open `http://localhost:3004` in a browser to reach the hub.

---

## How It Works

### Backend

`server.py` is a single-file Python HTTP server built on `http.server.SimpleHTTPRequestHandler`. It serves every file in the `quiz/` directory statically and suppresses access logs. There are no API endpoints, no authentication, and no database — purely static file serving.

### Frontend

All quiz logic runs entirely in the browser. Each quiz HTML file embeds its questions directly in a `<script>` block as a JavaScript array. No network requests are made after the page loads.

**Question object shape:**
```js
{
  section: "S1 · Architecture & Core Concepts",
  question: "What is the core thesis of VelocityHire?",
  choices: ["A) ...", "B) ...", "C) ...", "D) ..."],
  correct: 1,        // zero-based index of the correct choice
  explanation: "..." // shown immediately after the user answers
}
```

### State Management

- **In-memory JS state** — tracks the current question index, per-question selections, and running score.
- **LocalStorage** — persists progress so a page refresh resumes where the user left off.

### User Interaction Flow

1. User opens the hub (`index.html`) and clicks a quiz card.
2. The quiz page loads; the first question is displayed with four choice buttons.
3. The user clicks a choice — the answer is locked immediately and color-coded feedback appears (✓ green / ✗ red) together with the explanation text.
4. The user clicks **Next** to advance. The progress bar and section tabs update.
5. Section tabs can be clicked directly to jump between the eight sections.
6. After the 40th question the results screen shows the total score and a per-section breakdown.

### Scoring Tiers

| Score | Level |
|-------|-------|
| 38–40 | Expert |
| 30–37 | Proficient |
| 20–29 | Familiar |
| < 20  | Review the codebase |

---

## Quiz Content Areas

Each quiz is divided into **8 sections** of 5 questions:

| # | Topic |
|---|-------|
| 1 | Architecture & Core Concepts |
| 2 | The Three Agents (adaptability → matching → outreach) |
| 3 | Demo Features & UI |
| 4 | API Endpoints |
| 5 | ATS Integrations (Greenhouse, Lever, BambooHR) |
| 6 | Security Fixes (XSS via `_strip_html()`, HTML escaping) |
| 7 | Database & Analytics |
| 8 | Production Roadmap |

---

## UI / Styling

- Dark theme with per-quiz accent colors:
  - **Docs Quiz** — Teal (`#00d4aa`)
  - **Demo Quiz** — Purple (`#6c63ff`)
  - **Arch Quiz** — Amber (`#f59e0b`)
- Responsive layout with a mobile breakpoint at ~600 px.
- Sticky header containing the quiz title and progress bar.
- Smooth CSS transitions (0.2 s – 0.4 s) on choice hover/select states.
