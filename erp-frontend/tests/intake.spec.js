import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function ensureFixture() {
    const dir = path.join(__dirname, 'fixtures');
    const filePath = path.join(dir, 'mock-document.pdf');
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (!fs.existsSync(filePath)) {
        const pdfContent = '%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF';
        fs.writeFileSync(filePath, pdfContent);
    }
    return filePath;
}

async function smartLogin(page) {
    await page.goto('http://localhost:5173/login');
    await page.waitForTimeout(1000);

    // Try target password first
    await page.locator('input[autocomplete="username"]').fill('admin_root');
    await page.locator('input[autocomplete="current-password"]').fill('Manager@123');
    await page.locator('button[type="submit"]').click();

    await page.waitForTimeout(1500);

    // If it failed, the DB is fresh. Fall back to TestPassword123
    const errorAlert = page.locator('text=/Wrong username or password/i');
    if (await errorAlert.isVisible()) {
        await page.locator('input[autocomplete="current-password"]').fill('TestPassword123');
        await page.locator('button[type="submit"]').click();
    }

    await expect(page).toHaveURL(/\/dashboard|\/settings/, { timeout: 15000 });

    // Handle mandatory password reset if we landed on settings
    if (page.url().includes('/settings')) {
        await page.locator('input[type="password"]').nth(0).fill('TestPassword123');
        await page.locator('input[type="password"]').nth(1).fill('Manager@123');
        await page.locator('input[type="password"]').nth(2).fill('Manager@123');
        await page.locator('button:has-text("REWRITE HARDWARE KEY")').click();

        await expect(page).toHaveURL(/\/login/, { timeout: 15000 });
        await page.waitForTimeout(1000);

        await page.locator('input[autocomplete="username"]').fill('admin_root');
        await page.locator('input[autocomplete="current-password"]').fill('Manager@123');
        await page.locator('button[type="submit"]').click();

        await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
    }
}

test('should register a new plot and redirect to the ledger', async ({ page }) => {
    await smartLogin(page);

    await page.goto('http://localhost:5173/land/new');
    await expect(page.locator('text=/New Plot Registration/i').first()).toBeVisible({ timeout: 10000 });

    const plotId = 'TEST-PLOT-' + Date.now();
    await page.locator('//label[contains(text(), "PLOT ID")]/ancestor::div[2]//input').fill(plotId);
    await page.locator('//label[contains(text(), "DISTRICT")]/ancestor::div[2]//input').fill('KAMPALA');

    await page.locator('//label[contains(text(), "FULL NAME")]/ancestor::div[2]//input').first().fill('TEST OWNER');
    await page.locator('//label[contains(text(), "PHONE")]/ancestor::div[2]//input').first().fill('0712345678');

    await page.locator('//label[contains(text(), "TOTAL COST")]/ancestor::div[2]//input').fill('5000000');
    await page.locator('//label[contains(text(), "INITIAL PAYMENT")]/ancestor::div[2]//input').fill('1000000');

    const filePath = ensureFixture();
    await page.locator('input[type="file"]').setInputFiles(filePath);

    await expect(page.locator('text=mock-document.pdf').first()).toBeVisible({ timeout: 5000 });

    await page.getByRole('button', { name: /SAVE NEW PLOT/i }).click();

    await expect(page).toHaveURL(/\/land\/projects/, { timeout: 20000 });
});
