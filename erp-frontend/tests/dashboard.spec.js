// PATH: erp-frontend/tests/dashboard.spec.js
// Runs with stored admin auth state -- no login needed.
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/dashboard");
    await expect(page.locator("text=/System Dashboard/i").first()).toBeVisible({ timeout: 12000 });
});

// ---------------------------------------------------------------------------
test("should load dashboard with stat tiles", async ({ page }) => {
    const statTiles = page.locator("[class*=\"statTile\"]");
    await expect(statTiles.first()).toBeVisible({ timeout: 8000 });
    const count = await statTiles.count();
    expect(count).toBeGreaterThan(0);
});

// ---------------------------------------------------------------------------
test("should show pipeline stages gauge", async ({ page }) => {
    const gauge = page.locator("[class*=\"gaugeRow\"]").first();
    await expect(gauge).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should navigate to New Plot via quick action button", async ({ page }) => {
    const btn = page.locator("button:has-text(\"NEW PLOT\")").first();
    await expect(btn).toBeVisible({ timeout: 6000 });
    await btn.click();
    await expect(page).toHaveURL(/\/land\/new/, { timeout: 8000 });
});

// ---------------------------------------------------------------------------
test("should navigate to Ledger via sidebar", async ({ page }) => {
    const ledgerLink = page.locator("a[href=\"/land/projects\"]").first();
    await expect(ledgerLink).toBeVisible({ timeout: 5000 });
    await ledgerLink.click();
    await expect(page).toHaveURL(/\/land\/projects/, { timeout: 8000 });
});

// ---------------------------------------------------------------------------
test("should log out and redirect to login", async ({ page }) => {
    const logoutBtn = page.locator("[class*=\"logoutTrigger\"]").first();
    await expect(logoutBtn).toBeVisible({ timeout: 5000 });
    await logoutBtn.click();
    await expect(page).toHaveURL(/\/login/, { timeout: 8000 });
});
