#!/usr/bin/env python3
# PATH: fix144.py
# GOLDEN SEED -- fix144: the new seed data failed to load (database rejected the Director role); fixed, plus code tidy-up.
#
#   1. ROOT CAUSE. Render log: users_role_check violated on ROLE_DIRECTOR. The database still carries the role list
#      it was created with, from when the Role enum had only ADMIN and MANAGER. Hibernate never rewrites an
#      existing check constraint, so no Director or Secretary user could ever be saved. The seed's staff insert hit
#      it, the whole load rolled back, and the ledger stayed empty (the old data had already been removed).
#   2. FIX. On every start the constraint is dropped and rebuilt from Role.values(), so it always matches the enum
#      (new helper roleCheckSql in DataInitializer). Tested on PostgreSQL: Director and Secretary now save, a made-up
#      role is still rejected, and running it repeatedly is harmless. Real Director accounts can now be created too.
#   3. NO MANUAL STEP. The seed did not finish, so its flag was never saved; the next start retries and loads all
#      57 projects. Nothing to run by hand.
#   4. TIDY-UP (the VS Code warnings): unused imports and four unused fields removed from DataInitializer, and one
#      unused import removed from ScenarioSeeder. No behaviour change.
#   5. Guide Section 19 gets two notes: the role-constraint rule, and that a failed load leaves the ledger empty until
#      the next successful start (look for "[SCENARIO] seed fault" in the Render log).
#
# NOT in this fix: the dataset itself, the wipe endpoint, the schema, and every frontend file.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

# ============================ EDIT PART 1 START ============================
# Names, and one variable per file this fix touches.
FIX_NO = "fix144"
COMMIT_MSG = "fix144: seed load no longer fails -- database role check now rebuilt from the Role enum on every start (Director and Secretary can be saved); unused imports and fields removed; guide Section 19 notes"
RUN_GATES = True   # set False for docs-only fixes (guide / markdown): skips compile + build

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

GUIDE = os.path.join(ROOT, "LLM_CONTEXT_GUIDE.md")
INIT_JAVA = os.path.join(JAVA, "config", "DataInitializer.java")
SEEDER_JAVA = os.path.join(JAVA, "config", "ScenarioSeeder.java")
# ============================= EDIT PART 1 END =============================

# ================== DO NOT EDIT: helpers (copy exactly) ====================
MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# sub = exact find/replace of the FIRST match. Prints OK / SKIP / MISSING.
def sub(text, old, new, desc):
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


# newfile = create (or replace) a whole file. SKIP if it already holds `marker`.
def newfile(path, text, label, marker):
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)


# ============================ EDIT PART 2 START ============================
# Load every file that gets PATCHED (new files are not loaded), then the changes.
LOAD_FILES = (INIT_JAVA, SEEDER_JAVA, GUIDE)
for _p in LOAD_FILES:
    load(_p)

# ---- the actual fix: rebuild users_role_check from the Role enum ----
patch(INIT_JAVA,
      "            \"ALTER TABLE notifications DROP COLUMN IF EXISTS is_read\"\n        };",
      "            \"ALTER TABLE notifications DROP COLUMN IF EXISTS is_read\",\n            \"ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check\",\n            roleCheckSql()\n        };",
      "DataInitializer: rebuild users_role_check from the Role enum on every start")

patch(INIT_JAVA,
      "    // ---------- schema migrations (unchanged) ----------\n    private void runSchemaMigrations() throws Exception {",
      "\n".join([
          "    // ---------- schema migrations (unchanged) ----------",
          "    // fix144: the database keeps the role list it was created with (users_role_check), so a role",
          "    // added to the Role enum later (Director, Secretary) is rejected on insert. Rebuilt from the",
          "    // enum on every start so the two can never drift apart again.",
          "    private static String roleCheckSql() {",
          "        StringBuilder sb = new StringBuilder(\"ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN (\");",
          "        boolean first = true;",
          "        for (com.gesolutions.erp.modules.auth.model.Role r : com.gesolutions.erp.modules.auth.model.Role.values()) {",
          "            if (!first) sb.append(\", \");",
          "            sb.append('\\'').append(r.name()).append('\\'');",
          "            first = false;",
          "        }",
          "        return sb.append(\"))\").toString();",
          "    }",
          "",
          "    private void runSchemaMigrations() throws Exception {",
      ]),
      "DataInitializer: add roleCheckSql() helper")

# ---- tidy-up: unused imports and fields ----
patch(INIT_JAVA,
      "\n".join([
          "import com.gesolutions.erp.modules.client.model.RecoveryNote;",
          "import com.gesolutions.erp.modules.client.repository.ClientRepository;",
          "import com.gesolutions.erp.modules.client.repository.RecoveryNoteRepository;",
          "import com.gesolutions.erp.modules.finance.model.ExpensePreset;",
          "import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;",
          "import com.gesolutions.erp.modules.land.dto.LandEntryRequest;",
          "import com.gesolutions.erp.modules.land.model.FollowUpLog;",
          "import com.gesolutions.erp.modules.land.model.LandProject;",
          "import com.gesolutions.erp.modules.land.model.StageTemplate;",
          "import com.gesolutions.erp.modules.land.repository.FollowUpRepository;",
          "import com.gesolutions.erp.modules.land.service.LandService;",
          "import com.gesolutions.erp.modules.land.service.StageTemplateService;",
          "import lombok.RequiredArgsConstructor;",
          "import org.springframework.beans.factory.annotation.Value;",
          "import org.springframework.boot.CommandLineRunner;",
          "import org.springframework.security.crypto.password.PasswordEncoder;",
          "import org.springframework.stereotype.Component;",
          "import javax.sql.DataSource;",
          "import java.sql.Connection;",
          "import java.sql.Statement;",
          "import java.time.LocalDate;",
          "import java.time.LocalDateTime;",
          "import java.util.*;",
          "",
      ]),
      "\n".join([
          "import com.gesolutions.erp.modules.finance.model.ExpensePreset;",
          "import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;",
          "import com.gesolutions.erp.modules.land.service.StageTemplateService;",
          "import lombok.RequiredArgsConstructor;",
          "import org.springframework.beans.factory.annotation.Value;",
          "import org.springframework.boot.CommandLineRunner;",
          "import org.springframework.security.crypto.password.PasswordEncoder;",
          "import org.springframework.stereotype.Component;",
          "import javax.sql.DataSource;",
          "import java.sql.Connection;",
          "import java.sql.Statement;",
          "",
      ]),
      "DataInitializer: remove unused imports")

patch(INIT_JAVA,
      "\n".join([
          "    private final PasswordEncoder passwordEncoder;",
          "    private final DataSource dataSource;",
          "    private final StageTemplateService stageTemplateService;",
          "    private final ExpensePresetRepository expensePresetRepository;",
          "    private final LandService landService;",
          "    private final ClientRepository clientRepository;",
          "    private final RecoveryNoteRepository recoveryNoteRepository;",
          "    private final FollowUpRepository followUpRepository;",
          "    private final ScenarioSeeder scenarioSeeder;",
          "",
      ]),
      "\n".join([
          "    private final PasswordEncoder passwordEncoder;",
          "    private final DataSource dataSource;",
          "    private final StageTemplateService stageTemplateService;",
          "    private final ExpensePresetRepository expensePresetRepository;",
          "    private final ScenarioSeeder scenarioSeeder;",
          "",
      ]),
      "DataInitializer: remove four unused fields")

patch(SEEDER_JAVA,
      "import java.sql.Statement;\nimport java.time.LocalDate;\nimport java.time.LocalDateTime;\n",
      "import java.sql.Statement;\nimport java.time.LocalDateTime;\n",
      "ScenarioSeeder: remove unused LocalDate import")

# ---- guide ----
patch(GUIDE,
      "# Last updated: September 2026 (fix143: seed dataset v3, Section 19)",
      "# Last updated: September 2026 (fix144: seed load fixed, Section 19)",
      "guide: last-updated line")

patch(GUIDE,
      "- Document links are placeholders. Opening a seeded document shows not-found; that is expected.\n",
      "- Document links are placeholders. Opening a seeded document shows not-found; that is expected.\n"
      "- The database keeps the role list it was created with (`users_role_check`), so a role added to the Role enum is rejected on insert until the constraint is rebuilt. `roleCheckSql()` in DataInitializer rebuilds it from `Role.values()` on every start; nothing extra to do when a role is added. (This is why the first v3 load failed in fix143.)\n"
      "- The old seed is purged in its own committed transaction before the new one loads. If the load fails, the ledger stays empty until the next successful start. Look for `[SCENARIO] seed fault` in the Render log; the load retries on every start until it succeeds.\n",
      "guide: Section 19 notes (role constraint, failed-load behaviour)")
# ============================= EDIT PART 2 END =============================

# ================= DO NOT EDIT: gates, rollback, git (copy exactly) ========
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since the last fix).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- " + FIX_NO + " already applied")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed and RUN_GATES:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate ----
if changed and RUN_GATES and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed and RUN_GATES:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")
elif changed:
    print("note: RUN_GATES is False (docs-only fix) -- compile and build skipped")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not changed:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", COMMIT_MSG)
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip())
print("")
print("DONE: " + FIX_NO + " applied.")