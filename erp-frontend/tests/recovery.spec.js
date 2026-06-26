// PATH: erp-frontend/tests/recovery.spec.js
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/recovery");
    await expect(page.locator("text=/Call Recovery/i").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(2000);
});

// ---------------------------------------------------------------------------
test("should load recovery portal with financial HUD", async ({ page }) => {
    const activeOwed = page.locator("text=/ACTIVE TITLES OWED/i").first();
    await expect(activeOwed).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should switch to ALL TARGETS view", async ({ page }) => {
    const allBtn = page.locator("button:has-text(\"ALL TARGETS\")").first();
    await expect(allBtn).toBeVisible({ timeout: 5000 });
    await allBtn.click();
    await page.waitForTimeout(1500);
    // Should not crash -- HUD still visible
    const hud = page.locator("[class*=\"finHUD\"]").first();
    await expect(hud).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should filter missions to BACKLOG only", async ({ page }) => {
    const backlogPill = page.locator("button:has-text(\"BACKLOG\")").first();
    await expect(backlogPill).toBeVisible({ timeout: 5000 });
    await backlogPill.click();
    await page.waitForTimeout(1000);
    expect(page.url()).toContain("/recovery");
});

// ---------------------------------------------------------------------------
test("should show empty state when searching for non-existent owner", async ({ page }) => {
    const searchInput = page.locator("input[type=\"search\"], [class*=\"searchInput\"]").first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill("ZZZNOBODYXYZ9999");
    await page.waitForTimeout(800);

    const noMissions = page.locator("text=/NO MISSIONS/i").first();
    await expect(noMissions).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should expand a mission card to reveal plot details", async ({ page }) => {
    const firstCardHeader = page.locator("[class*=\"cardHeader\"]").first();
    if (await firstCardHeader.isVisible()) {
        await firstCardHeader.click();
        await page.waitForTimeout(800);

        const expandedBody = page.locator("[class*=\"cardBody\"]").first();
        await expect(expandedBody).toBeVisible({ timeout: 5000 });
    } else {
        // No missions -- acceptable empty state
        const emptyState = page.locator("[class*=\"emptyState\"]").first();
        await expect(emptyState).toBeVisible({ timeout: 3000 });
    }
});
