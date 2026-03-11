# JOYN Visual Regression Checklist
**Version:** 1.0
**Last Updated:** March 2026

## Purpose

This checklist ensures visual consistency after each deploy. Run before pushing any frontend changes to production.

---

## Pre-Push Checklist

### 1. Typography Check (All Pages)
- [ ] Cormorant Garamond loads for headings
- [ ] DM Mono loads for labels and metadata
- [ ] No font fallbacks visible (check for system font flash)
- [ ] Line heights match spec (1.15 for headings, 1.6 for body)

### 2. Colour Palette Check
- [ ] `--ink` (#1a1a1a) used for primary text
- [ ] `--white` (#f7f5ef) used for backgrounds
- [ ] `--gold-text` (#b8993a) used for accents
- [ ] `--rule` (#d4d0c4) used for dividers
- [ ] No hardcoded hex values outside CSS variables

### 3. Component Consistency
- [ ] Staff cards: Same height, consistent tag placement
- [ ] Buttons: `.btn-primary`, `.btn-ghost`, `.btn-gold` styling correct
- [ ] Forms: Input borders, focus states, error states
- [ ] Modals: Backdrop blur, close button position

### 4. Responsive Breakpoints
- [ ] Desktop (1200px+): Full layout
- [ ] Tablet (768px-1199px): Stacked cards, adjusted nav
- [ ] Mobile (< 768px): Single column, hamburger nav

### 5. Interactive States
- [ ] Hover states on all buttons
- [ ] Focus rings on interactive elements (accessibility)
- [ ] Active/selected states on filters
- [ ] Loading states on forms

### 6. Page-Specific Checks

#### Homepage (index.html)
- [ ] Hero section: Heading, subheading, CTA alignment
- [ ] Staff grid: Cards aligned, tags visible
- [ ] Navigation: Logo, links, mobile toggle
- [ ] Footer: Links, copyright

#### Marketplace (marketplace/index.html)
- [ ] Filter bar: Sticky, toggles work
- [ ] Staff cards: Live/Coming Soon states
- [ ] Empty state: Shows if no staff match filter

#### Hire Flow (iris.html, tdd-hire.html)
- [ ] Step indicator: Current step highlighted
- [ ] Form fields: Validation states
- [ ] Success/error messages

#### Builder Dashboard (builder-dashboard.html)
- [ ] Sidebar: Correct width, scrollable
- [ ] Journey cards: Checkmarks, active states
- [ ] Main content: Responsive layout

---

## Forbidden Terms Check

Before every push, grep for forbidden terms:

```bash
grep -rn "activate\|subscribe\|agents\|bots\|cancel\|tryjoin" . --include="*.html" --include="*.js" --include="*.css"
```

Expected result: **No matches** (except this file)

### Forbidden Terms List
| Term | Reason | Use Instead |
|------|--------|-------------|
| `activate` | Subscription language | "start", "begin", "onboard" |
| `subscribe` | Subscription language | "hire", "onboard", "join" |
| `agents` | Robotic framing | "staff", "team member" |
| `bots` | Robotic framing | "staff", "AI staff" |
| `cancel` | Subscription language | "offboard", "pause", "end" |
| `tryjoin` | Misspelling | "tryjoyn" |

---

## Broken Link Check

Run monthly using a link checker:

```bash
# Using linkchecker (install: pip install linkchecker)
linkchecker https://tryjoyn.me --no-robots --check-extern
```

### Critical Links to Verify Manually
- [ ] "Browse AI Staff" → marketplace/index.html
- [ ] "Hire Iris" → iris.html
- [ ] "View TDD Team" → practice/tdd-practice-team.html
- [ ] "Creator Studio" → marketplace/creator-studio.html
- [ ] Footer: Privacy, Terms links

---

## Post-Deploy Verification

After every deploy to production:

1. [ ] Load homepage on desktop
2. [ ] Load homepage on mobile (use Chrome DevTools)
3. [ ] Click through main navigation
4. [ ] Submit a test interest form
5. [ ] Check marketplace filter functionality
6. [ ] Verify no console errors

---

## Known Gotchas

### data-mode vs Display Label
- Filter uses `always-on` / `craft` internally
- Display shows `Autonomous` / `Supervised`
- **Do not change filter values** — they are intentional

### Sticky Nav Offset
- Nav: 60px
- Filter bar: 60px
- Total offset for scroll-to: 120px
- Update `scroll-margin-top` if adding new sticky elements

### Mobile Back-to-Top Offsets
- Iris, TDD: `bottom: 5rem`
- Other pages: `bottom: 2rem`
- Standardize if adding new pages

---

## Contact

Design questions: hire@tryjoyn.me
