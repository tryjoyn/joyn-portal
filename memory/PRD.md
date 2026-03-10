# Joyn Builders - PRD

## Original Problem Statement
Builders/creators marketplace for Joyn - AI staffing platform where domain experts build AI staff and earn revenue share.

## Architecture
- **Backend**: Flask API on Railway (PostgreSQL) - `/app/joyn-builders/`
- **Frontend**: Static HTML on GitHub Pages (tryjoyn.me) - `/app/marketplace/`
- **Payments**: Stripe ($99/yr Founding Builder Seats)
- **Email**: SendGrid
- **AI Agents**: OpenAI GPT-4.1-mini (Architect, Reviewer, Deployment agents)

## User Personas
1. **Builders**: Domain experts who build AI staff and earn 75% revenue share
2. **Hirers**: Businesses who hire AI staff on the marketplace
3. **Admins**: Joyn team managing the platform

## Core Requirements (Static)
- Builder application + Stripe payment flow
- Creator Brief → Visionary Spec generation
- Pre-flight check against The Bar (5 gates)
- Marketplace catalogue with search/filter
- Builder dashboard with stage tracking

## What's Been Implemented
- ✅ Full catalogue API with filtering
- ✅ Builder application + Stripe checkout
- ✅ Creator Brief form (6 sections)
- ✅ Architect Agent (generates Visionary Spec)
- ✅ Pre-flight check system
- ✅ Marketplace with live staff (Iris, TDD Practice Team, Probe)

## Recent Fixes (Jan 2026)
- Fixed Creator Brief submission bug:
  - Corrected payload format (`answers` not `brief`)
  - Added `completed: true` flag
  - Field name mapping for Architect Agent
  - API now returns `visionary_spec` in response

## Prioritized Backlog
### P0 (Critical)
- [ ] Deploy fixed Creator Brief (push to GitHub)

### P1 (High)
- [ ] Add error logging for Architect Agent failures
- [ ] Retry logic for spec generation timeouts

### P2 (Medium)
- [ ] Email notifications when Visionary Spec is ready
- [ ] Better loading states during generation

## Next Tasks
1. Push changes to GitHub
2. Verify Railway auto-deploys backend
3. Test full Creator Brief flow with test account
