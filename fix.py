# PATH: fix_stage14.py  (STAGE 14)
# STAGE 14 -- remove the /api/v1/vault/** route (suggestion #4, deferred from Stage 13)
# Run from project root: py fix_stage14.py
#
# Stage 13 deliberately skipped this because FolderPage.jsx's getDocUrl() falls
# back to building a /vault/... URL for any document whose stored file_path
# ISN'T already a full http(s) URL -- i.e. an old, pre-Cloudinary local path.
# There was no way to tell from the code alone whether any such rows still
# existed in the live database.
#
# David ran the check directly against the live Neon database:
#   SELECT COUNT(*) FROM project_documents WHERE file_path NOT LIKE 'http%';
# Result: 0. Every document row already stores a full Cloudinary URL, so the
# /vault/ fallback in getDocUrl() is confirmed dead code with nothing behind
# it, and the route it points at is safe to remove entirely.
#
# What this does:
# 1. Deletes WebConfig.java -- its only job was mapping /api/v1/vault/** to
#    a local "ge_uploads" folder that nothing ever writes to (confirmed in
#    the Stage 13 investigation: zero writers anywhere in the codebase).
# 2. Removes the ".requestMatchers("/api/v1/vault/**").permitAll()" line from
#    SecurityConfig.java -- this was the one publicly-unauthenticated route
#    in the whole app; removing the resource handler alone would just 404
#    requests to it, but removing the permitAll rule too means an unmatched
#    /api/v1/vault/** request now correctly falls through to
#    ".anyRequest().authenticated()" and gets a clean 401 instead of being
#    treated as public.
# 3. Leaves getDocUrl() in FolderPage.jsx untouched. Its fallback branch is
#    now unreachable in practice (every real file_path is a full URL), but
#    deleting it isn't necessary for this fix and isn't worth the risk of
#    touching a 1900-line file for a branch that costs nothing to leave in.
#    Flagging it here in case a future session wants to clean it up too.

import os

ROOT = os.path.dirname(os.path.abspath(__file__))
results = []


def patch(label, rel_path, old, new):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print("[STAGE 14] " + label + " ... MISSING (file not found: " + rel_path + ")")
        results.append(False)
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if new in content:
        print("[STAGE 14] " + label + " ... OK (already applied)")
        results.append(True)
        return

    if old not in content:
        print("[STAGE 14] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        results.append(False)
        return

    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("[STAGE 14] " + label + " ... OK")
    results.append(True)


def delete_file(label, rel_path):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print("[STAGE 14] " + label + " ... OK (already deleted)")
        results.append(True)
        return
    os.remove(path)
    print("[STAGE 14] " + label + " ... OK (deleted)")
    results.append(True)


# ── 1. Delete WebConfig.java (the /vault resource-handler mapping) ─────────
delete_file(
    "Delete WebConfig.java (mapped /api/v1/vault/** to a local folder nothing writes to)",
    "erp-backend/src/main/java/com/gesolutions/erp/config/WebConfig.java",
)

# ── 2. Remove the public permitAll rule for /vault ──────────────────────────
patch(
    "SecurityConfig.java: remove permitAll for /api/v1/vault/** (route no longer exists)",
    "erp-backend/src/main/java/com/gesolutions/erp/config/SecurityConfig.java",
    "                        .requestMatchers(HttpMethod.OPTIONS, \"/**\").permitAll()\n"
    "                        .requestMatchers(\"/api/v1/auth/**\").permitAll()\n"
    "                        .requestMatchers(\"/api/v1/vault/**\").permitAll()\n"
    "                        .anyRequest().authenticated()\n",
    "                        .requestMatchers(HttpMethod.OPTIONS, \"/**\").permitAll()\n"
    "                        .requestMatchers(\"/api/v1/auth/**\").permitAll()\n"
    "                        .anyRequest().authenticated()\n",
)

print("")
if all(results):
    print("All Stage 14 patches applied cleanly.")
else:
    print("Some patches were MISSING -- review output above before committing.")