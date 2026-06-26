# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: dashboard.spec.js >> should navigate via quick action buttons
- Location: tests\dashboard.spec.js:33:1

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

# Test source

```ts
  1  | // PATH: erp-frontend/tests/dashboard.spec.js
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | async function login(page) {
  5  |     await page.goto('http://localhost:5173/login');
  6  |     await page.waitForTimeout(1200);
  7  |     await page.locator('input[autocomplete="username"]').fill('admin_root');
  8  |     await page.locator('input[autocomplete="current-password"]').fill('TestPassword123');
  9  |     await page.locator('button[type="submit"]').click();
  10 |     await expect(page).toHaveURL(/\/dashboard|\/settings/, { timeout: 15000 });
  11 |     if (page.url().includes('/settings')) {
  12 |         await page.goto('http://localhost:5173/dashboard');
  13 |     }
  14 | }
  15 | 
  16 | // ---------------------------------------------------------------------------
  17 | // TEST 1: Dashboard loads with stat tiles
  18 | // ---------------------------------------------------------------------------
  19 | test('should load dashboard with stat tiles', async ({ page }) => {
  20 |     await login(page);
  21 |     await page.goto('http://localhost:5173/dashboard');
  22 |     await expect(page.locator('text=/System Dashboard/i').first()).toBeVisible({ timeout: 10000 });
  23 | 
  24 |     // Stat tiles should be present
  25 |     const statTiles = page.locator('[class*="statTile"]');
  26 |     const count = await statTiles.count();
  27 |     expect(count).toBeGreaterThan(0);
  28 | });
  29 | 
  30 | // ---------------------------------------------------------------------------
  31 | // TEST 2: Quick action buttons navigate correctly
  32 | // ---------------------------------------------------------------------------
  33 | test('should navigate via quick action buttons', async ({ page }) => {
  34 |     await login(page);
  35 |     await page.goto('http://localhost:5173/dashboard');
> 36 |     await expect(page.locator('text=/System Dashboard/i').first()).toBeVisible({ timeout: 10000 });
     |                                                                    ^ Error: expect(locator).toBeVisible() failed
  37 |     await page.waitForTimeout(2000);
  38 | 
  39 |     const newPlotBtn = page.locator('button:has-text("NEW PLOT")').first();
  40 |     if (await newPlotBtn.isVisible()) {
  41 |         await newPlotBtn.click();
  42 |         await expect(page).toHaveURL(/\/land\/new/, { timeout: 8000 });
  43 |     }
  44 | });
  45 | 
  46 | // ---------------------------------------------------------------------------
  47 | // TEST 3: Sidebar navigation works
  48 | // ---------------------------------------------------------------------------
  49 | test('should navigate using sidebar links', async ({ page }) => {
  50 |     await login(page);
  51 |     await page.goto('http://localhost:5173/dashboard');
  52 |     await expect(page.locator('text=/System Dashboard/i').first()).toBeVisible({ timeout: 10000 });
  53 | 
  54 |     // Click LEDGER in sidebar
  55 |     const ledgerLink = page.locator('a[href="/land/projects"]').first();
  56 |     await expect(ledgerLink).toBeVisible({ timeout: 5000 });
  57 |     await ledgerLink.click();
  58 |     await expect(page).toHaveURL(/\/land\/projects/, { timeout: 8000 });
  59 |     await expect(page.locator('text=/Plot Ledger/i').first()).toBeVisible({ timeout: 8000 });
  60 | });
  61 | 
  62 | // ---------------------------------------------------------------------------
  63 | // TEST 4: Session logs out correctly
  64 | // ---------------------------------------------------------------------------
  65 | test('should log out and redirect to login', async ({ page }) => {
  66 |     await login(page);
  67 |     await page.goto('http://localhost:5173/dashboard');
  68 |     await expect(page.locator('text=/System Dashboard/i').first()).toBeVisible({ timeout: 10000 });
  69 | 
  70 |     const logoutBtn = page.locator('button[aria-label*="Sign out"], [class*="logoutTrigger"]').first();
  71 |     if (await logoutBtn.isVisible()) {
  72 |         await logoutBtn.click();
  73 |         await expect(page).toHaveURL(/\/login/, { timeout: 8000 });
  74 |     }
  75 | });
  76 | 
```