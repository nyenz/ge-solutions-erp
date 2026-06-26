# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.js >> should navigate using sidebar links
- Location: tests\dashboard.spec.js:49:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=/System Dashboard/i').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('text=/System Dashboard/i').first()

```

```yaml
- img: SYS.0 SYS.1 SYS.2 SYS.3
- banner:
  - button "Toggle sidebar navigation"
  - text: GOLDEN SEED
  - button "Open recovery missions"
  - text: admin_root ROOT OWNER
  - button "Sign out of session"
- complementary "System navigation":
  - navigation "Main menu":
    - link "DASHBOARD" [disabled]:
      - /url: /dashboard
    - link "NEW PLOT" [disabled]:
      - /url: /land/new
    - link "LEDGER" [disabled]:
      - /url: /land/projects
    - link "RECOVERY" [disabled]:
      - /url: /recovery
    - link "PAYMENTS" [disabled]:
      - /url: /payments
    - link "REPORTS" [disabled]:
      - /url: /reports
    - link "AUDIT" [disabled]:
      - /url: /audit
    - link "SETTINGS":
      - /url: /settings
- main:
  - heading "Security Mastery" [level=1]
  - paragraph: Hardware Protocols & Identity Registry
  - alert: KEY REWRITE MANDATORY
  - button "OPERATOR SECURITY CABINET, collapse" [expanded]: OPERATOR SECURITY CABINET
  - text: Updating this key will clear the mandatory reset handbrake. CURRENT MASTER KEY *
  - textbox
  - button "Show password"
  - text: NEW HARDWARE KEY *
  - textbox
  - button "Show new password"
  - text: CONFIRM CONFIGURATION *
  - textbox
  - button "Show confirmation"
  - button "REWRITE HARDWARE KEY"
  - button "GOVERNANCE LEDGER, collapse" [expanded]: GOVERNANCE LEDGER
  - button "Provision new operator": PROVISION NEW OPERATOR
  - text: Active Operator Suspended / Inactive
  - list "Operators":
    - listitem:
      - strong: admin_root
      - text: MASTER FOUNDER
      - paragraph: test@gesolutions.com
- region "Notifications"
```

```
Error: browserContext.close: Target page, context or browser has been closed
```