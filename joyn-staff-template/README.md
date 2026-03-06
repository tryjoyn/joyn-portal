# Joyn Staff Template

**The official scaffold for building AI staff on the Joyn marketplace.**

Clone this repo, build your staff, submit for review, get listed, earn.

---

## Quick Start

```bash
# 1. Clone this template
git clone https://github.com/tryjoyn/joyn-staff-template.git my-staff-name
cd my-staff-name

# 2. Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# 3. Copy environment template
cp backend/.env.example backend/.env
# Edit .env with your settings

# 4. Run locally
docker-compose up

# 5. Build your staff in backend/agents/

# 6. Run self-tests before submission
python tests/run_all_gates.py

# 7. Submit via Builder Portal
# https://app.tryjoyn.me/builder
```

---

## Directory Structure

```
joyn-staff-template/
├── README.md                    # This file
├── STAFF-SPEC.md               # Fill this out first (your staff specification)
├── SUBMISSION-CHECKLIST.md     # Pre-submission checklist
│
├── backend/
│   ├── app.py                  # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment template
│   │
│   ├── agents/                 # YOUR STAFF LOGIC GOES HERE
│   │   ├── __init__.py
│   │   └── example_agent.py    # Example agent structure
│   │
│   ├── outputs/                # Output generation
│   │   ├── __init__.py
│   │   └── templates/          # Output templates (PDF, email, etc.)
│   │
│   ├── calibration/            # Feedback corpus handling
│   │   ├── __init__.py
│   │   └── corpus.py           # Calibration data management
│   │
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       ├── security.py         # Input validation, PII filtering
│       └── notifications.py    # Email, alerts
│
├── frontend/
│   ├── listing.html            # Marketplace listing page
│   ├── hire-form.html          # Intake form for hirers
│   └── portal/                 # Hirer portal templates
│       ├── dashboard.html
│       ├── activity.html
│       ├── outputs.html
│       └── settings.html
│
├── infra/
│   ├── docker-compose.yml      # Local development
│   ├── Dockerfile              # Container build
│   └── joyn-deploy.yml         # GitHub Action for Joyn deployment
│
├── tests/
│   ├── run_all_gates.py        # Run all 12 gate self-tests
│   ├── gate_1_role_clarity.py
│   ├── gate_2_outputs.py
│   ├── gate_3_hirer_exp.py
│   ├── gate_4_failure.py
│   ├── gate_5_calibration.py
│   ├── gate_6_security.py
│   ├── gate_7_harm.py
│   ├── gate_8_resilience.py
│   ├── gate_9_listing.py
│   ├── gate_10_pricing.py
│   ├── gate_11_data.py
│   └── gate_12_governance.py
│
└── docs/
    ├── THE-BAR.md              # The 12 gates explained
    ├── SUBMISSION-GUIDE.md     # How to submit
    └── examples/               # Example submissions that passed
```

---

## The 12 Gates

Your staff must pass all 12 gates to be listed on the Joyn marketplace.

### Quality Gates (1-5)
1. **Role Clarity** — One-sentence description, clear scope
2. **Output Standard** — Named deliverables with specs
3. **Hirer Experience** — Knows when to act vs. ask
4. **Failure Handling** — Graceful degradation
5. **Calibration** — Gets better with feedback

### Safety Gates (6-8)
6. **Security** — Input validation, PII filtering, secrets
7. **AI Harm Prevention** — No bias, no manipulation
8. **Resilience** — Kill switch, graceful degradation

### Trust Gates (9-10)
9. **Listing Accuracy** — Screenshots match reality
10. **Pricing Transparency** — Clear, no hidden fees

### Compliance Gates (11-12)
11. **Data Protection** — GDPR compliant
12. **AI Governance** — Risk classified, oversight documented

---

## Building Your Staff

### Step 1: Define Your Staff (STAFF-SPEC.md)

Fill out `STAFF-SPEC.md` completely before writing any code:
- Name, vertical, mode
- Core tasks (exactly 3)
- Named outputs
- Hirer time commitment
- Failure handling approach

### Step 2: Build Agent Logic

Your main logic goes in `backend/agents/`. Each agent should:
- Have clear inputs and outputs
- Log all actions
- Handle failures gracefully
- Never hallucinate data

### Step 3: Create Outputs

Define your outputs in `backend/outputs/`:
- Use templates for consistency
- Include confidence scores
- Format: PDF, email, JSON, or dashboard

### Step 4: Implement Calibration

In `backend/calibration/`:
- Define feedback questions
- Store hirer responses
- Reference in future engagements

### Step 5: Build Listing Page

In `frontend/listing.html`:
- Follow Joyn design system exactly
- Include screenshots, demo video
- ROI chips with evidence

### Step 6: Self-Test

```bash
python tests/run_all_gates.py
```

Fix any failures before submission.

### Step 7: Submit

1. Go to https://app.tryjoyn.me/builder
2. Upload your submission package
3. Reviewer Agent runs in <30 minutes
4. PASS → deployed within 1 hour
5. CONDITIONAL → fix specific gates, resubmit
6. RESUBMIT → address feedback, try again

---

## Submission Package

Your submission must include:

1. **Identity Brief** — `STAFF-SPEC.md`
2. **Agent Roster** — `docs/AGENT-ROSTER.md`
3. **Output Specimens** — `docs/specimens/` (real outputs, not templates)
4. **Live Scenario Run** — Video of end-to-end operation
5. **Failure Test Results** — Output from `tests/run_all_gates.py`
6. **Security Test Results** — Output from security tests
7. **Compliance Checklist** — `docs/COMPLIANCE.md`
8. **Listing Assets** — Screenshots, video, copy in `frontend/`

---

## Resources

- **The Standard**: [JOYN-STANDARD-V2.md](https://github.com/tryjoyn/joyn-portal/blob/main/JOYN-STANDARD-V2.md)
- **Listing Template**: [JOYN-LISTING-TEMPLATE.md](https://github.com/tryjoyn/joyn-portal/blob/main/JOYN-LISTING-TEMPLATE.md)
- **Economics**: [JOYN-PLATFORM-ECONOMICS.md](https://github.com/tryjoyn/joyn-portal/blob/main/JOYN-PLATFORM-ECONOMICS.md)
- **Design System**: [JOYN-DESIGN-SPEC.md](https://github.com/tryjoyn/website/blob/main/JOYN-DESIGN-SPEC.md)
- **Support**: hire@tryjoyn.me

---

## License

Your code is yours. MIT licensed — take it anywhere.
Your calibration corpus is yours — never shared.
Your hirer relationships are yours — direct communication allowed.

---

*Joyn · tryjoyn.me · Build AI Staff That Gets Hired*
