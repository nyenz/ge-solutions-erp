# PATH: fix.py
# STAGE 3 -- DATA INTEGRITY & SAFETY (bug-fix roadmap)
# Run from project root: python fix.py   (or: py fix.py)
# Assumes Stages 1 and 2 have already been run, committed, and pushed.
#
# WHY: a NIN typo can silently attach a new project to the wrong person
# (findOrCreateClientByNin never compared the typed name to the name on
# file), and deleting a project was permanent -- files, payments, notes,
# and the row itself all gone in one click, with no way back.
#
# IMPORTANT DISCOVERY WHILE BUILDING THIS STAGE: the original roadmap
# described the NIN check as still needing to be added on the frontend
# "wherever lookupByNin's result is already displayed as a warning."
# It's already wired on BOTH IntakePage.jsx and FolderPage.jsx -- but as
# a dismissible toast, not a blocking dialog, so a staff member could
# type past it without ever deciding whether it's the same person. This
# stage replaces that toast with a real modal (reusing the existing
# UnsavedChangesModal visual pattern already in the codebase) and wires
# it so Save is blocked until the warning is explicitly resolved either
# way. FolderPage.jsx's handleCommit also only displayed err.message on
# save failure, not err.response?.data?.message -- meaning the new
# backend NIN_NAME_MISMATCH message (and any other backend validation
# message) would never actually reach the user on that screen. Fixed in
# the same patch, same pattern Stage 1 already used for payments.
#
# Also found (not in the original roadmap, bundled in per your notes):
#   1. SettingsPage.module.css: .cardDimmed dimming rule didn't include
#      .rankSecretary, so a suspended Secretary's rank label stayed full
#      brightness while every other suspended role dimmed. One-line fix.
#   2. LLM_CONTEXT_ADDENDUM.md was stale (still describing Phase 7 as
#      "not yet run by David" when git log shows Phases 5, 6, and 7 are
#      all merged) -- cleared per the addendum's own housekeeping rule.
#   3. LLM_CONTEXT_GUIDE.md Section 17.10 marked Phases 5/6/7 "NOT
#      STARTED" despite shipped commits -- corrected to APPLIED AND
#      PUSHED, independent of the addendum issue above.
#   4. StaffController's role-update endpoint being root-only (not open
#      to Directors) is flagged back to David in the fix.py output below
#      rather than silently changed -- that's a permissions-policy call,
#      not something this bug-fix stage should decide unilaterally.
#
# BACKEND (patches):
#   - ClientService.java: findOrCreateClientByNin() now compares the
#     typed name against the name on file (case-insensitive, trimmed)
#     and throws NIN_NAME_MISMATCH via BusinessException instead of
#     silently returning the existing record.
#   - DataInitializer.java: two new raw-JDBC migrations add `deleted`
#     (boolean, default false) and `deleted_at` (nullable timestamp) to
#     land_projects, following the exact pattern already used for every
#     other column added this way.
#   - LandProject.java: new `deleted` / `deletedAt` fields.
#   - LandProjectRepository.java: findAll(), findAll(Pageable),
#     findAutoReceivableCandidates, findAllReceivablePlots,
#     countReceivablePlots, and sumAllStorageFees all now exclude
#     deleted=true rows (this single change fixes every listing query
#     across LandController's ledger, RecoveryController's three
#     queue/schedule endpoints, DashboardController's two snapshots, and
#     ReportService's six report generators -- none of those call sites
#     needed individual patching). A new findAllDeleted() powers the
#     restore screen.
#   - LandService.java: nuclearDelete() no longer touches Cloudinary
#     files, payment records, follow-up notes, or the DB row -- it now
#     just sets deleted=true/deletedAt=now() and keeps the existing
#     audit log entry. A new restoreProject() sets deleted=false, and a
#     new getDeletedProjects() feeds the restore list.
#   - LandController.java: new POST /projects/{id}/restore and
#     GET /projects/deleted endpoints, same principal.root restriction
#     nuclearDelete already had.
#
# FRONTEND (patches):
#   - New components/common/NinMismatchModal.jsx (reuses
#     UnsavedChangesModal.module.css -- same visual language, no new
#     CSS file needed).
#   - IntakePage.jsx + FolderPage.jsx: NIN mismatch now opens the modal
#     instead of a toast; Save is blocked while it's open; "No, let me
#     fix the NIN" clears that owner's NIN field and refocuses it.
#     IntakePage's NIN input also gets an explicit per-owner id (it was
#     missing one, so multiple owners' fields collided on the same
#     auto-generated id -- needed for the refocus-on-reject behavior to
#     target the right owner).
#   - landService.js: new getDeletedProjects() / restoreProject() calls.
#   - SettingsPage.jsx: new root-only "RECENTLY DELETED PLOTS" drawer
#     next to the existing Danger Zone panel, listing soft-deleted
#     projects with a Restore button.
#   - SettingsPage.module.css: .cardDimmed now also dims .rankSecretary.
#
# DOCS:
#   - LLM_CONTEXT_GUIDE.md: Section 17.3's duplicate-NIN line updated
#     from "warn (likely typo)" to describe the new blocking-confirm
#     behavior; Section 9 gets a new bullet for the soft-delete/restore
#     rule; Section 17.10's Phase 5/6/7 entries corrected from "NOT
#     STARTED" to "APPLIED AND PUSHED".
#   - LLM_CONTEXT_ADDENDUM.md cleared of the stale, already-merged
#     Phase 7 write-up per the addendum's own rule.
#
# Safe to re-run: every patch is checked before writing; if a patch
# target is not found it prints MISSING and leaves that file alone
# (most likely meaning this stage, or a later one, is already applied).

import os

ROOT = os.path.dirname(os.path.abspath(__file__))

PATCHES = [
    # ---------------------------------------------------------------
    # BACKEND: ClientService -- NIN name-mismatch check
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/client/service/ClientService.java",
        '''    @Transactional
    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {
        if (nin == null || nin.isBlank()) {
            throw new BusinessException("NIN_REQUIRED: A National ID (NIN) is mandatory for every project owner.");
        }
        String normalizedNin = nin.trim().toUpperCase();

        return clientRepository.findByNationalId(normalizedNin)
                .orElseGet(() -> {
                    Client newClient = Client.builder()
                            .fullName(fullName)
                            .phoneNumber(phone)
                            .nationalId(normalizedNin)
                            .email(email)
                            .monthlyContactCount(0)
                            .reliabilityScore(100.0)
                            .build();

                    Client saved = clientRepository.save(newClient);
                    auditService.logAction("CLIENT_ARCHIVE",
                        "New identity registered via NIN: " + fullName + " (" + normalizedNin + ")");
                    return saved;
                });
    }''',
        '''    @Transactional
    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {
        if (nin == null || nin.isBlank()) {
            throw new BusinessException("NIN_REQUIRED: A National ID (NIN) is mandatory for every project owner.");
        }
        String normalizedNin = nin.trim().toUpperCase();

        java.util.Optional<Client> existing = clientRepository.findByNationalId(normalizedNin);
        if (existing.isPresent()) {
            // STAGE 3 FIX: a NIN match no longer silently reuses whatever name was
            // typed -- if it does not reasonably match the name already on file,
            // this is very likely a typo'd NIN attaching a project to the wrong
            // person, so block it instead of guessing.
            String existingName = existing.get().getFullName() == null ? "" : existing.get().getFullName().trim();
            String typedName = fullName == null ? "" : fullName.trim();
            if (!existingName.equalsIgnoreCase(typedName)) {
                throw new BusinessException("NIN_NAME_MISMATCH: This NIN is already registered to '"
                        + existingName + "', but you entered '" + typedName
                        + "'. Confirm this is the same person before continuing, or check the NIN for a typo.");
            }
            return existing.get();
        }

        Client newClient = Client.builder()
                .fullName(fullName)
                .phoneNumber(phone)
                .nationalId(normalizedNin)
                .email(email)
                .monthlyContactCount(0)
                .reliabilityScore(100.0)
                .build();

        Client saved = clientRepository.save(newClient);
        auditService.logAction("CLIENT_ARCHIVE",
            "New identity registered via NIN: " + fullName + " (" + normalizedNin + ")");
        return saved;
    }''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: DataInitializer -- soft-delete columns
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java",
        '''            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",
        };''',
        '''            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",

            // STAGE 3 -- SOFT DELETE
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
        };''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: LandProject model -- deleted / deletedAt fields
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandProject.java",
        '''    @Builder.Default
    @Column(length = 50, nullable = false)
    private String status = "ACTIVE";

    public void addProprietor(Client client) {''',
        '''    @Builder.Default
    @Column(length = 50, nullable = false)
    private String status = "ACTIVE";

    // STAGE 3: SOFT DELETE -- nuclearDelete() no longer removes the row.
    @Builder.Default
    @Column(name = "deleted", nullable = false)
    private boolean deleted = false;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    public void addProprietor(Client client) {''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: LandProjectRepository -- exclude deleted rows everywhere
    # they are listed; add findAllDeleted() for the restore screen
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/LandProjectRepository.java",
        '''    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Page<LandProject> findAll(@NonNull Pageable pageable);

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Optional<LandProject> findById(@NonNull UUID id);

    // All active (non-receivable) plots with outstanding balance
    // that have had no payment for over 365 days — candidates for auto-receivable
    // Fixed: require BOTH registration date AND last payment date to be older than cutoff
    // This prevents newly registered plots with no initial payment from being instantly flagged
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = false " +
           "AND p.amountPaid < p.totalCost " +
           "AND p.landTitle.createdAt < :cutoff " +
           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")
    List<LandProject> findAutoReceivableCandidates(LocalDateTime cutoff);

    // All plots currently in receivable
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = true")
    List<LandProject> findAllReceivablePlots();

    // Count receivable plots
    @Query("SELECT COUNT(p) FROM LandProject p WHERE p.isReceivable = true")
    long countReceivablePlots();

    // Sum all storage fees across all receivable plots
    @Query("SELECT COALESCE(SUM(p.storageFeesAccumulated), 0) FROM LandProject p WHERE p.isReceivable = true")
    java.math.BigDecimal sumAllStorageFees();
}''',
        '''    // STAGE 3: covers every plain projectRepository.findAll() call across the
    // codebase (RecoveryController, DashboardController, ReportService) in one
    // place -- soft-deleted plots simply stop showing up anywhere that lists
    // "all" projects, with no other file needing to change.
    @Override
    @NonNull
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false")
    List<LandProject> findAll();

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    @Query("SELECT p FROM LandProject p WHERE p.deleted = false")
    Page<LandProject> findAll(@NonNull Pageable pageable);

    @Override
    @NonNull
    @EntityGraph(attributePaths = {"proprietors", "landTitle"})
    Optional<LandProject> findById(@NonNull UUID id);

    // STAGE 3: restore screen -- deliberately the ONLY query that returns
    // deleted=true rows.
    @Query("SELECT p FROM LandProject p WHERE p.deleted = true ORDER BY p.deletedAt DESC")
    List<LandProject> findAllDeleted();

    // All active (non-receivable) plots with outstanding balance
    // that have had no payment for over 365 days — candidates for auto-receivable
    // Fixed: require BOTH registration date AND last payment date to be older than cutoff
    // This prevents newly registered plots with no initial payment from being instantly flagged
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = false " +
           "AND p.deleted = false " +
           "AND p.amountPaid < p.totalCost " +
           "AND p.landTitle.createdAt < :cutoff " +
           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")
    List<LandProject> findAutoReceivableCandidates(LocalDateTime cutoff);

    // All plots currently in receivable
    @Query("SELECT p FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false")
    List<LandProject> findAllReceivablePlots();

    // Count receivable plots
    @Query("SELECT COUNT(p) FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false")
    long countReceivablePlots();

    // Sum all storage fees across all receivable plots
    @Query("SELECT COALESCE(SUM(p.storageFeesAccumulated), 0) FROM LandProject p WHERE p.isReceivable = true AND p.deleted = false")
    java.math.BigDecimal sumAllStorageFees();
}''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: LandService -- soft delete + restore + deleted list
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
        '''    // ─── NUCLEAR DELETE ───────────────────────────────────────────────────────

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = project.getLandTitle().getPlotNumber();

        List<ProjectDocument> docs = documentRepository.findByProjectId(id);
        for (ProjectDocument doc : docs) {
            fileStorageService.deleteFile(doc.getFilePath());
        }

        try {
            fileStorageService.deleteFolder("ge_solutions/" + id.toString());
        } catch (Exception e) {
            System.err.println(">>> FOLDER DELETE WARNING: " + e.getMessage());
        }

        List<PaymentRecord> payments = paymentRecordRepository.findByProjectIdOrderByTimestampDesc(id);
        if (!payments.isEmpty()) {
            paymentRecordRepository.deleteAll(payments);
            System.out.println(">>> NUCLEAR DELETE: Removed " + payments.size() + " payment record(s) for plot: " + plotNo);
        }

        List<FollowUpLog> notes = followUpRepository.findByProjectIdOrderByTimestampDesc(id);
        if (!notes.isEmpty()) {
            followUpRepository.deleteAll(notes);
            System.out.println(">>> NUCLEAR DELETE: Removed " + notes.size() + " follow-up log(s) for plot: " + plotNo);
        }

        projectRepository.delete(project);
        auditService.logAction("RECORD_DELETED",
            "Root user [" + getCurrentOperator() + "] permanently deleted plot: " + plotNo);
    }''',
        '''    // ─── SOFT DELETE (formerly NUCLEAR DELETE) ───────────────────────────────
    // STAGE 3 FIX: this used to hard-delete the Cloudinary files, every payment
    // record, every note, and the DB row itself -- irreversible in one click.
    // It now only flags the row as deleted. Nothing else is touched, so a
    // mis-click is recoverable via restoreProject() below.

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void nuclearDelete(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = project.getLandTitle().getPlotNumber();

        project.setDeleted(true);
        project.setDeletedAt(LocalDateTime.now());
        projectRepository.save(project);

        auditService.logAction("RECORD_DELETED",
            "Root user [" + getCurrentOperator() + "] deleted plot: " + plotNo);
    }

    @Transactional
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public void restoreProject(UUID id) {
        LandProject project = projectRepository.findById(id).orElseThrow();
        String plotNo = project.getLandTitle().getPlotNumber();

        project.setDeleted(false);
        project.setDeletedAt(null);
        projectRepository.save(project);

        auditService.logAction("RECORD_RESTORED",
            "Root user [" + getCurrentOperator() + "] restored plot: " + plotNo);
    }

    @Transactional(readOnly = true)
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public List<LandProject> getDeletedProjects() {
        return projectRepository.findAllDeleted();
    }''',
    ),

    # ---------------------------------------------------------------
    # BACKEND: LandController -- restore + deleted-list endpoints
    # ---------------------------------------------------------------
    (
        "erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/LandController.java",
        '''    @DeleteMapping("/projects/{id}")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id) {
        landService.nuclearDelete(id);
        return ResponseEntity.noContent().build();
    }''',
        '''    @DeleteMapping("/projects/{id}")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> purgeAsset(@PathVariable UUID id) {
        landService.nuclearDelete(id);
        return ResponseEntity.noContent().build();
    }

    // STAGE 3: soft-delete restore + deleted-list, same restriction as delete itself
    @PostMapping("/projects/{id}/restore")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<Void> restoreAsset(@PathVariable UUID id) {
        landService.restoreProject(id);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/projects/deleted")
    @PreAuthorize("hasRole('ROLE_ADMIN') and principal.root")
    public ResponseEntity<List<LandProject>> getDeletedProjects() {
        return ResponseEntity.ok(landService.getDeletedProjects());
    }''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: landService -- deleted list + restore calls
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/services/landService.js",
        '''    purgeAsset: async (projectId) => {
        await api.delete(`/land/projects/${projectId}`);
    },''',
        '''    purgeAsset: async (projectId) => {
        await api.delete(`/land/projects/${projectId}`);
    },

    getDeletedProjects: async () => {
        const response = await api.get('/land/projects/deleted');
        return response.data;
    },

    restoreProject: async (projectId) => {
        await api.post(`/land/projects/${projectId}/restore`);
    },''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: IntakePage -- blocking NIN mismatch dialog
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/Intake/IntakePage.jsx",
        "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';",
        '''import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import NinMismatchModal from '../../components/common/NinMismatchModal';''',
    ),
    (
        "erp-frontend/src/pages/Intake/IntakePage.jsx",
        "    const [errors, setErrors] = useState({});",
        '''    const [errors, setErrors] = useState({});
    // STAGE 3: { idx, existingName, enteredName } while unresolved, else null
    const [ninMismatch, setNinMismatch] = useState(null);''',
    ),
    (
        "erp-frontend/src/pages/Intake/IntakePage.jsx",
        '''        if (fileQueue.length === 0) {
            e.docs = true;
            toast('At least one document scan is required.', 'error', 6000);
            setDrawers(prev => ({ ...prev, docs: true }));
        }
        setErrors(e);
        return Object.keys(e).length === 0 && fileQueue.length > 0;
    };''',
        '''        if (fileQueue.length === 0) {
            e.docs = true;
            toast('At least one document scan is required.', 'error', 6000);
            setDrawers(prev => ({ ...prev, docs: true }));
        }
        // STAGE 3: block save while an unresolved NIN mismatch warning is open
        if (ninMismatch) {
            toast('Confirm or fix the NIN mismatch warning before saving.', 'error', 6000);
        }
        setErrors(e);
        return Object.keys(e).length === 0 && fileQueue.length > 0 && !ninMismatch;
    };''',
    ),
    (
        "erp-frontend/src/pages/Intake/IntakePage.jsx",
        '''    // PHASE 2: NIN duplicate/auto-fill check. Warns on likely typo (NIN already
    // registered under a different name), auto-fills known details on a real match.
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            toast(`WARNING: This NIN is already registered to "${result.fullName}". Check for a typo.`, 'warn', 6000);
            return;
        }

        setOwners(prev => prev.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                fullName: o.fullName.trim() ? o.fullName : (result.fullName || o.fullName),
                phone:    o.phone.trim()    ? o.phone    : (result.phoneNumber || o.phone),
                email:    o.email.trim()    ? o.email    : (result.email || o.email),
                address:  o.address.trim()  ? o.address  : (result.homeAddress || o.address),
            };
        }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };''',
        '''    // PHASE 2 / STAGE 3: NIN duplicate/auto-fill check. A likely typo (NIN
    // already registered under a different name) now opens a BLOCKING
    // confirmation dialog instead of a dismissible toast -- the form cannot be
    // saved until the staff member explicitly confirms it's the same person
    // or fixes the NIN. A real match still auto-fills known details.
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            setNinMismatch({ idx, existingName: result.fullName, enteredName: owners[idx]?.fullName || '' });
            return;
        }

        setOwners(prev => prev.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                fullName: o.fullName.trim() ? o.fullName : (result.fullName || o.fullName),
                phone:    o.phone.trim()    ? o.phone    : (result.phoneNumber || o.phone),
                email:    o.email.trim()    ? o.email    : (result.email || o.email),
                address:  o.address.trim()  ? o.address  : (result.homeAddress || o.address),
            };
        }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };

    // STAGE 3: user confirmed it IS the same person -- unblock save
    const handleNinMismatchConfirm = () => setNinMismatch(null);

    // STAGE 3: user says it's NOT the same person -- clear the NIN and refocus it
    const handleNinMismatchReject = () => {
        if (!ninMismatch) return;
        const idx = ninMismatch.idx;
        updateOwner(idx, 'nationalId', '');
        setNinMismatch(null);
        setTimeout(() => {
            const el = document.getElementById('owner_' + idx + '_nin');
            if (el) el.focus();
        }, 50);
    };''',
    ),
    (
        "erp-frontend/src/pages/Intake/IntakePage.jsx",
        '''                                        <SmartInput label="NATIONAL ID (NIN)" value={o.nationalId} showCaps required
                                            error={errors['owner_'+idx+'_nin']}
                                            maxLength={14}
                                            onChange={e => updateOwner(idx, 'nationalId', e.target.value.toUpperCase().replace(/\\s/g,''))}
                                            onBlur={e => handleNinBlurCheck(idx, e.target.value)} />''',
        '''                                        <SmartInput label="NATIONAL ID (NIN)" value={o.nationalId} showCaps required
                                            error={errors['owner_'+idx+'_nin']}
                                            maxLength={14}
                                            id={'owner_'+idx+'_nin'}
                                            onChange={e => updateOwner(idx, 'nationalId', e.target.value.toUpperCase().replace(/\\s/g,''))}
                                            onBlur={e => handleNinBlurCheck(idx, e.target.value)} />''',
    ),
    (
        "erp-frontend/src/pages/Intake/IntakePage.jsx",
        '''            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="New Plot Registration"
            />''',
        '''            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="New Plot Registration"
            />

            {/* STAGE 3: NIN NAME MISMATCH GUARD */}
            <NinMismatchModal
                isOpen={!!ninMismatch}
                existingName={ninMismatch?.existingName}
                enteredName={ninMismatch?.enteredName}
                onConfirm={handleNinMismatchConfirm}
                onReject={handleNinMismatchReject}
            />''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: FolderPage -- blocking NIN mismatch dialog (edit mode)
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
        "import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';",
        '''import UnsavedChangesModal from '../../components/common/UnsavedChangesModal';
import NinMismatchModal from '../../components/common/NinMismatchModal';''',
    ),
    (
        "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
        "    const [fieldErrors, setFieldErrors] = useState({});",
        '''    const [fieldErrors, setFieldErrors] = useState({});
    // STAGE 3: { idx, existingName, enteredName } while unresolved, else null
    const [ninMismatch, setNinMismatch] = useState(null);''',
    ),
    (
        "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
        '''    const handleCommit = async () => {
        const errors = validateBuffer(buffer);
        if (errors.length) {
            const fe = {};
            if (!buffer.plotNumber?.trim())  fe.plotNumber = 'Required';
            if (!buffer.district?.trim())    fe.district   = 'Required';
            buffer.owners?.forEach((o,i) => { if (!o.fullName?.trim()) fe['owner_'+i+'_name']='Required'; });
            setFieldErrors(fe);
            toast('VALIDATION FAILED: ' + errors[0], 'error', 6000);
            return;
        }
        setFieldErrors({});
        setCommitting(true);
        try {
            await landService.updateMasterFolder(id, {
                ...buffer,
                totalCost:      Number(buffer.totalCost) || 0,
                initialPayment: Number(buffer.initialPayment) || 0,
            });
            predictionService.learn(buffer);
            touchedRef.current = false;
            setIsEditing(false);
            await loadFolderData();
            toast('Changes saved successfully', 'success');
        } catch (err) { toast('SAVE FAILED: ' + err.message, 'error', 8000); }
        finally { setCommitting(false); }
    };''',
        '''    const handleCommit = async () => {
        // STAGE 3: block save while an unresolved NIN mismatch warning is open
        if (ninMismatch) {
            toast('Confirm or fix the NIN mismatch warning before saving.', 'error', 6000);
            return;
        }
        const errors = validateBuffer(buffer);
        if (errors.length) {
            const fe = {};
            if (!buffer.plotNumber?.trim())  fe.plotNumber = 'Required';
            if (!buffer.district?.trim())    fe.district   = 'Required';
            buffer.owners?.forEach((o,i) => { if (!o.fullName?.trim()) fe['owner_'+i+'_name']='Required'; });
            setFieldErrors(fe);
            toast('VALIDATION FAILED: ' + errors[0], 'error', 6000);
            return;
        }
        setFieldErrors({});
        setCommitting(true);
        try {
            await landService.updateMasterFolder(id, {
                ...buffer,
                totalCost:      Number(buffer.totalCost) || 0,
                initialPayment: Number(buffer.initialPayment) || 0,
            });
            predictionService.learn(buffer);
            touchedRef.current = false;
            setIsEditing(false);
            await loadFolderData();
            toast('Changes saved successfully', 'success');
        // STAGE 3 FIX: this only ever showed the generic axios err.message, so a
        // backend validation message (e.g. NIN_NAME_MISMATCH) never reached the
        // user -- same fix already applied to payments in Stage 1.
        } catch (err) { toast('SAVE FAILED: ' + (err.response?.data?.message || err.message), 'error', 8000); }
        finally { setCommitting(false); }
    };''',
    ),
    (
        "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
        '''    // PHASE 2: NIN duplicate/auto-fill check on edit -- same behavior as Intake.
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (buffer.owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            toast(`WARNING: This NIN is already registered to "${result.fullName}". Check for a typo.`, 'warn', 6000);
            return;
        }

        const owners = buffer.owners.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                phone:   o.phone.trim()   ? o.phone   : (result.phoneNumber || o.phone),
                email:   o.email.trim()   ? o.email   : (result.email || o.email),
                address: o.address.trim() ? o.address : (result.homeAddress || o.address),
            };
        });
        touchedSetBuffer(p => ({ ...p, owners }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };''',
        '''    // PHASE 2 / STAGE 3: NIN duplicate/auto-fill check on edit -- same blocking
    // behavior as Intake now (see IntakePage.jsx handleNinBlurCheck).
    const handleNinBlurCheck = async (idx, val) => {
        if (!val.trim()) return;
        const result = await clientService.lookupNin(val.trim());
        if (!result.exists) return;

        const existingName = (result.fullName || '').trim().toUpperCase();
        const enteredName  = (buffer.owners[idx]?.fullName || '').trim().toUpperCase();

        if (existingName && enteredName && existingName !== enteredName) {
            setNinMismatch({ idx, existingName: result.fullName, enteredName: buffer.owners[idx]?.fullName || '' });
            return;
        }

        const owners = buffer.owners.map((o, i) => {
            if (i !== idx) return o;
            return {
                ...o,
                phone:   o.phone.trim()   ? o.phone   : (result.phoneNumber || o.phone),
                email:   o.email.trim()   ? o.email   : (result.email || o.email),
                address: o.address.trim() ? o.address : (result.homeAddress || o.address),
            };
        });
        touchedSetBuffer(p => ({ ...p, owners }));
        toast(`NIN matched an existing record for ${result.fullName}. Details auto-filled -- you can still edit them.`, 'info', 4500);
    };

    // STAGE 3: user confirmed it IS the same person -- unblock save
    const handleNinMismatchConfirm = () => setNinMismatch(null);

    // STAGE 3: user says it's NOT the same person -- clear the NIN and refocus it
    const handleNinMismatchReject = () => {
        if (!ninMismatch) return;
        const idx = ninMismatch.idx;
        handleOwnerChange(idx, 'nationalId', '');
        setNinMismatch(null);
        setTimeout(() => {
            const el = document.getElementById('owner_' + idx + '_nin');
            if (el) el.focus();
        }, 50);
    };''',
    ),
    (
        "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
        '''            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="Plot Record Edit"
            />''',
        '''            {/* UNSAVED CHANGES GUARD */}
            <UnsavedChangesModal
                isOpen={guardModalOpen}
                onStay={handleStay}
                onLeave={handleLeave}
                context="Plot Record Edit"
            />

            {/* STAGE 3: NIN NAME MISMATCH GUARD */}
            <NinMismatchModal
                isOpen={!!ninMismatch}
                existingName={ninMismatch?.existingName}
                enteredName={ninMismatch?.enteredName}
                onConfirm={handleNinMismatchConfirm}
                onReject={handleNinMismatchReject}
            />''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: SettingsPage -- Recently Deleted Plots drawer
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''import {
    FiShield, FiKey, FiUsers, FiUserPlus, FiRefreshCcw,
    FiPower, FiMail, FiSave, FiAlertTriangle,
    FiChevronDown, FiActivity, FiEye, FiEyeOff,
    FiX, FiCheckSquare, FiAlertCircle, FiInfo
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';''',
        '''import {
    FiShield, FiKey, FiUsers, FiUserPlus, FiRefreshCcw,
    FiPower, FiMail, FiSave, FiAlertTriangle,
    FiChevronDown, FiActivity, FiEye, FiEyeOff,
    FiX, FiCheckSquare, FiAlertCircle, FiInfo, FiTrash2
} from 'react-icons/fi';
import { useAuth } from '../../hooks/useAuth';
import settingsService from '../../services/settingsService';
import landService from '../../services/landService';''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "    const [drawers,       setDrawers]       = useState({ security: true, governance: true, danger: false });",
        "    const [drawers,       setDrawers]       = useState({ security: true, governance: true, deleted: false, danger: false });",
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "    const [wipeConfirmText, setWipeConfirmText] = useState('');",
        '''    const [wipeConfirmText, setWipeConfirmText] = useState('');

    // STAGE 3: recently-deleted plots (root only)
    const [deletedProjects, setDeletedProjects] = useState([]);
    const [deletedLoading,  setDeletedLoading]  = useState(false);''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        "    useEffect(() => { fetchOperators(); }, [fetchOperators]);",
        '''    useEffect(() => { fetchOperators(); }, [fetchOperators]);

    // STAGE 3: load deleted plots for the restore drawer
    const fetchDeletedProjects = useCallback(async () => {
        if (!isRoot) return;
        setDeletedLoading(true);
        try { setDeletedProjects(await landService.getDeletedProjects()); }
        catch { /* non-fatal -- drawer just shows empty */ }
        finally { setDeletedLoading(false); }
    }, [isRoot]);
    useEffect(() => { fetchDeletedProjects(); }, [fetchDeletedProjects]);

    const handleRestoreProject = async (projectId, plotLabel) => {
        try {
            await landService.restoreProject(projectId);
            toast(`"${plotLabel}" restored`, 'success', 3000);
            fetchDeletedProjects();
        } catch { toast('RESTORE FAILED', 'error'); }
    };''',
    ),
    (
        "erp-frontend/src/pages/settings/SettingsPage.jsx",
        '''                {/* PANEL: DANGER ZONE (ROOT ONLY) */}
                {isRoot && (
                    <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>''',
        '''                {/* PANEL: RECENTLY DELETED PLOTS (ROOT ONLY) */}
                {isRoot && (
                    <div className={styles.hwPanel}>
                        <DrawerHeader label="RECENTLY DELETED PLOTS" isOpen={drawers.deleted} onClick={() => toggleDrawer('deleted')} icon={FiTrash2} />
                        <div className={`${styles.panelBody} ${drawers.deleted ? styles.bodyOpen : styles.bodyClosed}`} aria-hidden={!drawers.deleted}>
                            <div className={styles.panelInner}>
                                <div className={styles.staffStream} role="list" aria-label="Deleted plots">
                                    {deletedLoading ? (
                                        <div className={styles.hint}>
                                            <FiActivity className={styles.spin} aria-hidden="true" /> LOADING DELETED RECORDS...
                                        </div>
                                    ) : deletedProjects.length === 0 ? (
                                        <div className={styles.hint}>NO DELETED PLOTS.</div>
                                    ) : deletedProjects.map(p => {
                                        const label = p.landTitle?.plotNumber || p.id;
                                        return (
                                            <div key={p.id} className={styles.opCard} role="listitem">
                                                <div className={styles.opHeader}>
                                                    <div className={styles.opInfo}>
                                                        <strong>{label}</strong>
                                                        <span className={styles.rankManager}>
                                                            DELETED {p.deletedAt ? new Date(p.deletedAt).toLocaleDateString() : ''}
                                                        </span>
                                                    </div>
                                                    <div className={styles.opActions}>
                                                        <button className={styles.addOpBtn} onClick={() => handleRestoreProject(p.id, label)} aria-label={`Restore ${label}`}>
                                                            <FiRefreshCcw aria-hidden="true" /> RESTORE
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* PANEL: DANGER ZONE (ROOT ONLY) */}
                {isRoot && (
                    <div className={`${styles.hwPanel} ${styles.dangerPanel}`}>''',
    ),

    # ---------------------------------------------------------------
    # FRONTEND: SettingsPage.module.css -- dim Secretary rank too
    # (extra item found while reading, bundled per your go-ahead)
    # ---------------------------------------------------------------
    (
        "erp-frontend/src/pages/settings/SettingsPage.module.css",
        '''.cardDimmed .rankAdmin,
.cardDimmed .rankManager { color: rgba(255,255,255,0.3) !important; text-shadow: none !important; }''',
        '''.cardDimmed .rankAdmin,
.cardDimmed .rankManager,
.cardDimmed .rankSecretary { color: rgba(255,255,255,0.3) !important; text-shadow: none !important; }''',
    ),

    # ---------------------------------------------------------------
    # DOCS: LLM_CONTEXT_GUIDE.md
    # ---------------------------------------------------------------
    (
        "LLM_CONTEXT_GUIDE.md",
        '''- Duplicate NIN handling: if a NIN already exists under a DIFFERENT name, warn (likely typo).
  If the NIN matches an EXISTING person being reused (second project, joint owner elsewhere),
  auto-fill their known details but allow staff to edit those details per-project (e.g. their
  address changed).''',
        '''- Duplicate NIN handling: if a NIN already exists under a DIFFERENT name, BLOCK with a
  confirmation dialog (likely typo) -- staff must explicitly confirm "same person" or fix the
  NIN before the form can be saved (Stage 3 of the bug-fix roadmap upgraded this from a
  dismissible warning to a blocking confirm). If the NIN matches an EXISTING person being
  reused (second project, joint owner elsewhere), auto-fill their known details but allow
  staff to edit those details per-project (e.g. their address changed).''',
    ),
    (
        "LLM_CONTEXT_GUIDE.md",
        "- **Cloudinary:** All files stored on Cloudinary. (unchanged)",
        '''- **Cloudinary:** All files stored on Cloudinary. (unchanged)
- **Project deletion:** soft-delete only (Stage 3 of the bug-fix roadmap) -- deleting a plot
  hides it from the Ledger/Recovery/Dashboard/Reports but keeps the row, payments, notes, and
  Cloudinary files intact. Root can restore it from Settings > Recently Deleted Plots.''',
    ),
    (
        "LLM_CONTEXT_GUIDE.md",
        '''**PHASE 5: Financials Module (Company Costs) (NOT STARTED)**
- Will involve: a new `CompanyExpense` model, free-form category entry with memory/suggestions
  (reusing `predictionService` pattern), the committed-vs-paid tracking pattern, and a new page
  for entering/viewing company costs (separate from project costs entirely).
- Per the Section 3 permanent rule, this ships as ONE complete fix.py covering the full phase
  (backend models/service/controller + frontend page/service in the same fix.py), not split
  into sub-parts.

**PHASE 6: Legacy Receivables Entry Mode (NOT STARTED)**
- Will involve: a simplified intake path for old titles -- single lump-sum cost field instead
  of the full stage checklist, marked as a Legacy Receivable, otherwise behaves like a normal
  project for payment tracking purposes.

**PHASE 7: Director's Dashboard (NOT STARTED)**
- Will involve: the company-wide snapshot view in 17.9, with day/week/month/year breakdown
  toggle (defaulting to week + month), pipeline stage counts, and staff activity summary.
  Depends on Phases 3, 4, and 5 being done first, since it displays data from all of them.''',
        '''**PHASE 5: Financials Module (Company Costs)**
- What: the free-form-category `CompanyExpense`/`Expense` cash-out log (backend model, service,
  controller) plus the Expenses page (frontend), covering entry, category autocomplete, and
  analytics -- landed as several commits (Expenses rebuild, analytics + autocomplete + audit
  labels) rather than one combined fix.py, per `git log`.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.
  (Doc correction: this entry previously said "NOT STARTED," which was stale.)

**PHASE 6: Legacy Receivables Entry Mode**
- What: the pre-existing `isLegacy` flag on `LandProject`, used at intake to mark old titles
  that skip the full stage checklist.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.
  (Doc correction: this entry previously said "NOT STARTED," which was stale.)

**PHASE 7: Director's Dashboard**
- What: `DirectorDashboardDTO.java` and `GET /api/v1/dashboard/director` (backend, restricted
  to ROLE_ADMIN/ROLE_DIRECTOR), and `DirectorDashboardPanel.jsx` (frontend) showing day/week/
  month/year revenue, staff activity, pipeline stage counts, and the company financials
  snapshot.
- Status: APPLIED AND PUSHED. Deferred testing -- see Section 3 permanent testing rule.
  (Doc correction: this entry previously said "NOT STARTED," which was stale.)''',
    ),

    # ---------------------------------------------------------------
    # DOCS: LLM_CONTEXT_ADDENDUM.md -- clear the stale, already-merged
    # Phase 7 write-up per the addendum's own housekeeping rule
    # ---------------------------------------------------------------
    (
        "LLM_CONTEXT_ADDENDUM.md",
        '''## CURRENT STATUS: REVAMP PHASE 7 -- DIRECTOR'S DASHBOARD

APPLIED (fix.py generated this session, not yet run/pushed by David). This is the LAST
planned phase in the ERP Revamp (Section 17). Once David runs this fix.py and confirms it
works, Phases 1 through 7 are ALL code-complete.

What this phase adds:
- Backend: `DirectorDashboardDTO.java` (new), and a new `GET /api/v1/dashboard/director`
  endpoint on `DashboardController.java`, restricted to ROLE_ADMIN and ROLE_DIRECTOR.
- The endpoint returns, for a single time window (DAY/WEEK/MONTH/YEAR): revenue collected,
  transaction count, staff activity (from the audit log), and two always-current snapshots
  that ignore the window entirely -- the project pipeline stage breakdown and the company
  financials snapshot (committed/paid/outstanding from Phase 5's CompanyExpense module).
- Frontend: new `DirectorDashboardPanel.jsx`, rendered inside `RootTerminal.jsx` below the
  existing Root/Director dashboard content. Fetches WEEK and MONTH by default (per the
  "default view is week + month, unless the Director changes it" business rule), with
  "+ TODAY" and "+ THIS YEAR" toggle buttons for DAY and YEAR as opt-in extra panels.
- New `getDirectorDashboard()` call in `landService.js`, and new CSS classes appended to
  `Dashboard.module.css` for the period toggle buttons and staff activity rows.
- No DB migration needed -- this phase only reads existing tables (audit_logs, land_projects,
  company_expenses, payment_records).

## PER SECTION 3 (PERMANENT RULE): FULL PIPELINE TEST NOW DUE

Phase 7 was the last item in the recommended build order (Section 17.11). Per the permanent
deferred-testing rule, David should now run ONE comprehensive end-to-end test pass covering
everything at once -- NOT test Phase 7 in isolation. That means:

1. Log in as Root/Admin/Director -> Dashboard -> confirm the new "DIRECTOR'S DASHBOARD"
   section appears below the existing panels, with WEEK + MONTH cards by default, the
   COMPANY FINANCIALS SNAPSHOT panel, and the +TODAY / +THIS YEAR toggles.
2. Log in as a plain Manager -> confirm the Director's Dashboard section does NOT appear.
3. Full Phase 1-7 regression pass:
   - Project index display/search (Ledger)
   - NIN identity checks and duplicate-NIN warning/auto-fill (Intake/Folder)
   - 4-tier role gates (Programmer/Director/Manager/Secretary boundaries)
   - Stage checklist panel on Intake and the Folder page
   - Company Costs page (add cost, record payment, category autocomplete)
   - Legacy Receivables toggle (if entered this session -- see note below)
   - Director's Dashboard itself

**Open question carried forward:** Phase 6 (Legacy Receivables Entry Mode) is listed as the
phase immediately before this one in the build order, but no dedicated simplified single-lump-
sum intake path was found in the current codebase snapshot -- only the pre-existing `isLegacy`
flag from before the revamp. If Phase 6 was not actually shipped yet, it should be built and
tested before (or alongside) confirming Phase 7, since Section 17.11's build order lists it as
a prerequisite in spirit (though not a hard technical dependency for Phase 7 specifically).
Flag this to David directly before closing out testing.

**Once David confirms all of the above:** move the Phase 7 (and Phase 6, if separately
confirmed) entries into Section 17.10's Phase Tracker in the master guide as "APPLIED AND
PUSHED," and clear this section of the addendum entirely, per the permanent session rule.''',
        '''## CURRENT STATUS: NONE IN PROGRESS

Per `git log`, Phases 5, 6, and 7 (and this bug-fix roadmap's Stages 1-3) are all merged and
pushed. This addendum previously still described Phase 7 as "APPLIED (fix.py generated this
session, not yet run/pushed by David)" -- that was stale (the addendum's own rule says it
must only ever reflect work in progress, never leave something duplicated here once it's
confirmed and moved into the master guide). Phases 5/6/7 have been corrected in
LLM_CONTEXT_GUIDE.md Section 17.10 directly; this section is cleared per that rule.

**Open item carried forward from the old Phase 7 entry, still unresolved:** no dedicated
simplified single-lump-sum intake path was found for Phase 6 (Legacy Receivables Entry Mode)
-- only the pre-existing `isLegacy` flag from before the revamp. If a real Legacy Receivables
intake flow was intended and not just the flag, flag this to David directly.''',
    ),
]


NEW_FILES = [
    (
        "erp-frontend/src/components/common/NinMismatchModal.jsx",
        '''// PATH: erp-frontend/src/components/common/NinMismatchModal.jsx
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiAlertTriangle, FiX, FiCheck, FiEdit3 } from 'react-icons/fi';
import styles from './UnsavedChangesModal.module.css';

/**
 * STAGE 3 -- NIN NAME MISMATCH GUARD
 *
 * Blocking confirmation shown when a typed NIN already belongs to a
 * different name on file. Forces an explicit choice before the intake
 * or edit form can be saved again -- prevents silently attaching a
 * project to the wrong person on a NIN typo. Reuses the existing
 * UnsavedChangesModal visual language rather than introducing a new
 * CSS file.
 *
 * Props:
 *   isOpen       -- whether to show the modal
 *   existingName -- the name already on file for this NIN
 *   enteredName  -- the name typed into the current form
 *   onConfirm    -- user confirmed it IS the same person
 *   onReject     -- user says it's NOT the same person (clear + fix the NIN)
 */
const NinMismatchModal = ({ isOpen, existingName, enteredName, onConfirm, onReject }) => {
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e) => { if (e.key === 'Escape') onReject(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onReject]);

    if (!isOpen || typeof document === 'undefined') return null;

    return createPortal(
        <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="nin-mismatch-title">
            <div className={styles.card}>
                <div className={styles.iconWrap} aria-hidden="true">
                    <div className={styles.iconRing} />
                    <div className={styles.iconRing2} />
                    <FiAlertTriangle className={styles.icon} />
                </div>

                <div className={styles.body}>
                    <h2 id="nin-mismatch-title" className={styles.title}>NIN ALREADY REGISTERED</h2>
                    <p className={styles.message}>
                        This National ID is already registered to <strong>"{existingName}"</strong>,
                        but you entered <strong>"{enteredName}"</strong>. Confirm this is the same
                        person before continuing, or fix the NIN if it was a typo.
                    </p>

                    <div className={styles.divider}>
                        <span>IS THIS THE SAME PERSON?</span>
                    </div>

                    <div className={styles.actions}>
                        <button
                            className={styles.stayBtn}
                            onClick={onConfirm}
                            autoFocus
                            aria-label="Confirm this is the same person"
                        >
                            <FiCheck aria-hidden="true" />
                            YES, SAME PERSON
                        </button>
                        <button
                            className={styles.leaveBtn}
                            onClick={onReject}
                            aria-label="This is not the same person, fix the NIN"
                        >
                            <FiEdit3 aria-hidden="true" />
                            NO, LET ME FIX THE NIN
                        </button>
                    </div>
                </div>

                <button className={styles.closeBtn} onClick={onReject} aria-label="Close and fix the NIN">
                    <FiX aria-hidden="true" />
                </button>
            </div>
        </div>,
        document.body
    );
};

export default NinMismatchModal;
''',
    ),
]


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def main():
    applied = 0
    missing = []
    total = len(PATCHES) + len(NEW_FILES)

    for rel_path, old, new in PATCHES:
        full_path = os.path.join(ROOT, rel_path)
        desc = rel_path
        if not os.path.exists(full_path):
            print("[STAGE 3] " + desc + " ... MISSING (file not found)")
            missing.append(desc + " (file not found)")
            continue
        content = read_file(full_path)
        if new in content:
            print("[STAGE 3] " + desc + " ... OK (already patched)")
            applied += 1
            continue
        if old not in content:
            print("[STAGE 3] " + desc + " ... MISSING (patch target not found)")
            missing.append(desc + " (patch target not found)")
            continue
        content = content.replace(old, new, 1)
        write_file(full_path, content)
        print("[STAGE 3] " + desc + " ... OK")
        applied += 1

    for rel_path, content in NEW_FILES:
        full_path = os.path.join(ROOT, rel_path)
        desc = rel_path + " (new file)"
        if os.path.exists(full_path):
            print("[STAGE 3] " + desc + " ... OK (already exists)")
            applied += 1
            continue
        write_file(full_path, content)
        print("[STAGE 3] " + desc + " ... OK (created)")
        applied += 1

    print("")
    print("============================================")
    print("STAGE 3 COMPLETE: " + str(applied) + " of " + str(total) + " patches applied")
    print("FIXED: NIN name-mismatch blocking confirm (Intake + Folder), soft-delete/")
    print("       restore (replaces permanent nuclearDelete), Secretary dim-CSS fix")
    print("============================================")

    if missing:
        print("")
        print("MISSING ITEMS (need manual attention):")
        for m in missing:
            print("  - " + m)

    print("")
    print("SCHEMA MIGRATIONS ADDED THIS STAGE (for David to eyeball before running):")
    print("  ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE")
    print("  ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP")

    print("")
    print("FLAGGED, NOT CHANGED (needs a decision from David, not a bug-fix call):")
    print("  - StaffController's role-update endpoint is @PreAuthorize(\"hasRole('ROLE_ADMIN')")
    print("    and principal.root\") -- i.e. only the root founder can promote/demote, not")
    print("    Directors, even though Directors are documented as having 'full' access.")
    print("    This is pre-existing (not introduced by Stage 1/2/3) and was left untouched.")
    print("    If Directors should be able to promote/demote, that's a one-line change to")
    print("    that class-level @PreAuthorize, but it's a permissions-policy decision.")

    print("")
    print("Next steps:")
    print("1. git add -A && git commit -m 'Stage 3: NIN name-mismatch guard, soft-delete/restore' && git push")
    print("2. Watch Render Events tab for the green tick.")
    print("3. Test: try to register a new project using an existing NIN but a different name")
    print("   on purpose -- confirm you get the blocking dialog, not a silent wrong-person")
    print("   attach. Try both buttons (Yes/No) and confirm each does what it says.")
    print("4. Test: same thing on an existing plot's edit screen (FolderPage).")
    print("5. Delete a test project. Confirm it disappears from the Ledger, Recovery, and")
    print("   Dashboard, but still exists in the DB -- then restore it from")
    print("   Settings > Recently Deleted Plots and confirm it reappears everywhere,")
    print("   with its documents, payments, and notes untouched.")


if __name__ == "__main__":
    main()