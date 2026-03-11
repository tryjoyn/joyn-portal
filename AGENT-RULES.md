# AGENT-RULES.md — Joyn Claude Agent Rules of Engagement
**Version 1.0 · March 2026**
**Upload this file alongside JOYN-CONTEXT.md and JOYN-DESIGN-SPEC.md on every build session.**

---

## 00 — Purpose

This document defines how Claude agents behave when building or modifying the Joyn codebase. It is a binding contract between the human operator (Shiva) and any Claude session working on this project. All rules below are non-negotiable unless explicitly overridden in the session prompt.

---

## 01 — Determinism Contract

**Same input → same output. Always.**

- Given identical instructions and context files, the agent must produce identical output across sessions.
- Never introduce variation, creativity, or "improvements" unless explicitly instructed.
- If the agent detects ambiguity in the instruction, it must **stop and ask one clarifying question** before writing any code.
- Do not infer intent from partial instructions. Missing fields = blocked execution.

```
RULE: If instruction is ambiguous → ASK. Never assume.
RULE: If context files conflict → flag the conflict. Never resolve silently.
RULE: Design decisions not in JOYN-CONTEXT.md or JOYN-DESIGN-SPEC.md → defer to human.
```

---

## 02 — Context Hierarchy (read in this order)

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `JOYN-CONTEXT.md` | Source of truth — tech stack, locked decisions, page inventory |
| 2 | `JOYN-DESIGN-SPEC.md` | Visual system — colours, fonts, components, do/don't |
| 3 | `VISION.md` | Product philosophy — terminology, two modes, brand rules |
| 4 | `AGENT-RULES.md` | This file — behavioural contract |
| 5 | Session prompt | Current task — overrides nothing in 1–4 unless explicitly stated |

**If a session prompt contradicts a locked decision in JOYN-CONTEXT.md, the agent must flag the conflict before proceeding.**

---

## 03 — Tool Usage Rules

```
RULE: Call tools only when the output cannot be produced from context alone.
RULE: Never loop on the same tool call more than once without new input.
RULE: No redundant reads — if a file's content is already in context, do not re-read it.
RULE: Validate before calling — check that required inputs exist before executing.
```

**Permitted tool calls per session (guidelines):**
- File creation: unlimited, but each file must be necessary and named before creation
- File reads: only for files not already in context
- Web search: not permitted during build sessions (no external dependencies)
- Terminal/bash: only for file operations, never for package installs without explicit instruction

**Fail-safe on tool errors:**
1. Retry once with corrected parameters
2. If retry fails → return structured error (see §08)
3. Never silently skip a failed tool call

---

## 04 — Input Validation Rules

Before executing any build task, the agent must verify:

```json
{
  "required_context": ["JOYN-CONTEXT.md", "JOYN-DESIGN-SPEC.md"],
  "required_fields": {
    "task": "clear description of what to build or change",
    "target_file": "specific file path(s) to create or modify",
    "scope": "new page | edit existing | fix bug | add component"
  },
  "blocking_conditions": [
    "instruction references a file not in the site structure",
    "instruction contradicts a locked decision",
    "instruction requires a new colour not in the palette",
    "instruction requires a new font not in the type system",
    "instruction requires external npm/CDN dependency"
  ]
}
```

If any blocking condition is met → **stop, report the block, ask for resolution.**

---

## 05 — Scope Boundaries

**The agent may:**
- Create new single-file HTML pages following the page template in JOYN-DESIGN-SPEC.md §08
- Edit existing HTML files to add or modify sections
- Fix bugs explicitly described in JOYN-CONTEXT.md "Known Issues"
- Update `data/roster.json` when instructed
- Write or update markdown documentation files

**The agent may NOT (without explicit unlock):**
- Change the colour palette
- Add new fonts
- Add `border-radius` to any element
- Use external CSS frameworks (Bootstrap, Tailwind, etc.)
- Use JavaScript frameworks (React, Vue, etc.)
- Add animations beyond 0.15s–0.2s transitions
- Change the Web3Forms API key
- Modify `.github/workflows/` files
- Create separate CSS or JS files (all styles and scripts stay inline)
- Use `git add .` or `git add -A`

**Locked decisions (from JOYN-CONTEXT.md) — never reverse:**
- Autonomous vs Supervised distinction
- No pricing on site
- Staffing language (hire / staff / role / letting someone go)
- Chick-fil-A creator admission model
- No live deployment counter until 50+ deployments
- No revenue share % on creator-studio
- No build tools — single-file HTML only

---

## 06 — State Summarisation Protocol

At the start of every session, the agent must output a state summary before writing any code:

```
SESSION STATE
─────────────
Task:        [what is being built/changed]
Files in:    [which context files were provided]
Target:      [specific file(s) to be created or modified]
Scope:       [new page | edit existing | fix bug | add component]
Locked deps: [any locked decisions relevant to this task]
Conflicts:   [any conflicts detected — NONE if clean]
Proceeding:  [YES | BLOCKED — reason]
```

This is logged to the top of the response. It is not optional.

---

## 07 — Output Standards

### File output format
Every created or modified file must be:
- A single self-contained HTML file (all CSS and JS inline)
- Starting from the page template in JOYN-DESIGN-SPEC.md §08
- Using only CSS variables from the palette — never hardcoded hex values
- Using only the three permitted fonts: Cormorant Garamond, DM Mono, Syne
- Mobile responsive using `clamp()` and CSS Grid/Flexbox
- Forms wired to Web3Forms key `5b972adb-feba-4546-a657-02d5e29b6e29` → hire@tryjoyn.me

### Diff output format
When modifying an existing file, the agent must provide:
```
FILE: [path/to/file.html]
CHANGE: [one-line description]
FIND (exact string to locate):
───
[exact existing text to find]
───
REPLACE WITH:
───
[new text]
───
```

Never output entire modified files for edits — only the diff blocks. This keeps context windows small.

### Structured error format
```json
{
  "status": "ERROR",
  "code": "BLOCKING_CONDITION | TOOL_FAILURE | VALIDATION_FAILURE | SCOPE_VIOLATION",
  "message": "human-readable description",
  "resolution": "what the human needs to provide or decide",
  "file": "which file was being processed",
  "line_hint": "approximate location if known"
}
```

---

## 08 — Terminology Enforcement

The agent must auto-correct any terminology violations before output. No exceptions.

| ❌ Never write | ✅ Always write |
|---------------|----------------|
| activate | hire |
| subscribe | hire |
| agents | staff |
| bots | staff |
| function / task | role |
| cancel / unsubscribe | let go |
| Ready / Always On | Autonomous |
| Custom / Craft | Supervised |
| tryjoin | tryjoyn |
| agents.html | staff.html |

If the session prompt uses forbidden terminology, the agent silently corrects it in output and notes the correction in the session state summary.

---

## 09 — Git Discipline Rules

The agent must output Git commands in this exact format at the end of every build session:

```bash
# ── JOYN DEPLOY SEQUENCE ──────────────────────────────────────
# Run from your Joyn/ directory. Add files INDIVIDUALLY.
# Never use git add . or git add -A

cd Joyn

# Add each file explicitly
git add [file1]
git add [file2]

# Single commit per logical change
git commit -m "[type]: [what changed] — [why or ticket ref]"

# Push — Pages deploys in ~60 seconds
git push

# Verify at: tryjoyn.me/[path-to-new-file]
# ─────────────────────────────────────────────────────────────
```

**Commit message types:** `add` | `fix` | `update` | `refactor` | `data`

---

## 10 — Cost-Awareness Rules

```
RULE: Never re-read files already in context.
RULE: For edits to existing files, output diffs only — not full file rewrites.
RULE: Keep session prompts focused — one task per session where possible.
RULE: Do not produce explanatory text that restates the task after completing it.
RULE: Session state summary (§06) replaces any preamble — go directly to output.
```

---

## 11 — Quality Gates

Before finalising any output, the agent runs this internal checklist:

```
[ ] No hardcoded hex colours — only CSS variables
[ ] No border-radius anywhere
[ ] No box-shadows anywhere
[ ] No external CSS or JS frameworks
[ ] No animations beyond 0.15s–0.2s transitions
[ ] Cormorant Garamond used for all headings
[ ] DM Mono used for all labels, tags, nav items
[ ] Syne used for all body text
[ ] All gold text uses --gold-text, not --gold-display
[ ] Forms wired to correct Web3Forms key
[ ] All links use correct paths (marketplace/index.html not marketplace/)
[ ] No forbidden terminology in output
[ ] Mobile responsive (clamp + grid/flex, no fixed px widths)
[ ] "Browse AI Staff" links to marketplace/index.html (known bug — always fix if touched)
[ ] Structured error returned if any gate fails
```

---

## 12 — Session Prompt Template

Use this template when starting a new build session. Paste it as your first message:

```
CONTEXT FILES ATTACHED: JOYN-CONTEXT.md, JOYN-DESIGN-SPEC.md, VISION.md, AGENT-RULES.md

TASK: [one sentence — what to build or change]

TARGET FILE(S): [exact path(s) — e.g. marketplace/iris-insurance-regulatory.html]

SCOPE: [new page | edit existing | fix bug | add component]

ADDITIONAL NOTES: [any one-off instructions for this session only]
```

---

## 13 — Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | March 2026 | Initial rules of engagement |

---

*Joyn · tryjoyn.me · AGENT-RULES.md v1.0*
