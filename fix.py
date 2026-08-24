import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

def patch(path, old, new, count=1):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        print("MISSING FILE: " + path)
        return
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if old not in content:
        print("MISSING ANCHOR in " + path + ": " + old[:60].replace("\n", " | "))
        return
    content = content.replace(old, new) if count == 0 else content.replace(old, new, count)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: " + path)

RS = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java"

# 1. Add null-safe plotLabel helper after the CSV constants.
patch(RS,
    '    private static final String NEW_LINE = "\\n";',
    '    private static final String NEW_LINE = "\\n";\n'
    '\n'
    '    // HOTFIX (Phase D deviation follow-up): physicalBoxNumber was fully\n'
    '    // dropped, and titleless folder-stage projects (Phase A) can now hit\n'
    '    // these CSV exports. Null-safe plot label with projectIndex fallback,\n'
    '    // same pattern as Phase B\'s audit-log fallback.\n'
    '    private String plotLabel(LandProject p) {\n'
    '        if (p.getLandTitle() != null && p.getLandTitle().getPlotNumber() != null) {\n'
    '            return p.getLandTitle().getPlotNumber();\n'
    '        }\n'
    '        return p.getProjectIndex() != null ? p.getProjectIndex() : "---";\n'
    '    }')

# 2. Pillar 1: drop BOX_LOC from header and row.
patch(RS,
    'csv.append("PLOT_ID,PRIMARY_OWNER,PHONE,TOTAL_VAL,PAID_VAL,ARREARS,BOX_LOC,STATUS").append(NEW_LINE);',
    'csv.append("PLOT_ID,PRIMARY_OWNER,PHONE,TOTAL_VAL,PAID_VAL,ARREARS,STATUS").append(NEW_LINE);')

patch(RS,
    '                   .append(balance).append(CSV_DIVIDER)\n'
    '                   .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)\n'
    '                   .append(p.getStatus()).append(NEW_LINE);',
    '                   .append(balance).append(CSV_DIVIDER)\n'
    '                   .append(p.getStatus()).append(NEW_LINE);')

# 3. Pillar 2: Archive Map loses its box column; sort by plot label instead.
patch(RS,
    '        data.stream()\n'
    '            .sorted((a, b) -> a.getLandTitle().getPhysicalBoxNumber().compareTo(b.getLandTitle().getPhysicalBoxNumber()))\n'
    '            .forEach(p -> {\n'
    '                csv.append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)\n'
    '                   .append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)\n'
    '                   .append(p.getLandTitle().getTenure()).append(CSV_DIVIDER)\n'
    '                   .append(p.getLandTitle().getDistrict()).append(CSV_DIVIDER)\n'
    '                   .append(p.getCurrentStageIndex()).append(CSV_DIVIDER)\n'
    '                   .append(p.isLegacy()).append(NEW_LINE);\n'
    '            });',
    '        data.stream()\n'
    '            .sorted((a, b) -> plotLabel(a).compareTo(plotLabel(b)))\n'
    '            .forEach(p -> {\n'
    '                LandTitle lt = p.getLandTitle();\n'
    '                csv.append(plotLabel(p)).append(CSV_DIVIDER)\n'
    '                   .append(lt != null && lt.getTenure() != null ? lt.getTenure() : "").append(CSV_DIVIDER)\n'
    '                   .append(p.getDistrict() != null ? p.getDistrict() : (lt != null && lt.getDistrict() != null ? lt.getDistrict() : "")).append(CSV_DIVIDER)\n'
    '                   .append(p.getCurrentStageIndex()).append(CSV_DIVIDER)\n'
    '                   .append(p.isLegacy()).append(NEW_LINE);\n'
    '            });')

# 4. Priority 2 Report 1 + 2 headers: drop the BOX column.
patch(RS,
    'csv.append("PLOT_ID,BOX,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,RECEIVABLE_START,TITLE_COST_UGX,STORAGE_FEES_UGX,MONTHS_IN_RECEIVABLE,TOTAL_PAID,TOTAL_OWED").append(NEW_LINE);',
    'csv.append("PLOT_ID,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,RECEIVABLE_START,TITLE_COST_UGX,STORAGE_FEES_UGX,MONTHS_IN_RECEIVABLE,TOTAL_PAID,TOTAL_OWED").append(NEW_LINE);')

patch(RS,
    'csv.append("PLOT_ID,BOX,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,TOTAL_COST,AMOUNT_PAID,STATUS").append(NEW_LINE);',
    'csv.append("PLOT_ID,DISTRICT,TENURE,PRIMARY_OWNER,PHONE,TOTAL_COST,AMOUNT_PAID,STATUS").append(NEW_LINE);')

# 5. Reports 1 + 2 share this identical 4-line row prefix; one global replace
#    fixes both. Removes getPhysicalBoxNumber, null-guards tenure/district,
#    and prefers LandProject.district (source of truth since Phase A).
patch(RS,
    '            csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)\n'
    '               .append(p.getLandTitle().getPhysicalBoxNumber()).append(CSV_DIVIDER)\n'
    '               .append(p.getLandTitle().getDistrict() != null ? p.getLandTitle().getDistrict() : "").append(CSV_DIVIDER)\n'
    '               .append(p.getLandTitle().getTenure() != null ? p.getLandTitle().getTenure() : "").append(CSV_DIVIDER)',
    '            LandTitle lt = p.getLandTitle();\n'
    '            csv.append(plotLabel(p)).append(CSV_DIVIDER)\n'
    '               .append(p.getDistrict() != null ? p.getDistrict() : (lt != null && lt.getDistrict() != null ? lt.getDistrict() : "")).append(CSV_DIVIDER)\n'
    '               .append(lt != null && lt.getTenure() != null ? lt.getTenure() : "").append(CSV_DIVIDER)',
    count=0)

# 6. Completed Titles: null-guard isReleased for titleless rows.
patch(RS,
    'boolean released = p.getLandTitle().isReleased();',
    'boolean released = p.getLandTitle() != null && p.getLandTitle().isReleased();')

# 7. Remaining direct plotNumber reads (Pillar 1 row, Pillar 5 row) go through
#    the null-safe helper. Runs last so the blocks above are already rewritten.
patch(RS,
    'csv.append(p.getLandTitle().getPlotNumber()).append(CSV_DIVIDER)',
    'csv.append(plotLabel(p)).append(CSV_DIVIDER)',
    count=0)

# PERMANENT Section 3 rule: commit and push automatically.
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "Hotfix: finish physicalBoxNumber drop in ReportService CSV exports (build fix)"], check=True)
subprocess.run(["git", "push"], check=True)
print("DONE: committed and pushed.")