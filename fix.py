import os

path = "erp-frontend/playwright.config.js"

content = """\
// PATH: erp-frontend/playwright.config.js
import { defineConfig, devices } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

const BASE_URL = "http://localhost:5173";
const STORAGE_STATE = path.join(__dirname, "tests/.auth/admin.json");

export default defineConfig({
    testDir: "./tests",
    fullyParallel: false,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 1,
    workers: 1,
    reporter: [["list"], ["html", { open: "never" }]],
    timeout: 60000,

    globalSetup: "./tests/global-setup.js",

    use: {
        baseURL: BASE_URL,
        trace: "on-first-retry",
        screenshot: "only-on-failure",
        video: "retain-on-failure",
        actionTimeout: 15000,
        navigationTimeout: 30000,
    },

    projects: [
        // All tests use saved admin auth state -- no per-test login needed
        {
            name: "chromium-admin",
            use: {
                ...devices["Desktop Chrome"],
                headless: false, // Set to false to watch the ghost mouse
                viewport: { width: 1280, height: 900 },
                storageState: STORAGE_STATE,
            },
            testMatch: [
                "tests/dashboard.spec.js",
                "tests/intake.spec.js",
                "tests/ledger.spec.js",
                "tests/folder.spec.js",
                "tests/recovery.spec.js",
                "tests/payments.spec.js",
                "tests/audit.spec.js",
                "tests/reports.spec.js",
                "tests/settings.spec.js",
            ],
        },
        // Login tests run WITHOUT stored state (they test the login flow itself)
        {
            name: "chromium-login",
            use: {
                ...devices["Desktop Chrome"],
                headless: false,
                viewport: { width: 1280, height: 900 },
                // No storageState -- fresh browser
            },
            testMatch: ["tests/login.spec.js"],
        },
    ],

    webServer: {
        command: "npm run dev",
        url: "http://localhost:5173",
        reuseExistingServer: true,
        timeout: 120000,
        env: {
            VITE_API_BASE_URL: 'http://localhost:8080/api/v1'
        }
    },
});
"""

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)
print("OK: playwright.config.js fixed (BASE_URL moved to top + VITE_API_BASE_URL restored)")