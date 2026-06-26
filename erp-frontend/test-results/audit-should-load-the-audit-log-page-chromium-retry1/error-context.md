# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: audit.spec.js >> should load the audit log page
- Location: tests\audit.spec.js:16:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=/Audit Log/i').first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('text=/Audit Log/i').first()

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

# Test source

```ts
  1  | // PATH: erp-frontend/tests/audit.spec.js
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | async function login(page) {
  5  |     await page.goto('http://localhost:5173/login');
  6  |     await page.waitForTimeout(1200);
  7  |     await page.locator('input[autocomplete="username"]').fill('admin_root');
  8  |     await page.locator('input[autocomplete="current-password"]').fill('TestPassword123');
  9  |     await page.locator('button[type="submit"]').click();
  10 |     await expect(page).toHaveURL(/\/dashboard|\/settings/, { timeout: 15000 });
  11 | }
  12 | 
  13 | // ---------------------------------------------------------------------------
  14 | // TEST 1: Audit page loads
  15 | // ---------------------------------------------------------------------------
  16 | test('should load the audit log page', async ({ page }) => {
  17 |     await login(page);
  18 |     await page.goto('http://localhost:5173/audit');
> 19 |     await expect(page.locator('text=/Audit Log/i').first()).toBeVisible({ timeout: 10000 });
     |                                                             ^ Error: expect(locator).toBeVisible() failed
  20 | });
  21 | 
  22 | // ---------------------------------------------------------------------------
  23 | // TEST 2: Log entries are displayed
  24 | // ---------------------------------------------------------------------------
  25 | test('should display audit log entries', async ({ page }) => {
  26 |     await login(page);
  27 |     await page.goto('http://localhost:5173/audit');
  28 |     await expect(page.locator('text=/Audit Log/i').first()).toBeVisible({ timeout: 10000 });
  29 |     await page.waitForTimeout(3000);
  30 | 
  31 |     // Either log rows show or empty state shows -- either is fine
  32 |     const logRow = page.locator('[class*="logRow"]').first();
  33 |     const emptySignal = page.locator('[class*="emptySignal"]').first();
  34 |     const eitherVisible = (await logRow.isVisible()) || (await emptySignal.isVisible());
  35 |     expect(eitherVisible).toBeTruthy();
  36 | });
  37 | 
  38 | // ---------------------------------------------------------------------------
  39 | // TEST 3: Keyword search works
  40 | // ---------------------------------------------------------------------------
  41 | test('should allow keyword search in audit log', async ({ page }) => {
  42 |     await login(page);
  43 |     await page.goto('http://localhost:5173/audit');
  44 |     await expect(page.locator('text=/Audit Log/i').first()).toBeVisible({ timeout: 10000 });
  45 | 
  46 |     const searchInput = page.locator('input[type="search"], input[placeholder*="Investigate"]').first();
  47 |     if (await searchInput.isVisible()) {
  48 |         await searchInput.fill('LOGIN');
  49 |         await page.waitForTimeout(2000);
  50 |         // Just verify no crash
  51 |         expect(page.url()).toContain('/audit');
  52 |     }
  53 | });
  54 | 
```