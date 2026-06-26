# FRONTEND_TEST_PLAN.md
# GOLDEN SEED ERP — COMPREHENSIVE END-TO-END UI TEST PLAN
# Version: 1.0 | Prepared for: Manual QA Execution

---

## HOW TO USE THIS DOCUMENT

- Work through each Phase in strict order — later Phases depend on data created in earlier ones.
- Mark each item `[x]` when passed, `[FAIL]` when failed (add a note describing what went wrong).
- The **Action** column describes exactly what to click/type. The **Expected Result** column describes what the UI and/or database must show.
- Any item marked `[FAIL]` must be logged before proceeding to the next Phase.

---

## PHASE 0: ENVIRONMENT RESET (START FROM ZERO)

> **Goal:** Guarantee the test begins with a clean database and no stale browser state.
> This eliminates false positives caused by leftover data (like "ghost" payment records) from previous sessions.

### 0.1 — DATABASE WIPE VIA NEON SQL EDITOR

**Location:** https://console.neon.tech → Select project `neondb` → SQL Editor tab

**Action:** Copy and paste the following SQL block in its entirety, then click **Run**:

```sql
-- GOLDEN SEED ERP — FULL DATABASE WIPE
-- Run this in the Neon SQL Editor before every full test cycle.
-- The CASCADE keyword ensures all foreign key relationships are destroyed cleanly.

DROP TABLE IF EXISTS audit_logs           CASCADE;
DROP TABLE IF EXISTS follow_up_logs       CASCADE;
DROP TABLE IF EXISTS project_documents    CASCADE;
DROP TABLE IF EXISTS payment_records      CASCADE;
DROP TABLE IF EXISTS payment_schedules    CASCADE;
DROP TABLE IF EXISTS project_proprietors  CASCADE;
DROP TABLE IF EXISTS notifications        CASCADE;
DROP TABLE IF EXISTS land_projects        CASCADE;
DROP TABLE IF EXISTS land_titles          CASCADE;
DROP TABLE IF EXISTS clients              CASCADE;
DROP TABLE IF EXISTS users                CASCADE;