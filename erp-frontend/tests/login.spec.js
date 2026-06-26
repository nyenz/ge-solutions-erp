// PATH: erp-frontend/tests/login.spec.js
// Tests the login page mechanics. Runs WITHOUT stored auth state.
import { test, expect } from "@playwright/test";

const OFFICIAL_PASS = "GoldenSeed2024!";
const INITIAL_PASS  = "TestPassword123";

// ---------------------------------------------------------------------------
// TEST 1: Successful login with official password
// ---------------------------------------------------------------------------
test("should log in with the official password and reach dashboard", async ({ page }) => {
    await page.goto("http://localhost:5173/login");
    await page.waitForTimeout(1200);

    // Login page should show
    await expect(page.locator("text=/Golden Seed|Enterprise Portal/i").first()).toBeVisible({ timeout: 10000 });

    await page.locator("input[autocomplete=\"username\"]").fill("admin_root");
    await page.locator("input[autocomplete=\"current-password\"]").fill(OFFICIAL_PASS);
    await page.locator("button[type=\"submit\"]").click();

    // Should reach dashboard (password already set by global-setup)
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
});

// ---------------------------------------------------------------------------
// TEST 2: Wrong password shows error, stays on login
// ---------------------------------------------------------------------------
test("should show error on wrong password", async ({ page }) => {
    await page.goto("http://localhost:5173/login");
    await page.waitForTimeout(1200);

    await page.locator("input[autocomplete=\"username\"]").fill("admin_root");
    await page.locator("input[autocomplete=\"current-password\"]").fill("DEFINITELY_WRONG_XYZ_999");
    await page.locator("button[type=\"submit\"]").click();

    // Wait for response
    await page.waitForTimeout(4000);

    // Must still be on login
    expect(page.url()).toContain("/login");

    // Error message visible
    const errorEl = page.locator("[class*=\"errorAlert\"], [role=\"alert\"]").first();
    await expect(errorEl).toBeVisible({ timeout: 5000 });
});

// ---------------------------------------------------------------------------
// TEST 3: Password visibility toggle
// ---------------------------------------------------------------------------
test("should toggle password visibility", async ({ page }) => {
    await page.goto("http://localhost:5173/login");
    await page.waitForTimeout(1200);

    const passwordInput = page.locator("input[autocomplete=\"current-password\"]");
    await passwordInput.fill("TestVisible123");

    // Default hidden
    await expect(passwordInput).toHaveAttribute("type", "password");

    // Click eye button
    const eyeBtn = page.locator(".eyeBtn").first();
    if (await eyeBtn.isVisible()) {
        await eyeBtn.click();
        await expect(passwordInput).toHaveAttribute("type", "text");

        // Toggle back
        await eyeBtn.click();
        await expect(passwordInput).toHaveAttribute("type", "password");
    }
});

// ---------------------------------------------------------------------------
// TEST 4: Unauthenticated user redirected from protected route
// ---------------------------------------------------------------------------
test("should redirect unauthenticated user to login from protected route", async ({ page }) => {
    // Clear any stored state by going directly -- fresh context has no token
    await page.goto("http://localhost:5173/dashboard");
    await page.waitForTimeout(2000);
    // Should end up on /login
    expect(page.url()).toContain("/login");
});
