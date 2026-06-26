import os
import json
import shutil

def delete_file(path):
    if os.path.isfile(path):
        os.remove(path)
        print(f"OK: Deleted file {path}")
    else:
        print(f"SKIP: File not found {path}")

def delete_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
        print(f"OK: Deleted directory {path}")
    else:
        print(f"SKIP: Directory not found {path}")

# 1. Delete playwright.config.js
delete_file("erp-frontend/playwright.config.js")

# 2. Delete tests directory
delete_dir("erp-frontend/tests")

# 3. Delete test-results directory
delete_dir("erp-frontend/test-results")

# 4 & 5. Update package.json
pkg_path = "erp-frontend/package.json"
if not os.path.isfile(pkg_path):
    print(f"MISSING: {pkg_path} not found")
else:
    with open(pkg_path, "r", encoding="utf-8", errors="replace") as f:
        pkg = json.load(f)

    # Remove @playwright/test from devDependencies
    dev_deps = pkg.get("devDependencies", {})
    if "@playwright/test" in dev_deps:
        del dev_deps["@playwright/test"]
        print("OK: Removed @playwright/test from devDependencies")
    else:
        print("SKIP: @playwright/test not found in devDependencies")
    pkg["devDependencies"] = dev_deps

    # Remove scripts starting with "test:"
    scripts = pkg.get("scripts", {})
    keys_to_remove = [k for k in scripts if k.startswith("test:")]
    for k in keys_to_remove:
        del scripts[k]
        print(f"OK: Removed script '{k}'")
    if not keys_to_remove:
        print("SKIP: No test: scripts found")
    pkg["scripts"] = scripts

    with open(pkg_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pkg, f, indent=2)
        f.write("\n")
    print(f"OK: Updated {pkg_path}")