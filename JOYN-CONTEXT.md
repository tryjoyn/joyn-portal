# JOYN-CONTEXT.md — Project Context for Claude.ai

*Upload this file to your Claude.ai project to give Claude full context about the Joyn codebase.*

Last updated: March 2026

---

## Project Overview

**Joyn** is a static marketing site for an AI staffing platform. Live at **tryjoyn.me**. Hosted on GitHub Pages, auto-deploys from `main` branch of `github.com/tryjoyn/website` (~60s deploy time).

Businesses hire AI staff the same way they hire people. Brand language: say *hire* (not activate), *staff* (not agents), *role* (not function), *letting someone go* (not unsubscribing).

---

## Tech Stack (Locked — Do Not Change Without Instruction)

- Every page is a **single self-contained HTML file** — all CSS and JS inline
- No React, Vue, Tailwind, Bootstrap, or any npm dependency
- Fonts via Google Fonts CDN only: **Cormorant Garamond** (headings), **DM Mono** (labels/mono), **Syne** (body)
- Forms use **Web3Forms** API key `5b972adb-feba-4546-a657-02d5e29b6e29` → hire@tryjoyn.me
- Deploy: `git push` from `Joyn/` directory → GitHub Pages auto-deploys

### Colour Palette

```css
--white: #fafaf8;
--ink: #111110;
--ink-secondary: #3f3f3e;
--rule: #e8e4dc;
--rule-mid: #d0ccc4;
--surface: #f4f1eb;
--gold-display: #b8902a;
--gold-text: #8B6914;
--gold-hover: #7a5c10;
```

---

## Site Structure

```
Joyn/
├── index.html                                  # Homepage (tryjoyn.me)
├── VISION.md                                   # Living vision document
├── JOYN-CONTEXT.md                             # This file
├── data/
│   └── roster.json                             # Staff roster (source of truth)
├── scripts/
│   └── unlock_roster.py                        # Auto-unlock script (GitHub Actions)
├── .github/
│   └── workflows/
│       └── weekly-roster.yml                   # Monday 9am UTC cron
├── marketplace/
│   ├── index.html                              # AI staff marketplace
│   ├── iris-insurance-regulatory.html          # Iris listing page
│   ├── creator-studio.html                     # Apply to build AI staff
│   └── admin.html                              # Founder dashboard (NOT publicly linked)
├── practice/
│   └── tdd-practice-team.html                  # TDD Practice Team listing
├── JOYN-DEPLOYMENT-STANDARD.md                 # The Bar — machine-readable source of truth
└── docs/
    └── the-bar-v1.docx                         # The Bar — creator-facing deployment standard
```

---

## Terminology (Critical)

| Use this | Not this |
|----------|----------|
| **Autonomous** | Ready, Always On |
| **Supervised** | Custom, Craft |
| **hire** | activate, subscribe |
| **staff** | agents, bots |
| **role** | function, task |
| **letting someone go** | unsubscribing, cancelling |

---

## The Two Modes

### Autonomous
Fully autonomous AI staff. Pre-trained by vetted domain experts. Live in 10 minutes. No configuration or oversight required after setup.

### Supervised
Practitioner-led AI staff. Works alongside your team on complex, judgment-intensive work. Practitioners direct, review, and calibrate.

---

## AI Staff Roster

### Live Now

| Name | Role | Mode | Vertical |
|------|------|------|----------|
| **Iris** | Insurance Regulatory Intelligence | Autonomous | Insurance |
| **TDD Practice Team** | Technology Due Diligence · 8 Agents | Supervised | Technology |

### Pipeline (auto-unlocks on schedule)

| Name | Role | Mode | Unlock Date |
|------|------|------|-------------|
| **Renew** | Renewal Specialist | Autonomous | 2026-03-31 |
| **Dispatch** | Field Services Dispatcher | Autonomous | 2026-03-31 |
| **Scout** | Lead Qualifier & Showing Coordinator | Autonomous | 2026-04-14 |
| **Comply** | Compliance Monitor | Autonomous | 2026-04-28 |
| **Brief** | Client Brief Specialist | Autonomous | 2026-05-12 |
| **File** | Document Filing Specialist | Autonomous | 2026-05-26 |
| **Counsel** | Legal Counsel Support | Supervised | 2026-06-09 |
| **Accord** | Contract Review Specialist | Supervised | 2026-06-23 |
| **Ledger** | Financial Reconciliation | Supervised | 2026-07-07 |
| **Publish** | Content Strategist | Autonomous | 2026-07-21 |

---

## Page-by-Page Notes

### `index.html` — Homepage

- Mode cards show Autonomous and Supervised
- Staff section links to marketplace
- Video embed: Vimeo, max-width 720px, top 55px clipped (overflow hidden)
- Copy: "Performance-linked income on every hire" (not "Revenue share")
- Known issue: "Browse AI Staff" button links to `#` — should be `marketplace/index.html`

### `marketplace/index.html` — Marketplace

- Filter bar: Mode (All / Autonomous / Supervised) + Vertical (7 options)
- Verticals: Insurance & Risk, Financial Services, Healthcare, Legal & Compliance, Real Estate, Operations, Technology
- Live staff cards: Iris (with ROI chips), TDD Practice Team (with ROI chips)
- 10 coming-soon pipeline cards
- Card markup classes: `.card-top`, `.card-name`, `.card-role`, `.card-desc`
- ROI chips on Iris: "~4h analyst time saved/week", "0 missed bulletins"
- ROI chips on TDD: "vs 2–4 week standard", "8 analysts in parallel"

### `marketplace/iris-insurance-regulatory.html` — Iris Listing

- Mode shown as "Autonomous · Live Now"
- Monitors Florida OIR continuously

### `practice/tdd-practice-team.html` — TDD Practice Team Listing

- Mode shown as "Supervised Mode"
- Technology Due Diligence, Pre-LOI screening to IC-ready in 72h

### `marketplace/creator-studio.html` — Creator Studio

For domain experts applying to build AI staff on the platform.

Sections:
1. Hero + qualifications panel
2. Platform tiles: Claude, Emergent, Manus, make.com
3. 5-layer knowledge architecture: Domain → Methodology → Workflow → Voice → Standards
4. Earnings calculator: log-scale slider (10–500 deployments), illustrative £50–£120/deployment range, **no specific % shown** — "Performance-linked income, confirmed at offer"
5. Open roles: 21 roles across 7 verticals (3 per vertical), with Mode + Vertical filter bar, 6-per-page pagination
6. Web3Forms application form

Open roles verticals: Insurance & Risk, Financial Services, Healthcare, Legal & Compliance, Real Estate, Operations, Technology

### `marketplace/admin.html` — Founder Dashboard

- Not publicly linked anywhere
- URL: tryjoyn.me/marketplace/admin.html
- Sections: New hires this week (editable table), Interest forms this week (editable table), Pipeline status
- Week labels auto-set from JS
- Rows are contentEditable — data is not persisted (manual tracking only)

### `data/roster.json`

JSON array, source of truth for all staff. Fields per entry:
```json
{
  "name": "string",
  "role": "string",
  "mode": "autonomous | supervised",
  "vertical": "string",
  "status": "live | coming-soon",
  "unlockDate": "YYYY-MM-DD | null",
  "description": "string"
}
```

### `scripts/unlock_roster.py`

- Reads `data/roster.json`
- Checks `unlockDate` vs today's date
- If `unlockDate <= today` and `status == "coming-soon"`, flips to `"live"`
- Commits changes via subprocess
- Designed to be called by GitHub Actions

### `.github/workflows/weekly-roster.yml`

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday 9am UTC
  workflow_dispatch:

jobs:
  update-roster:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # Required — allows github-actions[bot] to push
```

---

## Deploy Process

```bash
cd Joyn
git add <specific files>
git commit -m "descriptive message"
git push
# GitHub Pages deploys automatically in ~60 seconds
```

**Never use** `git add -A` or `git add .` — always add specific files by name.

The remote URL includes a PAT with `workflow` scope (required for pushing to `.github/workflows/`).

---

## Locked Decisions

- **Autonomous vs Supervised** — core product differentiation, do not rename again
- **No pricing on site** — too early, revisit at first revenue
- **Staffing language** — staff, hire, role, let go (never agent language)
- **Chick-fil-A creator model** — selective quality over open marketplace
- **Human expertise amplified not replaced** — core values
- **No live deployment counter** — add at 50+ deployments
- **No revenue share % on creator-studio** — "Performance-linked income, confirmed at offer"
- **No build tools** — single-file HTML with inline CSS/JS only
- **The Bar v1.0 is the deployment standard** — Five gates, all must pass, no partial credit. Probe is the reference implementation. Reviewer Agent evaluates all submissions. Lives at JOYN-DEPLOYMENT-STANDARD.md. Creator docx at docs/the-bar-v1.docx. Linked from Creator Studio.

---

## Contact & Access

- Live site: tryjoyn.me
- GitHub repo: github.com/tryjoyn/website
- Email: hire@tryjoyn.me
- Web3Forms key: `5b972adb-feba-4546-a657-02d5e29b6e29`
