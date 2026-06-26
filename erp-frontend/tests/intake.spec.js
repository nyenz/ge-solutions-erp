// PATH: erp-frontend/tests/intake.spec.js
import { test, expect } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

function ensureFixture() {
    const dir      = path.join(__dirname, "fixtures");
    const filePath = path.join(dir, "mock-document.pdf");
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (!fs.existsSync(filePath)) {
        const pdf = Buffer.from(
            "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n" +
            "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" +
            "3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n" +
            "xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n" +
            "0000000058 00000 n\n0000000115 00000 n\n" +
            "trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        );
        fs.writeFileSync(filePath, pdf);
    }
    return filePath;
}

test.beforeEach(async ({ page }) => {
    await page.goto("http://localhost:5173/land/new");
    await expect(page.locator("text=/New Plot Registration/i").first()).toBeVisible({ timeout: 10000 });
});

// ---------------------------------------------------------------------------
test("should load the intake form", async ({ page }) => {
    // All main drawers should be visible
    await expect(page.locator("text=/PLOT DETAILS/i").first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator("text=/OWNERS/i").first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator("text=/FINANCIALS/i").first()).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
test("should block submit with no data filled", async ({ page }) => {
    await page.getByRole("button", { name: /SAVE NEW PLOT/i }).click();
    await page.waitForTimeout(1000);
    // Still on intake -- not redirected
    expect(page.url()).toContain("/land/new");
});

// ---------------------------------------------------------------------------
test("should register a new plot and redirect to ledger", async ({ page }) => {
    const plotId   = "AUTO-" + Date.now();
    const fixture  = ensureFixture();

    // -- Plot details --
    await page.locator("div:has-text(\"PLOT ID\")").locator("input").fill(plotId);
    await page.locator("div:has-text(\"DISTRICT\")").locator("input").fill("KAMPALA");

    // -- Owner --
    await page.locator("div:has-text(\"FULL NAME\")").first().locator("input").fill("AUTO TEST OWNER");
    await page.locator("div:has-text(\"PHONE NUMBER\")").first().locator("input").fill("0700000001");

    // -- Financials --
    await page.locator("div:has-text(\"TOTAL COST\")").locator("input").fill("5000000");
    await page.locator("div:has-text(\"INITIAL PAYMENT\")").locator("input").fill("1000000");

    // -- Open documents drawer and upload file --
    const docsDrawer = page.locator("div:has-text(\"DOCUMENTS\")").locator("[class*=\"drawerHeader\"]").first();
    if (await docsDrawer.isVisible()) {
        const isOpen = await page.locator("[class*=\"drawerHeader\"]").filter({ hasText: "DOCUMENTS" }).getAttribute("aria-expanded");
        if (isOpen !== "true") await docsDrawer.click();
    }
    const fileInput = page.locator("input[type=\"file\"]");
    await fileInput.setInputFiles(fixture);
    await page.waitForTimeout(600);

    // -- Submit --
    await page.getByRole("button", { name: /SAVE NEW PLOT/i }).click();

    // -- Verify redirect to ledger --
    await expect(page).toHaveURL(/\/land\/projects/, { timeout: 20000 });
    await expect(page.locator("text=/Plot Ledger/i").first()).toBeVisible({ timeout: 10000 });
});

// ---------------------------------------------------------------------------
test("should show unsaved changes guard when navigating away with data", async ({ page }) => {
    // Type something to dirty the form
    await page.locator("div:has-text(\"PLOT ID\")").locator("input").fill("TEMP-DIRTY");

    // Try navigating via sidebar
    const ledgerLink = page.locator("a[href=\"/land/projects\"]").first();
    await expect(ledgerLink).toBeVisible({ timeout: 5000 });
    await ledgerLink.click();
    await page.waitForTimeout(800);

    // Unsaved changes modal should appear
    const guardTitle = page.locator("text=/UNSAVED CHANGES/i").first();
    await expect(guardTitle).toBeVisible({ timeout: 6000 });

    // Choose to stay
    const stayBtn = page.locator("button:has-text(\"KEEP EDITING\")").first();
    await expect(stayBtn).toBeVisible({ timeout: 3000 });
    await stayBtn.click();

    // Still on intake
    expect(page.url()).toContain("/land/new");
});

// ---------------------------------------------------------------------------
test("should add a joint owner when ADD JOINT OWNER is clicked", async ({ page }) => {
    const addOwnerBtn = page.locator("button:has-text(\"ADD JOINT OWNER\")").first();
    await expect(addOwnerBtn).toBeVisible({ timeout: 5000 });

    const ownerBlocksBefore = await page.locator("[class*=\"ownerBlock\"]").count();
    await addOwnerBtn.click();
    await page.waitForTimeout(400);

    const ownerBlocksAfter = await page.locator("[class*=\"ownerBlock\"]").count();
    expect(ownerBlocksAfter).toBeGreaterThan(ownerBlocksBefore);
});
