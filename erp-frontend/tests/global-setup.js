// PATH: erp-frontend/tests/global-setup.js
// Runs ONCE before the entire test suite.
// Handles the mandatory password change and saves auth state to disk.

import { chromium } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL       = "http://localhost:5173";
const STORAGE_STATE  = path.join(__dirname, ".auth", "admin.json");
const USERNAME       = "admin_root";
const INITIAL_PASS   = "TestPassword123";    // the seeded default
const OFFICIAL_PASS  = "GoldenSeed2024!";    // the permanent test password

export default async function globalSetup() {
    // Ensure the .auth directory exists
    const authDir = path.join(__dirname, ".auth");
    if (!fs.existsSync(authDir)) fs.mkdirSync(authDir, { recursive: true });

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page    = await context.newPage();

    console.log("[setup] Navigating to login page...");
    await page.goto(BASE_URL + "/login");
    await page.waitForTimeout(1500);

    // --------------------------------------------------------
    // ATTEMPT 1: try the OFFICIAL password (may already be set)
    // --------------------------------------------------------
    console.log("[setup] Trying official password first...");
    await page.locator("input[autocomplete=\"username\"]").fill(USERNAME);
    await page.locator("input[autocomplete=\"current-password\"]").fill(OFFICIAL_PASS);
    await page.locator("button[type=\"submit\"]").click();

    try {
        await page.waitForURL(/\/dashboard|\/settings/, { timeout: 10000 });

        if (page.url().includes("/dashboard")) {
            // Official password already works -- we are done
            console.log("[setup] Official password works. Saving auth state...");
            await context.storageState({ path: STORAGE_STATE });
            await browser.close();
            return;
        }

        if (page.url().includes("/settings")) {
            // Official password works BUT mustChangePassword is still set
            // This means it was set to GoldenSeed2024! but flag not cleared
            // Fill the change form using official->official to clear the flag
            console.log("[setup] Settings page hit with official pass -- clearing mustChangePassword flag...");
            await fillPasswordChange(page, OFFICIAL_PASS, OFFICIAL_PASS);
            await page.waitForURL(/\/login/, { timeout: 15000 });
            // Now log back in
            await doLogin(page, USERNAME, OFFICIAL_PASS);
            await context.storageState({ path: STORAGE_STATE });
            await browser.close();
            return;
        }
    } catch (_) {
        // Official password failed -- try initial password
    }

    // --------------------------------------------------------
    // ATTEMPT 2: try the INITIAL seeded password
    // --------------------------------------------------------
    console.log("[setup] Official password failed. Trying initial password...");
    await page.goto(BASE_URL + "/login");
    await page.waitForTimeout(1200);

    await page.locator("input[autocomplete=\"username\"]").fill(USERNAME);
    await page.locator("input[autocomplete=\"current-password\"]").fill(INITIAL_PASS);
    await page.locator("button[type=\"submit\"]").click();

    await page.waitForURL(/\/dashboard|\/settings/, { timeout: 15000 });

    if (page.url().includes("/settings")) {
        // MANDATORY PASSWORD CHANGE -- fill form
        console.log("[setup] Mandatory password change detected. Resetting to official password...");
        await fillPasswordChange(page, INITIAL_PASS, OFFICIAL_PASS);

        // Wait for redirect back to /login
        await page.waitForURL(/\/login/, { timeout: 20000 });
        console.log("[setup] Password changed. Logging in with official password...");
        await page.waitForTimeout(1200);
        await doLogin(page, USERNAME, OFFICIAL_PASS);
    }

    // Save auth state
    console.log("[setup] Saving auth state to:", STORAGE_STATE);
    await context.storageState({ path: STORAGE_STATE });
    await browser.close();
    console.log("[setup] Auth state saved. All tests will use this session.");
}

// --------------------------------------------------------
// Fill the settings page password change form
// --------------------------------------------------------
async function fillPasswordChange(page, currentPass, newPass) {
    // Wait for the settings form to be ready
    await page.waitForSelector("text=/CURRENT MASTER KEY|OPERATOR SECURITY/i", { timeout: 10000 });

    // Current password field (label contains "CURRENT MASTER KEY")
    const currentInput = page.locator("div:has-text(\"CURRENT MASTER KEY\")").locator("input").first();
    const newInput     = page.locator("div:has-text(\"NEW HARDWARE KEY\")").locator("input").first();
    const confirmInput = page.locator("div:has-text(\"CONFIRM CONFIGURATION\")").locator("input").first();

    await currentInput.fill(currentPass);
    await newInput.fill(newPass);
    await confirmInput.fill(newPass);

    // Click the submit button
    const submitBtn = page.locator("button:has-text(\"REWRITE HARDWARE KEY\")");
    await submitBtn.click();
}

// --------------------------------------------------------
// Log in with given credentials, expect /dashboard
// --------------------------------------------------------
async function doLogin(page, username, password) {
    await page.locator("input[autocomplete=\"username\"]").fill(username);
    await page.locator("input[autocomplete=\"current-password\"]").fill(password);
    await page.locator("button[type=\"submit\"]").click();
    await page.waitForURL(/\/dashboard/, { timeout: 15000 });
    console.log("[setup] Logged in successfully. URL:", page.url());
}
