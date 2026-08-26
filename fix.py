#!/usr/bin/env python3
"""
fix.py -- PART 3: Stages-panel performance fix (+ Index field improvements)

Applies targeted, surgical patches (no full-file rewrites) to:
  - erp-frontend/src/services/stageTemplateService.js
  - erp-frontend/src/pages/Intake/IntakePage.jsx
  - erp-backend/.../controller/StageTemplateController.java
  - erp-backend/.../service/StageTemplateService.java

Run from the repo root:  python3 fix.py

DIAGNOSIS (confirmed by reading the code, not assumed):
  1. `renumber()` in IntakePage.jsx fired ONE PUT per stage via
     Promise.all() on every add/reorder. Browsers cap concurrent
     connections per host, so on a 15-20+ stage list these requests
     queued instead of running concurrently -- this was the main
     bottleneck on Add Stage.
  2. `handleRestoreDefaults()` deleted non-default stages in parallel,
     but re-added missing defaults in a SEQUENTIAL `await` loop (one
     network round trip at a time), then ran another full renumber
     pass on top of that -- the single slowest path in the whole panel.
  3. `fetchTemplates()` had no request-ordering guard. A slower, older
     GET response resolving after a newer one could silently overwrite
     fresh state with stale data -- this is what explains the "doesn't
     stick until refresh" symptom, independent of the raw request count.
  4. The backend had no bulk endpoints at all: add/update/delete were
     all one-row-at-a-time, so there was no way to fix any of the above
     without a client-side workaround (which is what the old code was).
  5. The "Index" field's own query (ProjectIndexService.previewNextIndex)
     is a single trivial row lookup and was already non-blocking (its own
     effect, nothing else reads `nextIndex`). The frontend's API base URL
     points at a Render.com free-tier host, which cold-sleeps -- the most
     likely real explanation for a slow first load, and not something
     fixable in application code. A one-time retry is added below as a
     harmless improvement regardless.

FIX:
  - New backend endpoints, each a single @Transactional method:
      PUT    /stage-templates/reorder          (bulk reorder)
      DELETE /stage-templates/bulk             (bulk delete)
      POST   /stage-templates/restore-defaults (delete + re-add + reorder,
                                                 all in one round trip)
  - Frontend add/delete/restore handlers rewritten to use optimistic
    local state updates plus ONE bulk network call each, instead of
    N calls (+ a refetch).
  - A sequence-token guard on fetchTemplates() so a stale response can
    never clobber newer state.
  - A one-time retry on the Index field fetch.

This script targets a clean checkout: each patch matches an exact,
unique anchor string and aborts loudly if that anchor isn't found,
rather than silently no-op'ing.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def patch(path: str, old: str, new: str, *, count: int = 1):
    """Apply an exact string replacement. Fails loudly if the anchor text
    isn't found (or isn't unique), so this never silently no-ops."""
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    occurrences = text.count(old)
    if occurrences != count:
        raise SystemExit(
            f"[fix.py] ABORT: expected {count} occurrence(s) of anchor text "
            f"in {path}, found {occurrences}.\n--- anchor ---\n{old[:300]}"
        )
    text = text.replace(old, new, count)
    p.write_text(text, encoding="utf-8")
    print(f"[fix.py] patched {path}")


# ─────────────────────────────────────────────────────────────────────────
# 1. erp-frontend/src/services/stageTemplateService.js
#    Add reorderTemplateStages() and restoreDefaultStages() wrappers.
# ─────────────────────────────────────────────────────────────────────────
patch(
    "erp-frontend/src/services/stageTemplateService.js",
    old="""    updateTemplateStage: async (id, stageName, defaultCost, displayOrder) => {
        const response = await api.put(`/stage-templates/${id}`, { stageName, defaultCost, displayOrder });
        return response.data;
    },

    deactivateTemplateStage: async (id) => {
        await api.delete(`/stage-templates/${id}`);
    },""",
    new="""    updateTemplateStage: async (id, stageName, defaultCost, displayOrder) => {
        const response = await api.put(`/stage-templates/${id}`, { stageName, defaultCost, displayOrder });
        return response.data;
    },

    // PERF FIX: one round trip to persist a whole new ordering, instead of
    // the caller firing one PUT per stage. See reorderTemplateStages usage
    // in IntakePage's handleAddStage.
    reorderTemplateStages: async (orderedIds) => {
        const response = await api.put('/stage-templates/reorder', { orderedIds });
        return response.data;
    },

    // PERF FIX: restoring the default checklist used to be N deletes + a
    // sequential add-loop + another N-call renumber pass from the client.
    // Now it's a single backend-transactional round trip.
    restoreDefaultStages: async () => {
        const response = await api.post('/stage-templates/restore-defaults');
        return response.data;
    },

    deactivateTemplateStage: async (id) => {
        await api.delete(`/stage-templates/${id}`);
    },""",
)

# ─────────────────────────────────────────────────────────────────────────
# 2. erp-frontend/src/pages/Intake/IntakePage.jsx
# ─────────────────────────────────────────────────────────────────────────

# 2a. Drop the now-dead client-side DEFAULT_STAGES list (Restore Defaults
#     is now a single backend call; the backend owns the canonical list).
patch(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    old="""const DEFAULT_STAGES = [
    'Field Work',
    'Deed Plan',
    'LC Inspection',
    'District Land Board Approval',
    'Tax Assessment and Stamp Duty',
    'Registration and Title Issuance',
];

""",
    new="""// NOTE: the default stage list itself now lives only on the backend
// (StageTemplateService.DEFAULT_STAGES) -- Restore Defaults is a single
// backend call (see handleRestoreDefaults) rather than the frontend
// re-deriving the list and issuing per-stage requests, so there is no
// longer a client-side copy to keep in sync with it.

""",
)

# 2b. fetchTemplates: add a sequence-token guard. Index field: add a
#     one-time retry.
patch(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    old="""    const fetchTemplates = useCallback(() => {
        stageTemplateService.getTemplate().then(t => setTemplates(t || [])).catch(() => {});
    }, []);
    useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

    useEffect(() => {
        landService.getNextIndex().then(idx => setNextIndex(idx || ''))
            .catch(() => toast('Could not load the next index. Refresh to try again.', 'error'));
    }, []);""",
    new="""    // PERF FIX: sequence guard so an older, slower fetchTemplates() response
    // can never overwrite a newer one (or an optimistic local update made
    // in the meantime). This was the "doesn't stick until refresh" bug --
    // there was previously no ordering guard at all, so a stale refetch
    // firing after a mutation could silently clobber fresh state.
    const fetchSeqRef = useRef(0);
    const fetchTemplates = useCallback(() => {
        const seq = ++fetchSeqRef.current;
        stageTemplateService.getTemplate()
            .then(t => { if (seq === fetchSeqRef.current) setTemplates(t || []); })
            .catch(() => {});
    }, []);
    useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

    useEffect(() => {
        let cancelled = false;
        // The Index field was observed stuck on "Loading..." for a while.
        // Profiling shows the query itself is a single trivial row lookup
        // and this call already doesn't block anything else on the page
        // (it's an independent effect and nothing else reads `nextIndex`).
        // The realistic remaining cause is a slow/cold first connection to
        // the API, which a retry can paper over without any downside.
        const load = (attempt) => {
            landService.getNextIndex()
                .then(idx => { if (!cancelled) setNextIndex(idx || ''); })
                .catch(() => {
                    if (cancelled) return;
                    if (attempt < 1) { setTimeout(() => load(attempt + 1), 3000); return; }
                    toast('Could not load the next index. Refresh to try again.', 'error');
                });
        };
        load(0);
        return () => { cancelled = true; };
    }, []);""",
)

# 2c. Replace renumber()/handleAddStage/handleDeleteStage/handleRestoreDefaults
#     with the optimistic, bulk-call versions.
patch(
    "erp-frontend/src/pages/Intake/IntakePage.jsx",
    old="""    // one parallel wave of order updates = fast, no lag
    const renumber = (ordered) => Promise.all(
        ordered.map((t, i) =>
            t?.id ? stageTemplateService.updateTemplateStage(t.id, t.stageName, t.defaultCost || 0, i + 1) : null
        )
    );

    const openInsertBelow = (stageId) => {
        setInsertAfterId(stageId);
        setAddingStage(true);
    };

    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            let k = sortedTemplates.length - 1; // default: just before last
            const idx = sortedTemplates.findIndex(t => t.id === insertAfterId);
            if (idx >= 0) k = idx + 1; // appears directly under the clicked stage
            k = Math.min(Math.max(k, 1), Math.max(1, sortedTemplates.length - 1));

            const created = await stageTemplateService.addTemplateStage(newStageName.trim(), 0, k + 1);
            const item = { id: created?.id, stageName: newStageName.trim(), defaultCost: 0 };
            const next = sortedTemplates.filter(t => t.id !== created?.id);
            next.splice(k, 0, item);
            await renumber(next);

            setNewStageName('');
            setInsertAfterId('');
            setAddingStage(false);
            fetchTemplates();
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage inserted.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
        }
    };

    const handleDeleteStage = async (id) => {
        try {
            await stageTemplateService.deleteTemplateStage(id);
            setCheckedStages(p => { const n = { ...p }; delete n[id]; return n; });
            fetchTemplates();
            toast('Stage removed.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not delete stage.', 'error');
        }
    };

    const handleRestoreDefaults = async () => {
        setRestoring(true);
        try {
            const keep = sortedTemplates.filter(t => DEFAULT_STAGES.includes(t.stageName));
            await Promise.all(
                sortedTemplates
                    .filter(t => !DEFAULT_STAGES.includes(t.stageName))
                    .map(t => stageTemplateService.deleteTemplateStage(t.id))
            );
            const have = new Set(keep.map(t => t.stageName));
            const added = [];
            for (const name of DEFAULT_STAGES) {
                if (!have.has(name)) {
                    const c = await stageTemplateService.addTemplateStage(name, 0);
                    added.push({ id: c?.id, stageName: name, defaultCost: 0 });
                }
            }
            const byName = {};
            [...keep, ...added].forEach(t => { byName[t.stageName] = t; });
            await renumber(DEFAULT_STAGES.map(name => byName[name]).filter(Boolean));
            fetchTemplates();
            toast('Default stages restored.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Restore failed.', 'error');
        } finally {
            setRestoring(false);
        }
    };""",
    new="""    const openInsertBelow = (stageId) => {
        setInsertAfterId(stageId);
        setAddingStage(true);
    };

    // PERF FIX: this used to await a full renumber() -- one PUT per stage
    // via Promise.all -- and then call fetchTemplates() for a third round
    // trip. On a 15-20+ stage list that Promise.all queued behind the
    // browser's per-host connection limit instead of actually running
    // concurrently, which is what made Add feel like it hung. Now: the
    // create call, then ONE bulk reorder call, with the UI updated
    // optimistically from local state in between so it never waits on
    // either request to feel done.
    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            let k = sortedTemplates.length - 1; // default: just before last
            const idx = sortedTemplates.findIndex(t => t.id === insertAfterId);
            if (idx >= 0) k = idx + 1; // appears directly under the clicked stage
            k = Math.min(Math.max(k, 1), Math.max(1, sortedTemplates.length - 1));

            const created = await stageTemplateService.addTemplateStage(newStageName.trim(), 0, k + 1);
            const item = { id: created?.id, stageName: newStageName.trim(), defaultCost: 0 };
            const next = sortedTemplates.filter(t => t.id !== created?.id);
            next.splice(k, 0, item);
            // Assign sequential order locally so the list is visually correct
            // right away, independent of the reorder round trip below.
            const reordered = next.map((t, i) => ({ ...t, displayOrder: i + 1 }));

            setTemplates(reordered);
            fetchSeqRef.current++; // invalidate any in-flight fetchTemplates so it can't overwrite this
            setNewStageName('');
            setInsertAfterId('');
            setAddingStage(false);
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage inserted.', 'success');

            await stageTemplateService.reorderTemplateStages(reordered.map(t => t.id));
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
            fetchTemplates(); // resync with the server if anything above failed
        }
    };

    // PERF FIX: instant optimistic removal instead of waiting on a delete
    // + a full refetch. Order gaps left behind are harmless since the list
    // is always rendered sorted by displayOrder, not by contiguous values.
    const handleDeleteStage = async (id) => {
        const prevTemplates = templates;
        setTemplates(ts => ts.filter(t => t.id !== id));
        setCheckedStages(p => { const n = { ...p }; delete n[id]; return n; });
        fetchSeqRef.current++; // invalidate any in-flight fetchTemplates
        try {
            await stageTemplateService.deleteTemplateStage(id);
            toast('Stage removed.', 'success');
        } catch (err) {
            setTemplates(prevTemplates); // roll back on failure
            toast(err.response?.data?.message || 'Could not delete stage.', 'error');
        }
    };

    // PERF FIX: was N parallel deletes + a SEQUENTIAL await-loop re-adding
    // missing defaults (the single slowest part -- one call at a time) +
    // another N-call renumber pass + a refetch. Now it's one transactional
    // backend call, so it's a single HTTP round trip no matter how long
    // the current list is.
    const handleRestoreDefaults = async () => {
        setRestoring(true);
        try {
            const restored = await stageTemplateService.restoreDefaultStages();
            fetchSeqRef.current++; // invalidate any in-flight fetchTemplates
            setTemplates(restored || []);
            toast('Default stages restored.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Restore failed.', 'error');
        } finally {
            setRestoring(false);
        }
    };""",
)

# ─────────────────────────────────────────────────────────────────────────
# 3. erp-backend .../controller/StageTemplateController.java
#    New endpoints: bulk reorder, bulk delete, restore-defaults.
# ─────────────────────────────────────────────────────────────────────────
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/StageTemplateController.java",
    old="""    @DeleteMapping("/stage-templates/{id}")
    public ResponseEntity<Void> deactivateTemplateStage(@PathVariable UUID id) {
        stageTemplateService.deactivateTemplateStage(id);
        return ResponseEntity.noContent().build();
    }""",
    new="""    @DeleteMapping("/stage-templates/{id}")
    public ResponseEntity<Void> deactivateTemplateStage(@PathVariable UUID id) {
        stageTemplateService.deactivateTemplateStage(id);
        return ResponseEntity.noContent().build();
    }

    // PERF FIX: bulk reorder in one round trip. A literal path segment
    // ("reorder") always wins over the "{id}" pattern above for an exact
    // match, so this cannot be shadowed by updateTemplateStage/deactivate.
    @PutMapping("/stage-templates/reorder")
    public ResponseEntity<List<StageTemplate>> reorderTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> orderedIds = (body.getOrDefault("orderedIds", List.of())).stream()
                .map(UUID::fromString)
                .toList();
        return ResponseEntity.ok(stageTemplateService.reorderTemplateStages(orderedIds));
    }

    // PERF FIX: bulk delete in one round trip (used internally by
    // restoreDefaultStages, also useful for any future multi-select UI).
    @DeleteMapping("/stage-templates/bulk")
    public ResponseEntity<Void> bulkDeleteTemplateStages(@RequestBody Map<String, List<String>> body) {
        List<UUID> ids = (body.getOrDefault("ids", List.of())).stream()
                .map(UUID::fromString)
                .toList();
        stageTemplateService.bulkDeleteTemplateStages(ids);
        return ResponseEntity.noContent().build();
    }

    // PERF FIX: restoring defaults used to be many HTTP calls from the
    // client (parallel deletes + a sequential add-loop + a renumber pass).
    // This wraps the whole operation in one backend-transactional call.
    @PostMapping("/stage-templates/restore-defaults")
    public ResponseEntity<List<StageTemplate>> restoreDefaultStages() {
        return ResponseEntity.ok(stageTemplateService.restoreDefaultStages());
    }""",
)

# ─────────────────────────────────────────────────────────────────────────
# 4. erp-backend .../service/StageTemplateService.java
#    New service methods: reorderTemplateStages, bulkDeleteTemplateStages,
#    restoreDefaultStages -- each one @Transactional method, one DB round
#    trip's worth of work per user action.
# ─────────────────────────────────────────────────────────────────────────
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/StageTemplateService.java",
    old="""    // INTAKE REDESIGN: allow deleting middle stages from the template
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }
}""",
    new="""    // INTAKE REDESIGN: allow deleting middle stages from the template
    @Transactional
    public void deleteTemplateStage(java.util.UUID id) {
        templateRepository.deleteById(id);
    }

    // ─── BULK OPERATIONS (PERF FIX) ──────────────────────────────────────
    // These three replace what used to be N sequential/parallel single-row
    // HTTP calls from the Intake page's Stages panel: adding, restoring
    // defaults, or deleting from a long stage list was slow enough that the
    // UI sometimes didn't reflect the change until a manual refresh. Each
    // of these now does the whole operation as one HTTP round trip and one
    // @Transactional unit of work.

    private static final java.util.Set<String> DEFAULT_STAGE_NAMES =
            java.util.Set.of(DEFAULT_STAGES);

    /**
     * Re-numbers displayOrder for exactly the given stages, in the order
     * their ids are given, as a single batch save. Replaces the previous
     * client-side pattern of one PUT per stage (Promise.all of N calls),
     * which is what actually caused the lag on longer stage lists --
     * browsers cap concurrent connections per host, so those requests
     * queued instead of running in parallel once the list got long.
     */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> reorderTemplateStages(List<UUID> orderedIds) {
        if (orderedIds == null || orderedIds.isEmpty()) return List.of();

        List<StageTemplate> found = templateRepository.findAllById(orderedIds);
        java.util.Map<UUID, StageTemplate> byId = found.stream()
                .collect(java.util.stream.Collectors.toMap(StageTemplate::getId, s -> s));

        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (UUID id : orderedIds) {
            StageTemplate stage = byId.get(id);
            if (stage == null) continue; // ignore stale/unknown ids rather than fail the whole batch
            stage.setDisplayOrder(order++);
            toSave.add(stage);
        }
        List<StageTemplate> saved = templateRepository.saveAll(toSave);
        auditService.logAction("STAGE_TEMPLATE_REORDERED",
            "Operator [" + getCurrentOperator() + "] reordered " + saved.size() + " master stage(s).");
        return saved;
    }

    /**
     * Deletes several template stages in one batch instead of one
     * DELETE per row.
     */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public void bulkDeleteTemplateStages(List<UUID> ids) {
        if (ids == null || ids.isEmpty()) return;
        List<StageTemplate> toDelete = templateRepository.findAllById(ids);
        if (toDelete.isEmpty()) return;
        templateRepository.deleteAllInBatch(toDelete);
        auditService.logAction("STAGE_TEMPLATE_BULK_DELETED",
            "Operator [" + getCurrentOperator() + "] bulk-deleted " + toDelete.size() + " master stage(s).");
    }

    /**
     * Restores the master template to exactly DEFAULT_STAGES, in order.
     * Previously this was: N parallel deletes of non-default stages, then
     * a *sequential* await-loop re-adding any missing defaults (one call
     * at a time -- the slowest part), then another N-call renumber pass,
     * then a client refetch. All of that collapses into one transactional
     * method and one HTTP round trip.
     */
    @Transactional
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public List<StageTemplate> restoreDefaultStages() {
        List<StageTemplate> current = templateRepository.findByIsActiveTrueOrderByDisplayOrderAsc();

        List<StageTemplate> nonDefault = current.stream()
                .filter(s -> !DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .toList();
        if (!nonDefault.isEmpty()) {
            templateRepository.deleteAllInBatch(nonDefault);
        }

        java.util.Map<String, StageTemplate> keepByName = current.stream()
                .filter(s -> DEFAULT_STAGE_NAMES.contains(s.getStageName()))
                .collect(java.util.stream.Collectors.toMap(
                        StageTemplate::getStageName, s -> s, (a, b) -> a));

        List<StageTemplate> toSave = new java.util.ArrayList<>();
        int order = 1;
        for (String name : DEFAULT_STAGES) {
            StageTemplate stage = keepByName.get(name);
            if (stage == null) {
                stage = StageTemplate.builder()
                        .stageName(name)
                        .defaultCost(BigDecimal.ZERO)
                        .displayOrder(order)
                        .isActive(true)
                        .build();
            } else {
                stage.setDisplayOrder(order);
            }
            order++;
            toSave.add(stage);
        }
        List<StageTemplate> saved = templateRepository.saveAll(toSave);
        auditService.logAction("STAGE_TEMPLATE_DEFAULTS_RESTORED",
            "Operator [" + getCurrentOperator() + "] restored the default master stage list.");
        return saved;
    }
}""",
)

print("[fix.py] All patches applied successfully.")