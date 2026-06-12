// PATH: erp-frontend/tests/login.spec.js
import { test, expect } from '@playwright/test';

test('should successfully log in and redirect to dashboard', async ({ page }) => {

  // ── STEP 1: Navigate to the login page ──
  await page.goto('http://localhost:5173/login');

  // Wait for the app load screen to finish (it has a 900ms timer)
  await page.waitForTimeout(1200);

  // ── STEP 2: Verify the login page heading is visible ──
  // The login card contains "Golden Seed" and "Enterprise Portal"
  const heading = page.locator('text=/Golden Seed|Enterprise Portal/i').first();
  await expect(heading).toBeVisible({ timeout: 10000 });

  // ── STEP 3: Type in test credentials ──
  const usernameInput = page.locator('input[autocomplete="username"]');
  const passwordInput = page.locator('input[autocomplete="current-password"]');

  await usernameInput.fill('admin');
  await passwordInput.fill('admin123');

  // ── STEP 4: Click the "Authorize" button ──
  const authorizeBtn = page.locator('button[type="submit"]');
  await expect(authorizeBtn).toBeVisible({ timeout: 5000 });
  await authorizeBtn.click();

  // ── STEP 5: Verify successful redirect ──
  // After login, the app routes to either /dashboard (normal) or
  // /settings (if mustChangePassword is set on the account)
  await expect(page).toHaveURL(
    /\/dashboard|\/settings/,
    { timeout: 15000 }
  );

});
