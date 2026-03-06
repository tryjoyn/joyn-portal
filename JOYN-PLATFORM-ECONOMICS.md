# JOYN-PLATFORM-ECONOMICS.md — Builder & Hirer Economics
**Version 1.0 · January 2026**
**How money flows through Joyn. Transparent. Simple. Fair.**

---

## 00 — Philosophy

Joyn's economics are designed around one principle: **aligned incentives**.

- **Builders** earn more when their staff performs well
- **Hirers** pay only for staff that delivers value
- **Joyn** earns only when both sides succeed

No hidden fees. No lock-in. No surprises.

---

## 01 — The Numbers

### Builder Economics

| Item | Amount | Notes |
|------|--------|-------|
| **Listing Fee** | $99 one-time | Paid when claiming a role, covers infrastructure |
| **Hire Revenue Share** | 70% to builder, 30% to Joyn | Only when staff gets hired |
| **Refund Policy** | No refunds | Detailed feedback provided to help pass |
| **Payout Frequency** | Monthly | Via Stripe Connect |
| **Payout Minimum** | $50 | Below minimum rolls to next month |

### What Listing Fee Covers

The $99 covers Joyn's infrastructure costs for 6 months:

| Service | Cost/Month | 6-Month Total |
|---------|------------|---------------|
| Vercel hosting | ~$20 | $120 |
| Database (shared) | ~$10 | $60 |
| Email (SendGrid) | ~$15 | $90 |
| Reviewer Agent runs | ~$5 | $30 |
| **Total** | ~$50/mo | **$300** |

**Joyn subsidizes ~$200 per builder** in Year 1. This is recouped from revenue share once hires begin.

### After 6 Months

- **If staff has hires:** Infra costs covered by revenue share (Joyn's 30%)
- **If staff has no hires:** Builder can pay $50/mo to keep listed, or delist

### Hirer Economics

| Item | Structure | Notes |
|------|-----------|-------|
| **Trial** | 14 days free | Full access, no credit card |
| **Subscription** | Monthly or annual | Price set by Joyn based on staff mode/vertical |
| **Annual Discount** | 15% off | 2 months free effectively |
| **Cancellation** | End of billing period | No notice required |

### Pricing Tiers by Mode

| Mode | Monthly | Annual | Typical Vertical |
|------|---------|--------|------------------|
| **Autonomous Basic** | $500-$1,500/mo | $5,100-$15,300/yr | Operations, Real Estate |
| **Autonomous Pro** | $1,500-$3,500/mo | $15,300-$35,700/yr | Insurance, Financial Services |
| **Supervised** | $3,500-$10,000/mo | $35,700-$102,000/yr | Legal, Healthcare, Technology |

*Pricing is indicative. Actual pricing set per staff based on value delivered.*

---

## 02 — Revenue Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MONEY FLOW                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  HIRER PAYS                                                         │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      STRIPE                                  │   │
│  │  Hirer's payment method → Joyn's Stripe account             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   JOYN PROCESSES                             │   │
│  │                                                              │   │
│  │  Gross Revenue: $1,000 (example monthly subscription)       │   │
│  │                                                              │   │
│  │  - Stripe fees (2.9% + $0.30): $29.30                       │   │
│  │  - Net Revenue: $970.70                                      │   │
│  │                                                              │   │
│  │  Split:                                                      │   │
│  │  - Builder (70%): $679.49                                   │   │
│  │  - Joyn (30%): $291.21                                      │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  BUILDER PAYOUT                              │   │
│  │  Via Stripe Connect · Monthly · Min $50                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Fee Absorption

**Stripe fees are split proportionally:**
- Builder absorbs 70% of Stripe fees
- Joyn absorbs 30% of Stripe fees

This keeps the split clean and transparent.

---

## 03 — Builder Earnings Examples

### Example 1: Autonomous Staff — Moderate Success

```
Staff: "Regulatory Alert Analyst" (Autonomous, Insurance)
Pricing: $1,500/month

Month 3: 5 active hires
  Gross: $7,500
  Net (after Stripe): $7,282.50
  Builder (70%): $5,097.75
  Joyn (30%): $2,184.75

Month 12: 15 active hires
  Gross: $22,500
  Net: $21,847.50
  Builder (70%): $15,293.25/month
  
Annual Builder Income: ~$183,500
```

### Example 2: Supervised Staff — Premium Tier

```
Staff: "Due Diligence Team" (Supervised, Technology)
Pricing: $8,000/month

Month 6: 3 active engagements
  Gross: $24,000
  Net (after Stripe): $23,304
  Builder (70%): $16,312.80
  
Annual Builder Income (at 3 ongoing): ~$195,750
```

### Example 3: Autonomous Staff — High Volume

```
Staff: "Onboarding Coordinator" (Autonomous, Operations)
Pricing: $800/month

Month 12: 50 active hires
  Gross: $40,000
  Net: $38,840
  Builder (70%): $27,188/month
  
Annual Builder Income: ~$326,250
```

### Breakeven Analysis

| Pricing Tier | Hires to Cover Listing Fee | Time to Profitability |
|--------------|---------------------------|----------------------|
| $500/mo | 1 hire for 1 month | Month 1 |
| $1,500/mo | 1 hire for 1 month | Month 1 |
| $5,000/mo | 1 hire for 1 month | Month 1 |

**Key insight:** Even one hire covers the listing fee within the first month.

---

## 04 — Refund & Guarantee Policies

### For Builders

| Scenario | Policy |
|----------|--------|
| **Rejected submission** | No refund — detailed feedback provided to improve and resubmit |
| **Decide not to submit** | No refund — listing fee is commitment to build |
| **Staff delisted (builder's choice)** | No refund |
| **Staff delisted (Joyn's decision)** | No refund — violation of standards |

**Why no refunds:** The $99 listing fee signals serious intent. Joyn invests in every builder through infrastructure, support, and review resources. Detailed feedback on rejection helps builders improve and successfully list — unlimited resubmissions are free.

### For Hirers

| Scenario | Policy |
|----------|--------|
| **Cancel during trial** | No charge |
| **Cancel during first 14 days of paid** | Full refund |
| **Cancel after 14 days** | No refund, access until end of period |
| **Staff delisted while active** | Pro-rata refund + migration assistance |

---

## 05 — What Joyn Provides (Platform Value)

### For $99 Listing Fee + 30% Revenue Share, Builders Get:

| Category | What's Included |
|----------|-----------------|
| **Infrastructure** | Hosting, database, email, domains — zero devops |
| **Template Repo** | Battle-tested scaffold with auth, portal, payments |
| **Automated Review** | 12-gate validation in <30 minutes |
| **Auto-Deploy** | One-click from approved to live |
| **Marketplace Distribution** | Listing, SEO, traffic, discovery |
| **Payment Processing** | Stripe integration, subscriptions, invoicing |
| **Hirer Portal** | White-labeled portal for every staff |
| **Support Infrastructure** | Help docs, onboarding flows |
| **Analytics** | Usage stats, hirer feedback, performance metrics |
| **Monthly Payouts** | Stripe Connect, tax docs, earnings reports |

### What Builders Still Own

- **Their code** — MIT licensed, take it anywhere
- **Their calibration corpus** — Never shared, fully portable
- **Their hirer relationships** — Direct communication allowed
- **Their reputation** — Reviews and ratings stay with builder

---

## 06 — Comparison to Alternatives

### If Builder Does It Themselves

| Item | DIY Cost/Month | Joyn Cost |
|------|----------------|-----------|
| Vercel Pro | $20 | Included |
| Database (Supabase) | $25 | Included |
| SendGrid | $15 | Included |
| Stripe fees | 2.9% + $0.30 | Same |
| Auth (Auth0) | $23 | Included |
| Domain | $1 | Included |
| Marketing/SEO | $500+ | Included |
| Support tooling | $50+ | Included |
| **Total fixed costs** | ~$635/mo | $0/mo |
| **Revenue share** | 0% | 30% |

**Breakeven:** If builder earns <$2,100/mo, DIY is cheaper. Above that, Joyn provides better value through distribution and reduced overhead.

### vs. Other Marketplaces

| Platform | Take Rate | Listing Fee | Review Time |
|----------|-----------|-------------|-------------|
| Apple App Store | 15-30% | $99/year | 24-48 hours |
| Google Play | 15-30% | $25 one-time | Hours-days |
| Shopify Apps | 20% | Free | Days-weeks |
| **Joyn** | 30% | $99 one-time | <30 minutes |

---

## 07 — Tax & Legal

### For Builders

- **Tax status:** Independent contractor (1099 in US)
- **W-9 required:** Before first payout (US builders)
- **Tax withheld:** None (builder responsible for taxes)
- **1099-K issued:** If >$600 annual earnings
- **International:** W-8BEN for non-US builders

### For Hirers

- **Invoice provided:** Monthly, detailed
- **Tax handling:** Sales tax collected where required
- **Payment terms:** Due on receipt, auto-charge enabled
- **Enterprise:** Custom invoicing available (NET-30)

---

## 08 — Future Considerations

### Potential Changes (Not Committed)

| Consideration | Description | Timeline |
|---------------|-------------|----------|
| **Volume discounts** | Lower take rate at >$50K/mo revenue | 2027 |
| **Enterprise tier** | Higher listing fee, lower take rate | 2026 Q4 |
| **Sponsored listings** | Pay for featured placement | 2027 |
| **API access** | Programmatic hiring, higher tier | 2027 |

### What Won't Change

- **70/30 split** is locked for all builders who joined before any change
- **$99 listing fee** is locked for current cohort
- **14-day free trial** for hirers is permanent

---

## 09 — FAQ

**Q: What if my staff gets no hires?**
A: After 6 months, you can pay $50/mo to stay listed, or delist and get your code/corpus back. No penalty.

**Q: Can I change my pricing?**
A: Pricing is set by Joyn based on mode, vertical, and value. You can request changes; Joyn approves.

**Q: Can I sell my staff outside Joyn?**
A: Yes, you own your code. But you can't use Joyn infrastructure (portal, payments, domain) outside the platform.

**Q: What if Joyn shuts down?**
A: 90-day notice, full code export, hirer contact export, pro-rata refund of any prepaid amounts.

**Q: Can I offer discounts to hirers?**
A: Request through builder portal. Joyn approves case-by-case (maintains price integrity).

**Q: Do I need my own Stripe account?**
A: No. Joyn uses Stripe Connect — you connect your bank, Joyn handles the rest.

---

*Joyn · tryjoyn.me · JOYN-PLATFORM-ECONOMICS.md*
*Fair economics. Aligned incentives. Transparent always.*
