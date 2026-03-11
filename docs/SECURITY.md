# JOYN Security Documentation
**Version:** 1.0
**Last Updated:** March 2026

## 1. TLS / Encryption in Transit

### Certificate Status

| Endpoint | Protocol | Certificate Authority | Verified |
|----------|----------|----------------------|----------|
| tryjoyn.me | HTTPS (TLS 1.3) | Let's Encrypt via GitHub Pages | Yes |
| app.tryjoyn.me | HTTPS (TLS 1.3) | Let's Encrypt via Railway | Yes |
| Railway Backend (internal) | HTTPS | Railway managed | Yes |

### Data Flow Encryption

All data in transit is encrypted:
1. **Browser → GitHub Pages (marketing site):** TLS 1.3
2. **Browser → Railway (portal/API):** TLS 1.3
3. **Portal → Iris Agent:** HTTPS with X-Joyn-Secret header
4. **Portal → SendGrid:** TLS (SendGrid managed)
5. **Portal → Stripe:** TLS (Stripe managed)

---

## 2. JWT Secret Management

### Storage Location
- **Environment:** Railway environment variables
- **Key Name:** `JWT_SECRET`
- **Access:** Only Railway deployment has access
- **Source Code:** Never committed (verified via .gitignore)

### Security Properties
- Algorithm: HS256
- Token Expiry: 7 days
- Cookie Settings:
  - HttpOnly: true
  - SameSite: Lax
  - Secure: true (production)

### Rotation Schedule
- Quarterly review recommended
- Emergency rotation: Invalidate all sessions by changing JWT_SECRET in Railway

---

## 3. API Key & Credential Management

| Credential | Storage | Rotation Schedule | Access Scope |
|------------|---------|-------------------|--------------|
| JWT_SECRET | Railway env | Quarterly | Portal auth only |
| JOYN_PORTAL_SECRET | Railway env | Quarterly | Iris ↔ Portal comms |
| ANTHROPIC_API_KEY | Railway env | As needed | Iris Claude calls only |
| SENDGRID_API_KEY | Railway env | Annual | Email send only (no read) |
| STRIPE_SECRET_KEY | Railway env | Annual | Payment processing |
| STRIPE_WEBHOOK_SECRET | Railway env | Per webhook endpoint | Webhook validation |

### Least Privilege Applied
- SendGrid key: Mail Send permission only
- Stripe key: Restricted to necessary operations
- Portal secret: Shared only between Portal and Iris

---

## 4. Authentication Architecture

### Portal Authentication
1. User submits email/password via `/login`
2. Server validates against bcrypt hash (12 rounds)
3. JWT issued with 7-day expiry
4. JWT stored in HttpOnly cookie
5. All authenticated routes check JWT validity

### API Authentication (Internal)
1. Iris → Portal: `X-Joyn-Secret` header
2. Portal validates against `JOYN_PORTAL_SECRET` env var
3. Fallback: Bearer token with API key (hashed in DB)

---

## 5. Data Protection

### Sensitive Data Inventory
| Data Type | Storage | Encryption | Retention |
|-----------|---------|------------|-----------|
| Passwords | SQLite | bcrypt hash (12 rounds) | Indefinite |
| Email addresses | SQLite | Plaintext | Until deletion request |
| JWT tokens | Cookie | Base64 + HS256 signature | 7 days |
| API keys | SQLite | SHA-256 hash | Until revoked |
| Bulletin content | SQLite | Plaintext | 90 days (policy) |

### Data Isolation (Multi-Hirer)
See DATA-ISOLATION.md for detailed isolation statement.

---

## 6. Verification Checklist (Monthly)

- [ ] TLS certificates valid for tryjoyn.me
- [ ] TLS certificates valid for app.tryjoyn.me
- [ ] Railway deployment uses HTTPS
- [ ] JWT_SECRET in Railway env (not in code)
- [ ] All API keys in Railway env (not in code)
- [ ] No secrets in recent commits (git log review)

---

## 7. Contact

Security issues: security@tryjoyn.me (or hire@tryjoyn.me)
