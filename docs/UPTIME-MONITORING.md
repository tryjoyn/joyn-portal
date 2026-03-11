# JOYN Uptime Monitoring Setup
**Version:** 1.0
**Last Updated:** March 2026

## Purpose

This document provides instructions for setting up uptime monitoring for Joyn services.

---

## Health Endpoints

### Portal API (app.tryjoyn.me)
```
GET https://app.tryjoyn.me/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "joyn-portal",
  "timestamp": "2026-03-11T00:00:00Z"
}
```

### Iris Agent (Railway)
```
GET https://iris.tryjoyn.me/health  (if exposed)
```

---

## UptimeRobot Setup (Free Tier)

### Step 1: Create Account
1. Go to https://uptimerobot.com
2. Sign up for free account
3. Verify email

### Step 2: Add Monitors

#### Monitor 1: Portal Health
- **Monitor Type:** HTTP(s)
- **Friendly Name:** Joyn Portal
- **URL:** `https://app.tryjoyn.me/health`
- **Monitoring Interval:** 5 minutes
- **Alert Contacts:** Your email

#### Monitor 2: Marketing Site
- **Monitor Type:** HTTP(s)
- **Friendly Name:** Joyn Marketing
- **URL:** `https://tryjoyn.me`
- **Monitoring Interval:** 5 minutes
- **Alert Contacts:** Your email

#### Monitor 3: Marketplace
- **Monitor Type:** HTTP(s)
- **Friendly Name:** Joyn Marketplace
- **URL:** `https://tryjoyn.me/marketplace/index.html`
- **Monitoring Interval:** 5 minutes
- **Alert Contacts:** Your email

### Step 3: Configure Alerts
1. Go to My Settings → Alert Contacts
2. Add email: hire@tryjoyn.me
3. (Optional) Add Slack webhook for instant alerts

---

## Alternative: Better Uptime (Free Tier)

If UptimeRobot is unavailable:

1. Go to https://betteruptime.com
2. Sign up for free Hobby plan
3. Add same monitors as above
4. Configure email alerts

---

## Expected Response Times

| Endpoint | Expected P95 | Alert Threshold |
|----------|--------------|-----------------|
| /health | < 200ms | > 2000ms |
| Homepage | < 500ms | > 3000ms |
| Marketplace | < 500ms | > 3000ms |

---

## Incident Response

When alert fires:

1. Check Railway dashboard for backend status
2. Check GitHub Pages for frontend status
3. Review logs: `railway logs --service joyn-portal`
4. Follow BREACH-RUNBOOK.md if data incident suspected

---

## Monthly Review

- [ ] Check uptime percentage (target: 99.5%+)
- [ ] Review any incidents from past month
- [ ] Verify alert contacts are current
- [ ] Test alert delivery manually

---

## Contact

Monitoring questions: hire@tryjoyn.me
