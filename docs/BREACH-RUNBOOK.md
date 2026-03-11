# JOYN Breach Response Runbook
**Version:** 1.0
**Last Updated:** March 2026

## Purpose

This runbook defines the immediate response procedure for any data incident involving customer data collected through the Joyn platform.

---

## 1. Data at Risk

### Customer Data Inventory
| Data Type | Source | Impact if Exposed |
|-----------|--------|-------------------|
| Email addresses | Hire forms, registration | Spam, phishing risk |
| Company names | Hire forms | Business intelligence leak |
| Contact names | Hire forms | Personal data exposure |
| Passwords | Portal accounts | Account compromise (hashed) |
| Jurisdictions/States | Iris clients | Business intelligence |

### Current Scale
- Active hirers: < 100
- Email addresses stored: < 500
- Forms of intake: 3 (Web3Forms, Portal registration, In-portal hire)

---

## 2. Immediate Response Checklist (< 1 hour)

### Step 1: Confirm & Contain (0-15 minutes)
- [ ] Verify breach is real (not false positive)
- [ ] Identify affected data types and scope
- [ ] **DISABLE INTAKE IMMEDIATELY:**
  ```bash
  # Railway dashboard → Suspend service
  # OR set maintenance mode in portal
  ```
- [ ] Preserve logs before any changes
- [ ] Document timestamp of discovery

### Step 2: Assess Impact (15-30 minutes)
- [ ] Count affected records
- [ ] Identify attack vector (if known)
- [ ] Determine if attacker still has access
- [ ] Check for lateral movement

### Step 3: Remediate (30-60 minutes)
- [ ] Rotate compromised credentials immediately:
  - JWT_SECRET
  - JOYN_PORTAL_SECRET
  - API keys (regenerate in provider dashboards)
- [ ] If DB exposed: Take offline, backup, forensics
- [ ] Close attack vector (patch, disable endpoint)

---

## 3. Notification Requirements

### Internal (Immediate)
- **Founder/CEO:** Shiva (hire@tryjoyn.me)
- **Technical Lead:** (as applicable)

### Regulatory (24-72 hours)
- **GDPR (if EU data):** Supervisory authority within 72 hours
- **CCPA (if CA residents):** No mandatory timeline, but prompt
- **State breach laws:** Varies by state (check affected jurisdictions)

### Affected Users (Prompt)
Email template:
```
Subject: Security Notice — Joyn

We are writing to inform you of a security incident affecting your account.

What happened: [Brief description]
What data was involved: [Specific data types]
What we are doing: [Remediation steps]
What you should do: [User actions recommended]

Contact: hire@tryjoyn.me
```

---

## 4. Recovery Procedure

### Database Recovery
1. Restore from latest backup (Railway automatic backups)
2. Verify data integrity
3. Re-enable services in maintenance mode
4. Test critical flows
5. Gradual traffic restoration

### Credential Reset
1. Force password reset for all portal users
2. Regenerate all API keys
3. Update all environment variables
4. Verify integrations still function

---

## 5. Post-Incident Review (Within 7 days)

- [ ] Root cause analysis document
- [ ] Timeline reconstruction
- [ ] Gap analysis (what failed)
- [ ] Remediation verification
- [ ] Process improvement recommendations
- [ ] Update this runbook if needed

---

## 6. Quick Reference

### Emergency Contacts
| Role | Contact |
|------|---------|
| Founder/CEO | Shiva — hire@tryjoyn.me |
| Railway Support | support@railway.app |
| SendGrid Security | security@sendgrid.com |
| Stripe Security | security@stripe.com |

### Key Actions Summary
1. **Confirm** the breach is real
2. **Contain** by disabling affected services
3. **Assess** scope and impact
4. **Remediate** by rotating credentials
5. **Notify** affected parties
6. **Review** and improve

---

## 7. Prevention Measures

- No secrets in source code (use env vars)
- Regular credential rotation
- Access logging enabled
- Minimal data retention (90-day bulletin purge)
- Input validation on all endpoints
- Rate limiting on public endpoints
