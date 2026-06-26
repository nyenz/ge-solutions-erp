// PATH: erp-frontend/tests/settings.spec.js
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/settings");
    await page.waitForTimeout(2000);
    expect(page.url()).toContain("/settings");
});

// ---------------------------------------------------------------------------
test("should load settings page with security panel", async ({ page }) => {
    const securityPanel = page.locator("text=/OPERATOR SECURITY CABINET|SECURITY MASTERY/i").first();
    await expect(securityPanel).toBeVisible({ timeout: 8000 });
});

// ---------------------------------------------------------------------------
test("should show governance ledger panel", async ({ page }) => {
    const govPanel = page.locator("text=/GOVERNANCE LEDGER/i").first();
    await expect(govPanel).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should show admin_root in the governance ledger", async ({ page }) => {
    const adminCard = page.locator("text=/admin_root/i").first();
    await expect(adminCard).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should reject password change with mismatched new passwords", async ({ page }) => {
    const currentInput = page.locator("div:has-text(\"CURRENT MASTER KEY\")").locator("input").first();
    const newInput     = page.locator("div:has-text(\"NEW HARDWARE KEY\")").locator("input").first();
    const confirmInput = page.locator("div:has-text(\"CONFIRM CONFIGURATION\")").locator("input").first();

    await currentInput.fill("GoldenSeed2024!");
    await newInput.fill("NewPassword123!");
    await confirmInput.fill("DIFFERENT_PASSWORD!");

    const commitBtn = page.locator("button:has-text(\"REWRITE HARDWARE KEY\")").first();
    await commitBtn.click();
    await page.waitForTimeout(1500);

    // Should still be on settings -- not logged out
    expect(page.url()).toContain("/settings");
});

// ---------------------------------------------------------------------------
test("should reject weak password in change form", async ({ page }) => {
    const currentInput = page.locator("div:has-text(\"CURRENT MASTER KEY\")").locator("input").first();
    const newInput     = page.locator("div:has-text(\"NEW HARDWARE KEY\")").locator("input").first();
    const confirmInput = page.locator("div:has-text(\"CONFIRM CONFIGURATION\")").locator("input").first();

    await currentInput.fill("GoldenSeed2024!");
    await newInput.fill("weak");
    await confirmInput.fill("weak");

    const commitBtn = page.locator("button:has-text(\"REWRITE HARDWARE KEY\")").first();
    await commitBtn.click();
    await page.waitForTimeout(1500);

    // Should stay on settings
    expect(page.url()).toContain("/settings");
});
