# JOYN Deploy Checklist
**Version:** 1.0
**Last Updated:** March 2026

## Purpose

This checklist ensures every deploy is validated before and after pushing to production.

---

## Pre-Push Checks

### 1. Forbidden Terms Check
```bash
grep -rn "activate\|subscribe\|agents\|bots\|cancel\|tryjoin" . --include="*.html" --include="*.js" --include="*.css"
```
**Expected:** No matches

### 2. Broken Link Check (Local)
```bash
# Quick check for href="#" that should have destinations
grep -rn 'href="#"' . --include="*.html" | grep -v "skip-link\|modal\|onclick\|faq-"
```
**Expected:** Only intentional anchors

### 3. Context File Currency
- [ ] JOYN-CONTEXT.md version date updated?
- [ ] Changed files have corresponding context updates?
- [ ] CLAUDE.md sync rules followed?

### 4. Code Quality
- [ ] No console.log statements in production code
- [ ] No hardcoded API keys
- [ ] No commented-out code blocks > 5 lines

---

## Post-Push Verification

### Desktop Checks (Chrome/Firefox)
1. [ ] Homepage loads without errors
2. [ ] Navigation links work
3. [ ] Staff cards display correctly
4. [ ] Interest form submits
5. [ ] Marketplace filters work
6. [ ] Hire flow completes (test mode)

### Mobile Checks (DevTools or Real Device)
1. [ ] Hamburger menu opens/closes
2. [ ] Staff cards stack correctly
3. [ ] Forms are usable (tap targets)
4. [ ] No horizontal scroll
5. [ ] Back-to-top button works

### Portal Checks (app.tryjoyn.me)
1. [ ] Login page loads
2. [ ] JWT auth works
3. [ ] Dashboard displays data
4. [ ] Settings page accessible

---

## Monthly Maintenance

### Week 1
- [ ] Run broken link checker on tryjoyn.me
- [ ] Check GitHub Actions cron last run date
- [ ] Verify roster.json vs marketplace cards sync

### Week 2
- [ ] Check TLS certificates (tryjoyn.me, app.tryjoyn.me)
- [ ] Review SendGrid delivery stats
- [ ] Check Railway health endpoint

### Week 3
- [ ] Run retention purge API
- [ ] Review Iris cost logs
- [ ] Check llm_usage table growth

### Week 4
- [ ] Full visual regression test
- [ ] Review and close any open issues
- [ ] Update this checklist if needed

---

## Quarterly Review

- [ ] Re-read ETHICS.md, HUMAN-COLLAB.md, 5V.md
- [ ] Review BVD gap tracker
- [ ] Check pricing model validity
- [ ] Review Creator Studio applications
- [ ] Design system audit
- [ ] Update all context file version dates

---

## Emergency Contacts

| Issue | Contact | Action |
|-------|---------|--------|
| Site down | Railway dashboard | Check deployment status |
| Security incident | BREACH-RUNBOOK.md | Follow runbook |
| Payment issues | Stripe dashboard | Check webhook logs |
| Email failures | SendGrid dashboard | Check delivery status |

---

## Git Commands

### Standard Deploy
```bash
git add -A
git commit -m "feat: [description]"
git push origin main
```

### Specific File Deploy (per CLAUDE.md)
```bash
git add index.html marketplace/iris.html
git add context/JOYN-CONTEXT.md
git commit -m "fix: update hire CTA links"
git push origin main
```

---

## Contact

Deploy questions: hire@tryjoyn.me
