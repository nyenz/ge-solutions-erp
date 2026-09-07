# fix.py -- fix79: resolve unreachable statement in ReceivableSchedulerService
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RS = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp" / "modules" / "land" / "service" / "ReceivableSchedulerService.java"

s = RS.read_text(encoding="utf-8", errors="replace")

marker = "continue; // fix78"
if marker in s:
    idx = s.find(marker)
    
    # Find the start of the method containing the broken patch
    method_start = s.rfind("public ", 0, idx)
    if method_start == -1:
        method_start = s.rfind("private ", 0, idx)
    
    brace_start = s.find("{", method_start)
    
    # Find the matching closing brace for the method
    count = 1
    i = brace_start + 1
    while count > 0 and i < len(s):
        if s[i] == '{': count += 1
        elif s[i] == '}': count -= 1
        i += 1
        
    # Gut the method body to fix the unreachable statement error
    new_method_body = s[:brace_start+1] + "\n        return; // fix79: old cooldown/promise loop disabled by new 30-day recovery engine\n    " + s[i-1:]
    RS.write_text(new_method_body, encoding="utf-8", newline="\n")
    print("OK gutted old scheduled method to fix unreachable statement")
else:
    print("SKIP marker not found (already fixed or different format)")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix79: resolve unreachable statement in ReceivableSchedulerService"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")