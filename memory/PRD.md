# Joyn Portal - PRD

## Original Problem Statement
User unable to login on tryjoyn.me signin page (404 error). Need to investigate and verify multi-agentic iris v2.0 model is intact.

## Architecture
- **joyn-portal**: Flask-based client portal (auth, dashboard, staff management)
- **iris-agent**: Multi-agent regulatory intelligence system (SupervisorAgent + Worker + 4 tools)
- **Static site**: GitHub Pages hosting tryjoyn.me main landing page

## Core Requirements
1. User authentication (JWT-based with cookies)
2. Client dashboard with hired staff management
3. Iris integration for regulatory monitoring
4. Activity logging and output tracking

## What's Been Implemented (Jan 2026)
- [x] Investigated 404 login issue - identified Railway misconfiguration
- [x] Fixed Railway deployment configs (railway.json, nixpacks.toml)
- [x] Verified login works locally with test credentials
- [x] Audited iris-agent multi-agentic architecture (intact)
- [x] Created test user in local database

## Prioritized Backlog
### P0 - Critical
- [ ] Redeploy joyn-portal on Railway with correct root directory

### P1 - High
- [ ] Verify production login after deployment
- [ ] Test iris-agent end-to-end integration

### P2 - Medium
- [ ] Implement password reset email flow (SendGrid TODO)
- [ ] Add more comprehensive error handling in auth routes

## Next Tasks
1. Push updated railway.json and nixpacks.toml to GitHub
2. In Railway dashboard, set Root Directory to `joyn-portal`
3. Trigger redeployment
4. Verify https://app.tryjoyn.me/login works
5. Test with provided credentials
