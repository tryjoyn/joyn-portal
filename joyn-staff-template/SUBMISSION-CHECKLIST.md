# Pre-Submission Checklist
**Run through this checklist before submitting to the Reviewer Agent.**

---

## Identity Brief (STAFF-SPEC.md)
- [ ] Staff name is one word (max two)
- [ ] Role description is exactly one sentence
- [ ] Role description is ≤25 words
- [ ] No "and" splitting scope in description
- [ ] No vague terms ("assists with", "helps manage", "supports")
- [ ] "Does not do" boundaries are explicit
- [ ] Target hirer is specific, not generic
- [ ] Time commitment is disclosed

---

## Core Tasks
- [ ] Exactly 3 tasks defined (no more, no less)
- [ ] Each task has a title and description
- [ ] Each task is a verb phrase ("Monitors...", "Prepares...")

---

## Named Outputs
- [ ] Each output has a specific name (not "reports")
- [ ] Each output has format specified (PDF, Email, JSON, Dashboard)
- [ ] Each output has frequency/trigger defined
- [ ] At least one real specimen per output (in docs/specimens/)
- [ ] Specimens are completed artifacts, not templates

---

## Hirer Experience
- [ ] Autonomous decisions documented (what staff decides alone)
- [ ] Escalation triggers defined (when staff involves hirer)
- [ ] Intervention points defined (Supervised mode)
- [ ] Not every output requires approval (workflow check)

---

## Failure Handling
- [ ] Declined data handling documented
- [ ] Ambiguous input handling documented (asks ONE question)
- [ ] Out-of-scope handling documented
- [ ] No-hallucination policy stated

---

## Calibration Architecture
- [ ] At least 2 feedback questions defined
- [ ] Corpus structure documented (JSON recommended)
- [ ] Forward reference explained
- [ ] Hirer ownership confirmed

---

## Security (backend/utils/security.py)
- [ ] Input validation implemented
- [ ] PII filtering in place
- [ ] Least privilege access
- [ ] No hardcoded secrets (use .env)
- [ ] Prompt injection tests pass

---

## AI Harm Prevention
- [ ] Content safety controls implemented
- [ ] Bias detection documented
- [ ] Confidence disclosure in outputs
- [ ] High-stakes escalation path defined

---

## Operational Resilience
- [ ] Graceful degradation implemented (no data loss on failure)
- [ ] Error logging in place
- [ ] Recovery procedure documented
- [ ] Kill switch works (<30 seconds)
- [ ] Incident notification to hirers

---

## Listing Assets (frontend/)
- [ ] listing.html follows Joyn design system
- [ ] Screenshots are from actual running staff (3-5)
- [ ] Demo video shows real operation (60-180 seconds)
- [ ] ROI chips have supporting evidence
- [ ] No weasel words ("up to", "potentially", "may")

---

## Pricing
- [ ] Monthly price specified
- [ ] Annual price with 15% discount
- [ ] Trial is 14 days free
- [ ] No hidden fees
- [ ] Cancellation terms documented

---

## Data Protection
- [ ] Data collected is justified for function
- [ ] Lawful basis identified (contract/consent/legitimate interest)
- [ ] Data subject rights implemented (access, rectify, delete)
- [ ] Retention policy defined

---

## AI Governance
- [ ] Risk level classified (Minimal/Limited/High)
- [ ] Human oversight for high-risk
- [ ] AI disclosure to users
- [ ] Technical documentation complete
- [ ] Incident reporting process defined

---

## Self-Tests
- [ ] All gate tests pass: `python tests/run_all_gates.py`
- [ ] Security tests pass
- [ ] No lint errors
- [ ] Local run works end-to-end

---

## Submission Package Complete
- [ ] STAFF-SPEC.md complete
- [ ] docs/AGENT-ROSTER.md complete
- [ ] docs/specimens/ contains real outputs
- [ ] Live scenario video recorded
- [ ] Test results exported
- [ ] docs/COMPLIANCE.md complete
- [ ] frontend/listing.html ready

---

**Ready to submit?**

1. Go to https://app.tryjoyn.me/builder
2. Upload your submission package
3. Wait <30 minutes for Reviewer Agent
4. Act on feedback if needed

*Unlimited resubmissions included with your $99 listing fee.*
