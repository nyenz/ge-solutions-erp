# fix.py -- FULL-FILE repair: rewrite FolderPortalController.java + dedupe LandProject.problem
import re, subprocess, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BE = ROOT / "erp-backend" / "src" / "main" / "java" / "com" / "gesolutions" / "erp"

CONTROLLER = '''package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/v1/land/portal")
@RequiredArgsConstructor
public class FolderPortalController {

    private final LandProjectRepository projectRepository;
    private final AuditService auditService;

    private String op() {
        var a = SecurityContextHolder.getContext().getAuthentication();
        return a != null ? a.getName() : "SYSTEM";
    }

    @GetMapping("/{id}/receivable")
    @Transactional(readOnly = true)
    public Map<String, Object> receivable(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        Map<String, Object> m = new HashMap<>();
        m.put("receivable", p.isReceivable());
        m.put("actual", p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO);
        m.put("storage", p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO);
        m.put("paid", p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        m.put("total", p.receivableTotalOwed());
        m.put("rate", p.getStorageFeeOverride());
        m.put("deadline", p.getNegotiationDeadline());
        m.put("startDate", p.getReceivableStartDate());
        m.put("backlog", p.getLandTitle() == null);
        m.put("problem", p.isProblem());
        return m;
    }

    @GetMapping("/{id}/portfolio")
    @Transactional(readOnly = true)
    public List<Map<String, Object>> portfolio(@PathVariable UUID id) {
        LandProject current = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        List<Map<String, Object>> out = new ArrayList<>();
        if (current.getProprietors() == null) return out;
        for (LandProject other : projectRepository.findAll()) {
            if (other.getId().equals(id) || other.getProprietors() == null) continue;
            for (var owner : current.getProprietors()) {
                if (other.getProprietors().stream().anyMatch(c -> c.getId().equals(owner.getId()))) {
                    Map<String, Object> m = new HashMap<>();
                    m.put("projectId", other.getId());
                    m.put("index", other.getProjectIndex());
                    m.put("plot", other.getLandTitle() != null ? other.getLandTitle().getPlotNumber() : null);
                    m.put("titled", other.getLandTitle() != null);
                    m.put("receivable", other.isReceivable());
                    m.put("sharedOwner", owner.getFullName());
                    out.add(m);
                    break;
                }
            }
        }
        return out;
    }

    @PostMapping("/{id}/receivable/enter")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> enter(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setReceivable(true);
        p.setReceivableStartDate(LocalDateTime.now());
        p.setReceivableMonthsBilled(0);
        BigDecimal owed = (p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO)
                .add(p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO)
                .subtract(p.getAmountPaid() != null ? p.getAmountPaid() : BigDecimal.ZERO);
        p.setOriginalDebt(owed.max(BigDecimal.ZERO));
        p.setStatus("RECEIVABLE");
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_ENTER", "Operator [" + op() + "] moved project #" + p.getProjectIndex() + " into receivables.");
        return receivable(id);
    }

    @PostMapping("/{id}/receivable/exit")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> exit(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        String action = body.getOrDefault("action", "SET_ASIDE");
        BigDecimal fees = p.getStorageFeesAccumulated() != null ? p.getStorageFeesAccumulated() : BigDecimal.ZERO;
        if ("WAIVE".equals(action)) {
            auditService.logAction("FEES_WAIVED", "Operator [" + op() + "] waived UGX " + fees + " on #" + p.getProjectIndex() + ".");
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
        } else if ("CAPITALIZE".equals(action)) {
            p.setTotalCost((p.getTotalCost() != null ? p.getTotalCost() : BigDecimal.ZERO).add(fees));
            p.setStorageFeesAccumulated(BigDecimal.ZERO);
            auditService.logAction("FEES_CAPITALIZED", "Operator [" + op() + "] capitalized UGX " + fees + " into total cost on #" + p.getProjectIndex() + ".");
        } else {
            auditService.logAction("RECEIVABLE_SET_ASIDE", "Operator [" + op() + "] set aside #" + p.getProjectIndex() + " (fees UGX " + fees + " retained, billing stopped).");
        }
        p.setReceivable(false);
        p.setStatus("ACTIVE");
        projectRepository.save(p);
        return receivable(id);
    }

    @PostMapping("/{id}/toggle-problem")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER','ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> toggleProblem(@PathVariable UUID id) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        p.setProblem(!p.isProblem());
        projectRepository.save(p);
        auditService.logAction("PROBLEM_FLAG", "Operator [" + op() + "] " + (p.isProblem() ? "flagged" : "cleared") + " PROBLEM on #" + p.getProjectIndex() + ".");
        return receivable(id);
    }

    @PostMapping("/{id}/receivable/settings")
    @PreAuthorize("hasAnyRole('ROLE_ADMIN','ROLE_DIRECTOR')")
    @Transactional
    public Map<String, Object> settings(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        LandProject p = projectRepository.findById(id).orElseThrow(() -> new BusinessException("NOT_FOUND"));
        if (body.containsKey("rate")) {
            p.setStorageFeeOverride(body.get("rate") == null || body.get("rate").isBlank() ? null : new BigDecimal(body.get("rate")));
        }
        if (body.containsKey("deadline")) {
            p.setNegotiationDeadline(body.get("deadline") == null || body.get("deadline").isBlank() ? null : LocalDateTime.parse(body.get("deadline")));
        }
        projectRepository.save(p);
        auditService.logAction("RECEIVABLE_SETTINGS", "Operator [" + op() + "] updated receivable settings on #" + p.getProjectIndex() + ".");
        return receivable(id);
    }
}
'''

# ---- 1) overwrite controller with the complete known-good file ----
ctrl = BE / "modules" / "land" / "controller" / "FolderPortalController.java"
ctrl.write_text(CONTROLLER, encoding="utf-8", newline="\n")
print("WROTE full FolderPortalController.java (single toggleProblem)")

# ---- 2) dedupe LandProject.problem (adjacent-block regex, keep first) ----
lp = BE / "modules" / "land" / "model" / "LandProject.java"
s = lp.read_text(encoding="utf-8", errors="replace")
block = r'(@Builder\.Default\s*@Column\(name\s*=\s*"is_problem"[^)]*\)\s*private\s+boolean\s+problem\s*=\s*false;)'
s2 = re.sub(block + r'(\s*' + block + r')+', r'\1', s)
if s2 != s:
    lp.write_text(s2, encoding="utf-8", newline="\n")
    print("OK  LandProject.problem collapsed to 1")
else:
    # streaming fallback: keep first, drop later decls + their annotations
    lines = s.split("\n"); out = []; seen = False
    for line in lines:
        if re.match(r'^\s*private\s+boolean\s+problem\b', line):
            if seen:
                j = len(out) - 1
                while j >= 0 and out[j].strip().startswith("@"): out.pop(); j -= 1
                if out and out[-1].strip() == "": out.pop()
                continue
            seen = True
        out.append(line)
    lp.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print("OK  LandProject.problem streaming dedupe")

# ---- verify ----
bad = 0
c = lp.read_text(encoding="utf-8", errors="replace")
n = len(re.findall(r'private\s+boolean\s+problem\b', c))
print("LandProject problem count =", n); bad += (n != 1)
c = ctrl.read_text(encoding="utf-8", errors="replace")
n = c.count("public Map<String, Object> toggleProblem(")
print("toggleProblem count =", n); bad += (n != 1)
print("VERIFY:", "CLEAN" if bad == 0 else "STILL BAD - do not push")

for p in ROOT.glob("fix*.py"):
    if p.name != "fix.py": shutil.move(str(p), str(p) + ".done"); print("retired", p.name)

if bad == 0:
    try:
        subprocess.run(["git","add","-A"],cwd=ROOT,check=True)
        subprocess.run(["git","commit","-m","FULL-FILE: rewrite FolderPortalController + dedupe LandProject.problem"],cwd=ROOT,check=True)
        subprocess.run(["git","push"],cwd=ROOT,check=True)
        print("GIT pushed")
    except Exception as e:
        print("GIT WARN", e)
print("DONE")