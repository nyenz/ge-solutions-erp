# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login.spec.js >> should successfully log in and redirect to dashboard
- Location: tests\login.spec.js:4:1

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/dashboard|\/settings/
Received string:  "http://localhost:5173/login"
Timeout: 15000ms

Call log:
  - Expect "toHaveURL" with timeout 15000ms
    32 × unexpected value "http://localhost:5173/login"

```

```yaml
- img: SYS.0 SYS.1 SYS.2 SYS.3
- text: 🌱
- heading "Golden Seed" [level=1]
- paragraph: Enterprise Portal
- text: Could not connect to the server. Please check your internet and try again. USERNAME
- textbox: admin
- text: PASSWORD
- textbox: admin123
- button:
  - img
- button "Authorize":
  - img
  - text: Authorize
- button "Lost Master Key?"
- paragraph: Logins are Audited for Accountability.
```

# Test source

```ts
  1  | // PATH: erp-frontend/tests/login.spec.js
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | test('should successfully log in and redirect to dashboard', async ({ page }) => {
  5  | 
  6  |   // ── STEP 1: Navigate to the login page ──
  7  |   await page.goto('http://localhost:5173/login');
  8  | 
  9  |   // Wait for the app load screen to finish (it has a 900ms timer)
  10 |   await page.waitForTimeout(1200);
  11 | 
  12 |   // ── STEP 2: Verify the login page heading is visible ──
  13 |   // The login card contains "Golden Seed" and "Enterprise Portal"
  14 |   const heading = page.locator('text=/Golden Seed|Enterprise Portal/i').first();
  15 |   await expect(heading).toBeVisible({ timeout: 10000 });
  16 | 
  17 |   // ── STEP 3: Type in test credentials ──
  18 |   const usernameInput = page.locator('input[autocomplete="username"]');
  19 |   const passwordInput = page.locator('input[autocomplete="current-password"]');
  20 | 
  21 |   await usernameInput.fill('admin');
  22 |   await passwordInput.fill('admin123');
  23 | 
  24 |   // ── STEP 4: Click the "Authorize" button ──
  25 |   const authorizeBtn = page.locator('button[type="submit"]');
  26 |   await expect(authorizeBtn).toBeVisible({ timeout: 5000 });
  27 |   await authorizeBtn.click();
  28 | 
  29 |   // ── STEP 5: Verify successful redirect ──
  30 |   // After login, the app routes to either /dashboard (normal) or
  31 |   // /settings (if mustChangePassword is set on the account)
> 32 |   await expect(page).toHaveURL(
     |                      ^ Error: expect(page).toHaveURL(expected) failed
  33 |     /\/dashboard|\/settings/,
  34 |     { timeout: 15000 }
  35 |   );
  36 | 
  37 | });
  38 | 
```