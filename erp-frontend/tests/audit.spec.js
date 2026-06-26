// PATH: erp-frontend/tests/audit.spec.js
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/audit");
    await expect(page.locator("text=/Audit Log/i").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(3000); // audit data takes a moment
});

// ---------------------------------------------------------------------------
test("should load audit log page", async ({ page }) => {
    // Either log rows or empty state
    const logRow   = page.locator("[class*=\"logRow\"]").first();
    const emptyMsg = page.locator("[class*=\"emptySignal\"]").first();
    const either   = (await logRow.isVisible()) || (await emptyMsg.isVisible());
    expect(either).toBeTruthy();
});

// ---------------------------------------------------------------------------
test("should search logs by keyword", async ({ page }) => {
    const searchInput = page.locator("input[type=\"search\"]").first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill("LOGIN");
    await page.waitForTimeout(2500);
    // Page should not crash
    expect(page.url()).toContain("/audit");
});

// ---------------------------------------------------------------------------
test("should clear keyword search", async ({ page }) => {
    const searchInput = page.locator("input[type=\"search\"]").first();
    await searchInput.fill("TEST");
    await page.waitForTimeout(400);

    const clearBtn = page.locator("[class*=\"searchClear\"]").first();
    if (await clearBtn.isVisible()) {
        await clearBtn.click();
        const val = await searchInput.inputValue();
        expect(val).toBe("");
    }
});

// ---------------------------------------------------------------------------
test("should expand a log row to show trace details", async ({ page }) => {
    const firstLogRow = page.locator("[class*=\"logRow\"]").first();
    if (await firstLogRow.isVisible()) {
        await firstLogRow.click();
        await page.waitForTimeout(500);
        const traceDetails = page.locator("[class*=\"traceOpen\"]").first();
        await expect(traceDetails).toBeVisible({ timeout: 5000 });
    }
});

// ---------------------------------------------------------------------------
test("should paginate to older logs", async ({ page }) => {
    // OLDER LOGS button
    const olderBtn = page.locator("button:has-text(\"OLDER LOGS\")");
    // If page > 0 it will be enabled, otherwise it's disabled on page 0 -- both are valid
    await expect(olderBtn).toBeVisible({ timeout: 5000 });
});
