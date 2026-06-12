import os

# ── PATCH 1: application.properties — fix server port ──────────────
props_path = 'erp-backend/src/main/resources/application.properties'

with open(props_path, 'r', encoding='utf-8', errors='replace') as f:
    props_content = f.read()

if 'server.port=10000' in props_content:
    props_content = props_content.replace('server.port=10000', 'server.port=8080')
    with open(props_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(props_content)
    print('OK  ' + props_path + ' — server.port set to 8080')
elif 'server.port=8080' in props_content:
    print('OK  ' + props_path + ' — server.port already 8080, no change needed')
else:
    print('MISSING  server.port line not found in ' + props_path)

# ── PATCH 2: login.spec.js — fix credentials ────────────────────────
spec_path = 'erp-frontend/tests/login.spec.js'

with open(spec_path, 'r', encoding='utf-8', errors='replace') as f:
    spec_content = f.read()

patched = spec_content

if "await usernameInput.fill('admin');" in patched:
    patched = patched.replace(
        "await usernameInput.fill('admin');",
        "await usernameInput.fill('admin_root');"
    )
    print('OK  ' + spec_path + ' — username patched to admin_root')
elif "await usernameInput.fill('admin_root');" in patched:
    print('OK  ' + spec_path + ' — username already admin_root, no change needed')
else:
    print('MISSING  username fill line not found in ' + spec_path)

if "await passwordInput.fill('admin123');" in patched:
    patched = patched.replace(
        "await passwordInput.fill('admin123');",
        "await passwordInput.fill('TestPassword123');"
    )
    print('OK  ' + spec_path + ' — password patched to TestPassword123')
elif "await passwordInput.fill('TestPassword123');" in patched:
    print('OK  ' + spec_path + ' — password already TestPassword123, no change needed')
else:
    print('MISSING  password fill line not found in ' + spec_path)

if patched != spec_content:
    with open(spec_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(patched)
    print('OK  ' + spec_path + ' — file written')