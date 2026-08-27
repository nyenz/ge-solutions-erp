#!/usr/bin/env python3
"""
fix9.py — attach sample DOCUMENTS to the auto-seeded SAMPLE projects.
The seed (fix8) created projects with no scans (atomicIntake(..., null)),
so Folder pages showed "NO DOCUMENTS ATTACHED". This backfills 2 sample
docs per SAMPLE project (public sample PDFs so View opens a real file).
Idempotent: only inserts where a project has 0 documents.
Run: py fix9.py
"""
import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
WROTE, FAILED = [], []

def patch(rel, old, new, count=1):
    p = ROOT / rel
    try: text = p.read_text(encoding="utf-8")
    except Exception as e: FAILED.append((rel, "read: " + str(e))); return
    if text.count(old) < 1:
        FAILED.append((rel, "ANCHOR NOT FOUND: " + old[:70].replace("\n", "\\n"))); return
    text = text.replace(old, new, count)
    try: p.write_text(text, encoding="utf-8"); WROTE.append(rel + " (patched)")
    except Exception as e: FAILED.append((rel, str(e)))

# 1) call the new seeder from run()
patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""        seedSampleProjects();
        seedDefaultExpensePresets();""",
"""        seedSampleProjects();
        seedSampleDocuments();
        seedDefaultExpensePresets();""")

# 2) add the seeder method (raw JDBC, matches project_documents schema:
#    id, project_id, file_name, file_type, file_path, internal_notes,
#    uploaded_by, uploaded_at)
patch("erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
"""        b.selectedStages(ss);
        LandProject saved = landService.atomicIntake(b.build(), null);
        return saved.getId();
    }""",
"""        b.selectedStages(ss);
        LandProject saved = landService.atomicIntake(b.build(), null);
        return saved.getId();
    }

    // PASS 6b: attach 2 sample documents to every SAMPLE project that has
    // none yet. Independent guard (per-project doc count) so it also
    // backfills projects seeded by an earlier deploy, and never duplicates.
    // Uses public sample PDFs so the Folder page "View" opens a real file.
    private void seedSampleDocuments() {
        String[][] docs = {
            { "SAMPLE_DEED_PLAN.pdf",  "DEED_PLAN",  "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf" },
            { "SAMPLE_TITLE_CERT.pdf", "TITLE_CERT", "https://unec.edu.az/application/uploads/2014/12/pdf-sample.pdf" },
        };
        try (java.sql.Connection conn = dataSource.getConnection();
             java.sql.PreparedStatement ps = conn.prepareStatement(
                "SELECT id FROM land_projects WHERE district = 'SAMPLE DATA'")) {
            int attached = 0;
            try (java.sql.ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    Object pid = rs.getObject(1);
                    try (java.sql.PreparedStatement c = conn.prepareStatement(
                            "SELECT COUNT(*) FROM project_documents WHERE project_id = ?")) {
                        c.setObject(1, pid);
                        try (java.sql.ResultSet crs = c.executeQuery()) {
                            if (crs.next() && crs.getInt(1) > 0) continue;
                        }
                    }
                    for (String[] d : docs) {
                        try (java.sql.PreparedStatement ins = conn.prepareStatement(
                                "INSERT INTO project_documents (id, project_id, file_name, file_type, file_path, uploaded_by, uploaded_at) VALUES (?,?,?,?,?,?,?)")) {
                            ins.setObject(1, java.util.UUID.randomUUID());
                            ins.setObject(2, pid);
                            ins.setString(3, d[0]);
                            ins.setString(4, d[1]);
                            ins.setString(5, d[2]);
                            ins.setString(6, "SYSTEM");
                            ins.setTimestamp(7, java.sql.Timestamp.valueOf(java.time.LocalDateTime.now()));
                            ins.executeUpdate();
                        }
                    }
                    attached++;
                }
            }
            System.out.println(">>> [SAMPLE] Documents attached to " + attached + " sample project(s).");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] document seed failed (non-fatal): " + e.getMessage());
        }
    }""")

# =====================================================================
print(f"\n=== fix9.py completed ===")
print(f"  Wrote:   {len(WROTE)} file(s)")
for f in WROTE: print(f"    + {f}")
if FAILED:
    print(f"  FAILED:  {len(FAILED)}")
    for f, e in FAILED: print(f"    ! {f} -> {e}")
    sys.exit(1)

if WROTE:
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix9: backfill 2 sample documents (DEED_PLAN + TITLE_CERT) onto SAMPLE projects'], check=True, cwd=ROOT, capture_output=True)
        print("\n  Git: Committed")
        subprocess.run(['git', 'push'], check=True, cwd=ROOT, capture_output=True)
        print("  Git: Pushed")
    except subprocess.CalledProcessError as e:
        print(f"\n  Git: failed (exit {e.returncode})")
    except FileNotFoundError:
        print("\n  Git: not found")
print()