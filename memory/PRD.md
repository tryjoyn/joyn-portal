# Joyn Builders - PRD

## Original Problem Statement
Builders/creators marketplace for Joyn - AI staffing platform where domain experts build AI staff and earn revenue share.

## Architecture
- **Backend**: Flask API on Railway (PostgreSQL) - `/app/joyn-builders/`
- **Frontend**: Static HTML on GitHub Pages (tryjoyn.me) - `/app/marketplace/`
- **Payments**: Stripe ($99/yr Founding Builder Seats)
- **Email**: SendGrid
- **AI Agents**: OpenAI GPT-4.1-mini (Architect, Reviewer, Deployment, Sage)

## What's Been Implemented (Jan 2026)

### Sage v2 — Conversational Brief System
- **Frontend**: `creator-brief-v2.html` — Chat UI with Sage persona
- **Backend**: `/api/sage/*` endpoints — start, chat, voice, status, complete, resume
- **Prompts**: `prompts/sage_v1.py` — Versioned system prompts
- **Gate Scoring**: `shared/gate_scoring.py` — Real-time quality scoring
- **Features**:
  - Conversational brief collection (replaces 6-section form)
  - Real-time gate progress visualization
  - Voice input via Whisper
  - Session persistence and resume
  - Rate limiting (60 msg/hour)
  - Graceful fallback when LLM unavailable
  - A/B testing via `?v=2` URL param

### Files Created
- `/app/joyn-builders/agents/sage_agent.py`
- `/app/joyn-builders/prompts/sage_v1.py`
- `/app/joyn-builders/prompts/__init__.py`
- `/app/joyn-builders/shared/gate_scoring.py`
- `/app/joyn-builders/shared/__init__.py`
- `/app/marketplace/creator-brief-v2.html`

### Files Modified
- `/app/joyn-builders/app.py` — Added Sage endpoints
- `/app/joyn-builders/agents/__init__.py` — Updated docs
- `/app/marketplace/creator-brief.html` — Added A/B redirect

## Next Tasks
1. Push changes to GitHub
2. Test Sage flow end-to-end with real builder account
3. Monitor A/B metrics (v1 form vs v2 chat completion rates)

## Backlog
See `/app/BACKLOG.md` for full backlog and parking lot.
