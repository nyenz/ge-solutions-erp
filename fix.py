import os

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read_file(path)
    if old in content:
        write_file(path, content.replace(old, new, 1))
        print(f"OK: {label}")
    else:
        print(f"MISSING: {label}")

BASE = os.path.dirname(os.path.abspath(__file__))

# ── PATCH 1: Auto-backlog glitch ─────────────────────────────────
# LandTitle has createdAt. LandProject links to LandTitle via landTitle.
# We update the JPQL query to also require landTitle.createdAt older than cutoff.

scheduler_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com',
    'gesolutions', 'erp', 'modules', 'land', 'service', 'BacklogSchedulerService.java')

patch(
    scheduler_path,
    '    @Scheduled(cron = "0 0 6 * * *")\n    @Transactional\n    public void autoFlagStaleAsBacklog() {\n        LocalDateTime cutoff = LocalDateTime.now().minusDays(365);\n        List<LandProject> candidates = projectRepository.findAutoBacklogCandidates(cutoff);',
    '    @Scheduled(cron = "0 0 6 * * *")\n    @Transactional\n    public void autoFlagStaleAsBacklog() {\n        LocalDateTime cutoff = LocalDateTime.now().minusDays(365);\n        // Pass cutoff for both lastPaymentDate AND registration date checks\n        List<LandProject> candidates = projectRepository.findAutoBacklogCandidates(cutoff);',
    'BacklogSchedulerService cron comment (no-op marker)'
)

# Update the repository query to also check landTitle.createdAt
repo_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com',
    'gesolutions', 'erp', 'modules', 'land', 'repository', 'LandProjectRepository.java')

patch(
    repo_path,
    '    @Query("SELECT p FROM LandProject p WHERE p.isBacklog = false " +\n           "AND p.amountPaid < p.totalCost " +\n           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")\n    List<LandProject> findAutoBacklogCandidates(LocalDateTime cutoff);',
    '    // Fixed: require BOTH registration date AND last payment date to be older than cutoff\n    // This prevents newly registered plots with no initial payment from being instantly flagged\n    @Query("SELECT p FROM LandProject p WHERE p.isBacklog = false " +\n           "AND p.amountPaid < p.totalCost " +\n           "AND p.landTitle.createdAt < :cutoff " +\n           "AND (p.lastPaymentDate IS NULL OR p.lastPaymentDate < :cutoff)")\n    List<LandProject> findAutoBacklogCandidates(LocalDateTime cutoff);',
    'LandProjectRepository.findAutoBacklogCandidates - require registration date also old'
)

# ── PATCH 2 & 3: Joint owner contact spreading + multi-plot sync ──
land_service_path = os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com',
    'gesolutions', 'erp', 'modules', 'land', 'service', 'LandService.java')

old_follow_up = '''    @Transactional(rollbackFor = Exception.class)
    public void logFollowUp(UUID projectId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();
        if (project.getProprietors() != null) {
            for (Client owner : project.getProprietors()) {
                if (owner != null && owner.getId() != null) {
                    try { clientService.logManagerContact(owner.getId()); } catch (Exception e) {}
                }
            }
        }
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(content)
                .recordedBy(getCurrentOperator())
                .build();
        followUpRepository.save(entry);
        auditService.logAction("RECOVERY_SYNC",
            "Operator [" + getCurrentOperator() + "] logged call for plot: "
            + project.getLandTitle().getPlotNumber());
    }'''

new_follow_up = '''    @Transactional(rollbackFor = Exception.class)
    public void logFollowUp(UUID projectId, String content) {
        LandProject project = projectRepository.findById(projectId).orElseThrow();

        // PATCH 2: Only increment call counter for the PRIMARY owner (alphabetically first),
        // not all joint owners, to avoid accidental counter inflation.
        Client primaryOwner = null;
        if (project.getProprietors() != null && !project.getProprietors().isEmpty()) {
            primaryOwner = project.getProprietors().stream()
                    .filter(o -> o != null && o.getId() != null)
                    .min(java.util.Comparator.comparing(Client::getFullName))
                    .orElse(null);
            if (primaryOwner != null) {
                try { clientService.logManagerContact(primaryOwner.getId()); } catch (Exception e) {}
            }
        }

        // Save note to this plot
        String operator = getCurrentOperator();
        FollowUpLog entry = FollowUpLog.builder()
                .projectId(projectId)
                .notes(content)
                .recordedBy(operator)
                .build();
        followUpRepository.save(entry);

        // PATCH 3: If the primary owner also owns other outstanding plots,
        // automatically copy this follow-up note to those plots as well.
        if (primaryOwner != null) {
            final Client finalPrimary = primaryOwner;
            List<LandProject> allProjects = projectRepository.findAll();
            for (LandProject otherPlot : allProjects) {
                if (otherPlot.getId().equals(projectId)) continue;
                boolean ownedByPrimary = otherPlot.getProprietors() != null &&
                    otherPlot.getProprietors().stream()
                        .anyMatch(o -> o != null && o.getId() != null &&
                                  o.getId().equals(finalPrimary.getId()));
                if (!ownedByPrimary) continue;
                // Only sync to plots with outstanding balance (active cases)
                java.math.BigDecimal bal = otherPlot.isBacklog()
                        ? otherPlot.backlogTotalOwed() : otherPlot.activeTotalOwed();
                if (bal.compareTo(java.math.BigDecimal.ZERO) <= 0) continue;
                FollowUpLog syncEntry = FollowUpLog.builder()
                        .projectId(otherPlot.getId())
                        .notes("[SYNCED FROM " + project.getLandTitle().getPlotNumber() + "] " + content)
                        .recordedBy(operator)
                        .build();
                followUpRepository.save(syncEntry);
            }
        }

        auditService.logAction("RECOVERY_SYNC",
            "Operator [" + operator + "] logged call for plot: "
            + project.getLandTitle().getPlotNumber());
    }'''

patch(land_service_path, old_follow_up, new_follow_up,
      'LandService.logFollowUp - primary owner only + multi-plot sync')

# ── PATCH 4: Duplicate plot resets surveyDate ─────────────────────
intake_path = os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx')

patch(
    intake_path,
    "            setPlotNumber('');\n            setInitialPayment('');\n            setInitialStorageFee('');\n            setFileQueue([]);\n            setNotesList([]);\n            setErrors({});",
    "            setPlotNumber('');\n            setInitialPayment('');\n            setInitialStorageFee('');\n            setSurveyDate('');\n            setFileQueue([]);\n            setNotesList([]);\n            setErrors({});",
    'IntakePage.handleDuplicatePlot - reset surveyDate'
)

print('Done.')