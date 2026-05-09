import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    dir_ = os.path.dirname(path)
    if dir_:
        os.makedirs(dir_, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING patch target in {path}")
        return
    write(path, content.replace(old, new, 1))


# ============================================================
# FIX 1: JwtAuthenticationFilter — add missing UserRepository import
# The package declaration is always at the top, use it as anchor
# ============================================================
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/config/JwtAuthenticationFilter.java",
    "package com.gesolutions.erp.config;",
    "package com.gesolutions.erp.config;\n\nimport com.gesolutions.erp.modules.auth.repository.UserRepository;"
)

# ============================================================
# FIX 2: FolderPage.jsx — fix broken regex on line 613
# /\/g is an unterminated string literal; should be /\\/g
# ============================================================
patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    "return `${base}/vault/` + rel.replace(/\\/g, '/');",
    "return `${base}/vault/` + rel.replace(/\\\\/g, '/');"
)

print("\n=== FIXES COMPLETE ===")
print("1. JwtAuthenticationFilter.java: UserRepository import added")
print("2. FolderPage.jsx: broken regex fixed (line 613)")
print("\nNow run: git add -A && git commit -m 'fix build errors' && git push")