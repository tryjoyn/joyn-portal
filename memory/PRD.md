# Joyn - Probe Insurance Innovation Page PRD

## Original Problem Statement
Build marketplace/probe-insurance-innovation.html following the structure of practice/tdd-practice-team.html exactly.

## Probe Details
- **Name**: Probe
- **Full name**: Insurance Innovation Experimentation Team
- **Mode**: Supervised
- **Vertical**: Technology
- **Status**: Live
- **Agents (7)**: Intake, Scout, Architect, Challenger, Environ, Run, Debrief
- **One line**: Runs structured insurance innovation experiments end to end — from hypothesis to verdict
- **Hirer**: Innovation leads at carriers, MGAs, and insurtechs running regulated experiments
- **Hirer time commitment**: ~2.5 hours across full experiment lifecycle
- **Intervention points (3)**: Intake, Challenger sign-off, Debrief verdict
- **Named outputs (6)**: Experiment Brief, Landscape Memo, Design Canvas, Red Team Memo, Weekly Status Reports, Verdict Report + Demo Video

## Architecture
- Single self-contained HTML file with inline CSS and JS
- No npm dependencies, React, Vue, or external CSS frameworks
- Fonts: Google Fonts CDN (Cormorant Garamond, DM Mono, Syne)
- Forms: Web3Forms API with key `5b972adb-feba-4546-a657-02d5e29b6e29`

## User Personas
1. **Innovation leads at carriers** - Running regulated experiments in insurance
2. **MGA leaders** - Testing new insurance products and services
3. **Insurtech founders** - Validating hypotheses before scaling

## Core Requirements (Static)
- Follow Joyn Design Spec v2.0
- Use Joyn terminology (hire, staff, role)
- Match TDD Practice Team page structure exactly
- Web3Forms integration for hire CTA

## What's Been Implemented
- [x] Hero section with stats (7 agents, 2.5h time, 3 interventions, 6 outputs)
- [x] Benchmark band with experiment lifecycle stats
- [x] Roster section with all 7 agents (Intake through Debrief)
- [x] Synthesis card for Debrief with input sources and output
- [x] Intervention tags on mandatory intervention points
- [x] Named outputs section (6 deliverables)
- [x] Engagement model (3 intervention points)
- [x] Experiment protocol section
- [x] Web3Forms hire form
- [x] Mobile responsive design
- [x] Back-to-top button
- [x] Mobile brief bar
- [x] Footer with navigation

**Date**: January 2026

## Backlog
- P0: None remaining (MVP complete)
- P1: Connect to marketplace listing when published
- P2: Add testimonials section when available

## Next Tasks
1. Deploy to GitHub Pages via `git push` from Joyn/ directory
2. Link from marketplace/index.html when ready
3. Add to roster.json with status: live
