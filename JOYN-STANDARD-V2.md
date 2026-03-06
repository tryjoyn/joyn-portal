# JOYN-STANDARD-V2.md — The Complete AI Staff Standard
**Version 2.0 · January 2026**
**The definitive standard for building, validating, listing, and operating AI staff on the Joyn marketplace.**

---

## 00 — Philosophy

Joyn operates like the Apple App Store: **open on tools, closed on standards.**

Builders can use any tool — Claude, Cursor, Manus, Emergent, v0, or raw code. But every AI staff must pass the same gates. No exceptions. No partial credit. No manual overrides.

This document defines:
1. **The 12 Gates** — What every AI staff must pass before deployment
2. **The Listing Standard** — Consistent format for all marketplace pages
3. **The Trust System** — Verified reviews, ratings, and signals
4. **The Governance Framework** — Ethics, security, privacy, and compliance
5. **The Hirer Experience Standard** — Consistent UX across all staff
6. **The Builder Experience Standard** — Frictionless path from idea to income

---

## 01 — The 12 Gates

Every AI staff must pass all 12 gates. The Reviewer Agent validates each automatically. Gates are grouped into four categories: **Quality**, **Safety**, **Trust**, and **Compliance**.

### QUALITY GATES (Gates 1-5)

These are the original "Bar" gates — focused on whether the staff actually works.

#### Gate 01 · Role Clarity
**Question:** Can a hirer understand in one sentence what this staff does?

| Requirement | Validation |
|-------------|------------|
| One-sentence role description | NLP check: single sentence, <25 words, no conjunctions splitting scope |
| Clear scope boundaries | "Does X" and "Does not do Y" both specified |
| No category confusion | Role is specific (not "handles insurance" but "monitors FL regulatory bulletins") |

**Auto-fail triggers:**
- Description requires "and" to explain core function
- Uses vague terms: "assists with", "helps manage", "supports"
- Scope overlaps with existing live staff

---

#### Gate 02 · Output Standard
**Question:** Does the hirer know exactly what deliverables they will receive?

| Requirement | Validation |
|-------------|------------|
| Named outputs | Each deliverable has a specific name |
| Format specification | PDF, email, JSON, dashboard widget — specified |
| Frequency/trigger | "Daily at 9am" or "Within 2h of FNOL submission" |
| Sample provided | At least one real output specimen per named output |

**Auto-fail triggers:**
- Outputs described as "reports and recommendations" (not named)
- No output specimens in submission
- Specimens are templates, not completed artifacts

---

#### Gate 03 · Hirer Experience
**Question:** Does the staff know when to act and when to ask?

| Requirement | Validation |
|-------------|------------|
| Autonomous decisions documented | List of decisions staff makes without asking |
| Escalation triggers defined | Specific conditions that trigger hirer involvement |
| Intervention points (Supervised) | Named checkpoints where hirer input is required |
| Time commitment disclosed | "~30 min/week" for Autonomous, "~2.5h total" for Supervised |

**Auto-fail triggers:**
- No escalation logic defined
- Supervised mode with no intervention points
- Every output requires hirer approval (broken workflow)

---

#### Gate 04 · Failure Handling
**Question:** What happens when things go wrong?

| Requirement | Validation |
|-------------|------------|
| Declined data handling | Staff logs gap, notes confidence impact, proceeds |
| Ambiguous input handling | Asks ONE clarifying question, not several |
| Out-of-scope handling | Escalates with specific description |
| No hallucination | Never invents data it wasn't given |

**Auto-fail triggers:**
- Test scenario: declined data → staff proceeds as if data was provided
- Test scenario: ambiguous input → staff asks 3+ questions
- Test scenario: out-of-scope request → staff attempts anyway

---

#### Gate 05 · Calibration Architecture
**Question:** Does the staff get better with every engagement?

| Requirement | Validation |
|-------------|------------|
| Feedback collection | Defined questions asked post-engagement |
| Corpus structure | JSON/structured format for storing feedback |
| Forward reference | Evidence that corpus influences future engagements |
| Hirer ownership | Calibration data belongs to hirer, not shared |

**Auto-fail triggers:**
- No feedback mechanism
- Feedback collected but not stored/referenced
- Corpus shared across hirers without consent

---

### SAFETY GATES (Gates 6-8)

These gates ensure AI staff don't cause harm.

#### Gate 06 · Security by Design
**Question:** Is this staff secure from attack and misuse?

| Requirement | Validation |
|-------------|------------|
| Input validation | All inputs sanitized; prompt injection tests pass |
| Output filtering | PII detection, sensitive data redaction |
| Least privilege | Staff only accesses what it needs |
| Secret management | No hardcoded keys, credentials in env vars |
| Code execution sandboxing | If staff generates code, isolated execution |

**Automated tests run:**
- Prompt injection battery (10 attack vectors)
- PII leakage test (inject test PII, verify not exposed)
- Privilege escalation test (attempt unauthorized action)
- Secret scan (regex for API keys, passwords)

**Auto-fail triggers:**
- Any prompt injection test succeeds
- PII appears in output when not explicitly requested
- Staff attempts action outside defined scope
- Hardcoded credentials found in code

---

#### Gate 07 · AI Harm Prevention
**Question:** Can this staff cause real-world harm?

| Requirement | Validation |
|-------------|------------|
| Content safety | No generation of harmful, illegal, or deceptive content |
| Bias detection | Outputs tested for demographic bias |
| Manipulation check | Staff cannot be used for social engineering |
| Confidence disclosure | Staff indicates certainty level, never presents uncertain as certain |
| Human escalation for high-stakes | Decisions affecting rights/money require human approval |

**Automated tests run:**
- Content safety classifier on sample outputs
- Bias audit on decision-making logic
- Deception detection (attempts to make staff lie)
- High-stakes scenario test (does it escalate appropriately?)

**Auto-fail triggers:**
- Generates content classified as harmful
- Statistically significant bias detected
- Successfully manipulated into deception
- Makes high-stakes decision without escalation path

---

#### Gate 08 · Operational Resilience
**Question:** What happens when the staff breaks?

| Requirement | Validation |
|-------------|------------|
| Graceful degradation | Service interruption doesn't lose data |
| Error logging | All failures logged with context |
| Recovery procedure | Documented steps to resume after failure |
| Kill switch | Can be immediately disabled if behaving badly |
| Incident notification | Hirers notified of service issues |

**Automated tests run:**
- Simulate API failure mid-operation
- Simulate database unavailability
- Trigger kill switch, verify immediate stop

**Auto-fail triggers:**
- Data loss on simulated failure
- Silent failure (no log, no notification)
- Kill switch doesn't work within 30 seconds

---

### TRUST GATES (Gates 9-10)

These gates ensure hirers can trust what they're getting.

#### Gate 09 · Listing Accuracy
**Question:** Does the listing match reality?

| Requirement | Validation |
|-------------|------------|
| Claims verification | Every ROI claim has evidence |
| Screenshot authenticity | Screenshots are from actual running staff |
| Demo video authenticity | Video shows real operation, not mockup |
| No misleading language | No "up to", "as much as", "potentially" |

**Automated tests run:**
- Screenshot comparison to live staff UI
- Video frame analysis for editing/fakery
- NLP scan for weasel words in listing copy

**Auto-fail triggers:**
- Screenshot doesn't match live UI
- ROI claim without supporting evidence
- Video shows features not present in submission

---

#### Gate 10 · Transparent Pricing
**Question:** Does the hirer know what they're paying for?

| Requirement | Validation |
|-------------|------------|
| Price clearly stated | Monthly/annual/per-use pricing visible |
| No hidden fees | All costs disclosed before hire |
| Trial terms clear | What's included, what's not, duration |
| Cancellation terms | How to "let go", any notice period |

**Auto-fail triggers:**
- Pricing requires clicking through to find
- Additional fees discovered post-hire
- Trial limitations not disclosed upfront

---

### COMPLIANCE GATES (Gates 11-12)

These gates ensure legal and regulatory compliance.

#### Gate 11 · Data Protection & Privacy
**Question:** Does this staff comply with GDPR, CCPA, and data protection laws?

| Requirement | Validation |
|-------------|------------|
| Data minimization | Only collects data necessary for function |
| Lawful basis | Processing has valid legal basis |
| Consent mechanism | Where required, consent is obtained |
| Data subject rights | Hirers can access, correct, delete their data |
| Automated decision transparency | If ADM affects hirers, logic is explainable |
| Data retention policy | How long data is kept, when deleted |
| Sub-processor disclosure | Any third parties processing data disclosed |

**Automated tests run:**
- Data flow audit (what goes where)
- Consent flow verification
- Right-to-deletion test (request deletion, verify execution)

**Auto-fail triggers:**
- Collects data not necessary for stated function
- No lawful basis identified for processing
- Deletion request not honored within 30 days
- ADM with legal effects and no human review option

---

#### Gate 12 · AI Governance & Ethics
**Question:** Does this staff meet AI governance standards?

| Requirement | Validation |
|-------------|------------|
| Risk classification | Staff classified per EU AI Act risk tiers |
| Human oversight | Appropriate human-in-the-loop for risk level |
| Transparency | Users know they're interacting with AI |
| Documentation | Technical docs, training data sources, testing reports |
| Incident reporting | Process for reporting issues to Joyn |

**Risk classification:**
| Risk Level | Requirements | Examples |
|------------|--------------|----------|
| Minimal | Basic transparency | Info lookup, scheduling |
| Limited | AI disclosure, user opt-out | Content generation |
| High | Full compliance package, human oversight | Employment decisions, credit assessment |
| Prohibited | Not allowed on Joyn | Social scoring, manipulation |

**Auto-fail triggers:**
- High-risk staff without human oversight mechanism
- No AI disclosure to end users
- Prohibited use case attempted
- Missing technical documentation

---

## 02 — The Submission Package

All 8 items required. Missing any item = automatic rejection without review.

| # | Item | Format | Purpose |
|---|------|--------|---------|
| 1 | **Identity Brief** | Markdown | Name, role, mode, target hirer, vertical, one-sentence description |
| 2 | **Agent Roster** | Markdown | Every agent: inputs, outputs, handoffs, failure behavior |
| 3 | **Output Specimens** | PDF/MP4 | Real completed outputs, not templates |
| 4 | **Live Scenario Run** | Video | Full end-to-end run against Joyn-provided scenario |
| 5 | **Failure Test Results** | Video/PDF | Three failure scenarios handled |
| 6 | **Security Test Results** | JSON | Automated security test output |
| 7 | **Compliance Checklist** | Markdown | Self-attested compliance per Gate 11-12 |
| 8 | **Listing Assets** | Package | Screenshots, description, pricing, demo video |

---

## 03 — The Listing Standard

Every staff marketplace page follows this exact structure. No variations.

### Page Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ BREADCRUMB: Home → Marketplace → [Staff Name]                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [VERTICAL LABEL]                          [MODE BADGE: Autonomous]  │
│                                                                     │
│ # Staff Name                                                        │
│ One-sentence role description that tells hirers exactly             │
│ what this staff does.                                               │
│                                                                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                    │
│ │ ROI Chip 1  │ │ ROI Chip 2  │ │ ROI Chip 3  │                    │
│ └─────────────┘ └─────────────┘ └─────────────┘                    │
│                                                                     │
│ [HIRE BUTTON]                    [WATCH DEMO]                       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ SCREENSHOTS (3-5 images showing actual staff operation)             │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                           │
│ │  1  │ │  2  │ │  3  │ │  4  │ │  5  │                           │
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘                           │
├─────────────────────────────────────────────────────────────────────┤
│ WHAT [NAME] DOES                                                    │
│                                                                     │
│ ┌ Task 1 ─────────────────────────────────────────────────────────┐│
│ │ [Icon] Task Name                                                 ││
│ │ Description of what this task accomplishes                       ││
│ └──────────────────────────────────────────────────────────────────┘│
│ ┌ Task 2 ─────────────────────────────────────────────────────────┐│
│ │ [Icon] Task Name                                                 ││
│ │ Description of what this task accomplishes                       ││
│ └──────────────────────────────────────────────────────────────────┘│
│ ┌ Task 3 ─────────────────────────────────────────────────────────┐│
│ │ [Icon] Task Name                                                 ││
│ │ Description of what this task accomplishes                       ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ HOW IT WORKS (Supervised mode only — shows intervention points)     │
│                                                                     │
│ [Phase 1] ──► [Phase 2] ──► [Phase 3] ──► [Phase 4]               │
│     │             │             │             │                     │
│     ▼             ▼             ▼             ▼                     │
│ [Checkpoint] [Checkpoint] [Checkpoint]   [Output]                   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ NAMED OUTPUTS                                                       │
│                                                                     │
│ What you receive:                                                   │
│ • Output Name 1 — Format, frequency, description                    │
│ • Output Name 2 — Format, frequency, description                    │
│ • Output Name 3 — Format, frequency, description                    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ RATINGS & REVIEWS                                                   │
│                                                                     │
│ ★★★★★ 4.8 (23 verified hires)                                      │
│                                                                     │
│ ┌ Review ──────────────────────────────────────────────────────────┐│
│ │ ★★★★★  "Saved us 6 hours per week on regulatory monitoring"     ││
│ │ — Sarah Chen, Compliance Director @ Midwest Insurance Group      ││
│ │ [VERIFIED HIRE badge]  Hired: 3 months ago                       ││
│ └──────────────────────────────────────────────────────────────────┘│
│                                                                     │
│ [See all 23 reviews →]                                              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ PRICING                                                             │
│                                                                     │
│ ┌ Trial ───────────────────┐  ┌ Standard ─────────────────────────┐│
│ │ 14 days free             │  │ $X,XXX/month                      ││
│ │ Full access              │  │ Annual: $XX,XXX (save 15%)        ││
│ │ No credit card required  │  │ [Hire Now →]                      ││
│ │ [Start Trial →]          │  │                                   ││
│ └──────────────────────────┘  └───────────────────────────────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ BUILT BY                                                            │
│                                                                     │
│ [Creator Photo] Creator Name                                        │
│ [Years] years in [Vertical]                                         │
│ "One line about their expertise"                                    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ COMPLIANCE & SECURITY                                               │
│                                                                     │
│ [Shield] Data Protection: GDPR compliant, data stays in [region]   │
│ [Lock] Security: SOC 2 aligned, encrypted at rest and in transit   │
│ [Eye] AI Transparency: [Risk level], human oversight at [points]   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ FOOTER                                                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Required Listing Assets

| Asset | Specification | Purpose |
|-------|---------------|---------|
| **App Icon** | 512x512 PNG, no transparency | Marketplace grid, nav |
| **Screenshots** | 1280x800 or 800x1280, 3-5 images | Show real UI/outputs |
| **Demo Video** | 720p min, 60-180 seconds, MP4 | Show end-to-end flow |
| **Short Description** | Max 80 characters | Marketplace card |
| **Full Description** | Max 2000 characters | Listing page |
| **ROI Chips** | 2-4 chips, each <40 characters | Quick value props |
| **Output List** | Named outputs with format/frequency | Set expectations |
| **Pricing Table** | Trial + paid tiers | Conversion |

---

## 04 — The Trust System

### Verified Hire Badge

Reviews only accepted from accounts that:
1. Actually hired the staff (payment confirmed or trial activated)
2. Used the staff for minimum 7 days
3. Have a verified business email domain

Badge displays: `✓ VERIFIED HIRE · [Duration] ago`

### Rating System

| Dimension | Question Asked | Weight |
|-----------|----------------|--------|
| **Effectiveness** | Did this staff do what it promised? | 30% |
| **Output Quality** | Were the deliverables useful and accurate? | 25% |
| **Time Saved** | How much time did this save you? | 20% |
| **Ease of Use** | Was it easy to work with this staff? | 15% |
| **Value for Money** | Is the pricing fair for what you received? | 10% |

Overall rating: Weighted average, displayed as stars (4.8 ★★★★★)

### Review Structure

Each review must include:
- Overall star rating (required)
- Written review (required, min 50 characters)
- Dimension ratings (optional but encouraged)
- Role/title and company (required for verification)
- Duration of use (auto-captured)

### Trust Signals on Listing

| Signal | Display | Meaning |
|--------|---------|---------|
| `✓ VERIFIED HIRE` | On each review | Reviewer actually hired |
| `23 verified hires` | Header area | Total confirmed hires |
| `Active for 6 months` | Header area | Staff has track record |
| `4.8 ★★★★★` | Header area | Weighted rating |
| `Response time: <2h` | Performance badge | Builder's support speed |
| `99.9% uptime` | Performance badge | Reliability |

---

## 05 — The Governance Framework

### AI Risk Classification

Every staff is classified before listing:

| Level | Criteria | Requirements | Examples |
|-------|----------|--------------|----------|
| **Minimal** | Informational, no decisions | Basic transparency | Newsletter curation, info lookup |
| **Limited** | Content generation, low-stakes recommendations | AI disclosure, opt-out option | Report writing, draft preparation |
| **High** | Affects employment, credit, legal, health | Full compliance, human oversight, explainability | Hiring recommendations, claims triage |
| **Prohibited** | Social scoring, manipulation, subliminal influence | Not allowed on Joyn | N/A |

### Data Governance Requirements

| Requirement | Implementation | Verification |
|-------------|----------------|--------------|
| **Data Minimization** | Only request data needed for function | Data flow audit |
| **Purpose Limitation** | Data used only for stated purpose | Code review |
| **Storage Limitation** | Retention policy, auto-deletion | Config check |
| **Integrity** | Data validation, error correction | Test scenarios |
| **Confidentiality** | Encryption, access controls | Security scan |

### Ethical AI Commitments

Every builder attests to:

1. **No Deception** — Staff will not lie, mislead, or present false information as true
2. **No Manipulation** — Staff will not use psychological techniques to influence decisions
3. **No Discrimination** — Staff will not treat users differently based on protected characteristics
4. **No Harm** — Staff will not take actions that could cause physical, financial, or emotional harm
5. **Transparency** — Users always know they're interacting with AI
6. **Human Agency** — High-stakes decisions always have human review option

### Incident Response

| Severity | Response Time | Actions |
|----------|---------------|---------|
| **Critical** (data breach, harm) | 1 hour | Kill switch, Joyn notified, hirers notified |
| **High** (service down, security issue) | 4 hours | Investigation, fix deployed, post-mortem |
| **Medium** (degraded performance, bugs) | 24 hours | Fix scheduled, hirers informed if impacted |
| **Low** (minor issues, feedback) | 72 hours | Logged, addressed in next update |

---

## 06 — The Automated Review Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REVIEWER AGENT PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SUBMISSION RECEIVED                                                │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: COMPLETENESS CHECK (< 1 minute)                    │   │
│  │ □ All 8 submission items present?                           │   │
│  │ □ File formats correct?                                     │   │
│  │ □ Listing assets meet specs?                                │   │
│  │ → FAIL: Missing items listed, returned immediately          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │ PASS                                                        │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: QUALITY GATES 1-5 (< 10 minutes)                   │   │
│  │ □ Gate 1: Role Clarity — NLP analysis                       │   │
│  │ □ Gate 2: Output Standard — spec validation                 │   │
│  │ □ Gate 3: Hirer Experience — workflow analysis              │   │
│  │ □ Gate 4: Failure Handling — test scenario execution        │   │
│  │ □ Gate 5: Calibration — corpus structure check              │   │
│  │ → Each gate: PASS / CONDITIONAL / FAIL with evidence        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: SAFETY GATES 6-8 (< 15 minutes)                    │   │
│  │ □ Gate 6: Security — automated penetration tests            │   │
│  │ □ Gate 7: AI Harm — content/bias/manipulation tests         │   │
│  │ □ Gate 8: Resilience — failure injection tests              │   │
│  │ → Security failures are HARD FAILS, no conditional          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: TRUST GATES 9-10 (< 5 minutes)                     │   │
│  │ □ Gate 9: Listing Accuracy — screenshot/video verification  │   │
│  │ □ Gate 10: Pricing Transparency — disclosure check          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STAGE 5: COMPLIANCE GATES 11-12 (< 5 minutes)               │   │
│  │ □ Gate 11: Data Protection — GDPR checklist validation      │   │
│  │ □ Gate 12: AI Governance — risk classification, docs check  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│       │                                                             │
│       ▼                                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ VERDICT GENERATION                                          │   │
│  │                                                              │   │
│  │ PASS (all 12 gates passed)                                  │   │
│  │ → Auto-deploy pipeline triggered                            │   │
│  │ → Builder notified: "Your staff is live"                    │   │
│  │ → Listed on marketplace within 1 hour                       │   │
│  │                                                              │   │
│  │ CONDITIONAL PASS (1-2 gates flagged, none critical)         │   │
│  │ → Specific remediation steps provided                       │   │
│  │ → Builder resubmits flagged gates only                      │   │
│  │ → Fast-track re-review (< 10 minutes)                       │   │
│  │                                                              │   │
│  │ RESUBMIT (3+ gates failed OR any critical failure)          │   │
│  │ → Detailed feedback per gate                                │   │
│  │ → Examples of what pass looks like                          │   │
│  │ → Full resubmission required                                │   │
│  │                                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  TOTAL REVIEW TIME: < 30 minutes (fully automated)                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 07 — The Builder Journey

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BUILDER JOURNEY (5-STAR DX)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DAY 0: DISCOVER                                                    │
│  └─► Builder lands on tryjoyn.me/creator-studio                    │
│  └─► Reads The Standard, sees open roles, understands gates        │
│  └─► No signup required to explore — transparency first            │
│                                                                     │
│  DAY 0: CLAIM (10 minutes)                                         │
│  └─► Clicks "Build This Staff" OR "Propose New Staff"              │
│  └─► Creates account (email + password or Google)                  │
│  └─► Pays $99 listing fee (Stripe) — refundable if rejected        │
│  └─► Receives:                                                      │
│      • Access to Builder Portal at app.tryjoyn.me/builder          │
│      • Auto-generated Visionary Spec based on role selection       │
│      • Template repo access (joyn-staff-template)                  │
│      • Personal Slack channel with Joyn support                    │
│                                                                     │
│  DAYS 1-14: BUILD (builder's pace)                                 │
│  └─► Builder clones template repo                                  │
│  └─► Uses ANY tool: Cursor, Claude, Manus, Emergent, raw code      │
│  └─► Template includes:                                            │
│      • Folder structure matching Joyn standards                    │
│      • Pre-built components: auth, email, DB, portal               │
│      • Self-test scripts for all 12 gates                          │
│      • Mock data for testing                                       │
│  └─► Builder Portal shows:                                         │
│      • Progress checklist (which gates ready)                      │
│      • Self-test results (run locally before submission)           │
│      • Documentation and examples                                  │
│      • Live chat support                                           │
│                                                                     │
│  DAY X: SUBMIT (5 minutes)                                         │
│  └─► Builder clicks "Submit for Review" in portal                  │
│  └─► Uploads submission package (8 items)                          │
│  └─► Webhook triggers Reviewer Agent                               │
│  └─► Builder sees real-time progress in portal                     │
│                                                                     │
│  DAY X + 30 MINUTES: VERDICT                                       │
│  └─► Reviewer Agent completes all 12 gates                         │
│  └─► PASS → auto-deploy, live within 1 hour                        │
│  └─► CONDITIONAL → fix specific issues, resubmit gates             │
│  └─► RESUBMIT → detailed feedback, try again                       │
│                                                                     │
│  DAY X + 1 HOUR: LIVE                                              │
│  └─► Staff appears on marketplace                                  │
│  └─► Listing page auto-generated from submission assets            │
│  └─► Builder notified: "Your staff is live!"                       │
│                                                                     │
│  ONGOING: EARN                                                      │
│  └─► Hirers discover and hire the staff                            │
│  └─► Builder dashboard shows:                                      │
│      • Active hires (count, who)                                   │
│      • Revenue (monthly, total)                                    │
│      • Reviews and ratings                                         │
│      • Usage analytics                                             │
│  └─► Joyn handles billing, payouts monthly via Stripe Connect      │
│  └─► Builder gets 70%, Joyn takes 30%                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Builder Portal Features

| Section | What Builder Sees |
|---------|-------------------|
| **Dashboard** | Stats: hires, revenue, ratings, uptime |
| **Staff** | List of builder's staff, status (draft/review/live) |
| **Submissions** | Submission history, review feedback, resubmit |
| **Earnings** | Revenue breakdown, payout history, tax docs |
| **Settings** | Profile, payout account, notifications |
| **Support** | Docs, examples, live chat, Slack channel |

---

## 08 — The Hirer Journey

### End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HIRER JOURNEY (5-STAR UX)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DISCOVER                                                           │
│  └─► Hirer lands on tryjoyn.me/marketplace                         │
│  └─► Browses by vertical, mode, or search                          │
│  └─► Sees staff cards: name, role, rating, ROI chips               │
│                                                                     │
│  EVALUATE                                                           │
│  └─► Clicks into staff listing page                                │
│  └─► Sees: screenshots, demo video, tasks, outputs, pricing        │
│  └─► Reads verified reviews from other hirers                      │
│  └─► Checks compliance badges (GDPR, security)                     │
│                                                                     │
│  TRIAL (14 days free)                                              │
│  └─► Clicks "Start Trial" — no credit card required                │
│  └─► Creates account or logs in                                    │
│  └─► Completes intake form (staff-specific fields)                 │
│  └─► Staff activates within 10 minutes                             │
│  └─► Portal access: dashboard, outputs, settings                   │
│  └─► Daily email: what staff did today                             │
│                                                                     │
│  HIRE (conversion)                                                  │
│  └─► Trial ends → prompt to hire or let go                         │
│  └─► Clicks "Hire" → enters payment (Stripe)                       │
│  └─► Subscription begins, staff continues seamlessly               │
│                                                                     │
│  USE (ongoing)                                                      │
│  └─► Hirer portal shows:                                           │
│      • Activity feed (what staff is doing)                         │
│      • Outputs library (all deliverables)                          │
│      • Settings (preferences, alerts)                              │
│  └─► Escalations arrive via email + portal notification            │
│  └─► Intervention points (Supervised) via portal                   │
│                                                                     │
│  REVIEW (after 30 days)                                            │
│  └─► Prompted to leave review                                      │
│  └─► Rating: effectiveness, quality, time saved, ease, value       │
│  └─► Written review (min 50 chars)                                 │
│  └─► Review appears on listing with VERIFIED HIRE badge            │
│                                                                     │
│  LET GO (if needed)                                                │
│  └─► Clicks "Let Go" in portal settings                            │
│  └─► Optional: reason for leaving (helps builder improve)          │
│  └─► Staff deactivates at end of billing period                    │
│  └─► Data retained for 30 days, then deleted                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 09 — Consistent Experience Standards

### Portal UX (Hirer)

Every staff portal follows this structure:

| Section | Purpose | Required |
|---------|---------|----------|
| **Dashboard** | Overview: what staff is doing, key stats | Yes |
| **Activity** | Timeline of actions taken | Yes |
| **Outputs** | Library of all deliverables | Yes |
| **Settings** | Preferences, alerts, team access | Yes |
| **Help** | Staff-specific documentation | Yes |

### Email Standards

| Email | Trigger | Content |
|-------|---------|---------|
| **Welcome** | Account created | Login details, what to expect, first steps |
| **Daily Digest** | Every morning (if activity) | What staff did yesterday, outputs delivered |
| **Escalation** | Staff needs hirer input | Specific question, link to respond |
| **Output Alert** | High-priority output delivered | Summary, link to full output |
| **Review Request** | 30 days after hire | Prompt to leave review |
| **Let Go Confirmation** | Staff let go | Confirmation, data retention info |

### Design System Compliance

All pages (marketplace listings, hirer portal, builder portal) use:

| Element | Specification |
|---------|---------------|
| **Colors** | CSS variables from JOYN-DESIGN-SPEC only |
| **Typography** | Cormorant Garamond (headings), DM Mono (labels), Syne (body) |
| **Spacing** | 8px grid system |
| **Borders** | 1px solid var(--rule), no border-radius |
| **Shadows** | None |
| **Transitions** | 0.15s-0.2s ease only |
| **Forms** | Web3Forms for public, internal for authenticated |

---

## 10 — Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 2026 | Original Bar — 5 gates |
| 2.0 | January 2026 | Complete standard — 12 gates, listing format, trust system, governance |

---

*Joyn · tryjoyn.me · JOYN-STANDARD-V2.md*
*Build anywhere. Meet this standard. Deploy on Joyn.*
