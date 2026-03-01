# JOYN. Design Specification
**Version 2.0 — March 2026**
**Upload this file to any Claude chat building a Joyn frontend page.**

---

## 01 — Design Philosophy

Joyn is a staffing platform, not a SaaS tool. The design reflects this — considered, professional, human. It borrows from high-end editorial and luxury brand aesthetics rather than tech startup conventions. No gradients. No purple. No rounded pill buttons. No generic sans-serif system fonts.

The visual language says: *this is where serious work gets done.*

Every page must feel like it belongs to the same world. When in doubt, do less. Restraint is the house style.

**Core principles:**
- Whitespace is not wasted space — it signals quality
- Typography does the heavy lifting; decoration is minimal
- Every element earns its place
- No dark mode — the warm off-white palette is intentional and fixed
- No animations beyond subtle transitions (0.15s–0.2s ease)

---

## 02 — Colour System

These are the only colours used across all Joyn pages. Use CSS variables exclusively — never hardcode hex values.

```css
:root {
  --white:         #fafaf8;   /* Primary background — warm off-white */
  --ink:           #111110;   /* Primary text — near black */
  --ink-secondary: #3f3f3e;   /* Secondary text — dark grey */
  --rule:          #e8e4dc;   /* Borders and dividers — light warm */
  --rule-mid:      #d0ccc4;   /* Mid-weight borders */
  --surface:       #f4f1eb;   /* Card and panel backgrounds */
  --gold-display:  #b8902a;   /* Gold for decorative and display use */
  --gold-text:     #8B6914;   /* Gold for text — accessible contrast */
  --gold-hover:    #7a5c10;   /* Gold hover state */
}
```

**Usage rules:**

- `--white` is the default page background. Always start here.
- `--ink` is the default text colour on light backgrounds.
- `--ink-secondary` is for supporting text, descriptions, captions, and metadata.
- `--rule` is for horizontal rules, card borders, and section dividers.
- `--rule-mid` is for stronger borders where more visual weight is needed.
- `--surface` is for card backgrounds, table header rows, and raised panels.
- `--gold-display` is used sparingly — decorative lines, label rule marks, active CTA backgrounds. One primary use per page maximum.
- `--gold-text` is gold applied to text — use wherever gold text needs to be readable (labels, links, tags). Never use `--gold-display` for text.
- `--gold-hover` is the hover state for any gold text or gold interactive element.
- Never use pure white (`#ffffff`) or pure black (`#000000`).
- No other colours without explicit instruction.

---

## 03 — Typography

Three fonts. Each has a defined role. Never swap them.

```html
<!-- Always include exactly this in <head> -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=DM+Mono:wght@300;400;500&family=Syne:wght@400;500;600;700&display=swap" rel="stylesheet">
```

| Font | Role | Usage |
|------|------|-------|
| **Cormorant Garamond** | Headings, hero text, display | Page titles, section headers, large feature text. Weight 300–500. Italics for emphasis. |
| **DM Mono** | Labels, metadata, tags, UI elements | Status badges, mode tags, filter buttons, navigation items, table headers, timestamps, small-caps labels. |
| **Syne** | Body text, descriptions, paragraphs | All running text, card descriptions, explanatory copy. Weight 400–600. |

**Base settings:**

```css
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--white);
  color: var(--ink);
  font-family: 'Syne', sans-serif;
  font-size: 1rem;
  line-height: 1.8;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4 {
  font-family: 'Cormorant Garamond', serif;
  font-weight: 400;
  color: var(--ink);
}
p { color: var(--ink-secondary); }
```

**Type scale:**

```css
/* Hero / page title */
font-size: clamp(2.5rem, 5vw, 4rem);
font-family: 'Cormorant Garamond', serif;
font-weight: 300;
line-height: 1.1;

/* Section heading */
font-size: clamp(1.75rem, 3vw, 2.5rem);
font-family: 'Cormorant Garamond', serif;
font-weight: 400;
line-height: 1.2;

/* Sub-heading / card title */
font-size: 1.25rem;
font-family: 'Cormorant Garamond', serif;
font-weight: 400;

/* Body */
font-size: 1rem;
font-family: 'Syne', sans-serif;
line-height: 1.8;

/* Small body / description */
font-size: 0.9rem;
font-family: 'Syne', sans-serif;
line-height: 1.7;

/* Label (DM Mono small-caps) */
font-size: 0.7rem;
font-family: 'DM Mono', monospace;
font-weight: 500;
letter-spacing: 0.12em;
text-transform: uppercase;

/* Micro label / tag */
font-size: 0.65rem;
font-family: 'DM Mono', monospace;
letter-spacing: 0.1em;
text-transform: uppercase;
```

---

## 04 — Layout & Spacing

**Page wrapper:**
```css
.main {
  padding: clamp(2rem, 4vw, 4rem) clamp(1.5rem, 5vw, 4rem);
  max-width: 1100px;
}
```

**Header:**
```css
.header {
  padding: 2rem clamp(1.5rem, 5vw, 4rem);
  border-bottom: 1px solid var(--rule);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-logo {
  font-family: 'DM Mono', monospace;
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  color: var(--ink);
  text-decoration: none;
}
```

**Section spacing:** `margin-bottom: 3rem` between sections.

**Section heading with rule:**
```css
.section-hd {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--rule);
}
```

**Grid columns:** Use CSS Grid with `gap: 1.5rem` or `gap: 2rem`. Never use floats or flexbox hacks for layout grids.

---

## 05 — Component Patterns

### Section Label
Gold label with rule-line prefix — used above section headings.

```html
<span class="label">Insurance</span>
```
```css
.label {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--gold-text);
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
}
.label::before {
  content: '';
  display: block;
  width: 1.5rem;
  height: 1px;
  background: var(--gold-text);
}
```

---

### Status Badges
Used on staff cards and pipeline tables.

```html
<span class="status-live">Live</span>
<span class="status-soon">Coming Soon</span>
```
```css
.status-live {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.2rem 0.6rem;
  border: 1px solid rgba(139, 105, 20, 0.3);
  color: var(--gold-text);
  background: rgba(139, 105, 20, 0.07);
}
.status-soon {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.2rem 0.6rem;
  border: 1px solid var(--rule-mid);
  color: var(--ink-secondary);
  background: var(--surface);
}
```

---

### Mode Tags
Autonomous = filled black. Supervised = outlined.

```html
<span class="mode-auto">Autonomous</span>
<span class="mode-sup">Supervised</span>
```
```css
.mode-auto {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  background: var(--ink);
  color: var(--white);
  padding: 0.2rem 0.5rem;
}
.mode-sup {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border: 1px solid var(--ink);
  color: var(--ink);
  padding: 0.2rem 0.5rem;
}
```

---

### Filter Bar
Used on marketplace and creator studio. Mode + Vertical filters.

```html
<div class="filter-bar">
  <div class="filter-group">
    <button class="filter-btn active">All</button>
    <button class="filter-btn">Autonomous</button>
    <button class="filter-btn">Supervised</button>
  </div>
</div>
```
```css
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 2rem;
  align-items: center;
}
.filter-group {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}
.filter-btn {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.4rem 0.9rem;
  border: 1px solid var(--rule-mid);
  background: transparent;
  color: var(--ink-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.filter-btn.active {
  background: var(--ink);
  color: var(--white);
  border-color: var(--ink);
}
.filter-btn:hover:not(.active) {
  border-color: var(--ink);
  color: var(--ink);
}
```

---

### Staff Card
Used in the marketplace grid.

```html
<div class="staff-card">
  <div class="card-top">
    <span class="mode-auto">Autonomous</span>
    <span class="status-live">Live</span>
  </div>
  <div class="card-name">Iris</div>
  <div class="card-role">Insurance Regulatory Intelligence</div>
  <div class="card-desc">Description text here.</div>
</div>
```
```css
.staff-card {
  border: 1px solid var(--rule);
  padding: 1.75rem;
  background: var(--white);
  transition: border-color 0.2s;
}
.staff-card:hover { border-color: var(--rule-mid); }
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}
.card-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--ink);
  margin-bottom: 0.2rem;
}
.card-role {
  font-family: 'DM Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-secondary);
  margin-bottom: 0.75rem;
}
.card-desc {
  font-size: 0.9rem;
  color: var(--ink-secondary);
  line-height: 1.7;
}
```

---

### Tables
Used in admin and pipeline sections.

```css
table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid var(--rule);
}
th {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-secondary);
  padding: 0.75rem 1rem;
  text-align: left;
  background: var(--surface);
  border-bottom: 1px solid var(--rule);
}
td {
  padding: 0.875rem 1rem;
  font-size: 0.9rem;
  color: var(--ink-secondary);
  border-bottom: 1px solid var(--rule);
  vertical-align: top;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--surface); }
```

---

### Primary CTA Button

```html
<a href="#" class="btn-primary">Hire Iris</a>
```
```css
.btn-primary {
  display: inline-block;
  font-family: 'DM Mono', monospace;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  padding: 0.875rem 2rem;
  background: var(--ink);
  color: var(--white);
  border: 1px solid var(--ink);
  transition: background 0.2s, color 0.2s;
  cursor: pointer;
}
.btn-primary:hover {
  background: var(--white);
  color: var(--ink);
}
```

**No rounded corners. No gradients. No shadows.**

---

### Ghost / Secondary Button

```css
.btn-ghost {
  display: inline-block;
  font-family: 'DM Mono', monospace;
  font-size: 0.8rem;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  padding: 0.875rem 2rem;
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--rule-mid);
  transition: border-color 0.2s;
  cursor: pointer;
}
.btn-ghost:hover { border-color: var(--ink); }
```

---

### Forms

```css
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1.25rem;
}
.form-label {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}
.form-input,
.form-select,
.form-textarea {
  font-family: 'Syne', sans-serif;
  font-size: 0.95rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--rule-mid);
  background: var(--white);
  color: var(--ink);
  outline: none;
  transition: border-color 0.15s;
  -webkit-appearance: none;
}
.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: var(--ink);
}
.form-textarea { resize: vertical; min-height: 100px; }
```

**All forms submit via Web3Forms. Key: `5b972adb-feba-4546-a657-02d5e29b6e29`. Submissions go to hire@tryjoyn.me.**

---

### Stats / Metrics Display

```css
.stat-n {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.5rem;
  font-weight: 400;
  color: var(--gold-text);
  line-height: 1;
  margin-bottom: 0.25rem;
}
.stat-l {
  font-family: 'DM Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-secondary);
}
```

---

## 06 — Do / Don't

| Do | Don't |
|----|-------|
| Use `clamp()` for responsive sizing | Use fixed px widths for text |
| Border: `1px solid var(--rule)` | Box shadows |
| Square corners everywhere | `border-radius` |
| Subtle transitions (0.15s–0.2s) | Animations, keyframes, entrance effects |
| DM Mono for all UI labels and tags | Syne or Cormorant for labels |
| `var(--gold-text)` for gold text | `var(--gold-display)` on small text |
| Single-file HTML with inline CSS/JS | External stylesheets, npm packages |
| `font-weight: 300–500` on Cormorant | Bold (600+) on Cormorant |
| Underline links only on hover | Always-underlined body links |
| Restraint — less is more | Feature creep, decorative clutter |

---

## 07 — Terminology (Always Use These)

| Use | Never use |
|-----|-----------|
| **Autonomous** | Ready, Always On |
| **Supervised** | Custom, Craft |
| **hire** | activate, subscribe |
| **staff** | agents, bots |
| **role** | function, task |
| **letting someone go** | unsubscribing, cancelling |

---

## 08 — Page Template

Every new page starts from this shell:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Page Title — Joyn</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=DM+Mono:wght@300;400;500&family=Syne:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --white: #fafaf8; --ink: #111110; --ink-secondary: #3f3f3e;
  --rule: #e8e4dc; --rule-mid: #d0ccc4; --surface: #f4f1eb;
  --gold-display: #b8902a; --gold-text: #8B6914; --gold-hover: #7a5c10;
}
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--white); color: var(--ink); font-family: 'Syne', sans-serif; font-size: 1rem; line-height: 1.8; -webkit-font-smoothing: antialiased; }
h1, h2, h3 { font-family: 'Cormorant Garamond', serif; font-weight: 400; color: var(--ink); }
p { color: var(--ink-secondary); }
</style>
</head>
<body>

<div class="header">
  <a href="../index.html" class="header-logo">JOYN.</a>
  <span class="label">Page Name</span>
</div>

<main class="main">
  <!-- content -->
</main>

</body>
</html>
```

---

*Joyn · tryjoyn.me · Version 2.0 · March 2026*
