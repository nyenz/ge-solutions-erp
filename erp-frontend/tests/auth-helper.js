// PATH: erp-frontend/tests/auth-helper.js
// Shared helper used by all spec files.
// Uses the saved storage state so no login needed per test.

export const OFFICIAL_PASS = "GoldenSeed2024!";
export const USERNAME      = "admin_root";
export const BASE_URL      = "http://localhost:5173";

/**
 * Navigate to a page as the already-authenticated admin.
 * Storage state is injected at the project level in playwright.config.js
 * so the browser context is already logged in.
 */
export async function goTo(page, path) {
    await page.goto(BASE_URL + path);
}
