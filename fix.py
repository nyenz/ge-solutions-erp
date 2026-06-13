import os

path = "erp-frontend/tests/intake.spec.js"

content = """\
// PATH: erp-frontend/tests/intake.spec.js
import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test('should register a new plot and redirect to the ledger', async ({ page }) => {

  // ── STEP 1: Log in first ──
  await page.goto('http://localhost:5173/login');
  await page.waitForTimeout(1200);

  const usernameInput = page.locator('input[autocomplete="username"]');
  const passwordInput = page.locator('input[autocomplete="current-password"]');
  await usernameInput.fill('admin_root');
  await passwordInput.fill('TestPassword123');
  await page.locator('button[type="submit"]').click();

  // Wait for either the dashboard or the settings page (if password change is mandatory)
  await expect(page).toHaveURL(/\\/dashboard|\\/settings/, { timeout: 15000 });

  // ── STEP 1b: Handle mandatory password change if redirected to /settings ──
  if (page.url().includes('/settings')) {
    // Locate the inputs inside their specific label-text container boxes
    await page.locator('div:has-text("CURRENT MASTER KEY")').locator('input').fill('TestPassword123');
    await page.locator('div:has-text("NEW HARDWARE KEY")').locator('input').fill('NewPassword123');
    await page.locator('div:has-text("CONFIRM CONFIGURATION")').locator('input').fill('NewPassword123');
    await page.locator('button:has-text("REWRITE HARDWARE KEY")').click();

    // Wait for redirect back to login screen
    await expect(page).toHaveURL(/\\/login/, { timeout: 15000 });
    await page.waitForTimeout(1200);

    // Log back in with the brand new password!
    await page.locator('input[autocomplete="username"]').fill('admin_root');
    await page.locator('input[autocomplete="current-password"]').fill('NewPassword123');
    await page.locator('button[type="submit"]').click();

    await expect(page).toHaveURL(/\\/dashboard/, { timeout: 15000 });
  }

  // ── STEP 2: Navigate to New Plot (Intake) page ──
  await page.goto('http://localhost:5173/land/new');
  await expect(page.locator('text=/New Plot Registration/i').first()).toBeVisible({ timeout: 10000 });

  // ── STEP 3: Fill PLOT DETAILS ──
  const plotId = 'TEST-PLOT-' + Date.now();
  await page.locator('div:has-text("PLOT ID")').locator('input').fill(plotId);
  await page.locator('div:has-text("DISTRICT")').locator('input').fill('KAMPALA');

  // ── STEP 4: Fill OWNER #1 (PRIMARY) ──
  await page.locator('div:has-text("FULL NAME")').first().locator('input').fill('TEST OWNER');
  await page.locator('div:has-text("PHONE")').first().locator('input').fill('0712345678');

  // ── STEP 5: Fill FINANCIALS ──
  await page.locator('div:has-text("TOTAL COST")').locator('input').fill('5000000');
  await page.locator('div:has-text("INITIAL PAYMENT")').locator('input').fill('1000000');

  // ── STEP 6: Upload a mock document ──
  const filePath = path.join(__dirname, 'fixtures', 'mock-document.pdf');
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(filePath);

  // ── STEP 7: Click SAVE NEW PLOT ──
  await page.getByRole('button', { name: /SAVE NEW PLOT/i }).click();

  // ── STEP 8: Verify redirect to the Ledger page ──
  await expect(page).toHaveURL(/\\/land\\/projects/, { timeout: 15000 });
  await expect(page.locator('text=/Plot Ledger/i').first()).toBeVisible({ timeout: 10000 });
});
"""

os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8", newline="\\n") as f:
    f.write(content)

print("OK: Re-written intake.spec.js with robust container-based selectors.")