import os

path = "erp-backend/src/test/java/com/gesolutions/erp/config/SingleSessionEnforcementTest.java"

old = "                .andExpect(status().isUnauthorized());"
new = "                .andExpect(status().isForbidden());"

with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: Patched Step 3 assertion to isForbidden() in " + path)
else:
    print("MISSING: patch target not found in " + path)