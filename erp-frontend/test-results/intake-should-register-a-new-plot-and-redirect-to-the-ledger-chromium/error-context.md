# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: intake.spec.js >> should register a new plot and redirect to the ledger
- Location: tests\intake.spec.js:58:1

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/land\/projects/
Received string:  "http://localhost:5173/land/new"
Timeout: 20000ms

Call log:
  - Expect "toHaveURL" with timeout 20000ms
    38 × unexpected value "http://localhost:5173/land/new"

```

```yaml
- img: SYS.0 SYS.1 SYS.2 SYS.3
- banner:
  - button "Toggle sidebar navigation"
  - text: GOLDEN SEED
  - button "1 recovery mission pending"
  - text: admin_root ROOT OWNER
  - button "Sign out of session"
- complementary "System navigation":
  - navigation "Main menu":
    - link "DASHBOARD":
      - /url: /dashboard
    - link "NEW PLOT":
      - /url: /land/new
    - link "LEDGER":
      - /url: /land/projects
    - link "RECOVERY":
      - /url: /recovery
    - link "PAYMENTS":
      - /url: /payments
    - link "REPORTS":
      - /url: /reports
    - link "AUDIT":
      - /url: /audit
    - link "SETTINGS":
      - /url: /settings
- main:
  - heading "New Plot Registration" [level=1]
  - paragraph: Register a new land title into the system
  - button "PLOT DETAILS" [expanded]
  - text: PLOT ID * CAPS
  - textbox "PLOT ID *": TEST-PLOT-1782468488427
  - text: TENURE
  - combobox "TENURE": MAILO
  - text: BOX LOCATION CAPS
  - textbox "BOX LOCATION"
  - text: DISTRICT * CAPS
  - combobox "DISTRICT *": KAMPALA
  - text: COUNTY CAPS
  - textbox "COUNTY"
  - text: BLOCK / ROAD CAPS
  - textbox "BLOCK / ROAD"
  - text: INSTRUMENT NO. CAPS
  - textbox "INSTRUMENT NO."
  - text: VOLUME
  - textbox "VOLUME"
  - text: FOLIO
  - textbox "FOLIO"
  - button "OWNERS 1" [expanded]
  - text: "OWNER #1 (PRIMARY) FULL NAME * CAPS"
  - textbox "FULL NAME *": TEST OWNER
  - text: PHONE NUMBER *
  - textbox "PHONE NUMBER *":
    - /placeholder: 0712 345 678
    - text: "0712345678"
  - text: Use '/' to separate multiple numbers (e.g. 077... / 075...) NATIONAL ID (NIN) CAPS
  - textbox "NATIONAL ID (NIN)"
  - text: EMAIL
  - textbox "EMAIL"
  - text: HOME ADDRESS
  - textbox "HOME ADDRESS"
  - button "ADD JOINT OWNER"
  - button "FINANCIALS" [expanded]
  - text: TOTAL COST * UGX
  - textbox "TOTAL COST *":
    - /placeholder: "0"
    - text: 5,000,000
  - text: INITIAL PAYMENT UGX
  - textbox "INITIAL PAYMENT":
    - /placeholder: "0"
    - text: 1,000,000
  - text: AMOUNT OWED AUTO UGX 4,000,000 BACKLOG STATUS
  - button "✓ STANDARD — NOT BACKLOG"
  - button "⚠ ENTER AS BACKLOG"
  - button "DOCUMENTS 1"
  - link "📄 mock-document.pdf":
    - /url: "#"
  - button:
    - img
  - button "SELECT SCANS"
  - button "NOTES"
  - img
  - text: No notes added yet
  - button "+ ADD NOTE"
  - button "DUPLICATE PLOT"
  - button "SAVE NEW PLOT"
- region "Notifications":
  - alert:
    - text: A plot with this ID already exists in the system.
    - button "Dismiss"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | import path from 'path';
  3  | import { fileURLToPath } from 'url';
  4  | import fs from 'fs';
  5  | 
  6  | const __filename = fileURLToPath(import.meta.url);
  7  | const __dirname = path.dirname(__filename);
  8  | 
  9  | function ensureFixture() {
  10 |     const dir = path.join(__dirname, 'fixtures');
  11 |     const filePath = path.join(dir, 'mock-document.pdf');
  12 |     if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  13 |     if (!fs.existsSync(filePath)) {
  14 |         const pdfContent = '%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF';
  15 |         fs.writeFileSync(filePath, pdfContent);
  16 |     }
  17 |     return filePath;
  18 | }
  19 | 
  20 | async function smartLogin(page) {
  21 |     await page.goto('http://localhost:5173/login');
  22 |     await page.waitForTimeout(1000);
  23 | 
  24 |     // Try target password first
  25 |     await page.locator('input[autocomplete="username"]').fill('admin_root');
  26 |     await page.locator('input[autocomplete="current-password"]').fill('Manager@123');
  27 |     await page.locator('button[type="submit"]').click();
  28 | 
  29 |     await page.waitForTimeout(1500);
  30 | 
  31 |     // If it failed, the DB is fresh. Fall back to TestPassword123
  32 |     const errorAlert = page.locator('text=/Wrong username or password/i');
  33 |     if (await errorAlert.isVisible()) {
  34 |         await page.locator('input[autocomplete="current-password"]').fill('TestPassword123');
  35 |         await page.locator('button[type="submit"]').click();
  36 |     }
  37 | 
  38 |     await expect(page).toHaveURL(/\/dashboard|\/settings/, { timeout: 15000 });
  39 | 
  40 |     // Handle mandatory password reset if we landed on settings
  41 |     if (page.url().includes('/settings')) {
  42 |         await page.locator('input[type="password"]').nth(0).fill('TestPassword123');
  43 |         await page.locator('input[type="password"]').nth(1).fill('Manager@123');
  44 |         await page.locator('input[type="password"]').nth(2).fill('Manager@123');
  45 |         await page.locator('button:has-text("REWRITE HARDWARE KEY")').click();
  46 | 
  47 |         await expect(page).toHaveURL(/\/login/, { timeout: 15000 });
  48 |         await page.waitForTimeout(1000);
  49 | 
  50 |         await page.locator('input[autocomplete="username"]').fill('admin_root');
  51 |         await page.locator('input[autocomplete="current-password"]').fill('Manager@123');
  52 |         await page.locator('button[type="submit"]').click();
  53 | 
  54 |         await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
  55 |     }
  56 | }
  57 | 
  58 | test('should register a new plot and redirect to the ledger', async ({ page }) => {
  59 |     await smartLogin(page);
  60 | 
  61 |     await page.goto('http://localhost:5173/land/new');
  62 |     await expect(page.locator('text=/New Plot Registration/i').first()).toBeVisible({ timeout: 10000 });
  63 | 
  64 |     const plotId = 'TEST-PLOT-' + Date.now();
  65 |     await page.locator('//label[contains(text(), "PLOT ID")]/ancestor::div[2]//input').fill(plotId);
  66 |     await page.locator('//label[contains(text(), "DISTRICT")]/ancestor::div[2]//input').fill('KAMPALA');
  67 | 
  68 |     await page.locator('//label[contains(text(), "FULL NAME")]/ancestor::div[2]//input').first().fill('TEST OWNER');
  69 |     await page.locator('//label[contains(text(), "PHONE")]/ancestor::div[2]//input').first().fill('0712345678');
  70 | 
  71 |     await page.locator('//label[contains(text(), "TOTAL COST")]/ancestor::div[2]//input').fill('5000000');
  72 |     await page.locator('//label[contains(text(), "INITIAL PAYMENT")]/ancestor::div[2]//input').fill('1000000');
  73 | 
  74 |     const filePath = ensureFixture();
  75 |     await page.locator('input[type="file"]').setInputFiles(filePath);
  76 | 
  77 |     await expect(page.locator('text=mock-document.pdf').first()).toBeVisible({ timeout: 5000 });
  78 | 
  79 |     await page.getByRole('button', { name: /SAVE NEW PLOT/i }).click();
  80 | 
> 81 |     await expect(page).toHaveURL(/\/land\/projects/, { timeout: 20000 });
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  82 | });
  83 | 
```