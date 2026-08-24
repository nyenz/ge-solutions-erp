# PATH: fix.py
# PHASE A (Section 18.10): Make LandTitle optional on LandProject, add
# subCounty/parish/village/area to LandProject, move district/county up from
# LandTitle (deprecated in place, not deleted), migrate existing data.
#
# Scope note: district/county are left in place on LandTitle.java as
# deprecated fields on purpose. LandService.java, ReportService.java, and the
# test files still read/write them directly, and repointing those call sites
# is Section 18.9.1's job, assigned to Phase B -- not this phase. This fix.py
# touches ONLY LandProject.java, LandTitle.java, and DataInitializer.java.

import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old not in content:
        print("MISSING: " + label + " (" + path + ")")
        return
    if content.count(old) > 1:
        print("MISSING: " + label + " -- old_str not unique in " + path)
        return
    content = content.replace(old, new)
    write_file(path, content)
    print("OK: " + label + " (" + path + ")")

LAND_PROJECT = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java"
LAND_TITLE = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java"
DATA_INIT = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"

# ---------------------------------------------------------------------------
# 1. LandProject.java -- landTitle becomes optional, add location fields
# ---------------------------------------------------------------------------

old_landtitle_field = "\n".join([
    "    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)",
    "    @JoinColumn(name = \"title_id\", nullable = false)",
    "    private LandTitle landTitle;",
    "",
    "    @Builder.Default",
    "    @ManyToMany(fetch = FetchType.EAGER)",
])

new_landtitle_field = "\n".join([
    "    // PHASE A (Section 18.10): landTitle is now optional. A LandProject",
    "    // exists from intake onward and only gains a LandTitle once the final",
    "    // processing stage is checked (or immediately, if the legacy preset is",
    "    // used). See Section 18.9 in LLM_CONTEXT_GUIDE.md for the full target",
    "    // model.",
    "    @OneToOne(cascade = CascadeType.ALL, fetch = FetchType.EAGER)",
    "    @JoinColumn(name = \"title_id\", nullable = true)",
    "    private LandTitle landTitle;",
    "",
    "    /**",
    "     * LOCATION (Section 18.4/18.9): permanent, not folder-only -- stays",
    "     * visible for the whole life of the record, title or no title.",
    "     * district/county are moved up from LandTitle (existing data migrated",
    "     * by DataInitializer below); subCounty, parish, village, and area are",
    "     * new. Area is left as free text since it is recorded in mixed units",
    "     * (acres, decimals, etc) and is optional per Section 18.9.3.",
    "     */",
    "    @Column(length = 100)",
    "    private String district;",
    "",
    "    @Column(length = 100)",
    "    private String county;",
    "",
    "    @Column(name = \"sub_county\", length = 100)",
    "    private String subCounty;",
    "",
    "    @Column(length = 100)",
    "    private String parish;",
    "",
    "    @Column(length = 100)",
    "    private String village;",
    "",
    "    @Column(length = 100)",
    "    private String area;",
    "",
    "    @Builder.Default",
    "    @ManyToMany(fetch = FetchType.EAGER)",
])

patch(LAND_PROJECT, old_landtitle_field, new_landtitle_field,
      "LandProject: landTitle nullable=true + new location fields")

# ---------------------------------------------------------------------------
# 2. LandTitle.java -- deprecate district/county in place, do NOT delete
# ---------------------------------------------------------------------------

old_title_location = "\n".join([
    "    @Column(length = 100)",
    "    private String district;",
    "",
    "    @Column(length = 100)",
    "    private String county;",
])

new_title_location = "\n".join([
    "    // DEPRECATED (Phase A, Section 18.10): district/county now live on",
    "    // LandProject and are the source of truth going forward. These",
    "    // columns are kept here on purpose -- not deleted -- because",
    "    // LandService.java and ReportService.java still read/write them",
    "    // directly. Repointing those call sites to LandProject is scoped to",
    "    // Phase B (Section 18.9.1), not this phase. Do not remove these",
    "    // fields until Phase B has migrated every call site.",
    "    @Deprecated",
    "    @Column(length = 100)",
    "    private String district;",
    "",
    "    @Deprecated",
    "    @Column(length = 100)",
    "    private String county;",
])

patch(LAND_TITLE, old_title_location, new_title_location,
      "LandTitle: mark district/county deprecated (not removed)")

# ---------------------------------------------------------------------------
# 3. DataInitializer.java -- add columns to land_projects + backfill migration
# ---------------------------------------------------------------------------

old_migrations_tail = "\n".join([
    "            // STAGE 3 -- SOFT DELETE",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP\",",
    "        };",
])

new_migrations_tail = "\n".join([
    "            // STAGE 3 -- SOFT DELETE",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP\",",
    "",
    "            // PHASE A -- FOLDER-TO-TITLE REDESIGN (Section 18.10)",
    "            // landTitle becomes optional on LandProject (see model change),",
    "            // and location fields move up so they are permanent even for",
    "            // titleless folder-stage projects.",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)\",",
    "            \"ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)\",",
    "            // Backfill: copy existing district/county from land_titles up to",
    "            // their parent land_projects row via the title_id FK. The",
    "            // \"lp.district IS NULL\" guard makes this safe to run on every",
    "            // boot -- once a row has been backfilled its district is no",
    "            // longer NULL, so this becomes a no-op for it from then on.",
    "            // land_titles.district/county are left in place (deprecated,",
    "            // not dropped) so this UPDATE is repeatable and non-destructive.",
    "            \"UPDATE land_projects lp SET district = lt.district, county = lt.county \" +",
    "                \"FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL \" +",
    "                \"AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)\",",
    "        };",
])

patch(DATA_INIT, old_migrations_tail, new_migrations_tail,
      "DataInitializer: add land_projects location columns + backfill migration")

# ---------------------------------------------------------------------------
# Commit and push (PERMANENT rule, Section 3)
# ---------------------------------------------------------------------------
import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m',
    'Phase A (Section 18.10): make LandTitle optional on LandProject, '
    'add subCounty/parish/village/area, migrate district/county up from LandTitle'])
subprocess.run(['git', 'push'])