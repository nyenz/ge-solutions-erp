# PATH: fix.py
import os

def patch(path, old, new, label):
    if not os.path.isfile(path):
        print(f"MISSING: {path}")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: {label}")
    elif new in content:
        print(f"SKIP (already applied): {label}")
    else:
        print(f"FAIL: {label}")

# ── 1. PATCH BACKEND MATH (LoginRateLimiter.java) ──
LIMITER_PATH = "erp-backend/src/main/java/com/gesolutions/erp/config/LoginRateLimiter.java"
OLD_LIMITER = "private static final long BLOCK_SECONDS = 15 * 60; // 15 minutes"
NEW_LIMITER = "private static final long BLOCK_SECONDS = 10 * 60; // 10 minutes"
patch(LIMITER_PATH, OLD_LIMITER, NEW_LIMITER, "PATCH 1/3: LoginRateLimiter.java -> 10 minutes")

# ── 2. PATCH BACKEND PAYLOAD (AuthController.java) ──
AUTH_CTRL_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/controller/AuthController.java"
OLD_AUTH_CTRL = "throw new BusinessException(\"TOO_MANY_ATTEMPTS: Account locked for 15 minutes. Try again later.\");"
NEW_AUTH_CTRL = "throw new BusinessException(\"TOO_MANY_ATTEMPTS: Account locked for 10 minutes. Try again later.\");"
patch(AUTH_CTRL_PATH, OLD_AUTH_CTRL, NEW_AUTH_CTRL, "PATCH 2/3: AuthController.java -> 10 minutes")

# ── 3. PATCH FRONTEND UI (LoginPage.jsx) ──
LOGIN_PAGE_PATH = "erp-frontend/src/pages/login/LoginPage.jsx"
OLD_LOGIN_UI = "msg = \"Account locked for 15 minutes due to too many failed attempts. Try again later.\";"
NEW_LOGIN_UI = "msg = \"Account locked for 10 minutes due to too many failed attempts. Try again later.\";"
patch(LOGIN_PAGE_PATH, OLD_LOGIN_UI, NEW_LOGIN_UI, "PATCH 3/3: LoginPage.jsx -> 10 minutes")