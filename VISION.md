# VISION.md — Joyn Living Vision Document

*Claude reads this before every autonomous build. Keep it current.*

Last updated: February 2026

---

## What Joyn Is

Joyn is the world's AI Workforce Operating System. Tagline: **We Staff Your Business With AI.**

Joyn is not a chatbot platform. Not automation software. Not HR tech. It is a staffing platform — businesses hire AI staff the same way they hire people.

**The philosophical foundation:** Human expertise is finite but the value it creates does not have to be. Joyn takes what a 30-year insurance veteran knows and makes it available to 10,000 clients simultaneously. Every product decision must pass one test: does this make human expertise more powerful, or does it merely replace it?

---

## The Two Modes

### ALWAYS ON
Fully autonomous AI staff. Pre-trained by vetted domain experts. Live in 10 minutes. No configuration, no calibration, no human oversight required after setup. Output delivered — just works.
- Best for: Solo and Team tiers, SMB verticals
- Examples: salon receptionist, insurance renewal specialist, trades dispatcher, lead qualifier, content strategist

### CRAFT
Practitioner-led AI staff. Works alongside your team on complex, judgment-intensive engagements. Your practitioners direct, review, and calibrate. Builds a private calibration corpus that belongs to the client firm — never shared.
- Best for: Practice and Enterprise tiers, professional services
- Examples: TDD Practice Team, legal research, financial analysis

---

## The Four Tiers

| Tier | Who | Mode |
|------|-----|------|
| **Solo** | Independent operators, local businesses | Always On — one AI staff member |
| **Team** | Growing businesses, mid-market | Always On — up to 5 coordinated AI staff |
| **Practice** | Professional services firms | Craft — engagement-scoped teams |
| **Enterprise** | Large organisations | Craft — right-to-hire, own AI staff outright |

---

## Brand & Language Rules

- Say **hire** — never activate
- Say **staff** — never agents
- Say **role** — never function
- Say **letting someone go** — never unsubscribing
- Platform name: **Joyn** (capital J)
- Website: **tryjoyn.me** (with Y — never tryjoin)
- Email: hire@tryjoyn.me
- GitHub org: github.com/tryjoyn

---

## Tech Stack (Do Not Change Without Instruction)

- Every page is a **single self-contained HTML file**. All CSS and JS inline.
- No React, Vue, Tailwind, Bootstrap, or any npm dependency on the frontend.
- **Fonts (Google Fonts CDN only):** Cormorant Garamond (headings/display), DM Mono (labels/mono), Syne (body)
- **Colour palette:** `--paper:#f5f1e8` `--ink:#0d0c0a` `--gold:#b8902a` `--gold2:#c9a84c` `--night:#0d0c0a` `--ntext:#f0ece3`
- **Forms:** Web3Forms API key `5b972adb-feba-4546-a657-02d5e29b6e29` — all submissions go to hire@tryjoyn.me
- **Hosting:** GitHub Pages — auto-deploys from main branch
- **Deploy time:** ~60 seconds from commit to live

---

## Live Pages (as of February 2026)

| URL | File | Status |
|-----|------|--------|
| tryjoyn.me | index.html | ✓ Live |
| tryjoyn.me/marketplace/index.html | marketplace/index.html | ✓ Live |
| tryjoyn.me/marketplace/iris-insurance-regulatory.html | marketplace/iris-insurance-regulatory.html | ✓ Live |
| tryjoyn.me/practice/tdd-practice-team.html | practice/tdd-practice-team.html | ✓ Live |

---

## Known Issues (fix on next relevant build)

- **Browse AI Staff button** on homepage scrolls to hero instead of linking to marketplace. Fix: change href from `#` to `marketplace/index.html` in Solo and Team tier panels.
- **marketplace/ URL** shows blank — must use full path `/marketplace/index.html`. GitHub Pages caching — resolves over time.

---

## Locked Decisions (do not reverse without explicit instruction)

- **Always On vs Craft distinction** — core product differentiation, everything builds on this
- **No pricing on site** — too early, revisit at first revenue
- **Staffing language not agent language** — staff, hire, role, let go
- **Chick-fil-A creator admission model** — selective quality over open marketplace
- **Human expertise amplified not replaced** — values commitment
- **No live deployment counter** — add at 50+ deployments

---

## AI Staff Available

| Name | Mode | Status |
|------|------|--------|
| Iris — Insurance Regulatory Intelligence | Always On | ✓ Live listing page |
| TDD Practice Team (8 agents) | Craft | ✓ Live listing page, pipeline built not deployed |
| Dispatch — Trades Field Services Dispatcher | Always On | Planned |
| Scout — Real Estate Lead Qualifier | Always On | Planned |
| Renew — Insurance Renewal Specialist | Always On | Planned |
| Publish — Marketing Content Strategist | Always On | Planned |

---

## First Revenue Path

1. **CelebrateFX** (digital marketing agency, Bahrain) — warm lead, needs Publish listing page
2. **Insurance independent agents** — Iris is live, direct outreach
3. **TDD proof engagement** — one PE firm or corp dev team, free proof to validate pipeline

---

*Joyn · tryjoyn.me · Where Human Expertise Comes to Scale Itself*
