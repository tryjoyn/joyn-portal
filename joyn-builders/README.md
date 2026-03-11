# joyn-builders

Backend service for the Joyn Creator Studio. Handles the full builder journey from catalogue browsing through to marketplace deployment.

## Stack

- **Runtime:** Python 3.11 / Flask 3.0
- **Database:** SQLite (Railway persistent volume)
- **Payments:** Stripe (subscriptions + webhooks)
- **Email:** SendGrid
- **Deploy:** Railway

## Environment Variables

Set these in Railway — never in code:

```
STRIPE_SECRET_KEY        = sk_live_...
STRIPE_PUBLISHABLE_KEY   = pk_live_...
STRIPE_WEBHOOK_SECRET    = whsec_...
SENDGRID_API_KEY         = SG....
STRIPE_PRICE_ID          = price_...   (Founding Builder Seat — $99/year)
DB_PATH                  = /data/joyn_builders.db
```

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/catalogue` | Browse catalogue (filter by vertical, mode, track, complexity) |
| GET | `/api/catalogue/verticals` | All verticals with role counts |
| POST | `/api/catalogue/search` | Full-text search |
| GET | `/api/catalogue/<role_id>` | Single role detail |
| POST | `/api/builder/apply` | Submit builder application |
| POST | `/api/builder/checkout` | Create Stripe checkout session |
| POST | `/api/stripe/webhook` | Stripe webhook handler |
| GET | `/api/builder/status/<email>` | Builder dashboard data |
| POST | `/api/builder/brief` | Save Creator Brief answers |
| GET | `/api/builder/brief/<builder_id>` | Get saved brief |
| POST | `/api/builder/preflight` | Run pre-flight check against The Bar |
| POST | `/api/builder/stage` | Update build stage |

## Revenue Model

- **Founding Builders (first 100):** $99/year seat fee + 75% revenue share from day one (lifetime)
- **Standard Builders:** $99/year seat fee + tiered revenue share:
  - Launch (0–$1k MRR): 70% builder / 30% Joyn
  - Traction ($1k–$5k MRR): 75% builder / 25% Joyn
  - Scale ($5k+ MRR): 80% builder / 20% Joyn

## Deploy Sequence

```bash
# 1. Deploy to Railway
git push

# 2. Seed the catalogue (run once in Railway shell)
python seed_catalogue.py

# 3. Configure Stripe webhook
# URL: https://[railway-url]/api/stripe/webhook
# Events: checkout.session.completed, customer.subscription.deleted, invoice.payment_failed

# 4. Verify
curl https://[railway-url]/health
curl "https://[railway-url]/api/catalogue?limit=5"
curl https://[railway-url]/api/catalogue/verticals
```

## Build Stages

```
applied → paid → briefing → brief_approved → building →
submitted → under_review → conditional_pass → revising →
deployed → earning
```

---
*Joyn · tryjoyn.me · joyn-builders v1.0 · March 2026*
