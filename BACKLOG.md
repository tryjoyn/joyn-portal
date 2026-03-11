# JOYN Backlog & Parking Lot

> **Purpose:** Single source of truth for parked features, architectural decisions, and future work.  
> **Rule:** Nothing gets forgotten. Everything gets reviewed quarterly.  
> **Last Updated:** January 2026

---

## How to Use This File

| Status | Meaning |
|--------|---------|
| 🔴 PARKED | Decided to defer. Review quarterly. |
| 🟡 NEXT | Approved for next sprint/cycle. |
| 🟢 IN PROGRESS | Currently being built. |
| ✅ DONE | Completed. Move to CHANGELOG. |
| ❌ DISCARDED | Reviewed and rejected. Keep for context. |

---

## 🔴 PARKED — Architecture & Infrastructure

### Performance
| Item | Context | Parked Date | Review Date |
|------|---------|-------------|-------------|
| Redis-based rate limiting | Currently in-memory. Need Redis when scaling beyond single instance. | Jan 2026 | Apr 2026 |
| Serverless provisioned concurrency | Railway works for now. Revisit if cold starts become an issue. | Jan 2026 | Apr 2026 |

### Privacy & Compliance
| Item | Context | Parked Date | Review Date |
|------|---------|-------------|-------------|
| GDPR "Delete my data" endpoint | Required before EU expansion. `/api/builder/delete-data` | Jan 2026 | Mar 2026 |
| Data retention auto-purge job | Conversations retained 90 days, then anonymized. Needs cron job. | Jan 2026 | Mar 2026 |
| Voice consent logging | When voice input launches, log explicit consent per session. | Jan 2026 | When voice ships |

### Security
| Item | Context | Parked Date | Review Date |
|------|---------|-------------|-------------|
| API key rotation schedule | Currently static. Add 90-day rotation policy. | Jan 2026 | Apr 2026 |
| LLM injection sanitization | Basic sanitization now. Need comprehensive input validation. | Jan 2026 | Feb 2026 |

### Observability & Controls
| Item | Context | Parked Date | Review Date |
|------|---------|-------------|-------------|
| Admin conversation viewer | `/api/admin/conversations` — see what builders are saying to Sage. | Jan 2026 | Feb 2026 |
| Cost monitoring alerts | Alert if avg tokens/conversation exceeds threshold. | Jan 2026 | Mar 2026 |
| Analytics dashboard | Track: conversation_started, gate_passed, fallback_triggered, brief_completed. | Jan 2026 | Mar 2026 |

---

## 🔴 PARKED — Features

### Sage (Conversational Brief)
| Item | Context | Parked Date | Review Date |
|------|---------|-------------|-------------|
| Multi-language support | Sage only speaks English. International builders need localization. | Jan 2026 | Q3 2026 |
| Mobile voice permissions | Voice works on desktop. Mobile browser permissions are tricky. | Jan 2026 | Mar 2026 |
| Accessibility audit | Screen reader support for chat UI. Voice is actually good for a11y. | Jan 2026 | Mar 2026 |

### Platform
| Item | Context | Parked Date | Review Date |
|------|---------|-------------|-------------|
| Builder referral program | Builders invite other builders. Track attribution. | Jan 2026 | Q2 2026 |
| Hirer feedback to builders | Close the loop — hirers rate AI staff, builders see feedback. | Jan 2026 | Q2 2026 |
| Public builder profiles | Builder reputation/portfolio page. | Jan 2026 | Q3 2026 |

---

## 🟡 NEXT — Approved for Build

| Item | Context | Owner | Target |
|------|---------|-------|--------|
| Streaming responses (SSE) | Real-time "typing" effect for Sage (currently batch response) | TBD | Feb 2026 |
| Admin conversation viewer | `/api/admin/conversations` — see what builders are saying to Sage | TBD | Feb 2026 |

---

## 🟢 IN PROGRESS

| Item | Context | Owner | Started |
|------|---------|-------|---------|
| — | — | — | — |

---

## ✅ DONE — Recently Completed

| Item | Context | Completed |
|------|---------|-----------|
| Creator Brief bug fix | Fixed payload format (answers not brief), added completed flag, return visionary_spec | Jan 2026 |
| Sage v2 Conversational Brief | Chat-based brief collection with real-time gate scoring | Jan 2026 |
| `/api/sage/chat` endpoint | New backend for Sage conversations (stateful, non-streaming for MVP) | Jan 2026 |
| Prompt versioning system | `/app/joyn-builders/prompts/` folder structure with sage_v1.py | Jan 2026 |
| Shared gate scoring module | `/app/joyn-builders/shared/gate_scoring.py` — reusable across agents | Jan 2026 |
| Rate limiting (in-memory) | Max 60 messages/hour per builder | Jan 2026 |
| Voice input endpoint | `/api/sage/voice` with Whisper transcription | Jan 2026 |
| A/B test redirect | `?v=2` param redirects to Sage from classic form | Jan 2026 |
| Session resume | Save conversation turns, allow builder to resume if they leave | Jan 2026 |
| Graceful LLM fallback | If OpenAI down, Sage says "unavailable" not crash | Jan 2026 |

---

## ❌ DISCARDED — Reviewed & Rejected

| Item | Reason | Discarded Date |
|------|--------|----------------|
| — | — | — |

---

## Architectural Decisions Log

### ADR-001: Sage Conversation State
- **Decision:** Stateful (server stores conversation history)
- **Context:** Stateless would resend full conversation each turn, increasing token costs
- **Consequences:** Need session management, but enables resume and cheaper long conversations
- **Date:** Jan 2026

### ADR-002: Sage Persona Naming
- **Decision:** "Sage" not "Joyn"
- **Context:** Using brand name for agent creates confusion ("I talked to Joyn" vs "I used Joyn")
- **Consequences:** Cleaner brand separation, can add more agents later with distinct names
- **Date:** Jan 2026

### ADR-003: A/B Testing Approach
- **Decision:** URL param redirect (`?v=2`)
- **Context:** Allows controlled rollout, easy to measure, no infrastructure changes
- **Consequences:** Manual assignment for now, can add random split later
- **Date:** Jan 2026

### ADR-004: New Endpoint vs Reuse
- **Decision:** New `/api/sage/chat` endpoint, feeds into existing `/api/builder/brief`
- **Context:** Conversation state is different from form state. Need per-turn metrics.
- **Consequences:** More code upfront, but clean separation and future-proof
- **Date:** Jan 2026

---

## Quarterly Review Checklist

- [ ] Review all 🔴 PARKED items
- [ ] Move ready items to 🟡 NEXT
- [ ] Discard irrelevant items (mark ❌)
- [ ] Update review dates
- [ ] Archive ✅ DONE items older than 6 months

---

*Joyn · tryjoyn.me · Backlog v1.0 · January 2026*
