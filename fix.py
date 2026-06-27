# PATH: fix.py
import os

path = "LLM_CONTEXT_ADDENDUM.md"

if not os.path.isfile(path):
    print(f"MISSING: {path} not found")
else:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    new_rule = """
---

## CRITICAL CLOUD DEBUGGING RULE (Added June 2026)
**RULE:** When debugging Authentication, Credential mismatches, or Database Seeding failures in a Cloud Environment (Render/Neon), **ALWAYS verify the live Environment Variables FIRST.** 
Never assume a Spring Boot framework bug, Hibernate caching issue, or write complex code workarounds until you have explicitly confirmed that the Cloud Environment is not injecting unexpected variables (e.g., `ADMIN_DEFAULT_PASSWORD`).
"""

    if "CRITICAL CLOUD DEBUGGING RULE" not in content:
        content += new_rule
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print("OK: Permanent cloud debugging rule added to LLM_CONTEXT_ADDENDUM.md")
    else:
        print("SKIP: Rule already exists in LLM_CONTEXT_ADDENDUM.md")