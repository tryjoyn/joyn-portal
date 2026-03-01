# VISION.md — Joyn Living Vision Document

*Claude reads this before every autonomous build. Keep it current.*

Last updated: March 2026

---

## What Joyn Is

Joyn is the world's AI Workforce Operating System. Tagline: **We Staff Your Business With AI.**

Joyn is not a chatbot platform. Not automation software. Not HR tech. It is a staffing platform — businesses hire AI staff the same way they hire people.

**The philosophical foundation:** Human expertise is finite but the value it creates does not have to be. Joyn takes what a 30-year insurance veteran knows and makes it available to 10,000 clients simultaneously. Every product decision must pass one test: does this make human expertise more powerful, or does it merely replace it?

---

## The Two Modes

### AUTONOMOUS
Fully autonomous AI staff. Pre-trained by vetted domain experts. Live in 10 minutes. No configuration, no calibration, no human oversight required after setup. Output delivered — just works.
- Best for: SMB verticals, solo operators, growing businesses
- Examples: Iris (regulatory intelligence), Renew (renewal specialist), Dispatch (field dispatcher), Scout (lead qualifier), Comply, Brief, File, Publish

### SUPERVISED
Practitioner-led AI staff. Works alongside your team on complex, judgment-intensive engagements. Your practitioners direct, review, and calibrate. Builds a private calibration corpus that belongs to the client firm — never shared.
- Best for: Professional services firms, enterprise
- Examples: TDD Practice Team, Counsel (legal support), Accord (contract review), Ledger (financial reconciliation)

---

## Brand & Language Rules

- Say **hire** — never activate
- Say **staff** — never agents
- Say **role** — never function
- Say **letting someone go** — never unsubscribing
- Say **Autonomous** — never "Ready" or "Always On"
- Say **Supervised** — never "Custom" or "Craft"
- Platform name: **Joyn** (capital J)
- Website: **tryjoyn.me** (with Y — never tryjoin)
- Email: hire@tryjoyn.me
- GitHub org: github.com/tryjoyn

---

## Tech Stack (Do Not Change Without Instruction)

- Every page is a **single self-contained HTML file**. All CSS and JS inline.
- No React, Vue, Tailwind, Bootstrap, or any npm dependency on the frontend.
- **Fonts (Google Fonts CDN only):** Cormorant Garamond (headings/display), DM Mono (labels/mono), Syne (body)
- **Colour palette (current):**
  - `--white: #fafaf8`
  - `--ink: #111110`
  - `--ink-secondary: #3f3f3e`
  - `--rule: #e8e4dc`
  - `--rule-mid: #d0ccc4`
  - `--surface: #f4f1eb`
  - `--gold-display: #b8902a`
  - `--gold-text: #8B6914`
  - `--gold-hover: #7a5c10`
- **Forms:** Web3Forms API key `5b972adb-feba-4546-a657-02d5e29b6e29` — all submissions go to hire@tryjoyn.me
- **Hosting:** GitHub Pages — auto-deploys from main branch of github.com/tryjoyn/website
- **Deploy time:** ~60 seconds from push to live

---

## Live Pages (as of March 2026)

| URL | File | Status |
|-----|------|--------|
| tryjoyn.me | `index.html` | ✓ Live |
| tryjoyn.me/marketplace/ | `marketplace/index.html` | ✓ Live |
| tryjoyn.me/marketplace/iris-insurance-regulatory.html | `marketplace/iris-insurance-regulatory.html` | ✓ Live |
| tryjoyn.me/marketplace/creator-studio.html | `marketplace/creator-studio.html` | ✓ Live |
| tryjoyn.me/practice/tdd-practice-team.html | `practice/tdd-practice-team.html` | ✓ Live |
| tryjoyn.me/marketplace/admin.html | `marketplace/admin.html` | ✓ Live (not publicly linked) |

---

## AI Staff Roster

### Live

| Name | Role | Mode | Vertical |
|------|------|------|----------|
| **Iris** | Insurance Regulatory Intelligence | Autonomous | Insurance |
| **TDD Practice Team** | Technology Due Diligence · 8 Agents | Supervised | Technology |

### Pipeline (coming-soon → auto-unlocks via GitHub Actions cron)

| Name | Role | Mode | Unlock Date |
|------|------|------|-------------|
| **Renew** | Renewal Specialist | Autonomous | 31 Mar 2026 |
| **Dispatch** | Field Services Dispatcher | Autonomous | 31 Mar 2026 |
| **Scout** | Lead Qualifier & Showing Coordinator | Autonomous | 14 Apr 2026 |
| **Comply** | Compliance Monitor | Autonomous | 28 Apr 2026 |
| **Brief** | Client Brief Specialist | Autonomous | 12 May 2026 |
| **File** | Document Filing Specialist | Autonomous | 26 May 2026 |
| **Counsel** | Legal Counsel Support | Supervised | 9 Jun 2026 |
| **Accord** | Contract Review Specialist | Supervised | 23 Jun 2026 |
| **Ledger** | Financial Reconciliation | Supervised | 7 Jul 2026 |
| **Publish** | Content Strategist | Autonomous | 21 Jul 2026 |

Roster data lives in `data/roster.json`. Auto-unlock runs every Monday 9am UTC via `.github/workflows/weekly-roster.yml` using `scripts/unlock_roster.py`.

---

## Known Issues (fix on next relevant build)

- **Browse AI Staff button** on homepage links to `#` — should link to `marketplace/index.html`

---

## Locked Decisions (do not reverse without explicit instruction)

- **Autonomous vs Supervised distinction** — core product differentiation, everything builds on this
- **No pricing on site** — too early, revisit at first revenue
- **Staffing language not agent language** — staff, hire, role, let go
- **Chick-fil-A creator admission model** — selective quality over open marketplace
- **Human expertise amplified not replaced** — values commitment
- **No live deployment counter** — add at 50+ deployments
- **No revenue share % on creator-studio** — replaced with "Performance-linked income, confirmed at offer"

---

## Roster Auto-Unlock System

Staff transition from `coming-soon` → `live` automatically:

1. `data/roster.json` — source of truth for all staff status and unlock dates
2. `scripts/unlock_roster.py` — reads roster, flips status if `unlockDate <= today`, commits
3. `.github/workflows/weekly-roster.yml` — GitHub Actions cron (`0 9 * * 1`) with `permissions: contents: write`
4. `marketplace/admin.html` — hidden founder dashboard for tracking hires and interest (not publicly linked)

---

## Creator Studio (`marketplace/creator-studio.html`)

Page for domain experts who want to build AI staff on the Joyn platform. Key sections:
- Qualifications panel (honest who Joyn looks for)
- Platform tiles: Claude, Emergent, Manus, make.com
- 5-layer knowledge architecture (Domain → Methodology → Workflow → Voice → Standards)
- Earnings calculator: log-scale slider (10–500 deployments), illustrative range, no specific % shown
- 21 open roles across 7 verticals (3 per vertical): Insurance & Risk, Financial Services, Healthcare, Legal & Compliance, Real Estate, Operations, Technology
- Filter bar: Mode (All / Autonomous / Supervised) + Vertical (7 options), with live count + 6-per-page pagination
- Web3Forms application form

---

*Joyn · tryjoyn.me · Where Human Expertise Comes to Scale Itself*
