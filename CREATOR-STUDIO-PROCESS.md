# CREATOR-STUDIO-PROCESS.md — Joyn Creator Build Process
**Version 1.1 · March 2026**
**Lives in repo root alongside AGENT-RULES.md, JOYN-CONTEXT.md, JOYN-DESIGN-SPEC.md, VISION.md**

---

## 00 — Purpose

This document defines the end-to-end process for any domain expert (creator) to build, validate and deploy AI staff on the Joyn marketplace. It is tool-agnostic — creators may use Claude Code, Manus, Emergent, Lovable, Cursor, v0, or any other build tool. The process and standards are non-negotiable regardless of tool choice.

**The north star:** A non-technical domain expert with zero coding knowledge should be able to go from idea to live AI staff on Joyn using nothing more than their domain knowledge, their preferred build tool, and this document as their guide.

**The model:** Apple App Store. Open on tools. Closed on standards. Nothing reaches the marketplace without passing the quality gate.

---

## 01 — The Five Stages

```
Apply → Brief → Build → Deploy → Earn
```

| Stage | Who acts | What happens |
|-------|----------|--------------|
| **Apply** | Creator submits, Joyn reviews | Qualifications gate — selective admission |
| **Brief** | Creator fills template, Claude produces spec | Scope and design locked before a line is built |
| **Build** | Creator builds using any tool | Against Joyn Build Standard |
| **Deploy** | Claude validates, Claude Code deploys | Quality gate → live on marketplace |
| **Earn** | Joyn tracks hires | Performance-linked income per active hire |

---

## 02 — Stage 1: Apply

### What the creator submits
- Full name and professional background
- Domain and years of verified experience
- The vertical they want to build in (Insurance & Risk / Financial Services / Healthcare / Legal & Compliance / Real Estate / Operations / Technology)
- One sentence: what AI staff they want to build and who it serves
- Why they are the right person to build it (domain credibility, not technical skill)

### Joyn's review criteria
- Verifiable domain expertise in the stated vertical
- The staff concept fills a real gap in the marketplace
- The creator can articulate what a client stops doing manually when they hire this staff
- No conflicts with existing live staff on the marketplace

### Outcome
- **Approved** → creator receives access to Stage 2 (Creator Brief template)
- **Not approved** → specific feedback provided, reapplication welcome after 90 days

### The admission model
Joyn operates a selective, quality-first admission model. Not every applicant is approved. The value of the marketplace depends on the quality of what is in it. A smaller roster of exceptional staff is always preferred over a large roster of mediocre staff.

---

## 03 — Stage 2: Brief

### The Creator Brief Template

Every approved creator completes this brief before any building begins. This is mandatory. No brief = no build.

```
CREATOR BRIEF
─────────────────────────────────────────────────────────────

CREATOR
Name:
Domain & years of experience:
Vertical:

STAFF CONCEPT
Staff name (one word preferred):
Staff role (one sentence — what this staff does):
Mode: [ ] Autonomous  [ ] Supervised

TARGET CLIENT
Who hires this staff (one sentence — be specific):
What does the client stop doing manually when they hire this staff:
What does the client get that they cannot easily get today:

CORE TASKS (exactly three — no more, no less for v1)
Task 1:
Task 2:
Task 3:

SUCCESS METRICS
How does the client know it is working (be specific — time saved,
cost avoided, accuracy improved, decisions enabled):
Metric 1:
Metric 2:

INPUTS & DATA
What data or inputs does this staff need to function:
Where does that data come from:
Any data the client must provide:

HUMAN INTERVENTION POINTS (Supervised mode only — leave blank if Autonomous)
Where in the workflow does a human review or approve before proceeding:
What decisions are never made autonomously:

BUILD TOOL PREFERENCE
Which tool will you use to build: [ ] Claude Code  [ ] Manus
[ ] Emergent  [ ] Lovable  [ ] Cursor  [ ] v0  [ ] Other: ______

─────────────────────────────────────────────────────────────
```

### What happens after the brief is submitted

Claude (acting as the visionary layer) reads the completed brief and produces a **Visionary Spec**. The creator reviews, approves or modifies the spec. Nothing is built until the spec is approved.

The Visionary Spec is the binding design document for the build. If the build deviates from the spec it fails validation.

---

## 04 — The Visionary Spec Template

Claude produces this from the Creator Brief. The creator takes the approved spec into their build tool.

```
VISIONARY SPEC
─────────────────────────────────────────────────────────────
Generated from Creator Brief · [Date]

STAFF IDENTITY
Name:
Role:
Mode:
Vertical:
Tagline (one sentence — what this staff does for the client):

LISTING PAGE
File path:  marketplace/[name-vertical].html
Page title: [Name] — [Role] · Joyn

HERO SECTION
Label (DM Mono gold): [Vertical]
Headline (Cormorant Garamond, large): [Staff Name]
Subhead (Syne body): [One sentence role description]
Mode badge: Autonomous · Live Now  OR  Supervised Mode
Primary CTA: Hire [Name]  →  links to brief/hire form

CORE TASKS SECTION
Section label: What [Name] Does
Three tasks displayed as structured rows:
  Task 1 — [title]: [description]
  Task 2 — [title]: [description]
  Task 3 — [title]: [description]

ROI CHIPS (minimum two — specific and verifiable)
Chip 1: [e.g. "~Xh of manual work eliminated per week"]
Chip 2: [e.g. "0 [problem] missed"]

HOW IT WORKS SECTION (Supervised mode only)
Four-phase workflow display:
  Phase 1 — [Scoping]: [what happens]
  Phase 2 — [Setup]: [what happens]
  Phase 3 — [Execution]: [what happens, checkpoints noted]
  Phase 4 — [Output & Refinement]: [what happens]
Human intervention points called out explicitly at each phase.

SUCCESS METRICS SECTION
Section label: How You Know It Is Working
Metric 1: [specific, measurable]
Metric 2: [specific, measurable]

HIRE / BRIEF FORM
Fields: Name, Company, Role, Email,
        [Mode-specific fields drawn from brief], Message
Web3Forms key: 5b972adb-feba-4546-a657-02d5e29b6e29
Submission → hire@tryjoyn.me

DESIGN DIRECTIVES
Follow JOYN-DESIGN-SPEC.md exactly.
No deviations. All components from spec §05.
Validation rubric in Stage 4 will catch any deviation.

─────────────────────────────────────────────────────────────
SPEC STATUS: [ ] Draft — awaiting creator approval
             [ ] Approved — ready to build
             [ ] Modified — [note changes]
─────────────────────────────────────────────────────────────
```

---

## 05 — Stage 3: Build

### Tool freedom
Creators build using any tool they choose. Claude Code, Manus, Emergent, Lovable, Cursor, v0 — all permitted. The tool does not matter. The output must meet the Joyn Build Standard regardless.

### How to prompt your build tool

When using any AI build tool, start your prompt with this block. Fill in the bracketed fields from your approved Visionary Spec.

```
I am building a listing page for an AI staff member on Joyn,
an AI staffing platform.

CONTEXT: Attach or paste JOYN-DESIGN-SPEC.md and JOYN-CONTEXT.md

TASK: Build a single self-contained HTML file for [Staff Name],
a [Mode] AI staff member in the [Vertical] vertical.

FILE PATH: marketplace/[name-vertical].html

SPEC: [Paste your approved Visionary Spec here]

CRITICAL REQUIREMENTS:
- Single HTML file. All CSS and JS inline. No external frameworks.
- Use only CSS variables from the palette. Never hardcode hex values.
- Fonts: Cormorant Garamond (headings), DM Mono (labels/tags),
  Syne (body). No other fonts.
- No border-radius anywhere. No box-shadows. No keyframe animations.
- Transitions: 0.15s–0.2s ease only.
- Forms via Web3Forms key: 5b972adb-feba-4546-a657-02d5e29b6e29
- Mobile responsive using clamp() and CSS Grid/Flexbox.
- Follow the page template in JOYN-DESIGN-SPEC.md §08 exactly.
- Terminology: hire (not activate), staff (not agents),
  role (not function), Autonomous/Supervised (correct mode labels).

OUTPUT: One complete HTML file ready for validation.
```

### Parallel building (recommended)
Run two build tools simultaneously — e.g. Manus + Emergent in parallel. Bring both outputs to validation. Claude will identify the stronger output or merge the best of both.

### What the creator must not do during build
- Change the colour palette
- Add fonts not in the type system
- Add border-radius to any element
- Use external CSS or JS frameworks
- Add animations beyond permitted transitions
- Deviate from the approved Visionary Spec without re-approval

---

## 06 — Stage 4: Deploy

### The Validation Rubric

Before any file touches the Joyn codebase, Claude runs this rubric against the build output. Every item must pass. Any failure is returned to the creator with specific correction instructions.

```
JOYN VALIDATION RUBRIC
─────────────────────────────────────────────────────────────
File: [path]
Creator: [name]
Staff: [name]
Date: [date]

DESIGN
[ ] CSS variables only — no hardcoded hex colours
[ ] No border-radius anywhere in the file
[ ] No box-shadows anywhere in the file
[ ] No external CSS frameworks
[ ] No keyframe animations
[ ] Transitions 0.15s–0.2s only
[ ] Cormorant Garamond for all headings and display text
[ ] DM Mono for all labels, tags, nav items, filter buttons
[ ] Syne for all body text and descriptions
[ ] All gold text uses --gold-text not --gold-display
[ ] Mobile responsive (clamp + grid/flex, no fixed px widths)
[ ] Page template from JOYN-DESIGN-SPEC.md §08 used as base

TERMINOLOGY
[ ] No forbidden terms in output (see table below)
[ ] Mode correctly labelled (Autonomous or Supervised)
[ ] Staffing language used throughout

INTEGRATION
[ ] Web3Forms key correct: 5b972adb-feba-4546-a657-02d5e29b6e29
[ ] Form submits to hire@tryjoyn.me
[ ] Nav structure matches global pattern (CLAUDE.md)
[ ] Breadcrumbs present
[ ] Favicon referenced correctly
[ ] Links use correct paths (marketplace/index.html not marketplace/)

CONTENT QUALITY
[ ] Staff role is specific and verifiable — not vague
[ ] Three core tasks clearly stated
[ ] Minimum two ROI chips present and specific
[ ] Success metrics stated on listing
[ ] Human intervention points documented (Supervised only)
[ ] No capability claims that cannot be delivered
[ ] Copy matches approved Visionary Spec

VERDICT
[ ] PASS → Claude Code prompt issued, deploy proceeds
[ ] FAIL → Failures listed below, returned to creator for correction

FAILURES (if any):
1.
2.
3.
─────────────────────────────────────────────────────────────
```

### Forbidden terminology — auto-fail if present

| Found in output | Must be |
|-----------------|---------|
| activate / subscribe | hire |
| agents / bots | staff |
| function / task | role |
| cancel / unsubscribe | let go |
| Ready / Always On | Autonomous |
| Custom / Craft | Supervised |
| tryjoin | tryjoyn |

### The Claude Code deploy prompt

Once validation passes, Claude issues this prompt for Claude Code:

```
CONTEXT FILES: JOYN-CONTEXT.md, JOYN-DESIGN-SPEC.md,
               AGENT-RULES.md, VISION.md, CLAUDE.md

TASK: Deploy new AI staff listing page to Joyn marketplace.

FILE: marketplace/[name-vertical].html
[Paste validated HTML file here]

ALSO UPDATE:
1. marketplace/index.html — add staff card to grid
   Name: [Name]
   Role: [Role]
   Mode: [Autonomous/Supervised]
   Vertical: [Vertical]
   Status: Live
   ROI chips: [Chip 1], [Chip 2]

2. data/roster.json — add entry
   {
     "name": "[Name]",
     "role": "[Role]",
     "mode": "[autonomous/supervised]",
     "vertical": "[Vertical]",
     "status": "live",
     "unlockDate": null,
     "description": "[One sentence from listing]"
   }

DEPLOY SEQUENCE:
git add marketplace/[name-vertical].html
git add marketplace/index.html
git add data/roster.json
git commit -m "add: [Name] — [Role] · [Vertical] vertical"
git push

Verify live at: tryjoyn.me/marketplace/[name-vertical].html
```

---

## 07 — Stage 5: Earn

Performance-linked income activates from the first hire. Rate confirmed at creator offer stage. Tracked by Joyn. Paid per active hire per period.

No further action required from the creator once staff is live. Joyn manages the client relationship, the hire process, and income tracking.

Creators are notified when:
- Their staff receives a new hire
- A client lets their staff go (with reason if provided)
- Their staff is eligible for an upgrade build based on client feedback

---

## 08 — Terminology Reference

| Use | Never use |
|-----|-----------|
| **Autonomous** | Ready, Always On |
| **Supervised** | Custom, Craft |
| **hire** | activate, subscribe |
| **staff** | agents, bots |
| **role** | function, task |
| **letting someone go** | unsubscribing, cancelling |
| **Joyn** | joyn, JOYN |
| **tryjoyn.me** | tryjoin.me |

---

## 09 — Context Files Reference

Every Claude session building on Joyn reads these files in priority order:

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `JOYN-CONTEXT.md` | Tech stack, site structure, locked decisions |
| 2 | `JOYN-DESIGN-SPEC.md` | Colour system, typography, every component with code |
| 3 | `VISION.md` | Product philosophy, two modes, brand rules |
| 4 | `AGENT-RULES.md` | Behavioural contract for build sessions |
| 5 | `CREATOR-STUDIO-PROCESS.md` | This file — creator workflow end to end |
| 6 | Session prompt | Current task — overrides nothing in 1–5 |

---

## 10 — Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | March 2026 | Initial codification |
| 1.1 | March 2026 | Removed worked example — generic and staff-agnostic |

---

*Joyn · tryjoyn.me · CREATOR-STUDIO-PROCESS.md v1.1*
*The process any domain expert follows to build AI staff on Joyn.*
