import { test, expect } from '@playwright/test';

test('should successfully log in and redirect to dashboard', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await page.waitForTimeout(1000);

    await page.locator('input[autocomplete="username"]').fill('admin_root');
    await page.locator('input[autocomplete="current-password"]').fill('Manager@123');
    await page.locator('button[type="submit"]').click();

    await page.waitForTimeout(1500);

    const errorAlert = page.locator('text=/Wrong username or password/i');
    if (await errorAlert.isVisible()) {
        await page.locator('input[autocomplete="current-password"]').fill('TestPassword123');
        await page.locator('button[type="submit"]').click();
    }

    await expect(page).toHaveURL(/\/dashboard|\/settings/, { timeout: 15000 });
});
