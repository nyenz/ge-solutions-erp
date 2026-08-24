### Phase A -- Folder-to-Title redesign: LandTitle optional + location fields moved up (Section 18.10)

`fix.py` implements Phase A exactly as scoped, and only that: `LandProject.landTitle` is now
`@OneToOne(nullable = true)` instead of required, `LandProject` gains `district`, `county`,
`subCounty`, `parish`, `village`, and `area` (all optional `VARCHAR(100)`, following the
existing location-field style), and `DataInitializer.runSchemaMigrations()` gets six new
`ADD COLUMN IF NOT EXISTS` lines plus one backfill `UPDATE` that copies each project's
`district`/`county` up from its linked `LandTitle` row via the `title_id` FK, guarded by
`lp.district IS NULL` so it is safe to run on every boot and becomes a no-op once backfilled --
same raw-JDBC, ignore-if-already-applied pattern as the existing `session_version` migration.

`district`/`county` are deliberately left in place on `LandTitle.java`, marked `@Deprecated`
with a comment explaining why, not deleted: `LandService.java` (`atomicIntake`, plus direct
`.district(...)`/`.county(...)` builder and setter calls) and `ReportService.java` (three CSV
export call sites reading `p.getLandTitle().getDistrict()`) still read/write them directly, and
repointing those call sites -- along with the `atomicIntake()` rewrite and the ~14-method
null-safety audit -- is Section 18.9.1's job, assigned to Phase B. This fix.py touches exactly
three files: `LandProject.java`, `LandTitle.java`, `DataInitializer.java`. Nothing else changes.

Tested by dry-running the patch logic against a fresh clone (git commit/push stripped out for
the test run): all three `str.replace` patches matched and applied cleanly, and the resulting
`LandProject.java`, `LandTitle.java`, and `DataInitializer.java` were inspected directly to
confirm the nullable change, the six new columns, the deprecation comment, and the backfill
`UPDATE` all look correct. Not yet run against David's real repo/deploy, and per Section 18.11
the testing-mode question (deferred vs. per-stage for this redesign) is still open -- David
hasn't decided yet, so that stays unresolved going into Phase B rather than being assumed either
way.

**Not yet run against David's real repo/deploy -- awaiting confirmation before this moves into
the Section 18.10 Phase Tracker (status: NOT STARTED -> DONE).**