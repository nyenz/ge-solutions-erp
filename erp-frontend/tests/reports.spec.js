// PATH: erp-frontend/tests/reports.spec.js
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/reports");
    await expect(page.locator("text=/Reports/i").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(1500);
});

// ---------------------------------------------------------------------------
test("should show FINANCIAL and OPERATIONAL sections", async ({ page }) => {
    await expect(page.locator("text=/FINANCIAL REPORTS/i").first()).toBeVisible({ timeout: 6000 });
    await expect(page.locator("text=/OPERATIONAL REPORTS/i").first()).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should show MORE REPORTS section for admin", async ({ page }) => {
    await expect(page.locator("text=/MORE REPORTS/i").first()).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should expand a report row to show description and download button", async ({ page }) => {
    const firstRow = page.locator("[class*=\"reportRow\"]").first();
    await expect(firstRow).toBeVisible({ timeout: 6000 });
    await firstRow.click();
    await page.waitForTimeout(600);

    const dlBtn = page.locator("button:has-text(\"DOWNLOAD CSV\")").first();
    await expect(dlBtn).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should collapse report row when clicked again", async ({ page }) => {
    const firstRow = page.locator("[class*=\"reportRow\"]").first();
    await firstRow.click();
    await page.waitForTimeout(400);

    // Click again to collapse
    await firstRow.click();
    await page.waitForTimeout(400);

    const dlBtn = page.locator("button:has-text(\"DOWNLOAD CSV\")").first();
    await expect(dlBtn).not.toBeVisible();
});

// ---------------------------------------------------------------------------
test("should collapse/expand a drawer section", async ({ page }) => {
    const finDrawer = page.locator("[class*=\"drawerHeader\"]:has-text(\"FINANCIAL\")").first();
    await expect(finDrawer).toBeVisible({ timeout: 5000 });

    // Toggle collapse
    await finDrawer.click();
    await page.waitForTimeout(400);

    // Toggle open again
    await finDrawer.click();
    await page.waitForTimeout(400);

    expect(page.url()).toContain("/reports");
});
