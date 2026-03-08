# CLAUDE.md

> **MANDATORY FIRST READ — ALL AGENTS**
> This codebase is worked on by **Claude Code**, **Claude.ai**, **Manus**, and **Emergent**.
> If you are any AI agent starting a session on the Joyn project, you MUST read this file before writing any code.
> Then read `JOYN-CONTEXT.md`, `JOYN-DESIGN-SPEC.md`, and `VISION.md` before any significant build.
> Run `git pull` first. Update context files in the same commit as your code changes.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Deploy

```bash
git add <specific files>   # NEVER use git add . or git add -A
git commit -m "type: what changed"
git push                   # GitHub Pages auto-deploys in ~60 seconds
```

Live at **tryjoyn.me** · Repo: github.com/tryjoyn/website

---

## Tech Stack (Locked — Never Change Without Instruction)

- Every page is a **single self-contained HTML file** — all CSS and JS inline
- No React, Vue, Tailwind, Bootstrap, or any npm dependency
- No separate CSS/JS files — everything stays inline
- No `border-radius`, no box-shadows, no keyframe animations
- Transitions: 0.15s–0.2s ease only

**Fonts (Google Fonts CDN — these three only):**

| Font | Role |
|------|------|
| Cormorant Garamond | Headings, hero, display (weight 300–500) |
| DM Mono | Labels, tags, nav items, filter buttons, metadata |
| Syne | Body text, descriptions, card copy |

**Colour palette — CSS variables only, never hardcode hex:**
```css
--white: #fafaf8;  --ink: #111110;  --ink-secondary: #3f3f3e;
--rule: #e8e4dc;   --rule-mid: #d0ccc4;  --surface: #f4f1eb;
--gold-display: #b8902a;  --gold-text: #8B6914;  --gold-hover: #7a5c10;
```
- Gold on text → always `--gold-text`, never `--gold-display`
- No pure `#ffffff` or `#000000`

---

## Site Architecture

```
index.html                              ← Homepage
marketplace/
  index.html                            ← Marketplace (staff cards + embedded staff designer)
  iris-insurance-regulatory.html        ← Iris listing
  creator-studio.html                   ← Apply to build AI staff
  staff-designer.html                   ← Standalone (also embedded in marketplace/index.html)
  admin.html                            ← Founder dashboard — NOT publicly linked
practice/
  tdd-practice-team.html                ← TDD Practice Team listing
data/
  roster.json                           ← Staff roster source of truth
scripts/
  unlock_roster.py                      ← Auto-unlock: flips status coming-soon → live
.github/workflows/
  weekly-roster.yml                     ← Cron: Monday 9am UTC, runs unlock_roster.py
```

---

## Global Nav Pattern

All public pages use this nav structure:

```html
<nav class="nav" aria-label="Main navigation">
  <a href="[path-to-index.html]" class="nav-logo" aria-label="Joyn home">JOYN.</a>
  <div class="nav-links">
    <a href="[path-to-marketplace]" class="nav-link" [aria-current="page" if in marketplace section]>Marketplace</a>
    <a href="[path-to-creator-studio]" class="nav-link" [aria-current="page" if on creator-studio]>Creator Studio</a>
  </div>
  <!-- optional right CTA on listing pages only -->
</nav>
```

Active state: `aria-current="page"` on the matching nav link. CSS:
```css
.nav-link[aria-current="page"] { color: var(--ink); font-weight: 500; }
```

Breadcrumbs (`<nav class="breadcrumb">`) appear on all marketplace sub-pages — **not** on the homepage.

---

## Staff Designer Embed

The staff designer form is **embedded directly inside `marketplace/index.html`** (not just a link to `staff-designer.html`). All its CSS is scoped under `#sd-wrap` to prevent class conflicts with marketplace styles:

```css
#sd-wrap .hero { ... }   /* scoped — won't collide with .hero on marketplace */
```

The standalone `staff-designer.html` page still exists but is a secondary entry point.

---

## Dynamic Counts — Never Hardcode

Badge counts and role counts are populated by JS on render, not hardcoded in HTML:

```html
<strong id="count-display"></strong> available   <!-- JS fills this -->
<strong id="roles-count"></strong>               <!-- JS fills this -->
```

Never write `<strong>2</strong> available` or `21 roles` in HTML — these go stale.

---

## Roster System

`data/roster.json` is the single source of truth. Each entry:
```json
{ "name": "...", "role": "...", "mode": "autonomous|supervised",
  "vertical": "...", "status": "live|coming-soon", "unlockDate": "YYYY-MM-DD" }
```

GitHub Actions cron (`.github/workflows/weekly-roster.yml`) runs `scripts/unlock_roster.py` every Monday 9am UTC, which flips `coming-soon` → `live` when `unlockDate <= today`.

---

## Terminology (Auto-Correct — No Exceptions)

| Use | Never use |
|-----|-----------|
| **Autonomous** | Ready, Always On |
| **Supervised** | Custom, Craft |
| **hire** | activate, subscribe |
| **staff** | agents, bots |
| **role** | function, task |
| **letting someone go** | unsubscribing, cancelling |

---

## Locked Decisions

- No pricing on site
- No live deployment counter until 50+ deployments
- No revenue share % on Creator Studio — use "Performance-linked income, confirmed at offer"
- Chick-fil-A creator admission model — selective, not open marketplace
- No dark mode — warm off-white palette is fixed
- No build tools — single-file HTML forever

---

## Forms

All forms submit via Web3Forms → hire@tryjoyn.me:
```html
<input type="hidden" name="access_key" value="5b972adb-feba-4546-a657-02d5e29b6e29">
```

---

## Favicon

`/favicon.svg` — dark rounded square, geometric J in warm white, gold period dot. Referenced in all public page `<head>` blocks as:
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/favicon.svg">
```

---

## Staff Card Data Attributes (Gotcha)

Filter logic uses internal values that differ from display labels:

| Display | `data-mode` value |
|---------|-------------------|
| Autonomous | `always-on` |
| Supervised | `craft` |

The filter JS targets `#mode-group` and `#vert-group` by ID — not by `:first-of-type` / `:last-of-type`. Don't rename these IDs.

---

## Sticky Nav & Filter Heights

The nav is `position: sticky; top: 0; min-height: 60px`. The marketplace filter bar sticks at `top: 60px`. Any new sticky element on a page must account for 60px nav offset. On mobile the nav collapses to ~56px (see `@media` in marketplace/index.html).

Back-to-top buttons on Iris and TDD pages use `bottom: 5rem` on mobile to clear their fixed hire/brief bars. Other pages use the default `bottom: 2rem`.

---

## Ambiguity Rule

If an instruction is ambiguous — stop and ask **one clarifying question** before writing any code. Never assume intent. If context files conflict with the session prompt, flag the conflict rather than resolving silently.

---

## Foundational Standards (Read Before Any Build Involving Staff Behaviour or Hirer-Facing Features)

These files are non-negotiable. They are read in priority order. If a session prompt conflicts with anything in these files, these files win. Flag the conflict to the founder before proceeding.

| Priority | File | Purpose | Read when |
|----------|------|---------|-----------|
| 1 | `ETHICS.md` | The constitution — five red lines, confidence standards, escalation ethics | Before any autonomous capability claim, any output design, any data handling spec |
| 2 | `HUMAN-COLLAB.md` | Human modification rights, intervention design, trust mechanics, DIKW architecture | Before any hirer-facing feature, any intervention point, any output display, any calibration mechanism |
| 3 | `5V.md` | Data governance — Veracity, Value, Vulnerability, Variability, Visibility assessed at four stages | Before any data source spec, any ROI claim, any storage design, any calibration mechanism, any deployment |
| 4 | `AGENT-RULES.md` | Behavioural contract — references all above at point of use | Every build session |

**Quick reference — which file to read for what:**

- Before any autonomous capability claim → `ETHICS.md` Red Lines 02 + 03
- Before designing any output display → `HUMAN-COLLAB.md` §02 Right 01 + 02
- Before designing any escalation flow → `ETHICS.md` §05 + `HUMAN-COLLAB.md` §03
- Before designing any intervention point → `HUMAN-COLLAB.md` §03 (use the template)
- Before designing any calibration mechanism → `HUMAN-COLLAB.md` §04 + `5V.md` V4 Variability
- Before specifying any data source → `5V.md` V1 Veracity
- Before writing any ROI chip → `5V.md` V2 Value
- Before any data storage or retention design → `5V.md` V3 Vulnerability
- Before designing any output display or audit trail → `5V.md` V5 Visibility
- Before deploying any staff → run `5V.md` Stage 02 deployment checklist in full
- Before any collaboration design decision → `ETHICS.md` §00 synergy test
- If session prompt conflicts with any foundational file → flag to founder, do not resolve silently

---

## Context Files (Read Before Major Builds)

- `VISION.md` — product philosophy, roster, two modes
- `JOYN-CONTEXT.md` — full page-by-page notes, locked decisions
- `JOYN-DESIGN-SPEC.md` — colour system, typography scale, every component pattern with code
- `AGENT-RULES.md` — full behavioural contract for autonomous build sessions
- `CREATOR-STUDIO-PROCESS.md` — end to end creator workflow, templates, build standards, validation rubric
- `ETHICS.md` — ethical constitution, five red lines, synergy vision
- `HUMAN-COLLAB.md` — human collaboration operating manual, DIKW architecture, hirer rights
- `5V.md` — data governance framework, four-stage assessment lifecycle

---

## Multi-Platform Sync Rules

This repo is worked on across Claude Code, Claude.ai, Emergent, and Manus. All platforms point to the same `main` branch. To keep context files accurate:

**Before starting any session:**
- Pull latest from `main` before making changes (`git pull`)

**After making changes, update the relevant context file if:**

| You changed | Update this file |
|-------------|-----------------|
| Added or removed a page | `JOYN-CONTEXT.md` → Site Structure section |
| Added or removed a staff member | `VISION.md` → AI Staff Roster + `JOYN-CONTEXT.md` |
| Changed the colour palette or fonts | `JOYN-DESIGN-SPEC.md` |
| Changed a locked decision | `JOYN-CONTEXT.md` + `VISION.md` |
| Changed the nav pattern or component | `JOYN-DESIGN-SPEC.md` + `CLAUDE.md` |
| Added a new portal route or template | `JOYN-CONTEXT.md` |
| Changed any ethical, collaboration, or data governance standard | `ETHICS.md` + `HUMAN-COLLAB.md` + `5V.md` |

**Context file update rule:** If the change you made would make a context file inaccurate, update that file in the same commit. Never commit a code change that makes a context file describe something that no longer exists.

**Commit discipline across platforms:**
```bash
# Always add files explicitly — never git add . or git add -A
git add [changed-file.html]
git add JOYN-CONTEXT.md   # if site structure changed
git commit -m "type: what changed"
git push
```
