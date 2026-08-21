# PATH: fix_stage11.py  (STAGE 11)
# STAGE 11 -- Dashboard "stale call" KPI still used the pre-Stage-9 alphabetical
#             "primary owner" bug, and 3.4 open question #2 (soft duplicate-
#             contact warning) was left undecided by Stage 10 -- decided here.
# Run from project root: py fix_stage11.py
#
# CONTEXT / WHAT WAS ACTUALLY VERIFIED (git-cloned repo read directly)
# -------------------------------------------------------------------------
# Confirmed via `git log`: Stage 8 (Edit-screen NIN check == "Issue #1"),
# Stage 9 (Recovery joint-owner card visibility == "Issue #2"), and Stage 10
# (per-owner call attribution, per-owner note, SOLO/JOINT card layout, merged
# log-a-contact action) are ALL already committed in this repo. Reading the
# code Stage 10 left behind (per its own "NOT addressed here" list) turned up
# one confirmed regression-class bug and one still-open 3.4 decision:
#
# BUG FOUND: DashboardController.getSummary() computes its own `staleCalls`
# KPI independently of RecoveryController, and never received the Stage 9/10
# fix. It still sorts each plot's proprietors alphabetically by fullName and
# tests ONLY that one "primary" owner's cooldown/monthly-count state:
#
#     Client primary = p.getProprietors().stream()
#             .sorted(Comparator.comparing(Client::getFullName))
#             .findFirst().orElse(null);
#     ... only `primary`'s eligibility is checked ...
#
# The method's own comment already says the intent is "unique owners (Client
# IDs) who are due for a call today" -- matching GET /api/v1/recovery/count,
# which (via RecoveryController.buildOwnerTasks) already counts every
# proprietor independently. The implementation just never matched that
# comment. Concretely: the dashboard KPI card and the Recovery page's own
# queue count can disagree, and a genuinely-eligible co-owner can be silently
# excluded from the dashboard number just because a co-owner who sorts first
# alphabetically happens not to be eligible right now.
#
# OPEN QUESTION ANSWERED (3.4 #2): "any soft warning when a second joint
# owner is called inside the same window" -- explicitly left open by Stage 10.
# Decision: yes, implement it, and make it SOFT (never blocks the save) and
# scoped to a 3-day look-back (not the full 14-day cooldown), because 3.3
# already agreed staff must be able to call different joint owners
# independently -- this is informational, not a restriction.
#
# THE FIX
# -------------------------------------------------------------------------
# Backend:
#   1. DashboardController.getSummary(): staleCalls now dedupes proprietors
#      by Client ID across every outstanding plot and tests EACH owner's own
#      eligibility independently, matching RecoveryController's definition of
#      "stale" exactly (same rule: monthly cap, 14-day cooldown, per person).
#   2. LandService.logFollowUp(...) now returns a small result map instead of
#      void: {ownerId, coOwnerWarning}. Before saving, it checks whether any
#      OTHER proprietor on the same project has a FollowUpLog entry (their
#      own, per Stage 10's owner_id column) within the last 3 days, and if
#      so, includes an advisory message -- it never blocks or delays the
#      save itself.
#   3. LandController's /follow-up endpoint returns that map instead of an
#      empty 200, so the frontend can see the warning.
#
# Frontend:
#   4. recoveryService.logRecoveryCall now returns the response body instead
#      of discarding it and returning `true`.
#   5. RecoveryPortal shows a small dismissible banner when a coOwnerWarning
#      comes back -- purely informational, appears AFTER the call has already
#      been logged and saved successfully.
#
# NOT addressed here (still open, not decided by this session):
#   - Whether "primary" should be dropped as a concept/label everywhere.
#     Read-only CSV headers (ReportService: PRIMARY_OWNER) and report-table
#     column labels (ReportHub.jsx) still use the word. Decision: leave them.
#     Those are external-facing report column names that downstream CSV
#     consumers may already depend on; renaming them is a labeling/reporting
#     change with its own migration concerns, not part of this bugfix, and
#     is intentionally out of scope here -- same reasoning Stage 10 gave for
#     not doing a global rename.
#   - No new DB migration is needed for this stage; no schema changed.
#
# Safe to re-run: each patch is checked before writing; if a target is not
# found it prints MISSING and leaves that file alone (most likely meaning
# this stage, or that specific patch, is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def patch(label, rel_path, old, new):
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        print("[STAGE 11] " + label + " ... MISSING (file not found: " + rel_path + ")")
        return False
    content = read_file(full_path)
    if old not in content:
        if new in content:
            print("[STAGE 11] " + label + " ... OK (already applied)")
            return True
        print("[STAGE 11] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        return False
    content = content.replace(old, new, 1)
    write_file(full_path, content)
    print("[STAGE 11] " + label + " ... OK")
    return True


def main():
    total = 0
    ok = 0

    # ------------------------------------------------------------------ #
    # 1. DashboardController: fix stale-count to match RecoveryController
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "DashboardController: staleCalls now dedupes owners by Client ID "
        "and tests each independently, instead of only the alphabetically "
        "first 'primary' proprietor per plot",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java",

        "        // Stale count = plots with outstanding balance whose primary owner is eligible to call\n"
        "        // This matches the buildPlotTasks() logic in RecoveryController exactly.\n"
        "        // Stale count = unique owners (Client IDs) who are due for a call today\n"
        "        long staleCalls = allPlots.stream()\n"
        "                .filter(p -> {\n"
        "                    java.math.BigDecimal bal = p.isReceivable()\n"
        "                            ? p.receivableTotalOwed() : p.activeTotalOwed();\n"
        "                    if (bal.compareTo(java.math.BigDecimal.ZERO) <= 0) return false;\n"
        "                    if (p.getProprietors() == null || p.getProprietors().isEmpty()) return false;\n"
        "                    com.gesolutions.erp.modules.client.model.Client primary = p.getProprietors()\n"
        "                            .stream().sorted(java.util.Comparator.comparing(\n"
        "                                com.gesolutions.erp.modules.client.model.Client::getFullName))\n"
        "                            .findFirst().orElse(null);\n"
        "                    if (primary == null) return false;\n"
        "                    if (primary.shouldResetMonthlyCounter()) primary.setMonthlyContactCount(0);\n"
        "                    if (primary.getMonthlyContactCount() >= 2) return false;\n"
        "                    if (primary.getLastContactedAt() == null) return true;\n"
        "                    java.time.LocalDate eligible = primary.getLastContactedAt().toLocalDate().plusDays(14);\n"
        "                    return !java.time.LocalDate.now().isBefore(eligible);\n"
        "                })\n"
        "                .count();",

        "        // STAGE 11 FIX: DASHBOARD_STALE_COUNT_PRIMARY_OWNER_BUG.\n"
        "        // This used to pick only the alphabetically-first proprietor per plot\n"
        "        // (\"primary\") and test THEIR cooldown/count -- the exact bug Stage 9/10\n"
        "        // already removed from Recovery itself, just never ported here, so this\n"
        "        // KPI could silently disagree with GET /api/v1/recovery/count. Decision\n"
        "        // (3.4): both must report the same definition of \"stale\" -- unique\n"
        "        // Client IDs, deduped across every plot they co-own, each independently\n"
        "        // eligible under their own cooldown/monthly-count state -- matching\n"
        "        // RecoveryController.buildOwnerTasks's eligibility rule exactly.\n"
        "        long staleCalls = allPlots.stream()\n"
        "                .filter(p -> {\n"
        "                    java.math.BigDecimal bal = p.isReceivable()\n"
        "                            ? p.receivableTotalOwed() : p.activeTotalOwed();\n"
        "                    return bal.compareTo(java.math.BigDecimal.ZERO) > 0;\n"
        "                })\n"
        "                .flatMap(p -> p.getProprietors() == null\n"
        "                        ? java.util.stream.Stream.<com.gesolutions.erp.modules.client.model.Client>empty()\n"
        "                        : p.getProprietors().stream())\n"
        "                .filter(owner -> owner != null && owner.getId() != null)\n"
        "                .collect(Collectors.toMap(\n"
        "                        com.gesolutions.erp.modules.client.model.Client::getId,\n"
        "                        owner -> owner,\n"
        "                        (keepFirst, ignored) -> keepFirst))\n"
        "                .values().stream()\n"
        "                .filter(owner -> {\n"
        "                    if (owner.shouldResetMonthlyCounter()) owner.setMonthlyContactCount(0);\n"
        "                    if (owner.getMonthlyContactCount() >= 2) return false;\n"
        "                    if (owner.getLastContactedAt() == null) return true;\n"
        "                    java.time.LocalDate eligible = owner.getLastContactedAt().toLocalDate().plusDays(14);\n"
        "                    return !java.time.LocalDate.now().isBefore(eligible);\n"
        "                })\n"
        "                .count();",
    )

    # ------------------------------------------------------------------ #
    # 2. LandService.logFollowUp: returns coOwnerWarning, decided by 3.4 #2
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "LandService.logFollowUp: returns a result map with an optional "
        "soft coOwnerWarning (design brief 3.4 open question #2) instead "
        "of void",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",

        "    @Transactional(rollbackFor = Exception.class)\n"
        "    public void logFollowUp(UUID projectId, UUID ownerId, String content) {\n"
        "        LandProject project = projectRepository.findById(projectId).orElseThrow();\n"
        "\n"
        "        boolean ownerIsProprietor = project.getProprietors() != null &&\n"
        "                project.getProprietors().stream()\n"
        "                        .anyMatch(o -> o != null && o.getId() != null && o.getId().equals(ownerId));\n"
        "        if (!ownerIsProprietor) {\n"
        "            throw new BusinessException(\n"
        "                    \"OWNER_NOT_ON_PROJECT: The selected owner is not a proprietor of this project.\");\n"
        "        }\n"
        "\n"
        "        // Update ONLY the specific owner who was actually reached. Cooldown\n"
        "        // state lives on Client (per person), so this cannot touch any\n"
        "        // co-owner who was not part of this call.\n"
        "        clientService.logManagerContact(ownerId);\n"
        "\n"
        "        String operator = getCurrentOperator();\n"
        "        FollowUpLog entry = FollowUpLog.builder()\n"
        "                .projectId(projectId)\n"
        "                .ownerId(ownerId)\n"
        "                .notes(content)\n"
        "                .recordedBy(operator)\n"
        "                .build();\n"
        "        followUpRepository.save(entry);\n"
        "\n"
        "        auditService.logAction(\"RECOVERY_SYNC\",\n"
        "            \"Operator [\" + operator + \"] logged call for plot: \"\n"
        "            + project.getLandTitle().getPlotNumber() + \" (owner reached: \" + ownerId + \")\");\n"
        "    }",

        "    // STAGE 11 FIX: SOFT_DUPLICATE_CONTACT_WARNING (design brief 3.4, open\n"
        "    // question #2 -- explicitly left undecided by Stage 10). Decision:\n"
        "    //   - SOFT, never blocks: 3.3 already agreed staff must be able to call\n"
        "    //     different joint owners independently, so a second co-owner call\n"
        "    //     inside the window is normal and is never prevented.\n"
        "    //   - 3-day look-back, not the full 14-day cooldown: this flags \"we just\n"
        "    //     called about this plot yesterday\", not ordinary independent contact.\n"
        "    //   - Surfaced on the existing endpoint's response, same pattern Stage 10\n"
        "    //     used for merging log-a-call/add-a-note into one action.\n"
        "    @Transactional(rollbackFor = Exception.class)\n"
        "    public java.util.Map<String, Object> logFollowUp(UUID projectId, UUID ownerId, String content) {\n"
        "        LandProject project = projectRepository.findById(projectId).orElseThrow();\n"
        "\n"
        "        boolean ownerIsProprietor = project.getProprietors() != null &&\n"
        "                project.getProprietors().stream()\n"
        "                        .anyMatch(o -> o != null && o.getId() != null && o.getId().equals(ownerId));\n"
        "        if (!ownerIsProprietor) {\n"
        "            throw new BusinessException(\n"
        "                    \"OWNER_NOT_ON_PROJECT: The selected owner is not a proprietor of this project.\");\n"
        "        }\n"
        "\n"
        "        // STAGE 11: advisory-only read -- does not touch any co-owner's state.\n"
        "        String coOwnerWarning = null;\n"
        "        LocalDateTime recentWindowStart = LocalDateTime.now().minusDays(3);\n"
        "        java.util.List<FollowUpLog> recentProjectLogs =\n"
        "                followUpRepository.findByProjectIdOrderByTimestampDesc(projectId);\n"
        "        for (FollowUpLog log : recentProjectLogs) {\n"
        "            if (log.getOwnerId() != null\n"
        "                    && !log.getOwnerId().equals(ownerId)\n"
        "                    && log.getTimestamp() != null\n"
        "                    && log.getTimestamp().isAfter(recentWindowStart)) {\n"
        "                Client coOwner = project.getProprietors().stream()\n"
        "                        .filter(o -> o != null && log.getOwnerId().equals(o.getId()))\n"
        "                        .findFirst().orElse(null);\n"
        "                String coOwnerName = coOwner != null ? coOwner.getFullName() : \"another owner\";\n"
        "                coOwnerWarning = coOwnerName + \" was already contacted about this plot on \"\n"
        "                        + log.getTimestamp().toLocalDate() + \".\";\n"
        "                break;\n"
        "            }\n"
        "        }\n"
        "\n"
        "        // Update ONLY the specific owner who was actually reached. Cooldown\n"
        "        // state lives on Client (per person), so this cannot touch any\n"
        "        // co-owner who was not part of this call.\n"
        "        clientService.logManagerContact(ownerId);\n"
        "\n"
        "        String operator = getCurrentOperator();\n"
        "        FollowUpLog entry = FollowUpLog.builder()\n"
        "                .projectId(projectId)\n"
        "                .ownerId(ownerId)\n"
        "                .notes(content)\n"
        "                .recordedBy(operator)\n"
        "                .build();\n"
        "        followUpRepository.save(entry);\n"
        "\n"
        "        auditService.logAction(\"RECOVERY_SYNC\",\n"
        "            \"Operator [\" + operator + \"] logged call for plot: \"\n"
        "            + project.getLandTitle().getPlotNumber() + \" (owner reached: \" + ownerId + \")\");\n"
        "\n"
        "        java.util.Map<String, Object> result = new java.util.HashMap<>();\n"
        "        result.put(\"ownerId\", ownerId);\n"
        "        result.put(\"coOwnerWarning\", coOwnerWarning);\n"
        "        return result;\n"
        "    }",
    )

    # ------------------------------------------------------------------ #
    # 3. LandController: pass the result map back instead of empty 200
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "LandController./follow-up: returns the {ownerId, coOwnerWarning} "
        "body instead of an empty 200",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",

        "    @PreAuthorize(\"hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')\")\n"
        "    @PostMapping(\"/projects/{id}/follow-up\")\n"
        "    public ResponseEntity<Void> logContact(@PathVariable UUID id,\n"
        "                                            @RequestParam UUID ownerId,\n"
        "                                            @RequestParam String content) {\n"
        "        landService.logFollowUp(id, ownerId, content);\n"
        "        return ResponseEntity.ok().build();\n"
        "    }",

        "    // STAGE 11 FIX: response now carries an optional soft coOwnerWarning\n"
        "    // (design brief 3.4 #2) instead of an empty body -- never blocks the\n"
        "    // save, frontend decides whether/how to surface it.\n"
        "    @PreAuthorize(\"hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')\")\n"
        "    @PostMapping(\"/projects/{id}/follow-up\")\n"
        "    public ResponseEntity<java.util.Map<String, Object>> logContact(@PathVariable UUID id,\n"
        "                                            @RequestParam UUID ownerId,\n"
        "                                            @RequestParam String content) {\n"
        "        return ResponseEntity.ok(landService.logFollowUp(id, ownerId, content));\n"
        "    }",
    )

    # ------------------------------------------------------------------ #
    # 4. recoveryService.js: stop discarding the response body
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "recoveryService.logRecoveryCall: returns response.data instead "
        "of a hardcoded true",
        "erp-frontend/src/services/recoveryService.js",

        "    logRecoveryCall: async (projectId, ownerId, text) => {\n"
        "        await api.post(`/land/projects/${projectId}/follow-up`, null, {\n"
        "            params: { ownerId, content: text }\n"
        "        });\n"
        "        return true;\n"
        "    },",

        "    // STAGE 11 FIX: return the response body (may include a soft\n"
        "    // coOwnerWarning, design brief 3.4 #2) instead of discarding it.\n"
        "    logRecoveryCall: async (projectId, ownerId, text) => {\n"
        "        const response = await api.post(`/land/projects/${projectId}/follow-up`, null, {\n"
        "            params: { ownerId, content: text }\n"
        "        });\n"
        "        return response.data;\n"
        "    },",
    )

    # ------------------------------------------------------------------ #
    # 5. RecoveryPortal.jsx: state + handler + banner for the soft warning
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "RecoveryPortal: add coOwnerWarning state",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "    const [callModal,    setCallModal]    = useState({ open: false, mission: null, ownerId: null, ownerName: '' });\n"
        "    const [logContent,   setLogContent]   = useState('');\n"
        "    const [committing,   setCommitting]   = useState(false);",

        "    const [callModal,    setCallModal]    = useState({ open: false, mission: null, ownerId: null, ownerName: '' });\n"
        "    const [logContent,   setLogContent]   = useState('');\n"
        "    const [committing,   setCommitting]   = useState(false);\n"
        "    // STAGE 11 FIX: soft, dismissible notice for \"a co-owner was already\n"
        "    // contacted about this plot recently\" (design brief 3.4 #2) -- never\n"
        "    // blocks the call log, which has already been saved by the time this shows.\n"
        "    const [coOwnerWarning, setCoOwnerWarning] = useState(null);",
    )

    total += 1
    ok += patch(
        "RecoveryPortal.handleLogCall: capture and surface coOwnerWarning "
        "from the response",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "    const handleLogCall = async () => {\n"
        "        if (!callModal.mission || !callModal.ownerId) return;\n"
        "        setCommitting(true);\n"
        "        try {\n"
        "            await recoveryService.logRecoveryCall(callModal.mission.projectId, callModal.ownerId, logContent);\n"
        "            setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' });\n"
        "            setLogContent('');\n"
        "            loadData();\n"
        "        } catch { /* silent */ }\n"
        "        finally { setCommitting(false); }\n"
        "    };",

        "    const handleLogCall = async () => {\n"
        "        if (!callModal.mission || !callModal.ownerId) return;\n"
        "        setCommitting(true);\n"
        "        try {\n"
        "            const result = await recoveryService.logRecoveryCall(callModal.mission.projectId, callModal.ownerId, logContent);\n"
        "            setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' });\n"
        "            setLogContent('');\n"
        "            // STAGE 11 FIX: purely informational -- the call was already\n"
        "            // logged successfully by this point regardless of this value.\n"
        "            setCoOwnerWarning(result && result.coOwnerWarning ? result.coOwnerWarning : null);\n"
        "            loadData();\n"
        "        } catch { /* silent */ }\n"
        "        finally { setCommitting(false); }\n"
        "    };",
    )

    total += 1
    ok += patch(
        "RecoveryPortal JSX: render the dismissible coOwnerWarning banner "
        "between the financial HUD and the filter bar",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "                <div className={styles.finHUDCard}>\n"
        "                    <label>STORAGE FEES</label>\n"
        "                    <strong>UGX {fmt(totalStorageFees)}</strong>\n"
        "                </div>\n"
        "            </div>\n"
        "\n"
        "            {/* FILTER BAR */}",

        "                <div className={styles.finHUDCard}>\n"
        "                    <label>STORAGE FEES</label>\n"
        "                    <strong>UGX {fmt(totalStorageFees)}</strong>\n"
        "                </div>\n"
        "            </div>\n"
        "\n"
        "            {/* STAGE 11: soft, dismissible co-owner-recently-contacted notice\n"
        "                (design brief 3.4 #2) -- purely informational, call is already\n"
        "                logged by the time this can appear. */}\n"
        "            {coOwnerWarning && (\n"
        "                <div className={styles.coOwnerWarningBanner} role=\"status\">\n"
        "                    <span>{coOwnerWarning}</span>\n"
        "                    <button\n"
        "                        type=\"button\"\n"
        "                        className={styles.coOwnerWarningDismiss}\n"
        "                        onClick={() => setCoOwnerWarning(null)}\n"
        "                        aria-label=\"Dismiss notice\"\n"
        "                    >\n"
        "                        &times;\n"
        "                    </button>\n"
        "                </div>\n"
        "            )}\n"
        "\n"
        "            {/* FILTER BAR */}",
    )

    # ------------------------------------------------------------------ #
    # 6. CSS: minimal additive styling for the new banner
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "RecoveryPortal.module.css: add styles for the coOwnerWarning "
        "banner (additive, appended at end of file)",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",

        ".coOwnerLink:hover { color: #f0a050; }\n"
        ".coOwnerLink:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }",

        ".coOwnerLink:hover { color: #f0a050; }\n"
        ".coOwnerLink:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }\n"
        "\n"
        "/* ── STAGE 11: soft co-owner-recently-contacted notice banner ── */\n"
        ".coOwnerWarningBanner {\n"
        "    display: flex; align-items: center; justify-content: space-between;\n"
        "    gap: clamp(8px, 1vw, 12px);\n"
        "    background: rgba(238, 140, 58, 0.12); border: 1px solid rgba(238, 140, 58, 0.4);\n"
        "    border-radius: 8px;\n"
        "    padding: clamp(8px, 1vw, 12px) clamp(12px, 1.4vw, 16px);\n"
        "    margin-bottom: clamp(10px, 1.2vw, 14px);\n"
        "    font-family: 'DM Sans', sans-serif; font-size: clamp(11px, 1vw, 13px);\n"
        "    font-weight: 700; color: rgba(255, 255, 255, 0.85);\n"
        "}\n"
        ".coOwnerWarningDismiss {\n"
        "    background: none; border: none; cursor: pointer;\n"
        "    font-size: 16px; line-height: 1; color: rgba(255, 255, 255, 0.6);\n"
        "    padding: 0 2px; flex-shrink: 0;\n"
        "}\n"
        ".coOwnerWarningDismiss:hover { color: #fff; }\n"
        ".coOwnerWarningDismiss:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }",
    )

    print("-" * 70)
    print(str(ok) + "/" + str(total) + " patches applied")
    if ok < total:
        print("Some patches were MISSING -- review output above before committing.")
    print()
    print("No DB schema change in this stage.")


if __name__ == "__main__":
    main()