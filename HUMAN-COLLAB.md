# HUMAN-COLLAB.md — Human Collaboration Operating Manual
**Version 1.0 · March 2026**
**This document defines how humans and Joyn AI staff work together.**
**Referenced by: CLAUDE.md, AGENT-RULES.md**
**Operates within the boundaries set by: ETHICS.md**

---

## 00 — Purpose

This document answers one question with precision: **what does human-AI collaboration actually mean inside Joyn, and how is it designed, built, and enforced?**

It is not a philosophy document — ETHICS.md is. This is the operating manual. It defines the mechanics of how hirers interact with AI staff, how they modify outputs, how their judgment is preserved, and how trust is built over time through the system's architecture — not through marketing copy.

Every listing page, every portal feature, and every staff behaviour involving a human touchpoint is designed against this document.

---

## 01 — The Collaboration Hierarchy

When human judgment and AI output are in tension, the resolution is always the same:

```
Hirer judgment
    └── overrides
Practitioner recommendation (Supervised)
    └── overrides
AI staff output
    └── informs
Calibration corpus
```

This hierarchy is not situational. It does not depend on how confident the AI is. It does not depend on how many times the AI has been right before. **Human judgment is always at the top.**

The AI's job is to make human judgment faster, better-informed, and less manually intensive — not to replace it.

---

## 02 — Hirer Rights (Non-Negotiable)

Every hirer, on every piece of Joyn staff, has the following rights by design. These are not features. They are defaults.

### Right 01 · The Right to Modify Any Output
A hirer may annotate, partially accept, reject, or override any output produced by AI staff. The modification is recorded. The original AI output is preserved alongside the modification. The hirer's version is what moves forward in any downstream workflow.

**How this is built:**
- Every output in the portal has an inline edit or annotation affordance
- Modifications are timestamped and attributed to the hirer
- Original AI output is stored in audit log — never overwritten
- Where a modification contradicts the AI's recommendation, the calibration corpus records the delta as a signal for future calibration

### Right 02 · The Right to Know Why
Every output must be explainable on demand. The hirer does not need to request an explanation — a summary reason must accompany every flagged item, scored document, or recommendation. Full reasoning must be available on request.

**How this is built:**
- Iris: every severity-scored document includes a one-sentence rationale inline
- TDD: every flagged risk in a report includes the evidence it is based on
- Any staff operating in Autonomous mode: the audit log is always accessible to the hirer via the portal
- "Because the model said so" is never an acceptable explanation

### Right 03 · The Right to Pause
A hirer may pause any Autonomous staff member at any time without consequence. Pausing stops all active processing. Outputs already produced are preserved. The audit log is frozen at the point of pause. Resuming restores exactly the state at pause.

**How this is built:**
- Pause/resume toggle is a primary control on every Autonomous staff dashboard — not buried in settings
- Pause state is logged with timestamp
- No data is processed, sent, or acted on while paused
- Resume does not retroactively process items that arrived during the pause — it picks up from the current state

### Right 04 · The Right to a Complete Audit Trail
Every action taken by AI staff — inputs received, processing steps, outputs produced, escalations triggered — is logged and accessible to the hirer. The hirer owns this log. It is exportable at any time.

**How this is built:**
- Audit log is a first-class feature in the hirer portal, not an afterthought
- Log entries include: timestamp, agent acting, input summary, output summary, confidence tier, any escalation triggered
- Hirer can export full log as CSV or JSON at any time
- Log is retained for the full duration of the hire plus 12 months after letting the staff go

### Right 05 · The Right to a Clean Exit
When a hirer lets a staff member go, they receive their full calibration corpus and audit log within 24 hours. All their data is deleted from Joyn systems within 30 days. No data is retained for platform training without explicit written consent.

---

## 03 — Intervention Point Design Standards

An intervention point is a moment in a workflow where the AI staff stops and a human makes a decision before the workflow continues. This section defines how they must be designed.

### What makes a good intervention point

| Criterion | Standard |
|-----------|----------|
| **Named** | Every intervention point has a name — not "checkpoint" but "Experiment Kick-off Approval" |
| **Specific** | The hirer knows exactly what they are being asked to review and what decision they are making |
| **Bounded** | The hirer is given enough context to decide — not everything, not a firehose |
| **Consequential** | The staff cannot proceed without the hirer's input — this is a hard stop, not a soft nudge |
| **Time-bounded** | A maximum response window is defined. If exceeded, an escalation triggers (see ETHICS.md §04) |
| **Low friction** | The cognitive load of the decision is minimised — the staff pre-digests the complexity |

### What makes a bad intervention point

- A checkpoint that asks the hirer to review everything and approve nothing specific
- An intervention that could have been handled autonomously within trained scope
- A checkpoint that fires so frequently it becomes noise and gets ignored
- A checkpoint with no consequence for non-response (staff proceeds anyway)

### Intervention point template (for any new staff design)

```
INTERVENTION POINT SPEC
─────────────────────────────────────────────────────────
Name: [e.g. Experiment Kick-off Approval]
Trigger: [What condition causes this intervention point to fire]
What the hirer sees: [Exactly what is presented for review]
What decision they make: [The specific yes/no or directional input required]
Time window: [Maximum hours before escalation triggers]
Escalation if no response: [What happens — staff pauses / Joyn notified / both]
What happens if approved: [Next step in workflow]
What happens if rejected: [Staff behaviour on rejection — revise / escalate / stop]
─────────────────────────────────────────────────────────
```

---

## 04 — Output Modification Mechanics

This section defines exactly how hirer modifications to AI outputs work, and how those modifications are fed back into the calibration system.

### The four modification types

| Type | What it means | How it is recorded |
|------|--------------|-------------------|
| **Accept** | Hirer accepts output as-is and acts on it | Logged as accepted. Positive calibration signal. |
| **Annotate** | Hirer accepts output but adds context or nuance | Original preserved. Annotation stored alongside. Calibration records the annotation topic. |
| **Partial accept** | Hirer accepts some of the output but rejects specific elements | Accepted and rejected elements both logged. Rejection reason captured if provided. |
| **Reject** | Hirer rejects the output entirely | Original preserved in audit log. Rejection reason captured. Strong calibration signal. |

### Rejection reason capture

When a hirer rejects or partially rejects an output, the portal prompts for a reason. This is optional but strongly encouraged. Reason categories:

- Factually incorrect
- Outside my context (the AI didn't have information I have)
- Wrong scope
- Right finding, wrong recommendation
- I disagree with the reasoning
- Other (free text)

Rejection reasons flow directly into the calibration corpus as structured signals — not free text for a human to read later, but tagged data that affects how the staff calibrates for this hirer.

### The calibration loop

```
AI output produced
    └── Hirer reviews
        ├── Accept → positive signal logged
        ├── Annotate → annotation topic logged
        ├── Partial accept → rejection elements and reason logged
        └── Reject → full rejection reason logged
            └── All signals feed calibration corpus
                └── Next engagement: staff references corpus
                    └── Calibration improves specificity for this hirer
```

This loop is how trust compounds over time. A staff member that has been working with a hirer for 6 months should be materially better calibrated than on day one. If it is not, the calibration architecture has failed.

---

## 05 — Trust Architecture by Mode

### Autonomous Mode — Trust Through Transparency

In Autonomous mode, the hirer is not in the loop between outputs. Trust is built through:

1. **Explainability** — every output carries a reason, not just a result
2. **Confidence signals** — every output carries a confidence tier (see ETHICS.md §03)
3. **Audit trail** — everything the staff did is visible and exportable
4. **Modification rights** — the hirer can always correct the record
5. **Pause control** — the hirer can stop the staff at any time with zero friction

The Autonomous trust model is: *you don't have to watch it, but you can always see what it did and correct it.*

### Supervised Mode — Trust Through Partnership

In Supervised mode, the practitioner is an active participant. Trust is built through:

1. **Named intervention points** — the practitioner always knows where they will be asked to engage
2. **Practitioner primacy** — the staff's recommendation is always framed as a recommendation, not a decision
3. **Deference by design** — at every intervention point, the default state is "awaiting practitioner input," never "proceeding unless objected to"
4. **Practitioner-weighted calibration** — the practitioner's corrections carry more weight in the corpus than hirer acceptance
5. **Disagreement logging** — when the staff's recommendation and the practitioner's decision diverge, the divergence is logged with both the AI's reasoning and the practitioner's decision

The Supervised trust model is: *the staff does the analytical work, the practitioner makes the calls.*

---

## 06 — Preventing Costly Mistakes — Design Patterns

These are required design patterns for any Joyn staff. They exist to prevent the most common and costly failure modes.

### Pattern 01 · The Pre-Action Confirmation Gate
Before any output or action that has material consequence, the staff produces a summary of what it is about to do and asks for confirmation. This is not an intervention point — it is a lightweight gate for significant autonomous actions.

**Example:** Iris is about to send a severity-high alert email to a hirer. Before sending, the portal shows the hirer: "Iris is about to send you a Severity High alert for Florida OIR Bulletin 2026-14. Review before sending?" This is overridable — the hirer can set "always send without preview" for a given severity level.

### Pattern 02 · The Irreversibility Flag
Any output or action that cannot be undone is flagged as irreversible before it executes. The hirer must explicitly confirm irreversible actions.

**Example:** Submitting a regulatory filing, sending an external communication, or deleting a document from the hirer's record. These cannot be undone. The staff surfaces this explicitly: "This action cannot be undone. Confirm?"

### Pattern 03 · The Scope Boundary Alert
When a hirer's input or instruction approaches or crosses the boundary of what the staff is designed to handle, the staff flags the boundary before proceeding. It does not attempt to handle out-of-scope requests by guessing.

**Example:** Iris is asked to monitor a state it doesn't currently cover. Iris responds: "This state is not currently in my monitoring scope. I can alert you when it is added. Would you like me to notify you?"

### Pattern 04 · The Disagreement Prompt
In Supervised mode, when the staff's analysis suggests a different direction than the practitioner's stated preference, the staff may express its view once — clearly, specifically, with evidence. It then defers. It does not persist, re-argue, or route around the practitioner.

**Example:** "Based on the technical architecture review, I flagged the API rate-limiting design as a significant risk. You've noted this as acceptable. I've logged your decision and will proceed with the engagement as directed."

### Pattern 05 · The Confidence-Before-Volume Gate
Staff must not produce high volumes of output at low confidence. If confidence drops below the Medium tier across a significant portion of an output set, the staff pauses and escalates rather than delivering a large volume of low-confidence outputs that the hirer will have to manually verify.

**Example:** Iris monitoring 24 states encounters a data feed disruption affecting 15 states. Rather than producing 15 low-confidence severity assessments, Iris pauses those assessments, flags the disruption, and alerts the hirer that monitoring is degraded.

---

## 10 — The Information Architecture (DIKW)

Every piece of Joyn staff operates at a defined layer of the DIKW pyramid — Data, Information, Knowledge, or Wisdom. This is not a theoretical model. It is a design constraint. Understanding which layer a staff member operates at determines what it is allowed to do autonomously, where it must escalate, and what the human's role is in the workflow.

### The pyramid mapped to Joyn

```
        ┌─────────────────────────────┐
        │          WISDOM             │  ← The human. Always.
        │  Judgment in novel context  │
        │  Ethical authority          │
        │  Irreversible decisions      │
        └────────────┬────────────────┘
                     │ human brings
        ┌────────────▼────────────────┐
        │         KNOWLEDGE           │  ← Calibration corpus.
        │  Patterns from experience   │     Practitioner-weighted signals.
        │  Hirer-specific calibration │     Built over time, owned by hirer.
        └────────────┬────────────────┘
                     │ AI builds toward
        ┌────────────▼────────────────┐
        │        INFORMATION          │  ← AI staff primary output layer.
        │  Data with context applied  │     Severity scores. Flagged risks.
        │  Scored, ranked, explained  │     Briefings. Recommendations.
        └────────────┬────────────────┘
                     │ AI processes from
        ┌────────────▼────────────────┐
        │           DATA              │  ← Raw inputs.
        │  Regulatory documents       │     Financial filings. Lead records.
        │  Monitoring feeds           │     Unstructured source material.
        └─────────────────────────────┘
```

### The design rule

**AI staff on Joyn operates at the Data and Information layers. It builds toward Knowledge through the calibration corpus. It never reaches Wisdom — that layer belongs to the human by design.**

This is not a capability limitation. It is an architectural commitment that flows directly from the synergy vision in ETHICS.md §00. The point is not that AI cannot approximate wisdom in narrow domains. The point is that Joyn's product is the partnership — the combined output of AI-at-Knowledge meeting human-at-Wisdom. Collapsing those two into one layer destroys the product.

### Layer definitions applied to Joyn staff

**Data layer** — what staff ingests
Raw, unprocessed inputs. Regulatory bulletins before they are read. Financial statements before they are analysed. Lead records before they are qualified. Staff at this layer collects, normalises, and structures. Output: clean, structured data ready for the next layer.

**Information layer** — what staff primarily produces
Data with context applied. A regulatory bulletin scored by severity and mapped to the hirer's lines of business. A financial statement with anomalies flagged and benchmarked. A lead record ranked by qualification criteria. This is the primary output layer for all Joyn autonomous staff. Output: scored, ranked, explained artifacts ready for human review.

**Knowledge layer** — what the calibration corpus builds toward
Patterns extracted from accumulated Information-layer outputs and hirer feedback. Not a single output — a living record of what has worked, what has been corrected, and what this specific hirer values. The calibration corpus is Joyn's knowledge layer. It belongs to the hirer. It improves with every engagement. Output: a hirer-specific calibration record that makes future Information-layer outputs more accurate and more relevant.

**Wisdom layer** — what the human brings
Judgment applied in novel, high-stakes, or ethically complex situations. The insurance veteran who knows that a bulletin technically applies but that their carrier has a regulatory relationship that changes the urgency. The PE partner who overrides a risk flag because they have relationship context the diligence team doesn't. The practitioner who disagrees with the staff's recommendation because they've seen this pattern fail before in a context the AI has no record of. Wisdom cannot be calibrated into a corpus. It is irreducibly human.

### What this means for staff design

Every new staff member built on Joyn must declare its primary operating layer at the Brief stage:

```
DIKW DECLARATION (required in Creator Brief)
─────────────────────────────────────────────
Primary operating layer: [ ] Data  [ ] Information  [ ] Knowledge (corpus-building)
Wisdom handoff point: [Where does this staff stop and the human take over?]
What the human brings that this staff cannot: [One sentence — be specific]
─────────────────────────────────────────────
```

**A staff member that cannot articulate its wisdom handoff point is not ready to be built.**

### The pattern recognition and corpus relationship

Pattern recognition and corpus-building are how staff moves from Information toward Knowledge over time. They are not separate from the DIKW model — they are the mechanism by which the Knowledge layer grows:

- Pattern recognition operates at the Information → Knowledge boundary: the staff begins to recognise that *this type of bulletin* from *this regulator* consistently precedes a specific class of enforcement action. That is pattern recognition producing knowledge.
- The corpus captures and structures those patterns in a form that is hirer-specific, portable, and owned by the hirer.
- Neither pattern recognition nor corpus-building crosses into Wisdom. Recognising a pattern is not the same as knowing when to override it. That judgment lives one layer up — with the human.

---

## 07 — What Claude Reads This For

When Claude (any instance) is designing, building, or reviewing any hirer-facing feature:

- Before designing any output display → check §02 Right 01 (modification affordance required)
- Before designing any automated action → check §02 Right 02 (explainability required) and Pattern 01
- Before designing any data handling → check §02 Right 04 and Right 05
- Before specifying any intervention point → check §03 and use the intervention point template
- Before designing any calibration mechanism → check §04
- Before making any trust claim in copy → check §05 for what trust is actually built on
- Before any autonomous action with consequence → check Pattern 01 and Pattern 02
- Before designing any new staff capability → check §10 and ask: which DIKW layer does this operate at, and where is the wisdom handoff?

---

## 08 — Amendment Process

Amendments require founder approval. When amended:

1. Version number increments
2. Change documented in version history
3. `AGENT-RULES.md` reviewed for consistency
4. Any live staff whose behaviour is affected is flagged for review

---

## 09 — Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | March 2026 | Initial operating manual — hirer rights, intervention design, output modification, trust architecture, mistake-prevention patterns |
| 1.1 | March 2026 | Added §10 The Information Architecture (DIKW) — layer definitions, design constraint, DIKW declaration template, pattern recognition and corpus relationship |

---

*Joyn · tryjoyn.me · HUMAN-COLLAB.md · How humans and AI staff work together.*
*The AI climbs to Knowledge. The human brings Wisdom. The product is the partnership.*
