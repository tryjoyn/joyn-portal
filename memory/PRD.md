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

> **Full backlog with parking lot:** See `/app/BACKLOG.md`

### Current Sprint (Jan 2026)
- [x] Deploy fixed Creator Brief (pushed to GitHub)
- [ ] Build Sage v2 — Conversational Brief with real-time gate scoring
- [ ] New `/api/sage/chat` endpoint (stateful, streaming)
- [ ] Voice input (Whisper integration)
- [ ] A/B test infrastructure (URL param redirect)

### Parked (See BACKLOG.md)
- Multi-language support
- Admin conversation viewer
- GDPR delete endpoint
- Cost monitoring alerts

## Architectural Decisions
- **ADR-001:** Sage is stateful (server stores conversation)
- **ADR-002:** Persona named "Sage" not "Joyn"
- **ADR-003:** A/B via URL param `?v=2`
- **ADR-004:** New `/api/sage/chat` → feeds into existing `/api/builder/brief`

## Next Tasks
1. Build Sage backend (`/api/sage/chat`)
2. Build Sage frontend (`creator-brief-v2.html`)
3. Integrate voice input
4. Test A/B redirect flow
