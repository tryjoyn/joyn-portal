# JOYN Infrastructure Migration Guide
**Version:** 1.0
**Last Updated:** March 2026

## Purpose

This document defines migration triggers and procedures for scaling infrastructure as Joyn grows.

---

## Current Architecture (Stage 0)

| Component | Current | Limit | Status |
|-----------|---------|-------|--------|
| Database | SQLite | ~100 concurrent writers | Adequate |
| Backend | Railway (Flask) | 500 req/day sustained | Adequate |
| Static Site | GitHub Pages | Unlimited | Adequate |
| Email | SendGrid Free | 100 emails/day | Adequate |
| Vector DB | None | N/A | Deferred |

---

## Migration Triggers

### SQLite → PostgreSQL

**Trigger Conditions (ANY):**
1. Active hirers > 100
2. Portal provisioning latency > 2 seconds
3. Write-lock contention errors in logs
4. Quarterly review decision

**Migration Procedure:**
1. Export SQLite to PostgreSQL-compatible SQL
2. Set up PostgreSQL on Railway (or Supabase)
3. Update connection strings in environment
4. Run parallel writes for 1 week
5. Switch reads to PostgreSQL
6. Decommission SQLite after 30 days

**Estimated Effort:** 2-3 days

### SendGrid Free → Pro

**Trigger Conditions:**
1. Total hirers × alert frequency > 80/day (80% of limit)
2. Email delivery failures due to rate limiting
3. Need for dedicated IP or advanced analytics

**Migration Procedure:**
1. Upgrade plan in SendGrid dashboard
2. No code changes required
3. Verify sender authentication settings

**Estimated Effort:** 1 hour

### Railway → Larger Plan

**Trigger Conditions:**
1. Sustained 500+ req/day
2. Memory pressure warnings
3. Response latency > 1 second P95

**Migration Procedure:**
1. Upgrade plan in Railway dashboard
2. Increase memory/CPU allocation
3. Monitor for 1 week

**Estimated Effort:** 30 minutes

### Vector DB (pgvector)

**Trigger Conditions:**
1. Active clients > 500
2. Bulletin history > 12 months
3. Semantic search feature required

**Migration Procedure:**
1. Enable pgvector extension in PostgreSQL
2. Create RegulatoryFacts table
3. Backfill embeddings for historical bulletins
4. Update Iris to use semantic retrieval

**Estimated Effort:** 1-2 weeks

---

## Scaling Estimates

| Hirers | Database | Backend | Email Plan | Est. Monthly Cost |
|--------|----------|---------|------------|-------------------|
| 1-50 | SQLite | Railway Free | SendGrid Free | $0 |
| 50-100 | SQLite | Railway Hobby ($5) | SendGrid Free | $5 |
| 100-250 | PostgreSQL | Railway Pro ($20) | SendGrid Essentials ($20) | $40 |
| 250-500 | PostgreSQL | Railway Pro | SendGrid Pro ($50) | $70 |
| 500+ | PostgreSQL + pgvector | Railway Team | SendGrid Pro | $100+ |

---

## Annual Infrastructure Review

### Questions to Answer
1. What is current hirer count?
2. Is SQLite still viable?
3. Are we approaching any trigger thresholds?
4. Is vector DB readiness needed in next 6 months?
5. Are current plans cost-efficient?

### Data to Collect
- Hirer count from portal database
- Request count from Railway metrics
- Email count from SendGrid dashboard
- Cost breakdown by service
- Performance metrics (latency, errors)

---

## Emergency Scaling

If sudden traffic spike:

1. **Railway:** Increase memory in dashboard (instant)
2. **Database:** Add read replica (if PostgreSQL)
3. **Email:** Upgrade plan immediately
4. **Static site:** No action needed (GitHub Pages handles it)

### Rate Limiting
Current limits:
- Portal API: 100 req/min per IP
- Form submission: 10/min per IP
- Stripe webhook: Unlimited (verified by signature)

---

## Contact

Infrastructure questions: hire@tryjoyn.me
