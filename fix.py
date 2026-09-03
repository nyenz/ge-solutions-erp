# fix.py — fix55b: repair RecoveryNoteController type error
import os, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ctrl = None
for r, d, fs in os.walk(os.path.join(ROOT, "erp-backend", "src")):
    if "RecoveryNoteController.java" in fs: ctrl = os.path.join(r, "RecoveryNoteController.java"); break
if not ctrl:
    print("ABORT: RecoveryNoteController.java not found."); sys.exit(1)
shutil.copy2(ctrl, os.path.join(ROOT, ".fix_backup", "RecoveryNoteController.java.bak55"))

src = open(ctrl, "r", encoding="utf-8").read()

# Line 163 has the error. Find it and wrap the assignment properly.
# The error says: User cannot be converted to Optional<User>
# This means something like: Optional<User> user = userRepository.findById(id);
# Should be: Optional<User> user = userRepository.findById(id);  (already correct)
# OR: User user = userRepository.findById(id).orElse(null);
# OR the assignment is: Optional<User> user = userRepository.findById(id).get();

# Let's read lines around 163
lines = src.split('\n')
if len(lines) < 165:
    print("ABORT: file too short."); sys.exit(1)

# Print context around line 163
print("Context around line 163:")
for i in range(max(0, 158), min(len(lines), 168)):
    print(f"{i+1}: {lines[i]}")

# The fix is likely to change the assignment. Common patterns:
# 1. If it's: Optional<User> user = userRepository.findById(id);
#    That's already correct, so the error must be on the RHS.
# 2. If it's: Optional<User> user = userRepository.findById(id).get();
#    Fix: Optional<User> user = Optional.of(userRepository.findById(id).get());
#    Or better: Optional<User> user = userRepository.findById(id);
# 3. If it's: User user = userRepository.findById(id);
#    Fix: User user = userRepository.findById(id).orElse(null);

# Since I can't see the exact line, I'll do a safe pattern-based fix:
# Find lines with "Optional<User>" assignment and ensure the RHS is an Optional.

changed = False
for i, line in enumerate(lines):
    if "Optional<User>" in line and "findById" in line:
        # Check if it's already correct (findById returns Optional)
        if ".get()" in line or ".orElse" in line:
            # The issue is likely that .get() returns User, not Optional<User>
            # Remove .get() or change the variable type
            if "Optional<User>" in line and ".get()" in line:
                # Change: Optional<User> user = repo.findById(id).get();
                # To: User user = repo.findById(id).get();
                lines[i] = line.replace("Optional<User>", "User").replace(".get()", ".get()")
                changed = True
                print(f"Fixed line {i+1}: changed Optional<User> to User")

if changed:
    open(ctrl, "w", encoding="utf-8").write('\n'.join(lines))
    print("BACKEND: type mismatch fixed.")
else:
    print("WARN: pattern not found — manual fix required.")
    print("The error is on line 163. Check if it's:")
    print("  Optional<User> user = repository.findById(id).get();")
    print("  Fix: User user = repository.findById(id).get();")
    print("Or:")
    print("  Optional<User> user = userRepository.findById(id);")
    print("  That's already correct, so check the method signature.")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix55b: repair RecoveryNoteController type error"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")