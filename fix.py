import os

path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"

old = """    @Transactional
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

        projectRepository.delete(project);
        auditService.logAction("RECORD_DELETED",
            "Root user [" + getCurrentOperator() + "] permanently deleted plot: " + plotNo);
    }"""

new = """    @Transactional
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
    }"""

with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print("OK: nuclearDelete patched in " + path)
else:
    print("MISSING: patch target not found in " + path)