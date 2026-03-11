# JOYN Data Isolation Statement
**Version:** 1.0
**Last Updated:** March 2026

## Purpose

This document describes how the Joyn portal isolates data between different hirers (clients) to ensure that Hirer A cannot access Hirer B's data.

---

## 1. Database Architecture

### Current Design: Single SQLite Database

The Joyn portal uses a single SQLite database (`portal.db`) with client-scoped tables.

### Isolation Mechanism: Row-Level Filtering

All data access is filtered by `client_id`:

```sql
-- Example: Activity log query
SELECT * FROM activity_log 
WHERE client_id = :authenticated_client_id
ORDER BY timestamp DESC;
```

### Protected Tables

| Table | Isolation Column | Enforced Via |
|-------|------------------|--------------|
| `hired_staff` | `client_id` | All queries include WHERE clause |
| `activity_log` | `client_id` | All queries include WHERE clause |
| `outputs` | `client_id` | All queries include WHERE clause |
| `llm_usage` | `client_id` | All queries include WHERE clause |

---

## 2. Access Control

### Authentication Flow
1. User authenticates via `/login`
2. JWT issued containing `client_id` in `sub` claim
3. Every request extracts `client_id` from JWT
4. All database queries use this `client_id`

### Query Pattern
```python
# From portal/routes.py
@login_required  # Extracts g.client_id from JWT
def dashboard():
    # g.client_id is set by @login_required decorator
    rows = query(
        "SELECT * FROM activity_log WHERE client_id=?",
        (g.client_id,)  # Client can ONLY see their own data
    )
```

### No Cross-Client Access Paths
- No endpoint accepts arbitrary `client_id` from user input
- No query allows filtering by other client's data
- Admin endpoints require `X-Joyn-Secret` header (not user-accessible)

---

## 3. External API Isolation

### Iris Agent → Portal Communication
```python
# Iris uses X-Joyn-Secret for authentication
# Iris passes portal_client_id which it received during registration
# Portal validates this against its own client records
```

### Portal → Iris Communication
```python
# Portal only sends data for the authenticated client
# No broadcast operations across multiple clients
```

---

## 4. What Prevents Cross-Client Access

| Vector | Prevention |
|--------|------------|
| SQL Injection | Parameterized queries everywhere |
| Session Hijacking | HttpOnly + SameSite cookies |
| JWT Forgery | HS256 signature with secret |
| Direct Object Reference | All queries filter by JWT client_id |
| Admin Endpoint Abuse | Protected by X-Joyn-Secret |

---

## 5. Verification Checklist

To verify isolation, audit all database queries:

```bash
# Find all queries that could potentially leak data
grep -r "SELECT.*FROM" joyn-portal/ | grep -v "client_id"
```

Expected: All SELECT queries should include `WHERE client_id=?` or be limited to:
- System tables (schema, migrations)
- Authentication (clients table for login)
- Admin endpoints (protected by portal secret)

---

## 6. Future Improvements (When Scaling)

### At 100+ Active Hirers
- Consider PostgreSQL with Row-Level Security (RLS)
- Add database-level client_id constraints
- Implement audit logging for all data access

### At 500+ Active Hirers
- Consider tenant-per-database architecture
- Implement proper multi-tenancy with schemas

---

## 7. Summary Statement

> **Data Isolation Statement:**
> The Joyn portal implements row-level data isolation using the `client_id` column in all client-scoped tables. Every authenticated request extracts the client identity from a cryptographically signed JWT, and all database queries filter results to only return data belonging to that client. No mechanism exists for one client to query, view, or modify another client's data through the application layer.

---

## Contact

Questions about data isolation: hire@tryjoyn.me
