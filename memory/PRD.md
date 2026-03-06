# Joyn Creator Studio PRD
**Last Updated:** January 2026

---

## Original Problem Statement
Build a streamlined Creator Studio flow for joyn-portal where builders can:
- Build AI staff using any tools
- Deploy to Joyn infrastructure
- List on marketplace automatically
- Get hired and paid — all fully automated like the Apple App Store model

Key requirements:
- Closed standards, open tools
- 12-gate automated validation (quality, safety, trust, compliance)
- Zero manual review process
- Verified reviews from actual hirers
- Consistent UX across all staff listings

---

## User Personas

### Builders (Creators)
- AI developers who want to monetize AI staff
- Domain experts (insurance, legal, healthcare) building vertical solutions
- Agencies creating custom AI staff for clients

### Hirers
- Insurance compliance officers, legal ops, healthcare admin
- Small-mid businesses seeking operational efficiency
- Enterprises with specific automation needs

---

## Core Requirements (Static)
1. **12-Gate Validation System** — Automated review in <30 minutes
2. **Template Repository** — Battle-tested scaffold for builders
3. **Builder Portal** — Claim roles, submit, track earnings
4. **Standardized Listings** — Consistent format across all staff
5. **Verified Reviews** — Only from actual hirers
6. **70/30 Revenue Split** — Builder takes 70%
7. **$99 Listing Fee** — No refunds, unlimited resubmissions

---

## What's Been Implemented (January 2026)

### A. Reviewer Agent ✅
- `/app/joyn-portal/reviewer/gates.py` — All 12 gate validators
- `/app/joyn-portal/reviewer/engine.py` — Review orchestration
- `/app/joyn-portal/reviewer/routes.py` — REST API endpoints
- Registered in app.py under `/api/reviewer/`

### B. Template Repository ✅
- `/app/joyn-staff-template/` — Complete scaffold
- `STAFF-SPEC.md` — Specification template
- `SUBMISSION-CHECKLIST.md` — Pre-submission checklist
- `backend/agents/` — Example agent structure
- `backend/utils/security.py` — Security utilities
- `tests/run_all_gates.py` — Self-test runner

### C. Standards Documentation ✅
- `JOYN-STANDARD-V2.md` — Complete 12-gate framework
- `JOYN-LISTING-TEMPLATE.md` — Standardized page structure
- `JOYN-PLATFORM-ECONOMICS.md` — Builder/hirer economics

### D. Standardized Listing (Iris v2) ✅
- `/app/marketplace/iris-v2.html` — Updated to new standard
- Breadcrumb, mode badge, ROI chips
- Screenshot gallery, named outputs
- Verified reviews, pricing cards
- Creator attribution, compliance badges

---

## Prioritized Backlog

### P0 (Must Have — Next)
- [ ] Builder Portal at `app.tryjoyn.me/builder/`
  - Sign up / login
  - Claim role / propose new staff
  - $99 payment (Stripe)
  - Submission upload
  - Review status dashboard
  - Earnings tracking
- [ ] Update Probe listing to v2 standard
- [ ] Update TDD Practice Team listing to v2 standard

### P1 (Should Have)
- [ ] Auto-deploy pipeline (webhook → provision infra → deploy)
- [ ] Stripe Connect integration for builder payouts
- [ ] Hirer review collection flow (post 30-day prompt)
- [ ] Calibration corpus storage per hirer

### P2 (Nice to Have)
- [ ] In-browser IDE for zero-Git builders
- [ ] AI pair-programming during build
- [ ] A/B testing for listing pages
- [ ] Advanced analytics dashboard

---

## Next Tasks
1. Build Builder Portal (Flask + auth + Stripe)
2. Convert Probe and TDD listings to v2 format
3. Create submission webhook → Reviewer Agent integration
4. Set up Stripe Connect for builder payouts
5. Create hirer review collection email flow
