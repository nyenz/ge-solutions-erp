// PATH: erp-frontend/tests/folder.spec.js
import { test, expect } from "@playwright/test";

// Navigate to the first available folder via the ledger
async function openFirstFolder(page) {
    await page.goto("http://localhost:5173/land/projects");
    await expect(page.locator("text=/Plot Ledger/i").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(2500);
    const firstRow = page.locator("tbody tr[tabindex=\"0\"]").first();
    await expect(firstRow).toBeVisible({ timeout: 8000 });
    await firstRow.click();
    await page.waitForTimeout(3000);
    await expect(page.url()).toMatch(/\/folder\//);
}

// ---------------------------------------------------------------------------
test("should load a folder page with pipeline HUD", async ({ page }) => {
    await openFirstFolder(page);
    const hud = page.locator("[class*=\"pipelineHUD\"]").first();
    await expect(hud).toBeVisible({ timeout: 8000 });
});

// ---------------------------------------------------------------------------
test("should show tab bar with OVERVIEW FINANCIALS OWNERS DOCUMENTS", async ({ page }) => {
    await openFirstFolder(page);
    const tabBar = page.locator("[role=\"tablist\"]").first();
    await expect(tabBar).toBeVisible({ timeout: 8000 });

    for (const tab of ["OVERVIEW", "FINANCIALS", "OWNERS", "DOCUMENTS"]) {
        const tabBtn = page.locator(`[role=\"tab\"]:has-text(\"${tab}\"), button:has-text(\"${tab}\")`).first();
        await expect(tabBtn).toBeVisible({ timeout: 5000 });
    }
});

// ---------------------------------------------------------------------------
test("should switch to FINANCIALS tab and show balance summary", async ({ page }) => {
    await openFirstFolder(page);

    const finTab = page.locator("[role=\"tab\"]:has-text(\"FINANCIALS\"), button:has-text(\"FIN\"), button:has-text(\"FINANCIALS\")").first();
    await expect(finTab).toBeVisible({ timeout: 5000 });
    await finTab.click();
    await page.waitForTimeout(800);

    const balance = page.locator("text=/BALANCE SUMMARY|AMOUNT OWED|PLOT VALUE/i").first();
    await expect(balance).toBeVisible({ timeout: 6000 });
});

// ---------------------------------------------------------------------------
test("should switch to OWNERS tab and display owner info", async ({ page }) => {
    await openFirstFolder(page);

    const ownersTab = page.locator("[role=\"tab\"]:has-text(\"OWNERS\"), button:has-text(\"OWN\")").first();
    await expect(ownersTab).toBeVisible({ timeout: 5000 });
    await ownersTab.click();
    await page.waitForTimeout(800);

    const ownersPanel = page.locator("text=/OWNERS/i").first();
    await expect(ownersPanel).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should open edit mode and show EDIT MODE badge", async ({ page }) => {
    await openFirstFolder(page);

    const editBtn = page.locator("button:has-text(\"EDIT\")").first();
    await expect(editBtn).toBeVisible({ timeout: 6000 });
    await editBtn.click();
    await page.waitForTimeout(600);

    const editBadge = page.locator("text=/EDIT MODE/i").first();
    await expect(editBadge).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should cancel edit mode without saving", async ({ page }) => {
    await openFirstFolder(page);

    const editBtn = page.locator("button:has-text(\"EDIT\")").first();
    await editBtn.click();
    await page.waitForTimeout(500);

    const cancelBtn = page.locator("button:has-text(\"CANCEL\")").first();
    await expect(cancelBtn).toBeVisible({ timeout: 5000 });
    await cancelBtn.click();
    await page.waitForTimeout(500);

    const editBadge = page.locator("text=/EDIT MODE/i");
    await expect(editBadge).not.toBeVisible();
});

// ---------------------------------------------------------------------------
test("should open payment modal when PAYMENT button clicked", async ({ page }) => {
    await openFirstFolder(page);

    const payBtn = page.locator("button:has-text(\"PAYMENT\")").first();
    await expect(payBtn).toBeVisible({ timeout: 6000 });
    await payBtn.click();
    await page.waitForTimeout(600);

    // Modal title
    const modalTitle = page.locator("text=/RECORD PAYMENT/i").first();
    await expect(modalTitle).toBeVisible({ timeout: 5000 });

    // Close it
    const closeBtn = page.locator("[class*=\"closeBtn\"]").first();
    if (await closeBtn.isVisible()) await closeBtn.click();
});
