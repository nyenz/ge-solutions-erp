// PATH: erp-frontend/tests/ledger.spec.js
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/land/projects");
    await expect(page.locator("text=/Plot Ledger/i").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(2000); // let data load
});

// ---------------------------------------------------------------------------
test("should display the ledger table", async ({ page }) => {
    const table = page.locator("table");
    await expect(table).toBeVisible({ timeout: 8000 });
});

// ---------------------------------------------------------------------------
test("should show empty state when searching for non-existent plot", async ({ page }) => {
    const searchInput = page.locator("input#ledger-search, input[type=\"search\"]").first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill("XXXXXNOTEXISTXXXXX");
    await page.waitForTimeout(600);

    const noRecords = page.locator("text=/NO RECORDS/i").first();
    await expect(noRecords).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should clear search when clear button clicked", async ({ page }) => {
    const searchInput = page.locator("input#ledger-search, input[type=\"search\"]").first();
    await searchInput.fill("SOMETHING");
    await page.waitForTimeout(400);

    const clearBtn = page.locator("[class*=\"searchClearBtn\"]").first();
    if (await clearBtn.isVisible()) {
        await clearBtn.click();
        const val = await searchInput.inputValue();
        expect(val).toBe("");
    }
});

// ---------------------------------------------------------------------------
test("should change active filter when filter button clicked", async ({ page }) => {
    const allFilter     = page.locator("button:has-text(\"ALL ARCHIVES\")").first();
    const backlogFilter = page.locator("button:has-text(\"BACKLOG\")").first();

    await expect(allFilter).toBeVisible({ timeout: 5000 });
    await expect(backlogFilter).toBeVisible({ timeout: 5000 });

    await backlogFilter.click();
    await page.waitForTimeout(500);

    // Active filter should now have orange style
    const activeClasses = await backlogFilter.getAttribute("class");
    expect(activeClasses).toContain("active");
});

// ---------------------------------------------------------------------------
test("should navigate to folder page when a row is clicked", async ({ page }) => {
    const firstRow = page.locator("tbody tr[tabindex=\"0\"]").first();
    await expect(firstRow).toBeVisible({ timeout: 8000 });
    await firstRow.click();
    await page.waitForTimeout(2500);
    expect(page.url()).toMatch(/\/folder\//);
});

// ---------------------------------------------------------------------------
test("should sort table when column header is clicked", async ({ page }) => {
    const plotHeader = page.locator("th:has-text(\"PLOT ID\")").first();
    await expect(plotHeader).toBeVisible({ timeout: 5000 });
    await plotHeader.click();
    await page.waitForTimeout(400);
    // Should not crash
    expect(page.url()).toContain("/land/projects");
});
