# PATH: fix_stage12.py  (STAGE 12)
# STAGE 12 -- Render the SOLO/JOINT ownership row and navigable co-owner
#             links on each Recovery plot sub-card (design brief 3.3).
# Run from project root: py fix_stage12.py
#
# CONTEXT / WHAT WAS ACTUALLY VERIFIED (git-cloned repo read directly)
# -------------------------------------------------------------------------
# Confirmed via `git log` and direct code read: Stage 9 (Recovery joint-owner
# card visibility) and Stage 10 (per-owner call attribution, per-owner note,
# merged log-a-contact action) are already committed and working on the
# BACKEND. RecoveryController.buildOwnerTasks already returns, per plot:
#   - ownershipType ("SOLO" or "JOINT")
#   - coOwners (list of {clientId, fullName} for every OTHER proprietor)
#   - ownerLastContactDate / ownerLastContactNote (THIS card-owner's own
#     reach status for this specific project, not a shared field)
# Stage 10 also added the CSS for this (.ownershipRow, .soloBadge,
# .jointBadge, .jointOwnersLabel, .coOwnerLink) to RecoveryPortal.module.css.
#
# BUG FOUND: none of that ever made it into RecoveryPortal.jsx's actual JSX.
# The Stage 10 JSX diff only touched the call modal (attributing a call to
# the right owner) -- it never added the badge row or co-owner links
# themselves. Result: every plot sub-card looks identical whether it is
# SOLO or JOINT, staff cannot see who else owns a joint plot, and there is
# no way to jump to a co-owner's own card. This is the single most-emphasized
# requirement in design brief 3.3 ("clearly labeled", "named and are
# navigable") and it was backend-ready but not user-visible.
#
# ALSO FOUND (smaller, same area): the existing "LAST CONTACT NOTE" block on
# each sub-card shows the most recent FollowUpLog for the PROJECT as a whole
# (any owner's call), not this card-owner's own note. On a JOINT plot that
# can read as "we already reached this person" when actually a co-owner was
# the one reached. Fixed by adding a distinct "YOU last reached" line/note
# using the owner-specific fields, and relabeling the shared note on JOINT
# plots to "MOST RECENT NOTE (ANY OWNER)" so the two are never confused.
#
# THE FIX
# -------------------------------------------------------------------------
# Frontend only (erp-backend already has everything it needs -- see above):
#   1. RecoveryPortal.jsx: add scrollTargetId state + an effect that scrolls
#      a co-owner's card into view once it is present in the loaded list.
#   2. RecoveryPortal.jsx: add handleGoToCoOwner(e, coOwnerId) -- clears
#      search/status filters, switches to ALL TARGETS (so a co-owner who is
#      currently locked/cooling-down is not hidden by the DUE FOR CALL
#      filter), expands their card, and queues the scroll.
#   3. RecoveryPortal.jsx: give each mission card a stable DOM id
#      ("recovery-card-<clientId>") so the scroll effect can find it.
#   4. RecoveryPortal.jsx: render the ownership badge row (SOLO/JOINT +
#      clickable co-owner names) and the "YOU last reached" per-owner line
#      on every plot sub-card, using fields the backend already returns.
#   5. RecoveryPortal.jsx: relabel the shared last-contact note on JOINT
#      plots so it cannot be mistaken for this owner's own contact history.
#   6. RecoveryPortal.module.css: add the one small new class this needs
#      (.ownerContactLine) -- everything else (.ownershipRow, .soloBadge,
#      .jointBadge, .jointOwnersLabel, .coOwnerLink) already exists from
#      Stage 10 and just gets used for the first time here.
#
# Nothing here touches the backend, the database, or any endpoint contract.
# Every field this patch reads (ownershipType, coOwners, ownerLastContactDate,
# ownerLastContactNote) is already present in RecoveryTaskDTO.PlotSummary and
# already sent by GET /api/v1/recovery/queue and /schedule.

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

results = []


def patch(label, rel_path, old, new):
    path = os.path.join(ROOT, rel_path)
    if not os.path.exists(path):
        print("[STAGE 12] " + label + " ... MISSING (file not found: " + rel_path + ")")
        results.append(False)
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Check idempotency FIRST: some of these patches' "new" text starts with
    # the same lines as "old" (we are inserting right after an anchor), so
    # checking "old in content" first would find that anchor again even
    # after the patch already landed and silently double-insert. Always
    # confirm the patch is not already applied before looking for the target.
    if new in content:
        print("[STAGE 12] " + label + " ... OK (already applied)")
        results.append(True)
        return

    if old not in content:
        print("[STAGE 12] " + label + " ... MISSING (patch target not found in " + rel_path + ")")
        results.append(False)
        return

    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("[STAGE 12] " + label + " ... OK")
    results.append(True)


# ─── 1. scrollTargetId state ────────────────────────────────────────────────
patch(
    "RecoveryPortal: add scrollTargetId state for co-owner navigation",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "    const [coOwnerWarning, setCoOwnerWarning] = useState(null);\n",
    "    const [coOwnerWarning, setCoOwnerWarning] = useState(null);\n"
    "    // STAGE 12 FIX: lets a co-owner link (design brief 3.3, \"navigable\")\n"
    "    // jump to that person's own card even if it is filtered out or\n"
    "    // collapsed right now -- clears filters, expands their card, then\n"
    "    // scrolls to it once it is present in the loaded mission list.\n"
    "    const [scrollTargetId, setScrollTargetId] = useState(null);\n",
)

# ─── 2. scroll-into-view effect ─────────────────────────────────────────────
patch(
    "RecoveryPortal: add scroll-to-co-owner effect",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "    useEffect(() => { loadData(); }, [loadData]);\n",
    "    useEffect(() => { loadData(); }, [loadData]);\n"
    "\n"
    "    // STAGE 12 FIX: once the mission list contains the co-owner we just\n"
    "    // navigated to, scroll their card into view. Runs again whenever\n"
    "    // missions reloads (e.g. after switching to ALL TARGETS) until found.\n"
    "    useEffect(() => {\n"
    "        if (!scrollTargetId) return;\n"
    "        const el = document.getElementById('recovery-card-' + scrollTargetId);\n"
    "        if (el) {\n"
    "            el.scrollIntoView({ behavior: 'smooth', block: 'center' });\n"
    "            setScrollTargetId(null);\n"
    "        }\n"
    "    }, [missions, scrollTargetId]);\n",
)

# ─── 3. handleGoToCoOwner handler ───────────────────────────────────────────
patch(
    "RecoveryPortal: add handleGoToCoOwner handler",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "        setCallModal({ open: true, mission: plot, ownerId, ownerName });\n"
    "        setLogContent(lastNote);\n"
    "    };\n"
    "\n"
    "    return (\n",
    "        setCallModal({ open: true, mission: plot, ownerId, ownerName });\n"
    "        setLogContent(lastNote);\n"
    "    };\n"
    "\n"
    "    // STAGE 12 FIX: co-owner link handler (design brief 3.3). Switches to\n"
    "    // ALL TARGETS so a locked/cooling-down co-owner is not hidden by the\n"
    "    // DUE FOR CALL filter, clears search/status filters that could hide\n"
    "    // their card, expands their card, and queues the scroll-to for the\n"
    "    // effect above.\n"
    "    const handleGoToCoOwner = (e, coOwnerId) => {\n"
    "        e.stopPropagation();\n"
    "        setSearchTerm('');\n"
    "        setStatusFilter('ALL');\n"
    "        setViewMode('FORECAST');\n"
    "        setExpandedId(coOwnerId);\n"
    "        setScrollTargetId(coOwnerId);\n"
    "    };\n"
    "\n"
    "    return (\n",
)

# ─── 4. stable DOM id on each mission card ──────────────────────────────────
patch(
    "RecoveryPortal: add stable id to each mission card for scroll targeting",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "                            <div\n"
    "                                key={m.clientId}\n"
    "                                className={`${styles.missionCard} ${m.hasReceivablePlots ? styles.cardReceivable : ''}`}\n"
    "                            >\n",
    "                            <div\n"
    "                                key={m.clientId}\n"
    "                                id={'recovery-card-' + m.clientId}\n"
    "                                className={`${styles.missionCard} ${m.hasReceivablePlots ? styles.cardReceivable : ''}`}\n"
    "                            >\n",
)

# ─── 5. ownership badge row + per-owner contact line ────────────────────────
patch(
    "RecoveryPortal: render SOLO/JOINT badge row + co-owner links + YOU-last-reached line",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "                                                <div className={styles.plotSubCardHeader}>\n"
    "                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>\n"
    "                                                    <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber || '---'}</span>\n"
    "                                                </div>\n"
    "                                                {p.isReceivable && p.surveyDate && (\n",
    "                                                <div className={styles.plotSubCardHeader}>\n"
    "                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>\n"
    "                                                    <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber || '---'}</span>\n"
    "                                                </div>\n"
    "\n"
    "                                                {/* STAGE 12 FIX: SOLO/JOINT badge + navigable co-owner links\n"
    "                                                    (design brief 3.3). The backend has supplied\n"
    "                                                    p.ownershipType / p.coOwners since Stage 10, and the CSS\n"
    "                                                    for this row has existed since Stage 10 too -- this was\n"
    "                                                    the missing piece that actually renders it. */}\n"
    "                                                <div className={styles.ownershipRow}>\n"
    "                                                    <span className={p.ownershipType === 'JOINT' ? styles.jointBadge : styles.soloBadge}>\n"
    "                                                        {p.ownershipType}\n"
    "                                                    </span>\n"
    "                                                    {p.ownershipType === 'JOINT' && p.coOwners && p.coOwners.length > 0 && (\n"
    "                                                        <>\n"
    "                                                            <span className={styles.jointOwnersLabel}>WITH:</span>\n"
    "                                                            {p.coOwners.map((co, i) => (\n"
    "                                                                <React.Fragment key={co.clientId}>\n"
    "                                                                    <button\n"
    "                                                                        type=\"button\"\n"
    "                                                                        className={styles.coOwnerLink}\n"
    "                                                                        onClick={e => handleGoToCoOwner(e, co.clientId)}\n"
    "                                                                    >\n"
    "                                                                        {co.fullName}\n"
    "                                                                    </button>\n"
    "                                                                    {i < p.coOwners.length - 1 && (\n"
    "                                                                        <span className={styles.jointOwnersLabel}>,</span>\n"
    "                                                                    )}\n"
    "                                                                </React.Fragment>\n"
    "                                                            ))}\n"
    "                                                        </>\n"
    "                                                    )}\n"
    "                                                </div>\n"
    "\n"
    "                                                {/* STAGE 12 FIX: THIS owner's own reach status for this\n"
    "                                                    project, separate from the general note below -- on a\n"
    "                                                    JOINT plot the general note can belong to a co-owner's\n"
    "                                                    call and must never be mistaken for this owner having\n"
    "                                                    been personally reached (design brief 3.3). */}\n"
    "                                                <div className={styles.ownerContactLine}>\n"
    "                                                    YOU last reached: <strong>{p.ownerLastContactDate || 'NEVER'}</strong>\n"
    "                                                </div>\n"
    "                                                {p.ownerLastContactNote && (\n"
    "                                                    <div className={styles.interactionNote}>\n"
    "                                                        <span className={styles.interactionNoteLabel}>YOUR LAST NOTE WITH THIS OWNER</span>\n"
    "                                                        <p className={styles.interactionNoteText}>{p.ownerLastContactNote}</p>\n"
    "                                                    </div>\n"
    "                                                )}\n"
    "\n"
    "                                                {p.isReceivable && p.surveyDate && (\n",
)

# ─── 6. relabel the shared note on JOINT plots ──────────────────────────────
patch(
    "RecoveryPortal: relabel shared last-contact note on JOINT plots",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.jsx",
    "                                                {p.lastInteractionNote && p.lastInteractionNote !== 'NO PRIOR CONTACT' && (\n"
    "                                                    <div className={styles.interactionNote}>\n"
    "                                                        <span className={styles.interactionNoteLabel}>LAST CONTACT NOTE</span>\n"
    "                                                        <p className={styles.interactionNoteText}>{p.lastInteractionNote}</p>\n"
    "                                                    </div>\n"
    "                                                )}\n",
    "                                                {p.lastInteractionNote && p.lastInteractionNote !== 'NO PRIOR CONTACT' && (\n"
    "                                                    <div className={styles.interactionNote}>\n"
    "                                                        {/* STAGE 12 FIX: on a JOINT plot this note can belong\n"
    "                                                            to a co-owner's call, not this card-owner's --\n"
    "                                                            relabeled so it is never confused with the\n"
    "                                                            YOUR LAST NOTE WITH THIS OWNER block above. */}\n"
    "                                                        <span className={styles.interactionNoteLabel}>\n"
    "                                                            {p.ownershipType === 'JOINT' ? 'MOST RECENT NOTE (ANY OWNER)' : 'LAST CONTACT NOTE'}\n"
    "                                                        </span>\n"
    "                                                        <p className={styles.interactionNoteText}>{p.lastInteractionNote}</p>\n"
    "                                                    </div>\n"
    "                                                )}\n",
)

# ─── 7. small new CSS class ──────────────────────────────────────────────────
patch(
    "RecoveryPortal.module.css: add .ownerContactLine style",
    "erp-frontend/src/pages/Recovery/RecoveryPortal.module.css",
    ".coOwnerWarningDismiss:hover { color: #fff; }\n"
    ".coOwnerWarningDismiss:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }\n",
    ".coOwnerWarningDismiss:hover { color: #fff; }\n"
    ".coOwnerWarningDismiss:focus-visible { outline: 2px solid var(--orange); outline-offset: 2px; }\n"
    "\n"
    "/* -- STAGE 12: per-owner \"you last reached\" line on each plot sub-card -- */\n"
    ".ownerContactLine {\n"
    "    font-family: 'DM Sans', sans-serif;\n"
    "    font-size: clamp(9px, 0.9vw, 11px);\n"
    "    font-weight: 700;\n"
    "    color: rgba(255, 255, 255, 0.5);\n"
    "    margin-bottom: clamp(6px, 0.8vw, 9px);\n"
    "}\n"
    ".ownerContactLine strong { color: rgba(255, 255, 255, 0.85); }\n",
)

print("")
if all(results):
    print("All Stage 12 patches applied cleanly.")
else:
    print("Some patches were MISSING -- review output above before committing.")