# JOYN BVD Compliance Gap Tracker
**Version:** 1.0
**Last Updated:** March 2026
**Assessment Period:** Q1 2026

## Gap Summary

| Gap ID | Category | Severity | Status | Resolution |
|--------|----------|----------|--------|------------|
| V3-001 | Encryption in transit | HIGH | ✅ CLOSED | SECURITY.md documents TLS chain |
| V3-002 | Data isolation | HIGH | ✅ CLOSED | DATA-ISOLATION.md created |
| V3-003 | Access scope | HIGH | ✅ CLOSED | SECURITY.md §3 documents least-privilege |
| V3-004 | Breach escalation | HIGH | ✅ CLOSED | BREACH-RUNBOOK.md created |
| V5-001 | Bulletin retention policy | MEDIUM | ✅ CLOSED | 90-day retention + purge API |
| V3-005 | Hirer data deletion | MEDIUM | ✅ CLOSED | /api/admin/delete-hirer endpoint |
| V5-002 | Calibration corpus ownership | LOW | ✅ CLOSED | Corpus namespaced by client_id in SQLite |

---

## Gap Details

### V3-001: Encryption in Transit (CLOSED)

**Issue:** TLS status for all Iris data flows not documented.

**Resolution:** 
- Created `/docs/SECURITY.md` §1
- Documents TLS 1.3 for all endpoints
- Includes verification checklist

### V3-002: Data Isolation (CLOSED)

**Issue:** No documented statement on multi-hirer data separation.

**Resolution:**
- Created `/docs/DATA-ISOLATION.md`
- Documents row-level filtering via client_id
- Includes query pattern examples

### V3-003: Access Scope (CLOSED)

**Issue:** API key and credential access scope not documented.

**Resolution:**
- Created `/docs/SECURITY.md` §3
- Documents least-privilege for all credentials
- Includes rotation schedule

### V3-004: Breach Escalation (CLOSED)

**Issue:** No runbook for data incident response.

**Resolution:**
- Created `/docs/BREACH-RUNBOOK.md`
- Defines immediate response checklist
- Includes notification requirements

### V5-001: Bulletin Retention Policy (CLOSED)

**Issue:** Raw bulletin HTML stored indefinitely.

**Resolution:**
- Added `/api/admin/purge-old-data` endpoint
- 90-day retention for outputs/bulletins
- 180-day retention for llm_usage
- Created `retention_purge_log` table for audit trail

### V3-005: Hirer Data Deletion (CLOSED)

**Issue:** No documented process for removing hirer data on offboarding.

**Resolution:**
- Added `/api/admin/delete-hirer` endpoint
- Deletes all data across all tables
- Logs deletion for compliance

### V5-002: Calibration Corpus Ownership (CLOSED)

**Issue:** ETHICS.md states corpus is hirer property. No technical mechanism enforces this.

**Resolution:**
- Corpus data stored in SQLite with client_id column
- All queries filter by authenticated client_id
- Same row-level isolation as documented in DATA-ISOLATION.md
- Export endpoint available via portal (hirer can download their data)

**Technical implementation:**
```sql
-- Corpus is implicitly namespaced via client_id in all tables
SELECT * FROM calibration_corpus WHERE client_id = ?
```

---

## Verification Schedule

### Monthly
- [ ] Review access logs for anomalies
- [ ] Verify TLS certificates valid
- [ ] Check retention purge ran successfully

### Quarterly
- [ ] Re-read ETHICS.md, HUMAN-COLLAB.md, 5V.md
- [ ] Run gap tracker review
- [ ] Update this document

---

## Contact

BVD compliance questions: hire@tryjoyn.me
