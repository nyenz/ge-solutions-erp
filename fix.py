#!/usr/bin/env python3
"""fix20.py — repair FolderPage duplicate import + make sample purge FK-safe.
Run: py fix20.py"""
import re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
DONE = []

# ----------------------------------------------------------------------
# 1) FolderPage.jsx — de-dupe BackToTopButton import/usage, add sidebar collapse
# ----------------------------------------------------------------------
p = ROOT / 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
t = p.read_text(encoding='utf-8')
lines = t.split('\n'); out = []; seenImp = False; seenUse = False
for ln in lines:
    if ln.strip().startswith('import BackToTopButton'):
        if seenImp: continue
        seenImp = True
    if '<BackToTopButton />' in ln:
        if seenUse: continue
        seenUse = True
    out.append(ln)
t = '\n'.join(out)
if 'import BackToTopButton' not in t:
    t = t.replace("import modalStyles from '../../components/common/HardwareModal.module.css';",
                  "import modalStyles from '../../components/common/HardwareModal.module.css';\nimport BackToTopButton from '../../components/common/BackToTopButton';", 1)
if '<BackToTopButton />' not in t:
    t = t.replace("</HardwareModal>\n</div>\n);\n};\n\nexport default FolderPage;",
                  "</HardwareModal>\n<BackToTopButton />\n</div>\n);\n};\n\nexport default FolderPage;", 1)
if 'sidebarToggle' not in t:
    t = re.sub(r"(const fileInputRef\s*=\s*useRef\(null\);)",
        r"""\1

// STANDARD: sidebar auto-collapses when the folder page is opened
useEffect(() => {
    const t = setTimeout(() => {
        const aside = document.querySelector('aside');
        const toggle = document.querySelector('[class*="sidebarToggle"]');
        if (aside && toggle && aside.getBoundingClientRect().width > 120) toggle.click();
    }, 150);
    return () => clearTimeout(t);
}, []);""", t, count=1)
p.write_text(t, encoding='utf-8'); DONE.append('FolderPage.jsx (deduped + sidebar standard)')

# ----------------------------------------------------------------------
# 2) DataInitializer.java — FK-safe, loud purge so re-seeds never collide
# ----------------------------------------------------------------------
p = ROOT / 'erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java'
t = p.read_text(encoding='utf-8')
OLD = '''    private void purgeSampleData() {
        String[] stmts = {
            "DELETE FROM payment_records WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM follow_up_logs WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_stages WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_proprietors WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM land_projects WHERE district = 'SAMPLE DATA'",
            "DELETE FROM land_titles WHERE plot_number LIKE 'SAMPLE-%'",
            "DELETE FROM clients WHERE national_id LIKE 'SMPL-%'",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) { try { st.execute(s); } catch (Exception ignore) {} }
            System.out.println(">>> [SAMPLE] Old sample data purged.");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] purge warning: " + e.getMessage());
        }
    }'''
NEW = '''    private void purgeSampleData() {
        // FK-safe order: detach sample titles from any project FIRST so the
        // land_titles delete can never hit an FK violation (the bug that left
        // orphan SAMPLE-1xx titles blocking every re-seed).
        String[] stmts = {
            "DELETE FROM payment_records WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM follow_up_logs WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_stages WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "DELETE FROM project_proprietors WHERE project_id IN (SELECT id FROM land_projects WHERE district = 'SAMPLE DATA')",
            "UPDATE land_projects SET title_id = NULL WHERE title_id IN (SELECT id FROM land_titles WHERE plot_number LIKE 'SAMPLE-%' OR title_id LIKE 'SMPL-T-%')",
            "DELETE FROM land_projects WHERE district = 'SAMPLE DATA'",
            "DELETE FROM land_titles WHERE plot_number LIKE 'SAMPLE-%' OR title_id LIKE 'SMPL-T-%'",
            "DELETE FROM clients WHERE national_id LIKE 'SMPL-%'",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) {
                try { st.execute(s); }
                catch (Exception e) { System.err.println(">>> [SAMPLE] purge stmt failed: " + s.substring(0, 40) + " -> " + e.getMessage()); }
            }
            System.out.println(">>> [SAMPLE] Old sample data purged.");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] purge warning: " + e.getMessage());
        }
    }'''
if OLD in t:
    t = t.replace(OLD, NEW, 1); p.write_text(t, encoding='utf-8'); DONE.append('DataInitializer.java (FK-safe purge)')
elif 'title_id = NULL WHERE title_id IN' in t:
    DONE.append('DataInitializer.java (already FK-safe)')
else:
    print('!! purge anchor not found — DataInitializer left untouched'); sys.exit(1)

# ----------------------------------------------------------------------
subprocess.run(['git', 'add', '.'], check=False, cwd=ROOT, capture_output=True)
subprocess.run(['git', 'commit', '-m', 'fix20: dedupe FolderPage BackToTopButton import (build fix) + FK-safe sample purge (seed fix)'], check=False, cwd=ROOT, capture_output=True)
subprocess.run(['git', 'push'], check=False, cwd=ROOT, capture_output=True)
print('Done:', *DONE, sep='\n  ')