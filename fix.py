# PATH: fix.py  (STAGE 10)
# STAGE 10 -- Recovery "log a call" always credits the wrong joint owner,
#             and joint projects share one anonymous note field
# Run from project root: py fix.py
#
# CONTEXT / WHAT WAS ACTUALLY VERIFIED
# -------------------------------------------------------------------------
# This builds directly on Stage 9 (already applied in this repo), which made
# every proprietor get their own Recovery card for a joint project instead
# of only the alphabetically-first "primary" owner. Reading the code that
# Stage 9 left behind turned up the actual blocker for the agreed design in
# section 3.3 of the brief:
#
#   LandService.logFollowUp(UUID projectId, String content)
#   -- called by POST /api/v1/land/projects/{id}/follow-up, which is what
#      fires every time staff hit "LOG CALL" in the Recovery UI --
#   ALWAYS resolved the contact to whichever proprietor's fullName sorts
#   first alphabetically, no matter which co-owner staff actually reached:
#
#       Client primaryOwner = project.getProprietors().stream()
#               .filter(o -> o != null && o.getId() != null)
#               .min(Comparator.comparing(Client::getFullName))
#               .orElse(null);
#       if (primaryOwner != null) {
#           clientService.logManagerContact(primaryOwner.getId());
#       }
#
#   Concretely, on a joint project with owners "Bob Okello" and "Alice
#   Namono": staff call Bob, log the note -- and the system resets ALICE's
#   14-day cooldown clock and increments ALICE's monthly counter, because
#   "Alice" sorts before "Bob". Bob's own lastContactedAt never moves. This
#   is the exact opposite of "contact/cooldown tracking stays per person...
#   staff should be able to call different joint owners... independently"
#   from the agreed direction (3.3) -- it was already broken before this
#   patch, for every joint project, regardless of the Stage 9 card-fanout
#   fix.
#
#   The note itself (FollowUpLog) also had no owner attached at all -- one
#   shared row per project, so a joint project's "last contact note" shown
#   on Bob's card and on Alice's card was literally the same string, which
#   is the "one shared/anonymous note field" the brief explicitly says NOT
#   to build (3.3, bullet 5).
#
#   On top of that, logFollowUp had a "PATCH 3" side effect that copied the
#   note verbatim (prefixed "[SYNCED FROM <plot>]") onto every OTHER
#   outstanding plot the resolved "primary" owner held -- including plots
#   totally unrelated to the call that was actually made, and doing so
#   under whichever co-owner won the alphabetical draw. That fabricates
#   contact history that never happened and had to go.
#
#   Neither the frontend (RecoveryPortal.jsx) nor the service layer
#   (recoveryService.js) ever sent an owner/client id with the call log at
#   all -- confirmed directly in both files -- so the backend had no way to
#   know who was actually reached even if it wanted to.
#
# THE FIX
# -------------------------------------------------------------------------
# Backend:
#   1. FollowUpLog gets a nullable ownerId column: which specific person
#      this contact/note is about. Null is fine for general project notes
#      added via the separate "add a note" action (logNewNote), which was
#      never owner-specific and stays that way.
#   2. FollowUpRepository gets a per-owner lookup
#      (findByProjectIdAndOwnerIdOrderByTimestampDesc) so Recovery can pull
#      a specific person's own contact history on a specific project.
#   3. LandService.logFollowUp now REQUIRES the caller to say which owner
#      was reached, verifies that owner is actually a proprietor of the
#      project (rejects otherwise), updates ONLY that person's cooldown
#      state, and stamps the saved note with that owner's id. This is the
#      "merge log-a-call and add-a-note into one action that captures
#      project + specific owner + when + what was said" from open question
#      3.4 #1 -- answered by requiring ownerId on the existing endpoint
#      rather than inventing a second one. The cross-plot note-sync side
#      effect is removed entirely: a call about one project no longer
#      writes fabricated notes onto someone else's other projects.
#   4. LandController's /follow-up endpoint takes the new required
#      ownerId param and passes it straight through.
#   5. RecoveryTaskDTO.PlotSummary gains: ownershipType ("SOLO"/"JOINT"),
#      coOwners (id + name, navigable client-side), and this card-owner's
#      OWN last-contact date/note on that project -- pulled via the new
#      per-owner repository method. The underlying balance calculation is
#      untouched: it is still computed once per project and only
#      referenced on each owner's card, never duplicated or re-totaled,
#      so this change cannot cause double-counting in reporting (3.3,
#      last bullet).
#   6. RecoveryController.buildOwnerTasks populates those new fields per
#      plot, per card-owner.
#
# Frontend:
#   7. recoveryService.logRecoveryCall now takes and sends ownerId.
#   8. RecoveryPortal's call modal is opened with the CARD's own
#      clientId/ownerName attached, so the log call action is always
#      attributed to the person whose card triggered it -- never silently
#      defaulted to some other co-owner -- and the modal pre-fills with
#      THAT owner's own last note, not a shared one. The plot sub-card now
#      shows a SOLO/JOINT label and, for JOINT lines, clickable co-owner
#      chips that expand straight to that co-owner's own card (3.3,
#      bullets 1-3).
#
# NOT addressed here (left for the next design session per 3.4):
#   - Whether joint calls should affect monthly report totals / dashboard
#     "stale count" math beyond what Stage 9 already changed.
#   - Any soft warning ("Bob was already called 3 days ago") when a second
#     joint owner is called inside the same window -- explicitly still
#     open in 3.4, not decided, so nothing was added for it.
#   - Whether "primary" should be dropped as a concept everywhere (some
#     read-only labels/comments elsewhere in the codebase still use the
#     word informally; this patch does not do a global rename).
#
# Safe to re-run: each patch is checked before writing; if a target is not
# found it prints MISSING and leaves that file alone (most likely meaning
# this stage, or that specific patch, is already applied). Nothing here
# touches the database directly -- the new `owner_id` column on
# follow_up_logs is picked up by Hibernate's schema update on next boot in
# dev; wire an explicit migration before shipping to an environment that
# doesn't auto-update schema.

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
        print("[STAGE 10] " + label + " ... MISSING (file not found: " + rel_path + ")")
        return False
    content = read_file(full_path)
    if old not in content:
        if new in content:
            print("[STAGE 10] " + label + " ... OK (already applied)")
            return True
        print("[STAGE 10] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        return False
    content = content.replace(old, new, 1)
    write_file(full_path, content)
    print("[STAGE 10] " + label + " ... OK")
    return True


def main():
    print("=" * 70)
    print("STAGE 10 -- joint-owner contact misattribution + shared note field")
    print("=" * 70)

    ok = 0
    total = 0

    # ------------------------------------------------------------------ #
    # 1. FollowUpLog: add per-owner column
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "FollowUpLog: add nullable ownerId so a contact/note can be tied "
        "to the specific person reached, not just the project",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/FollowUpLog.java",

        "    @Column(name = \"project_id\", nullable = false)\n"
        "    private UUID projectId;\n"
        "\n"
        "    /**\n"
        "     * THE INTELLIGENCE: Detailed record of the interaction or status.\n"
        "     */",

        "    @Column(name = \"project_id\", nullable = false)\n"
        "    private UUID projectId;\n"
        "\n"
        "    /**\n"
        "     * STAGE 10 FIX: WHICH PERSON THIS CONTACT BELONGS TO.\n"
        "     * Null for general project notes not tied to a specific call (e.g.\n"
        "     * logNewNote). Set whenever this entry comes from logFollowUp, so a\n"
        "     * joint project's contact history can be shown per owner instead of\n"
        "     * one shared/anonymous note field (design brief 3.3).\n"
        "     */\n"
        "    @Column(name = \"owner_id\")\n"
        "    private UUID ownerId;\n"
        "\n"
        "    /**\n"
        "     * THE INTELLIGENCE: Detailed record of the interaction or status.\n"
        "     */",
    )

    # ------------------------------------------------------------------ #
    # 2. FollowUpRepository: per-owner lookup
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "FollowUpRepository: add findByProjectIdAndOwnerIdOrderByTimestampDesc",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/FollowUpRepository.java",

        "    List<FollowUpLog> findByProjectIdOrderByTimestampDesc(UUID projectId);\n"
        "    \n"
        "    /**\n"
        "     * Recovery Search: Find logs by specific author (Admin/Manager).\n"
        "     */",

        "    List<FollowUpLog> findByProjectIdOrderByTimestampDesc(UUID projectId);\n"
        "\n"
        "    /**\n"
        "     * STAGE 10 FIX: per-owner contact history for a joint project -- lets\n"
        "     * Recovery show each owner's own last-reached note instead of one\n"
        "     * shared note field for the whole project (design brief 3.3).\n"
        "     */\n"
        "    List<FollowUpLog> findByProjectIdAndOwnerIdOrderByTimestampDesc(UUID projectId, UUID ownerId);\n"
        "    \n"
        "    /**\n"
        "     * Recovery Search: Find logs by specific author (Admin/Manager).\n"
        "     */",
    )

    # ------------------------------------------------------------------ #
    # 3. LandService.logFollowUp: require + honor the actual owner reached
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "LandService.logFollowUp: attribute the call to the owner staff "
        "actually reached, drop the cross-plot note-sync side effect",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",

        "    @Transactional(rollbackFor = Exception.class)\n"
        "    public void logFollowUp(UUID projectId, String content) {\n"
        "        LandProject project = projectRepository.findById(projectId).orElseThrow();\n"
        "\n"
        "        // PATCH 2: Only increment call counter for the PRIMARY owner (alphabetically first),\n"
        "        // not all joint owners, to avoid accidental counter inflation.\n"
        "        Client primaryOwner = null;\n"
        "        if (project.getProprietors() != null && !project.getProprietors().isEmpty()) {\n"
        "            primaryOwner = project.getProprietors().stream()\n"
        "                    .filter(o -> o != null && o.getId() != null)\n"
        "                    .min(java.util.Comparator.comparing(Client::getFullName))\n"
        "                    .orElse(null);\n"
        "            if (primaryOwner != null) {\n"
        "                try { clientService.logManagerContact(primaryOwner.getId()); } catch (Exception e) {}\n"
        "            }\n"
        "        }\n"
        "\n"
        "        // Save note to this plot\n"
        "        String operator = getCurrentOperator();\n"
        "        FollowUpLog entry = FollowUpLog.builder()\n"
        "                .projectId(projectId)\n"
        "                .notes(content)\n"
        "                .recordedBy(operator)\n"
        "                .build();\n"
        "        followUpRepository.save(entry);\n"
        "\n"
        "        // PATCH 3: If the primary owner also owns other outstanding plots,\n"
        "        // automatically copy this follow-up note to those plots as well.\n"
        "        if (primaryOwner != null) {\n"
        "            final Client finalPrimary = primaryOwner;\n"
        "            List<LandProject> allProjects = projectRepository.findAll();\n"
        "            for (LandProject otherPlot : allProjects) {\n"
        "                if (otherPlot.getId().equals(projectId)) continue;\n"
        "                boolean ownedByPrimary = otherPlot.getProprietors() != null &&\n"
        "                    otherPlot.getProprietors().stream()\n"
        "                        .anyMatch(o -> o != null && o.getId() != null &&\n"
        "                                  o.getId().equals(finalPrimary.getId()));\n"
        "                if (!ownedByPrimary) continue;\n"
        "                // Only sync to plots with outstanding balance (active cases)\n"
        "                java.math.BigDecimal bal = otherPlot.isReceivable()\n"
        "                        ? otherPlot.receivableTotalOwed() : otherPlot.activeTotalOwed();\n"
        "                if (bal.compareTo(java.math.BigDecimal.ZERO) <= 0) continue;\n"
        "                FollowUpLog syncEntry = FollowUpLog.builder()\n"
        "                        .projectId(otherPlot.getId())\n"
        "                        .notes(\"[SYNCED FROM \" + project.getLandTitle().getPlotNumber() + \"] \" + content)\n"
        "                        .recordedBy(operator)\n"
        "                        .build();\n"
        "                followUpRepository.save(syncEntry);\n"
        "            }\n"
        "        }\n"
        "\n"
        "        auditService.logAction(\"RECOVERY_SYNC\",\n"
        "            \"Operator [\" + operator + \"] logged call for plot: \"\n"
        "            + project.getLandTitle().getPlotNumber());\n"
        "    }",

        "    // STAGE 10 FIX: NIN_JOINT_OWNER_CONTACT_MISATTRIBUTION (design brief 3.3/3.4)\n"
        "    // Previously this always logged the contact against whichever proprietor's\n"
        "    // fullName sorted first alphabetically (\"primary owner\"), regardless of\n"
        "    // which co-owner staff actually reached -- silently resetting the WRONG\n"
        "    // person's 14-day cooldown clock while the person really contacted never\n"
        "    // got their own record updated. It also auto-copied the note onto every\n"
        "    // OTHER outstanding plot the resolved primary owner held, fabricating\n"
        "    // contact history on unrelated projects. Both behaviors are removed.\n"
        "    // The caller must now name the specific owner being logged (this is the\n"
        "    // \"merge log-a-call and add-a-note into one action\" from open question\n"
        "    // 3.4 #1 -- project + specific owner + timestamp + note, in one record).\n"
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
    )

    # ------------------------------------------------------------------ #
    # 4. LandController: require ownerId on the follow-up endpoint
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "LandController: /follow-up endpoint now requires ownerId",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",

        "    // STAGE 2 FIX: Secretary logs recovery calls (data-entry)\n"
        "    @PreAuthorize(\"hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')\")\n"
        "    @PostMapping(\"/projects/{id}/follow-up\")\n"
        "    public ResponseEntity<Void> logContact(@PathVariable UUID id, @RequestParam String content) {\n"
        "        landService.logFollowUp(id, content);\n"
        "        return ResponseEntity.ok().build();\n"
        "    }",

        "    // STAGE 2 FIX: Secretary logs recovery calls (data-entry)\n"
        "    // STAGE 10 FIX: ownerId is now required so a joint-project call is\n"
        "    // attributed to the specific person staff actually reached, instead of\n"
        "    // silently defaulting to whichever co-owner sorts first alphabetically\n"
        "    // (design brief 3.3/3.4).\n"
        "    @PreAuthorize(\"hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')\")\n"
        "    @PostMapping(\"/projects/{id}/follow-up\")\n"
        "    public ResponseEntity<Void> logContact(@PathVariable UUID id,\n"
        "                                            @RequestParam UUID ownerId,\n"
        "                                            @RequestParam String content) {\n"
        "        landService.logFollowUp(id, ownerId, content);\n"
        "        return ResponseEntity.ok().build();\n"
        "    }",
    )

    # ------------------------------------------------------------------ #
    # 5. RecoveryTaskDTO: SOLO/JOINT + co-owners + per-owner contact
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "RecoveryTaskDTO.PlotSummary: add ownershipType, coOwners, and "
        "this card-owner's own last-contact date/note",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java",

        "        private String paymentHealthBadge;\n"
        "        private String lastPaymentDate;\n"
        "        private String lastInteractionNote;\n"
        "        private LocalDate surveyDate;\n"
        "    }\n"
        "}",

        "        private String paymentHealthBadge;\n"
        "        private String lastPaymentDate;\n"
        "        private String lastInteractionNote;\n"
        "        private LocalDate surveyDate;\n"
        "\n"
        "        // STAGE 10: joint-owner visibility (design brief 3.3)\n"
        "        private String ownershipType; // \"SOLO\" or \"JOINT\"\n"
        "        private List<CoOwnerRef> coOwners; // other owners on this project, empty for SOLO\n"
        "        private String ownerLastContactDate; // THIS card-owner's own last-reached date, or \"NEVER\"\n"
        "        private String ownerLastContactNote; // THIS card-owner's own note from that contact, or null\n"
        "    }\n"
        "\n"
        "    @Data\n"
        "    @Builder\n"
        "    @NoArgsConstructor\n"
        "    @AllArgsConstructor\n"
        "    public static class CoOwnerRef {\n"
        "        private UUID clientId;\n"
        "        private String fullName;\n"
        "    }\n"
        "}",
    )

    # ------------------------------------------------------------------ #
    # 6. RecoveryController: populate the new per-owner fields
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "RecoveryController.buildOwnerTasks: label SOLO/JOINT, list "
        "navigable co-owners, and pull each owner's OWN contact history",
        "erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java",

        "            for (LandProject plot : plots) {\n"
        "                List<FollowUpLog> logs = followUpRepository.findByProjectIdOrderByTimestampDesc(plot.getId());\n"
        "                String lastNote = logs.isEmpty() ? \"NO PRIOR CONTACT\" : logs.get(0).getNotes();\n"
        "\n"
        "                BigDecimal plotBalance = plot.isReceivable() ? plot.receivableTotalOwed() : plot.activeTotalOwed();\n"
        "                totalDemand = totalDemand.add(plotBalance);\n"
        "\n"
        "                String badge = computePaymentBadge(plot);\n"
        "                String lastPaymentStr = plot.getLastPaymentDate() != null\n"
        "                        ? plot.getLastPaymentDate().toLocalDate().toString() : \"NEVER\";\n"
        "\n"
        "                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()\n"
        "                        .projectId(plot.getId())\n"
        "                        .plotNumber(plot.getLandTitle().getPlotNumber())\n"
        "                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())\n"
        "                        .isReceivable(plot.isReceivable())\n"
        "                        .lastInteractionNote(lastNote)\n"
        "                        .paymentHealthBadge(badge)\n"
        "                        .lastPaymentDate(lastPaymentStr)\n"
        "                        .surveyDate(plot.getLandTitle().getSurveyDate());",

        "            for (LandProject plot : plots) {\n"
        "                List<FollowUpLog> logs = followUpRepository.findByProjectIdOrderByTimestampDesc(plot.getId());\n"
        "                String lastNote = logs.isEmpty() ? \"NO PRIOR CONTACT\" : logs.get(0).getNotes();\n"
        "\n"
        "                BigDecimal plotBalance = plot.isReceivable() ? plot.receivableTotalOwed() : plot.activeTotalOwed();\n"
        "                totalDemand = totalDemand.add(plotBalance);\n"
        "\n"
        "                String badge = computePaymentBadge(plot);\n"
        "                String lastPaymentStr = plot.getLastPaymentDate() != null\n"
        "                        ? plot.getLastPaymentDate().toLocalDate().toString() : \"NEVER\";\n"
        "\n"
        "                // STAGE 10: SOLO vs JOINT label + navigable co-owners + this\n"
        "                // owner's OWN contact history on this project (design brief 3.3).\n"
        "                // The balance is still computed exactly once above, from the\n"
        "                // project (plotBalance / totalDemand) -- it is only ever\n"
        "                // referenced here, never duplicated or re-totaled per owner, so\n"
        "                // this cannot cause a joint debt to be double-counted in\n"
        "                // company-wide reporting just because it appears on more than\n"
        "                // one person's card.\n"
        "                Set<Client> plotOwners = plot.getProprietors();\n"
        "                String ownershipType = (plotOwners != null && plotOwners.size() > 1) ? \"JOINT\" : \"SOLO\";\n"
        "                List<RecoveryTaskDTO.CoOwnerRef> coOwners = new ArrayList<>();\n"
        "                if (plotOwners != null) {\n"
        "                    for (Client co : plotOwners) {\n"
        "                        if (co == null || co.getId() == null || co.getId().equals(client.getId())) continue;\n"
        "                        coOwners.add(RecoveryTaskDTO.CoOwnerRef.builder()\n"
        "                                .clientId(co.getId())\n"
        "                                .fullName(co.getFullName())\n"
        "                                .build());\n"
        "                    }\n"
        "                }\n"
        "\n"
        "                List<FollowUpLog> ownerLogs = followUpRepository\n"
        "                        .findByProjectIdAndOwnerIdOrderByTimestampDesc(plot.getId(), client.getId());\n"
        "                String ownerLastContactDate = ownerLogs.isEmpty()\n"
        "                        ? \"NEVER\" : ownerLogs.get(0).getTimestamp().toLocalDate().toString();\n"
        "                String ownerLastContactNote = ownerLogs.isEmpty() ? null : ownerLogs.get(0).getNotes();\n"
        "\n"
        "                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()\n"
        "                        .projectId(plot.getId())\n"
        "                        .plotNumber(plot.getLandTitle().getPlotNumber())\n"
        "                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())\n"
        "                        .isReceivable(plot.isReceivable())\n"
        "                        .lastInteractionNote(lastNote)\n"
        "                        .paymentHealthBadge(badge)\n"
        "                        .lastPaymentDate(lastPaymentStr)\n"
        "                        .surveyDate(plot.getLandTitle().getSurveyDate())\n"
        "                        .ownershipType(ownershipType)\n"
        "                        .coOwners(coOwners)\n"
        "                        .ownerLastContactDate(ownerLastContactDate)\n"
        "                        .ownerLastContactNote(ownerLastContactNote);",
    )

    # ------------------------------------------------------------------ #
    # 7. recoveryService.js: send ownerId
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "recoveryService.logRecoveryCall: send ownerId to the backend",
        "erp-frontend/src/services/recoveryService.js",

        "    logRecoveryCall: async (projectId, text) => {\n"
        "        await api.post(`/land/projects/${projectId}/follow-up`, null, {\n"
        "            params: { content: text }\n"
        "        });\n"
        "        return true;\n"
        "    },",

        "    logRecoveryCall: async (projectId, ownerId, text) => {\n"
        "        await api.post(`/land/projects/${projectId}/follow-up`, null, {\n"
        "            params: { ownerId, content: text }\n"
        "        });\n"
        "        return true;\n"
        "    },",
    )

    # ------------------------------------------------------------------ #
    # 8. RecoveryPortal.jsx: attribute the modal to the right owner,
    #    show SOLO/JOINT + navigable co-owners
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "RecoveryPortal: call-log state carries ownerId/ownerName",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "    const [callModal,    setCallModal]    = useState({ open: false, mission: null });",

        "    // STAGE 10 FIX: the call log has to say WHICH owner was reached, not\n"
        "    // just which plot -- carry the card's own clientId/ownerName through.\n"
        "    const [callModal,    setCallModal]    = useState({ open: false, mission: null, ownerId: null, ownerName: '' });",
    )

    total += 1
    ok += patch(
        "RecoveryPortal: handleLogCall / openCallModal attribute the "
        "call to the card's owner, not a shared default",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "    const handleLogCall = async () => {\n"
        "        if (!callModal.mission) return;\n"
        "        setCommitting(true);\n"
        "        try {\n"
        "            await recoveryService.logRecoveryCall(callModal.mission.projectId, logContent);\n"
        "            setCallModal({ open: false, mission: null });\n"
        "            setLogContent('');\n"
        "            loadData();\n"
        "        } catch { /* silent */ }\n"
        "        finally { setCommitting(false); }\n"
        "    };\n"
        "\n"
        "    const openCallModal = (e, plot) => {\n"
        "        e.stopPropagation();\n"
        "        // PRE-FILL textarea with the last interaction note so user can edit/append\n"
        "        const lastNote = plot.lastInteractionNote && plot.lastInteractionNote !== 'NO PRIOR CONTACT'\n"
        "            ? plot.lastInteractionNote\n"
        "            : '';\n"
        "        setCallModal({ open: true, mission: plot });\n"
        "        setLogContent(lastNote);\n"
        "    };",

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
        "    };\n"
        "\n"
        "    // STAGE 10 FIX: caller now passes ownerId/ownerName from the card that\n"
        "    // triggered this modal, so a joint call is attributed to the actual\n"
        "    // person on that card -- never silently defaulted to a co-owner -- and\n"
        "    // pre-fills with THAT owner's own last note, not a shared one.\n"
        "    const openCallModal = (e, plot, ownerId, ownerName) => {\n"
        "        e.stopPropagation();\n"
        "        const lastNote = plot.ownerLastContactNote ? plot.ownerLastContactNote : '';\n"
        "        setCallModal({ open: true, mission: plot, ownerId, ownerName });\n"
        "        setLogContent(lastNote);\n"
        "    };",
    )

    total += 1
    ok += patch(
        "RecoveryPortal: LOG CALL button passes this card's owner along",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "                                                onClick={e => openCallModal(e, m.plots[0])}",

        "                                                onClick={e => openCallModal(e, m.plots[0], m.clientId, m.ownerName)}",
    )

    total += 1
    ok += patch(
        "RecoveryPortal: plot sub-card shows SOLO/JOINT + navigable "
        "co-owners, and this owner's own contact note instead of a "
        "shared one",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "                                {/* Last interaction note — notebook style */}\n"
        "                                {p.lastInteractionNote && p.lastInteractionNote !== 'NO PRIOR CONTACT' && (\n"
        "                                    <div className={styles.interactionNote}>\n"
        "                                        <span className={styles.interactionNoteLabel}>LAST CONTACT NOTE</span>\n"
        "                                        <p className={styles.interactionNoteText}>{p.lastInteractionNote}</p>\n"
        "                                    </div>\n"
        "                                )}",

        "                                {/* STAGE 10: SOLO vs JOINT + navigable co-owners (design brief 3.3) */}\n"
        "                                <div className={styles.ownershipRow}>\n"
        "                                    <span className={p.ownershipType === 'JOINT' ? styles.jointBadge : styles.soloBadge}>\n"
        "                                        {p.ownershipType || 'SOLO'}\n"
        "                                    </span>\n"
        "                                    {p.ownershipType === 'JOINT' && p.coOwners && p.coOwners.length > 0 && (\n"
        "                                        <>\n"
        "                                            <span className={styles.jointOwnersLabel}>Also owed by:</span>\n"
        "                                            {p.coOwners.map(co => (\n"
        "                                                <button\n"
        "                                                    key={co.clientId}\n"
        "                                                    type=\"button\"\n"
        "                                                    className={styles.coOwnerLink}\n"
        "                                                    onClick={ev => { ev.stopPropagation(); setSearchTerm(co.fullName); setExpandedId(co.clientId); }}\n"
        "                                                >\n"
        "                                                    {co.fullName}\n"
        "                                                </button>\n"
        "                                            ))}\n"
        "                                        </>\n"
        "                                    )}\n"
        "                                </div>\n"
        "\n"
        "                                {/* STAGE 10 FIX: shows what THIS owner said, not a shared/\n"
        "                                    anonymous note that could actually be a co-owner's contact. */}\n"
        "                                {p.ownerLastContactNote ? (\n"
        "                                    <div className={styles.interactionNote}>\n"
        "                                        <span className={styles.interactionNoteLabel}>\n"
        "                                            LAST CONTACT WITH {(m.ownerName || '').toUpperCase()} ({p.ownerLastContactDate})\n"
        "                                        </span>\n"
        "                                        <p className={styles.interactionNoteText}>{p.ownerLastContactNote}</p>\n"
        "                                    </div>\n"
        "                                ) : (\n"
        "                                    <div className={styles.interactionNote}>\n"
        "                                        <span className={styles.interactionNoteLabel}>\n"
        "                                            NO PRIOR CONTACT WITH {(m.ownerName || '').toUpperCase()}\n"
        "                                        </span>\n"
        "                                    </div>\n"
        "                                )}",
    )

    total += 1
    ok += patch(
        "RecoveryPortal: modal title/reset carry ownerName, close/cancel "
        "reset the new state fields too",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "            <HardwareModal\n"
        "                isOpen={callModal.open}\n"
        "                onClose={() => { setCallModal({ open: false, mission: null }); setLogContent(''); }}\n"
        "                title={callModal.mission ? `LOG CALL — ${callModal.mission.plotNumber}` : 'LOG CALL'}\n"
        "            >",

        "            <HardwareModal\n"
        "                isOpen={callModal.open}\n"
        "                onClose={() => { setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' }); setLogContent(''); }}\n"
        "                title={callModal.mission ? `LOG CALL — ${callModal.mission.plotNumber} (${callModal.ownerName || 'owner'})` : 'LOG CALL'}\n"
        "            >",
    )

    total += 1
    ok += patch(
        "RecoveryPortal: CANCEL button resets the new state fields too",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",

        "                        className={modalStyles.modalBtnSecondary}\n"
        "                        onClick={() => { setCallModal({ open: false, mission: null }); setLogContent(''); }}\n"
        "                    >\n"
        "                        CANCEL",

        "                        className={modalStyles.modalBtnSecondary}\n"
        "                        onClick={() => { setCallModal({ open: false, mission: null, ownerId: null, ownerName: '' }); setLogContent(''); }}\n"
        "                    >\n"
        "                        CANCEL",
    )

    # ------------------------------------------------------------------ #
    # 9. CSS: minimal styling for the new SOLO/JOINT row (additive only)
    # ------------------------------------------------------------------ #
    total += 1
    ok += patch(
        "RecoveryPortal.module.css: add styles for SOLO/JOINT badges and "
        "co-owner links (additive, appended at end of file)",
        "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",

        "    .finHUDCard strong {\n"
        "        font-size: clamp(16px, 5vw, 20px);\n"
        "        text-align: left;\n"
        "    }\n"
        "}",

        "    .finHUDCard strong {\n"
        "        font-size: clamp(16px, 5vw, 20px);\n"
        "        text-align: left;\n"
        "    }\n"
        "}\n"
        "\n"
        "/* ── STAGE 10: SOLO / JOINT ownership row on each plot sub-card ── */\n"
        ".ownershipRow {\n"
        "    display: flex; align-items: center; flex-wrap: wrap;\n"
        "    gap: clamp(6px, 0.8vw, 9px);\n"
        "    margin-bottom: clamp(6px, 0.8vw, 9px);\n"
        "}\n"
        ".soloBadge, .jointBadge {\n"
        "    font-family: 'Space Mono', monospace; font-size: clamp(7px, 0.75vw, 9px);\n"
        "    font-weight: 900; letter-spacing: 1px; text-transform: uppercase;\n"
        "    padding: clamp(2px, 0.3vw, 3px) clamp(7px, 0.9vw, 10px);\n"
        "    border-radius: 4px; white-space: nowrap;\n"
        "}\n"
        ".soloBadge {\n"
        "    background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.18);\n"
        "    color: rgba(255, 255, 255, 0.55);\n"
        "}\n"
        ".jointBadge {\n"
        "    background: rgba(238, 140, 58, 0.15); border: 1px solid rgba(238, 140, 58, 0.5);\n"
        "    color: var(--orange);\n"
        "}\n"
        ".jointOwnersLabel {\n"
        "    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px);\n"
        "    font-weight: 700; color: rgba(255, 255, 255, 0.4);\n"
        "}\n"
        ".coOwnerLink {\n"
        "    background: none; border: none; padding: 0;\n"
        "    font-family: 'DM Sans', sans-serif; font-size: clamp(9px, 0.9vw, 11px);\n"
        "    font-weight: 800; color: var(--orange); text-decoration: underline;\n"
        "    cursor: pointer;\n"
        "}\n"
        ".coOwnerLink:hover { color: #f0a050; }\n"
        ".coOwnerLink:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }",
    )

    print("-" * 70)
    print(str(ok) + "/" + str(total) + " patches applied")
    if ok < total:
        print("Some patches were MISSING -- review output above before committing.")
    print()
    print("Reminder: DB schema for the new follow_up_logs.owner_id column")
    print("needs an explicit migration in any environment without")
    print("Hibernate ddl-auto=update running against it.")


if __name__ == "__main__":
    main()

git add -A && git commit -m "stg 10" && git push