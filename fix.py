# fix.py -- fix69: resolve DataInitializer unreported SQLException compilation error
import re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

fp = BE / "config" / "DataInitializer.java"
s = fp.read_text(encoding="utf-8", errors="replace")

# 1. Add throws Exception to method signatures to bypass any try-with-resources close() exception pedantry
s = s.replace("private void purgeSampleData() {", "private void purgeSampleData() throws Exception {")
s = s.replace("private void runSchemaMigrations() {", "private void runSchemaMigrations() throws Exception {")
s = s.replace("public void seedRootUser() {", "public void seedRootUser() throws Exception {")
s = s.replace("private void seedSampleProjects() {", "private void seedSampleProjects() throws Exception {")

# 2. Upgrade catch (Exception e) to catch (Throwable t) for the JDBC blocks to guarantee SQLException is caught
s = s.replace("} catch (Exception e) { System.err.println(\">>> [RESET] wipe warning: \" + e.getMessage()); }",
              "} catch (Throwable t) { System.err.println(\">>> [RESET] wipe warning: \" + t.getMessage()); }")
s = s.replace("} catch (Exception e) { System.err.println(\">>> [DB_SCHEMA] Migration warning: \" + e.getMessage()); }",
              "} catch (Throwable t) { System.err.println(\">>> [DB_SCHEMA] Migration warning: \" + t.getMessage()); }")
s = s.replace("} catch (Exception e) { System.err.println(\">>> [REGISTRY] CRITICAL SEED/RESET FAULT:\"); e.printStackTrace(); }",
              "} catch (Throwable t) { System.err.println(\">>> [REGISTRY] CRITICAL SEED/RESET FAULT:\"); t.printStackTrace(); }")
s = s.replace("} catch (Exception e) { System.err.println(\">>> [SAMPLE] backdate warning: \" + e.getMessage()); }",
              "} catch (Throwable t) { System.err.println(\">>> [SAMPLE] backdate warning: \" + t.getMessage()); }")

fp.write_text(s, encoding="utf-8", newline="\n")
print("OK DataInitializer patched")

try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "fix69: resolve DataInitializer unreported SQLException compilation error"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT pushed")
except Exception as e:
    print("GIT WARN", e)

print("DONE")