# PORTAL-STAFF-CONTEXT-PROBE.md
**Reusable context file for the Joyn hirer portal. This file tells the portal which staff is active and how to configure itself.**

**Version 1.0 · March 2026**

---

## 01 — Staff Identity

- **Name:** Probe
- **Mode:** Supervised
- **Vertical:** Technology
- **Status:** Live

---

## 02 — What the Hirer Sees on Login

- **Portal Title:** Probe Experiment Portal
- **Active Agents:** Intake, Scout, Challenger, Analyst, Designer, Debrief
- **Primary View:** Experiment dashboard showing current phase, active agent, and next intervention point.

---

## 03 — Intervention Points
*When the portal prompts the hirer for input.*

1.  **Experiment Kick-off:** Hirer reviews and approves the **Experiment Brief** produced by the **Intake** agent. Probe does not proceed without this approval.
2.  **Mid-point Check-in:** Hirer reviews the **Landscape Memo** and **Red Team Memo**. Hirer provides directional feedback before the **Analyst** and **Designer** agents begin solution design.
3.  **Final Debrief:** Hirer attends a live debrief session where the final outputs are presented. Hirer provides final feedback which is recorded in the Calibration Corpus.

---

## 04 — Named Outputs
*What appears in the portal's output library for the hirer to download.*

- **Experiment Brief:** The formalised hypothesis and experiment structure.
- **Landscape Memo:** What the **Scout** agent found (market precedents, competitive landscape).
- **Red Team Memo:** What the **Challenger** agent flagged (risks, assumptions, alternative views).
- **Executive Summary:** One-page summary of the experiment and its findings.
- **Detailed Report:** Full analysis, findings, and recommendations.
- **Demonstration Package:** Includes the demo video and any supporting artifacts.
- **Demo Video:** A short video demonstrating the proposed solution or finding.
- **Weekly Status Reports:** A weekly summary of progress, findings, and next steps.

---

## 05 — Calibration Corpus Structure
*How hirer feedback is recorded and structured for future use.*

- **Format:** A structured JSON file, private to the hirer's account.
- **Triggers:** Feedback is explicitly requested at the three intervention points.
- **Closing Questions (post-Debrief):**
    1.  How well did the final output match the initial hypothesis?
    2.  Which agent's output was most valuable to your team?
    3.  What is one thing you would change about the experiment process?
    4.  Based on this experiment, what is your next likely course of action?
- **Data Recorded:** Hirer responses, architectural preferences noted during check-ins, demographic context (organisation type), and methodology notes.

---

## 06 — Trial Configuration

- **Duration:** 14 days, no cost.
- **Day 1 Activation:**
    - Hirer portal is created.
    - **Intake** agent is activated.
    - Hirer receives a welcome email with a link to the portal and instructions to complete the initial hypothesis input.
- **Trial Limitations:** One experiment per trial. Full agent roster is active. All outputs are watermarked "Trial".

---

## 07 — Escalation Rules
*When the portal automatically notifies Joyn staff (hire@tryjoyn.me).*

- **Stalled Intervention:** If a hirer intervention point is pending for more than 72 hours, a notification is sent to Joyn for manual follow-up.
- **Scope Creep:** If the hirer attempts to materially change the experiment scope after the kick-off approval, the portal flags it and notifies Joyn.
- **Negative Feedback Loop:** If a hirer provides consistently negative feedback across two consecutive intervention points, a Joyn practitioner is notified to join the next check-in.
- **Technical Failure:** If any agent fails to produce a named output or the portal experiences an unrecoverable error, Joyn is notified immediately.
