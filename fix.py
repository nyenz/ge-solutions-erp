import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
    else:
        print(f"MISSING (not found): {path}")

# ================================================================
# FIX 1: Increase axios timeout from 15000ms to 60000ms
# The Render free tier takes up to 50 seconds to wake from sleep.
# 15 seconds is not enough -- increase to 60 seconds.
# ================================================================

patch(
    'erp-frontend/src/api/axios.js',
    'timeout: 15000,',
    'timeout: 60000,'
)

# ================================================================
# FIX 2: Show a friendly error message on the login page
# Instead of the raw "timeout of 60000ms exceeded" error,
# show a plain English message the user can understand.
# ================================================================

patch(
    'erp-frontend/src/services/authService.js',
    'throw new Error(error.message || "COMMUNICATION_FAULT");',
    '\n'.join([
        "            // Check if it was a timeout (server waking up on Render free tier)",
        "            if (error.code === 'ECONNABORTED' || (error.message && error.message.toLowerCase().includes('timeout'))) {",
        "                throw new Error('SERVER_STARTING_UP');",
        "            }",
        '            throw new Error(error.message || "COMMUNICATION_FAULT");',
    ])
)

patch(
    'erp-frontend/src/pages/login/LoginPage.jsx',
    'setError(err.message === "IDENTIFICATION_FAILED" ? "WRONG CREDENTIALS" : err.message);',
    '\n'.join([
        "            let msg = err.message;",
        '            if (msg === "IDENTIFICATION_FAILED") msg = "Wrong username or password. Please try again.";',
        '            else if (msg === "ACCOUNT_SUSPENDED") msg = "This account has been suspended. Contact the admin.";',
        '            else if (msg === "SERVER_STARTING_UP") msg = "The server is waking up (this takes up to 60 seconds on the free plan). Please wait a moment and try again.";',
        '            else msg = "Could not connect to the server. Please check your internet and try again.";',
        "            setError(msg);",
    ])
)

print("\nAll fixes applied!")
print("Now run: git add -A && git commit -m 'fix: increase timeout, friendlier login errors' && git push")