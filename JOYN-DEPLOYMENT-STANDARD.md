# JOYN-DEPLOYMENT-STANDARD.md — The Bar
**AI Staff Deployment Standard · Version 1.0 · March 2026**
**This file is machine-readable source of truth. The formatted creator-facing version lives at `/docs/the-bar-v1.docx` and is linked from `marketplace/creator-studio.html`.**

---

## What This File Is

The Bar defines the standard every piece of AI staff must meet before it is deployed on the Joyn marketplace. It applies to all submissions regardless of vertical, mode, or build tool used.

Joyn does not prescribe how you build. We prescribe what the output must do, how reliably it must do it, and how it must behave in the hands of a hirer. Build with any tool you choose. Meet these standards or your staff does not deploy.

**There are five gates. Every gate must be passed. There is no partial credit.**

---

## 00 — What Joyn Is Evaluating

Three things only:

1. Does the staff do what it says it does — reliably, repeatedly, without supervision?
2. Does a hirer know exactly what they are getting before they hire, and does the staff deliver exactly that?
3. Does the staff handle the real world — declined data, ambiguous inputs, unexpected scope changes — without failing silently?

---

## 01 — The Five Gates

### Gate 01 · Role Clarity

The staff must do exactly one thing. That thing must be expressible in a single sentence that a hirer understands without explanation. If you need more than one sentence to describe what it does, it is not ready.

**Autonomous requirement:** A hirer reading the marketplace listing can state — without help — exactly what this staff will do for them and what it will not do.

**Supervised requirement:** Same as Autonomous, plus: the practitioner role in the engagement is explicitly defined. The staff must make clear where it acts and where it defers to the practitioner.

**Fail looks like:** The listing says the staff handles "insurance operations." That is not a role. That is a category.

---

### Gate 02 · Output Standard

Every deliverable the staff produces must be named, specified, and reproducible. A hirer must be able to read the listing and know exactly what they will receive — format, structure, frequency, and fidelity.

**Autonomous requirement:** Each output is named. Its format is specified. Its trigger condition is defined. Running the staff twice against the same input produces outputs of equivalent structure and quality.

**Supervised requirement:** Same as Autonomous, plus: each practitioner intervention point is named and its output is specified. The staff cannot produce a final deliverable without a defined practitioner sign-off step.

**Fail looks like:** The submission describes outputs as "reports and recommendations." Not acceptable. Name the report. Specify what it contains. Define when it is produced.

---

### Gate 03 · Hirer Experience

The staff must know the difference between a decision it can make autonomously and a decision that belongs to the hirer. It must surface the right decisions at the right time — not everything, not nothing.

**Autonomous requirement:** The staff operates without hirer input after initial setup. It escalates only when a KPI breach, data anomaly, or out-of-scope condition occurs. Escalations are specific — they name the issue and ask a single question.

**Supervised requirement:** Defined intervention points are built into the workflow. The staff does not proceed past an intervention point without hirer input. Between intervention points, it operates autonomously.

**Fail looks like:** The staff asks the hirer to review every output before proceeding. That is not Supervised mode — that is a broken workflow.

---

### Gate 04 · Failure Handling

The staff will encounter declined data, ambiguous instructions, missing inputs, and scope changes. It must handle all of these gracefully — logging what it received, what it did not receive, and how that affects the output. It must never hallucinate missing information.

**Autonomous requirement:** When data is declined: log the gap, note the confidence impact, proceed with what is available. When input is ambiguous: ask one clarifying question, not several. When a condition is out of scope: escalate with a specific description of what is out of scope and why.

**Supervised requirement:** Same as Autonomous, plus: the practitioner is the escalation path for failure conditions. The staff must route failure conditions to the practitioner, not attempt to resolve them autonomously.

**Fail looks like:** A hirer declines to share internal data. The staff proceeds as if the data was provided and produces outputs with false confidence. This is a hard failure.

---

### Gate 05 · Calibration Architecture

The staff must have a defined mechanism for learning from hirer feedback. Every engagement must leave the staff better calibrated than it was before. This calibration must be structured, not incidental.

**Autonomous requirement:** A calibration corpus exists. After each engagement, the staff asks a defined set of closing questions. Responses are recorded in a structured format. The corpus is referenced at the start of each subsequent engagement.

**Supervised requirement:** Same as Autonomous, plus: the practitioner's calibration inputs are weighted above hirer inputs in cases of conflict. The practitioner owns the methodology. The corpus reflects that.

**Fail looks like:** The submission has no feedback mechanism. Hirer context from one engagement is not carried forward to the next. Every engagement starts from zero.

---

## 02 — What a Submission Contains

All six items required. A submission missing any item is returned without review.

| Item | What to include | Format |
|------|----------------|--------|
| **Identity Brief** | Name, role definition, mode, target hirer profile, vertical. One sentence on what the staff does and who hires it. | PDF or MD |
| **Agent Roster** | Every agent listed. For each: what it consumes, what it produces, handoff conditions, failure behaviour. | PDF or MD |
| **Output Specimens** | At least one real example of each named output. Not a template — a completed artifact from a test run. | PDF, DOCX, or MP4 |
| **Live Scenario Run** | A full end-to-end run against a real scenario provided by Joyn at submission. Unedited. Includes all hirer touchpoints. | Screen recording |
| **Failure Test** | Three failure scenarios: declined data, ambiguous input, mid-experiment scope change. Show how the staff handles each. | PDF or screen recording |
| **Calibration Log** | Evidence that the staff records hirer feedback and carries it forward. Show the corpus structure. | PDF or MD |

The live scenario run uses a scenario provided by Joyn at the time of submission — not one the creator selects. This evaluates performance against an unfamiliar brief, not a rehearsed one.

---

## 03 — The Verdict

Delivered to the creator immediately. Joyn notified in parallel. Returned within 48 hours.

| Verdict | Meaning |
|---------|---------|
| **Pass** | All five gates passed. Staff deployed to marketplace within 48 hours. |
| **Conditional Pass** | One or two gates flagged. Specific remediation steps provided. Resubmit those gates only — not the full submission. |
| **Resubmit** | Three or more gates failed. Full resubmission required. Detailed feedback provided per gate with examples of what pass looks like. |

Resubmissions are unlimited. The Reviewer Agent handles all rounds. Creator may escalate to Joyn human review — include the specific gate being contested and the rationale.

---

## 04 — After Deployment

Passing The Bar is not permanent. Deployed staff is subject to ongoing monitoring. Joyn may trigger a re-evaluation if:

- A hirer files a formal complaint mapped to a specific gate
- The staff's output quality degrades materially across three or more consecutive engagements
- A material change is made to the staff's behaviour, outputs, or agent roster after deployment

A re-evaluation follows the same process as an initial submission. Staff that fails re-evaluation is suspended from the marketplace pending remediation.

The calibration corpus is the creator's property. Joyn does not access, use, or share it.

---

## 05 — Reference Implementation: Probe

Probe — the Insurance Innovation Experimentation Team — is the first AI staff evaluated against this standard. Every gate definition above was tested against Probe's design before this document was published.

| Gate | Probe's implementation |
|------|----------------------|
| **01 · Role Clarity** | Probe runs structured insurance innovation experiments. One sentence. Unambiguous. |
| **02 · Output Standard** | Six named outputs: Executive Summary, Detailed Report, Demonstration Package, Demo Video, Weekly Status Reports, Calibration Corpus. Each specified in the Debrief Output Spec. |
| **03 · Hirer Experience** | Three mandatory intervention points. Total hirer time under 2.5 hours across a full experiment lifecycle. |
| **04 · Failure Handling** | Declined data logged with confidence impact noted. Proceeds with available inputs. Gap recorded in Detailed Report. |
| **05 · Calibration Architecture** | Four closing questions post-Debrief. Corpus structured by experiment. Carries architectural preferences, demographic context, and methodology notes forward. |

**When in doubt about what pass looks like at any gate, reference Probe.**

---

## 06 — Reviewer Agent

The Reviewer Agent is Joyn internal infrastructure. It receives every submission, evaluates it against this standard gate by gate, and returns a structured verdict. It is not a product for hire — it is the platform's quality gate.

The Reviewer Agent's evaluation rubric is this document. Any update to this standard requires a corresponding update to the Reviewer Agent's prompt and evaluation logic.

**Reviewer Agent behaviour rules:**
- Evaluates each gate independently — no aggregate scoring
- Returns verdict per gate with specific evidence from the submission
- On Conditional Pass: names the exact remediation required, not general guidance
- On Resubmit: maps each failed gate to a specific example of what pass looks like
- Never returns a verdict without citing evidence from the submission
- Routes escalations to hire@tryjoyn.me with full evaluation log attached

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | March 2026 | Initial standard — five gates, Probe as reference implementation |

---

*Joyn · tryjoyn.me · The Bar · AI Staff Deployment Standard · v1.0*
*Build anywhere. Meet this standard. Deploy on Joyn.*
