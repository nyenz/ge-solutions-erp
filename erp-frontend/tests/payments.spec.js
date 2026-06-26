// PATH: erp-frontend/tests/payments.spec.js
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/payments");
    await expect(page.locator("text=/Payment Records/i").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(2000);
});

// ---------------------------------------------------------------------------
test("should load payments page with summary cards", async ({ page }) => {
    const cards = page.locator("[class*=\"sumCard\"]");
    await expect(cards.first()).toBeVisible({ timeout: 6000 });
    const count = await cards.count();
    expect(count).toBe(3); // TOTAL SHOWN, TITLE PAYMENTS, BACKLOG PAYMENTS
});

// ---------------------------------------------------------------------------
test("should filter by Title Payment type", async ({ page }) => {
    const titleBtn = page.locator("button:has-text(\"Title Payment\")").first();
    await expect(titleBtn).toBeVisible({ timeout: 5000 });
    await titleBtn.click();
    await page.waitForTimeout(600);
    // Should stay on payments page
    expect(page.url()).toContain("/payments");
});

// ---------------------------------------------------------------------------
test("should filter by ALL TYPES", async ({ page }) => {
    const allBtn = page.locator("button:has-text(\"ALL TYPES\")").first();
    await expect(allBtn).toBeVisible({ timeout: 5000 });
    await allBtn.click();
    await page.waitForTimeout(600);
    expect(page.url()).toContain("/payments");
});

// ---------------------------------------------------------------------------
test("should show NO RECORDS when searching for unknown value", async ({ page }) => {
    const searchInput = page.locator("[class*=\"searchInput\"]").first();
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill("ZZZNORESULT9999");
    await page.waitForTimeout(600);

    const noRec = page.locator("text=/NO RECORDS|NO PAYMENT/i").first();
    await expect(noRec).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should sort table by clicking AMOUNT PAID header", async ({ page }) => {
    const amountHeader = page.locator("th:has-text(\"AMOUNT PAID\")").first();
    await expect(amountHeader).toBeVisible({ timeout: 5000 });
    await amountHeader.click();
    await page.waitForTimeout(400);
    expect(page.url()).toContain("/payments");
});
