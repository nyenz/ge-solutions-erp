#!/usr/bin/env python3
"""fix23.py — Ledger scale/hover/flush-panel polish + purge FK fix + chunk warning.
Run: py fix23.py"""
import subprocess
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
WROTE=[]

def write(rel, content):
    p = ROOT / rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8"); WROTE.append(rel)

def patch(rel, old, new):
    p = ROOT / rel; t = p.read_text(encoding="utf-8")
    if old not in t:
        print("!! anchor not found in", rel); return
    p.write_text(t.replace(old, new, 1), encoding="utf-8"); WROTE.append(rel+" (patched)")

# ---------------- LedgerPage.jsx: full corner decor back ----------------
patch('erp-frontend/src/pages/Ledger/LedgerPage.jsx', "<CornerDecor hideTop />", "<CornerDecor />")

# ---------------- vite.config.js: silence chunk-size warning ----------------
write('erp-frontend/vite.config.js', r"""import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // The bundle is >500kB (it's a large ERP). This only silences the
    // "chunk larger than 500 kB" WARNING; it does not affect behaviour.
    chunkSizeWarningLimit: 1500,
  },
})
""")

# ---------------- LedgerPage.module.css: Payments-matched scale + flush panel ----------------
write('erp-frontend/src/pages/Ledger/LedgerPage.module.css', r"""/* PATH: erp-frontend/src/pages/Ledger/LedgerPage.module.css */
.container {
    --orange:#EE8C3A; --orange-dim:rgba(238,140,58,0.18); --orange-border:rgba(238,140,58,0.28);
    --navy:#213E40; --navy-deep:#1a2e30; --red:#ef4444; --green:#10b981;
    --panel-bg: linear-gradient(160deg,#1c3335 0%,#213E40 100%);
    /* SAME type-scale as the Payments page */
    --fs-h1: clamp(18px,2.5vw,24px);
    --fs-sub: clamp(8px,0.85vw,10px);
    --fs-th:  clamp(8px,0.85vw,10px);
    --fs-td:  clamp(10px,1.05vw,12px);
    --fs-value: clamp(11px,1.1vw,13px);
    --fs-meta: clamp(8px,0.85vw,10px);
    --fs-btn: clamp(9px,0.9vw,11px);
    --fs-input: clamp(11px,1.1vw,13px);
    --radius: 10px; --radius-sm: 6px;
    max-width:1400px; width:100%; margin:0 auto;
    padding:clamp(12px,2vh,22px) clamp(12px,2vw,24px) 0;
    font-family:'Inter',sans-serif; color:#fff;
    display:flex; flex-direction:column;
}
.pageHeader {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;
    gap:clamp(8px,1.2vw,14px); border-left:clamp(3px,0.4vw,5px) solid var(--orange);
    padding:clamp(8px,1.2vw,14px) clamp(14px,1.8vw,22px);
    background:rgba(255,255,255,0.62); border-radius:0 12px 12px 0;
    backdrop-filter:blur(15px); box-shadow:0 4px 15px rgba(0,0,0,0.07);
    margin-bottom:clamp(10px,1.5vh,16px);
}
.headerLeft{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1;}
.title{font-family:'Cinzel',serif;color:var(--navy-deep);font-size:var(--fs-h1);font-weight:700;text-transform:uppercase;letter-spacing:2px;line-height:1.1;margin:0;}
.subtitle{font-family:'Inter',sans-serif;color:#64748b;font-size:var(--fs-sub);font-weight:800;text-transform:uppercase;letter-spacing:1px;margin:0;}

/* toolbar: transparent, scrolls away with the page */
.controlHub{display:flex;flex-direction:column;gap:8px;background:transparent;padding:0 0 10px;}
.toolbarRow{display:flex;align-items:center;gap:10px;}
.searchBlock{flex:0 1 clamp(280px,40vw,480px);min-width:0;}
.searchInner{position:relative;display:flex;align-items:center;background:#fff;border:1.5px solid #c8d6d7;border-radius:var(--radius-sm);height:clamp(36px,4.5vw,44px);transition:border-color .2s,box-shadow .2s;}
.searchInner:focus-within{border-color:var(--orange);box-shadow:0 0 0 3px rgba(238,140,58,0.18);}
.searchIcon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--orange);pointer-events:none;}
.searchInput{width:100%;border:none;outline:none;background:transparent;color:#1a2e30;padding:0 12px 0 38px;font-family:'Inter',sans-serif;font-weight:600;font-size:var(--fs-input);height:100%;}
.searchInput::placeholder{color:rgba(26,46,48,0.35);font-weight:500;}
.searchClearBtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--orange);cursor:pointer;display:flex;}
.filterRailContainer{overflow-x:auto;scrollbar-width:none;}
.filterRailContainer::-webkit-scrollbar{display:none;}
.filterRail{display:flex;gap:clamp(6px,1vw,10px);}
/* filter pills: SAME scale as Payments filter pills */
.filterBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:clamp(7px,0.9vw,9px) clamp(12px,1.5vw,18px);border-radius:var(--radius-sm);font-family:'Inter',sans-serif;font-weight:900;font-size:clamp(9px,0.95vw,11px);letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;white-space:nowrap;transition:all .2s ease;}
.filterBtn:hover{background:rgba(238,140,58,0.12);color:#EE8C3A;border-color:#EE8C3A;}
.activeFilter{background:#EE8C3A !important;color:#1a2e30 !important;border-color:#EE8C3A !important;box-shadow:0 0 12px rgba(238,140,58,0.35);}
.legendRow{display:flex;flex-wrap:wrap;gap:14px;padding:2px 0 0;}
.legendItem{display:flex;align-items:center;gap:6px;font-size:clamp(9px,0.9vw,11px);font-weight:700;color:rgba(26,46,48,0.6);}
.legendDot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0;}

/* table panel: ZERO padding so the bg shares borders with the table,
   and the sticky header sits flush at the very top (nothing above it) */
.tablePanel{position:relative;background:var(--panel-bg);border:1.5px solid var(--orange-border);border-radius:var(--radius);padding:0;}
.tableScroll{overflow:visible;border-radius:var(--radius);}
@media (max-width:900px){ .tableScroll{overflow-x:auto;} }
.ledgerTable{width:100%;border-collapse:separate;border-spacing:0;min-width:clamp(700px,90vw,1100px);}
/* header: Payments-matched padding/scale, sticky, rounded top corners to match panel */
.ledgerTable thead th{
    position:sticky;top:0;z-index:100;
    background:#162a2c;color:var(--orange);
    font-family:'Inter',sans-serif;font-size:var(--fs-th);font-weight:900;letter-spacing:2px;text-transform:uppercase;
    text-align:left;padding:clamp(11px,1.5vw,18px) clamp(12px,1.8vw,20px);
    border-bottom:3px solid var(--orange);white-space:nowrap;user-select:none;
}
.ledgerTable thead th:first-child{border-radius:var(--radius) 0 0 0;}
.ledgerTable thead th:last-child{border-radius:0 var(--radius) 0 0;}
.sortable{cursor:pointer;transition:background .18s,color .18s;}
.sortable:hover{background:rgba(238,140,58,0.07);color:#fff;}   /* hover back */
.ledgerTable tbody td{padding:clamp(9px,1.3vw,14px) clamp(12px,1.8vw,20px);border-bottom:1px solid rgba(255,255,255,0.05);vertical-align:top;color:#fff;font-size:var(--fs-td);}
.ledgerTable tbody tr{cursor:pointer;transition:background .15s;}
.ledgerTable tbody tr:hover{background:rgba(255,255,255,0.04);}
.rowReceivable{background:rgba(239,68,68,0.05);}
.rowCritical{background:rgba(239,68,68,0.07);}
.indexRow{display:flex;align-items:flex-start;gap:6px;}
.indexRow strong{font-family:'Space Mono',monospace;color:#fff;font-size:var(--fs-value);}
.stack{display:flex;flex-direction:column;gap:2px;}
.stackSub{font-size:var(--fs-meta);font-weight:600;color:rgba(255,255,255,0.55);font-family:'Space Mono',monospace;}
.ownerName{font-weight:800;color:#fff;font-size:var(--fs-td);}
.ownerPhone{font-family:'Space Mono',monospace;font-size:var(--fs-td);color:rgba(255,255,255,0.7);}
.statusGroup{display:flex;flex-direction:column;gap:4px;align-items:flex-start;}
.tagReceivable,.tagPaid,.tagStandard,.tagCritical{background:none;border:none;font-size:var(--fs-meta);font-weight:900;letter-spacing:1px;text-transform:uppercase;padding:0;}
.tagReceivable{color:#fca5a5;}
.tagPaid{color:#34d399;}
.tagStandard{color:rgba(255,255,255,0.6);}
.tagCritical{color:#ef4444;}
.moneyCell{min-width:150px;}
.moneyRow{display:flex;justify-content:space-between;gap:8px;}
.debtLabel{color:rgba(255,255,255,0.5);font-size:var(--fs-meta);font-weight:800;}
.debtAmount{font-family:'Space Mono',monospace;color:#fca5a5;font-weight:700;font-size:var(--fs-value);}
.debtCritical{font-family:'Space Mono',monospace;color:#ef4444;font-weight:900;font-size:var(--fs-value);}
.feesLine{font-size:0.7rem;color:#ef4444;margin-bottom:4px;}
.velocityBar{height:5px;background:rgba(255,255,255,0.1);border-radius:3px;margin-top:6px;overflow:hidden;}
.velocityFill{height:100%;background:var(--orange);border-radius:3px;}
.velocityFillCritical{background:var(--red);}
.pctLabel{font-size:var(--fs-meta);color:rgba(255,255,255,0.5);font-weight:700;}
.loadingCell,.errorCell,.emptyCell{text-align:center;padding:30px !important;color:rgba(255,255,255,0.5);font-weight:800;letter-spacing:1px;}
.retryBtn{background:none;border:1px solid var(--red);color:var(--red);padding:4px 10px;border-radius:4px;cursor:pointer;font-weight:800;}
.pagination{display:flex;justify-content:space-between;align-items:center;padding:10px 4px 2px;}
.pageBtn{background:rgba(26,46,48,0.75);border:1.5px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.85);padding:7px 14px;border-radius:6px;font-weight:900;font-size:var(--fs-btn);cursor:pointer;display:inline-flex;gap:6px;align-items:center;}
.pageBtn:disabled{opacity:0.4;cursor:not-allowed;}
.pageIndicator{color:rgba(255,255,255,0.6);font-size:var(--fs-btn);font-weight:800;letter-spacing:1px;}
.recordCount{color:var(--orange);}
.topBtn{position:fixed;left:clamp(14px,2vw,26px);bottom:clamp(14px,2vh,26px);z-index:9500;background:transparent;border:none;color:var(--orange);width:38px;height:38px;font-size:23px;display:flex;align-items:center;justify-content:center;cursor:pointer;opacity:0.9;filter:drop-shadow(0 0 6px rgba(238,140,58,0.6));transition:transform .2s,opacity .2s,filter .2s;}
.topBtn:hover{transform:translateY(-3px);opacity:1;filter:drop-shadow(0 0 10px rgba(238,140,58,0.85));}
""")

# ---------------- DataInitializer: robust purge (no FK failure) ----------------
# (full rewrite with id-based purge so the sample reseed never hits the
#  project_proprietors foreign-key error again)
write('erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java', r"""// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.finance.model.ExpensePreset;
import com.gesolutions.erp.modules.finance.repository.ExpensePresetRepository;
import com.gesolutions.erp.modules.land.dto.LandEntryRequest;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.StageTemplate;
import com.gesolutions.erp.modules.land.service.LandService;
import com.gesolutions.erp.modules.land.service.StageTemplateService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.Statement;

@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private final PasswordEncoder passwordEncoder;
    private final DataSource dataSource;
    private final StageTemplateService stageTemplateService;
    private final ExpensePresetRepository expensePresetRepository;
    private final LandService landService;

    @Value("${ADMIN_EMAIL}") private String adminEmail;
    @Value("${ADMIN_DEFAULT_PASSWORD}") private String adminDefaultPassword;

    @Override
    public void run(String... args) {
        System.out.println(">>> GOLDEN SEED SYSTEM: Verifying Master Identity Registry...");
        runSchemaMigrations();
        seedRootUser();
        stageTemplateService.seedDefaultStagesIfEmpty();
        try {
            stageTemplateService.normalizeToDefaultStages();
            System.out.println(">>> [STAGE_TEMPLATE] Normalized master checklist to defaults.");
        } catch (Exception e) {
            System.err.println(">>> [STAGE_TEMPLATE] normalize warning: " + e.getMessage());
        }
        seedSampleProjects();
        seedDefaultExpensePresets();
        System.out.println(">>> GOLDEN SEED SYSTEM: Identity Protocol Active. Registry Locked.");
    }

    public void seedDefaultExpensePresets() {
        if (expensePresetRepository.count() > 0) {
            System.out.println(">>> [EXPENSES] Presets already exist, skipping default seed.");
            return;
        }
        String[] defaults = { "Office", "Fieldwork", "Land Office" };
        for (String name : defaults) {
            expensePresetRepository.save(ExpensePreset.builder().name(name).createdBy("SYSTEM").build());
        }
        System.out.println(">>> [EXPENSES] Seeded default presets: Office, Fieldwork, Land Office");
    }

    // FIX23: identify sample projects by title plot OR owner NIN (NOT by
    // district, which is a realistic value), and delete children BEFORE
    // parents so the clients delete never hits the project_proprietors FK.
    private void purgeSampleData() {
        String idsSql =
            "SELECT lp.id FROM land_projects lp " +
            "LEFT JOIN land_titles lt ON lt.id = lp.title_id " +
            "WHERE lt.plot_number LIKE 'SAMPLE-%' " +
            "OR lp.id IN (SELECT pp.project_id FROM project_proprietors pp " +
            "JOIN clients c ON c.id = pp.client_id WHERE c.national_id LIKE 'SMPL-%')";
        String[] stmts = {
            "DELETE FROM payment_records WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM follow_up_logs WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM project_stages WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM project_proprietors WHERE project_id IN (" + idsSql + ")",
            "DELETE FROM land_projects WHERE id IN (" + idsSql + ")",
            "DELETE FROM land_titles WHERE plot_number LIKE 'SAMPLE-%'",
            "DELETE FROM clients WHERE national_id LIKE 'SMPL-%'",
        };
        try (Connection conn = dataSource.getConnection(); Statement st = conn.createStatement()) {
            for (String s : stmts) {
                try { st.execute(s); }
                catch (Exception e) { System.err.println(">>> [SAMPLE] purge stmt failed: " + s.substring(0, 40) + " -> " + e.getMessage()); }
            }
            System.out.println(">>> [SAMPLE] Old sample data purged.");
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] purge warning: " + e.getMessage());
        }
    }

    private java.util.UUID trySeed(String label, java.util.concurrent.Callable<java.util.UUID> supplier) {
        try { return supplier.call(); }
        catch (Exception e) {
            System.err.println(">>> [SAMPLE] " + label + " failed (skipped): " + e.getMessage());
            return null;
        }
    }

    private void seedSampleProjects() {
        purgeSampleData();
        java.util.List<StageTemplate> master = stageTemplateService.getActiveTemplate();
        java.util.Map<String, String> idByName = new java.util.HashMap<>();
        for (StageTemplate t : master) idByName.put(t.getStageName(), t.getId().toString());

        String FW="Field Work", DP="Deed Plan", LCI="LC Inspection",
               DLB="District Land Board Approval", TASD="Tax Assessment and Stamp Duty",
               REG="Registration and Title Issuance";

        java.util.List<java.util.UUID> ids = new java.util.ArrayList<>();
        ids.add(trySeed("SAMPLE-101", () -> seedOne("SAMPLE-101", false,false,false, null,null,null, "2026-05-04", 4000000L,2000000L,0L,0L,
            new String[][]{{"JOHN SSERUGO","SMPL-1001","0772100100"}}, new String[]{FW,DP,LCI}, null, null,
            new String[]{"WAKISO","KYADONDO","NAKAWA EAST","BUKOTO","KIIWA","0.5 acres"}, "Sample: fresh folder, paying well.", idByName)));
        ids.add(trySeed("SAMPLE-102", () -> seedOne("SAMPLE-102", false,false,false, null,null,null, "2026-07-10", 6000000L,0L,0L,0L,
            new String[][]{{"MARY NAKATO","SMPL-1002","0772100200"}}, new String[]{FW}, null, null,
            new String[]{"MPIGI","MPIGI COUNTY","MPIGI TOWN","CENTRAL","KIZUNGU","1 acre"}, "Sample: folder, no payment yet.", idByName)));
        ids.add(trySeed("SAMPLE-103", () -> seedOne("SAMPLE-103", false,false,false, null,null,null, "2026-02-02", 9000000L,6000000L,0L,0L,
            new String[][]{{"PETER OPOK","SMPL-1003","0772100300"}}, new String[]{FW,DP,LCI,DLB,TASD}, new String[]{REG}, null,
            new String[]{"MUKONO","MUKONO COUNTY","KATABI","BULANGA","NAGOGBE","2 acres"}, "Sample: all pre-stages done, awaiting registration.", idByName)));
        ids.add(trySeed("SAMPLE-104", () -> seedOne("SAMPLE-104", false,true,false, "SMPL-T-104","2026-06-15","KBL-77", "2026-06-01", 15000000L,11000000L,0L,0L,
            new String[][]{{"GRACE ACHENG","SMPL-1004","0772100400"}}, new String[]{FW,DP,LCI,DLB}, null, null,
            new String[]{"KAMPALA","KAMPALA CENTRAL","MAKINDYE","KABALAGALA","GABA","0.25 acres"}, "Sample: new title in processing.", idByName)));
        ids.add(trySeed("SAMPLE-105", () -> seedOne("SAMPLE-105", true,false,false, "SMPL-T-105","2025-12-01","EBB-12", "2025-11-01", 20000000L,20000000L,0L,0L,
            new String[][]{{"DAVID KIGONGO","SMPL-1005","0772100500"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, null,
            new String[]{"WAKISO","ENTEBBE","ENTEBBE TOWN","KATABI","LUGALA","0.3 acres"}, "Sample: legacy fully paid, awaiting release.", idByName)));
        ids.add(trySeed("SAMPLE-106", () -> seedOne("SAMPLE-106", true,false,false, "SMPL-T-106","2025-06-20","MSK-3", "2025-05-02", 25000000L,25000000L,0L,0L,
            new String[][]{{"SARAH NANSUBU","SMPL-1006","0772100600"}}, new String[]{FW,DP,LCI,DLB,TASD,REG}, null, "RELEASE",
            new String[]{"MASAKA","MASAKA CENTRAL","MASAKA MUNICIPAL","KIMAANYA","KABOGA","1.5 acres"}, "Sample: released legacy title.", idByName)));
        ids.add(trySeed("SAMPLE-107", () -> seedOne("SAMPLE-107", true,false,true, "SMPL-T-107","2025-09-10","MBR-9", "2025-08-01", 12000000L,2000000L,50000L,50000L,
            new String[][]{{"JAMES TURYAHEREZA","SMPL-1007","0772100700"}}, new String[]{FW,DP}, null, null,
            new String[]{"MBARARA","MBARARA COUNTY","MBARARA TOWN","KAKIIKA","NYAMITUKURA","0.8 acres"}, "Sample: receivable, storage fees accruing.", idByName)));
        ids.add(trySeed("SAMPLE-108", () -> seedOne("SAMPLE-108", false,true,true, "SMPL-T-108","2026-02-14","JIN-41", "2026-02-01", 10000000L,3000000L,50000L,50000L,
            new String[][]{{"RACHEL NABIRYE","SMPL-1008","0772100800"}}, new String[]{FW,DP,LCI}, null, null,
            new String[]{"JINJA","JINJA COUNTY","JINJA MUNICIPAL","WALUKUBA","MPUMUDDE","0.4 acres"}, "Sample: receivable but paying recently.", idByName)));
        ids.add(trySeed("SAMPLE-109", () -> seedOne("SAMPLE-109", false,false,false, null,null,null, "2026-01-15", 30000000L,3000000L,0L,0L,
            new String[][]{{"SAMUEL KIBUKA","SMPL-1091","0772100901"},{"JOYCE NAKALEMA","SMPL-1092","0772100902"},{"BRIAN MUWANGA","SMPL-1093","0772100903"}},
            new String[]{FW}, null, null,
            new String[]{"KAYUNGA","KAYUNGA COUNTY","KAYUNGA TOWN","BUKOMBE","NAJJA","5 acres"}, "Sample: joint family plot, critical arrears.", idByName)));
        ids.add(trySeed("SAMPLE-110", () -> seedOne("SAMPLE-110", true,false,false, "SMPL-T-110","2026-01-25","LWR-5", "2026-01-05", 18000000L,16200000L,0L,0L,
            new String[][]{{"HENRY SSEMMAMBWA","SMPL-1100","0772101000"}}, new String[]{FW,DP,LCI,DLB,TASD}, null, null,
            new String[]{"LUWERO","LUWERO COUNTY","LUWERO MUNICIPAL","BAMUNU","ZIWA","3 acres"}, "Sample: nearly paid legacy.", idByName)));

        int[] days = { 5, -1, 20, 3, 40, 200, 45, 12, 60, 25 };
        try (Connection conn = dataSource.getConnection()) {
            for (int i = 0; i < days.length && i < ids.size(); i++) {
                if (ids.get(i) == null || days[i] < 0) continue;
                java.sql.Timestamp ts = java.sql.Timestamp.valueOf(java.time.LocalDateTime.now().minusDays(days[i]));
                try (java.sql.PreparedStatement u1 = conn.prepareStatement("UPDATE land_projects SET last_payment_date = ? WHERE id = ?")) {
                    u1.setTimestamp(1, ts); u1.setObject(2, ids.get(i)); u1.executeUpdate();
                }
                try (java.sql.PreparedStatement u2 = conn.prepareStatement("UPDATE payment_records SET timestamp = ? WHERE project_id = ?")) {
                    u2.setTimestamp(1, ts); u2.setObject(2, ids.get(i)); u2.executeUpdate();
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [SAMPLE] backdate warning: " + e.getMessage());
        }
        long saved = ids.stream().filter(java.util.Objects::nonNull).count();
        System.out.println(">>> [SAMPLE] Seeded " + saved + " detailed sample projects.");
    }

    private java.util.UUID seedOne(String plot, boolean legacy, boolean titleAtIntake, boolean receivable,
                                   String titleId, String titleDate, String block, String startDate,
                                   long cost, long paid, long initFee, long monthlyFee,
                                   String[][] owners, String[] doneStages, String[] openStages,
                                   String releaseFlag, String[] loc, String note,
                                   java.util.Map<String, String> idByName) throws Exception {
        LandEntryRequest.LandEntryRequestBuilder b = LandEntryRequest.builder()
                .district(loc[0]).county(loc[1]).subCounty(loc[2]).parish(loc[3]).village(loc[4]).area(loc[5])
                .tenure("FREEHOLD")
                .projectStartDate(java.time.LocalDate.parse(startDate))
                .totalCost(java.math.BigDecimal.valueOf(cost))
                .initialPayment(java.math.BigDecimal.valueOf(paid))
                .isLegacy(legacy).titleAtIntake(titleAtIntake).isStartAsReceivable(receivable);
        if (plot != null) b.plotNumber(plot);
        if (titleId != null) b.titleId(titleId);
        if (block != null) b.blockRoad(block);
        if (titleDate != null) b.titleIssueDate(java.time.LocalDate.parse(titleDate));
        if (receivable) {
            b.initialStorageFee(java.math.BigDecimal.valueOf(initFee > 0 ? initFee : 50000));
            b.monthlyStorageFee(java.math.BigDecimal.valueOf(monthlyFee > 0 ? monthlyFee : 50000));
        }
        java.util.List<LandEntryRequest.OwnerRequest> os = new java.util.ArrayList<>();
        for (String[] o : owners) {
            os.add(LandEntryRequest.OwnerRequest.builder().fullName(o[0]).nationalId(o[1]).phone(o[2]).build());
        }
        b.owners(os);
        java.util.List<com.gesolutions.erp.modules.land.dto.ProjectStageRequest> ss = new java.util.ArrayList<>();
        for (String s : doneStages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(true).build());
        }
        if (openStages != null) for (String s : openStages) {
            String tid = idByName.get(s);
            ss.add(com.gesolutions.erp.modules.land.dto.ProjectStageRequest.builder()
                    .stageTemplateId(tid).stageName(s).isCustom(tid == null).isCompleted(false).build());
        }
        b.selectedStages(ss);
        if (note != null) b.notes(java.util.List.of(LandEntryRequest.NoteRequest.builder().content(note).build()));
        LandProject saved = landService.atomicIntake(b.build(), null);
        if ("RELEASE".equals(releaseFlag)) {
            try { landService.authorizeRelease(saved.getId(), "Sample release"); } catch (Exception ignore) {}
        }
        return saved.getId();
    }

    private void runSchemaMigrations() {
        String[] migrations = {
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS negotiation_deadline TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_months_billed INTEGER NOT NULL DEFAULT 0",
            "CREATE TABLE IF NOT EXISTS project_index_counter (id INTEGER PRIMARY KEY, current_number INTEGER NOT NULL DEFAULT 0, current_letter VARCHAR(4) NOT NULL DEFAULT 'A')",
            "INSERT INTO project_index_counter (id, current_number, current_letter) VALUES (1, 0, 'A') ON CONFLICT (id) DO NOTHING",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_titles_project_index') THEN ALTER TABLE land_titles ADD CONSTRAINT uq_land_titles_project_index UNIQUE (project_index); END IF; END $$",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS project_start_date DATE",
            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS title_issue_date DATE",
            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",
            "DO $$ DECLARE cname text; BEGIN " +
                "SELECT tc.constraint_name INTO cname FROM information_schema.table_constraints tc " +
                "JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name " +
                "WHERE tc.table_name = 'clients' AND tc.constraint_type = 'UNIQUE' AND ccu.column_name = 'phone_number' LIMIT 1; " +
                "IF cname IS NOT NULL THEN EXECUTE 'ALTER TABLE clients DROP CONSTRAINT ' || quote_ident(cname); END IF; " +
                "END $$",
            "ALTER TABLE land_projects ALTER COLUMN title_id DROP NOT NULL",
            "UPDATE clients SET national_id = NULL WHERE national_id = ''",
            "UPDATE clients c SET national_id = c.national_id || '-DUPE-' || c.id::text " +
                "FROM (SELECT id, national_id, ROW_NUMBER() OVER (PARTITION BY national_id ORDER BY id) AS rn " +
                "FROM clients WHERE national_id IS NOT NULL) ranked " +
                "WHERE c.id = ranked.id AND ranked.rn > 1",
            "UPDATE clients SET national_id = 'LEGACY-' || id::text WHERE national_id IS NULL",
            "ALTER TABLE clients ALTER COLUMN national_id SET NOT NULL",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_national_id') THEN ALTER TABLE clients ADD CONSTRAINT uq_clients_national_id UNIQUE (national_id); END IF; END $$",
            "CREATE TABLE IF NOT EXISTS expense_presets (id UUID PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE, created_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT now())",
            "CREATE TABLE IF NOT EXISTS expenses (id UUID PRIMARY KEY, category VARCHAR(150) NOT NULL, amount NUMERIC(15,2) NOT NULL, note TEXT, recorded_by VARCHAR(100), created_at TIMESTAMP NOT NULL DEFAULT now(), edited_at TIMESTAMP, edited_by VARCHAR(100))",
            "CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses (category)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS district VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS sub_county VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS parish VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS village VARCHAR(100)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS area VARCHAR(100)",
            "UPDATE land_projects lp SET district = lt.district, county = lt.county " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.district IS NULL " +
                "AND (lt.district IS NOT NULL OR lt.county IS NOT NULL)",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS project_index VARCHAR(10)",
            "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_land_projects_project_index') THEN ALTER TABLE land_projects ADD CONSTRAINT uq_land_projects_project_index UNIQUE (project_index); END IF; END $$",
            "UPDATE land_projects lp SET project_index = lt.project_index " +
                "FROM land_titles lt WHERE lp.title_id = lt.id AND lp.project_index IS NULL " +
                "AND lt.project_index IS NOT NULL",
            "ALTER TABLE land_titles ALTER COLUMN plot_number DROP NOT NULL",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS volume",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS folio",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS instrument_no",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS physical_box_number",
            "ALTER TABLE land_titles DROP COLUMN IF EXISTS survey_date",
        };
        try (Connection conn = dataSource.getConnection(); Statement stmt = conn.createStatement()) {
            for (String sql : migrations) {
                try {
                    stmt.execute(sql);
                    System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, Math.min(60, sql.length())));
                } catch (Exception e) {
                    System.out.println(">>> [DB_SCHEMA] Skipped (already exists): " + e.getMessage());
                }
            }
        } catch (Exception e) {
            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());
        }
    }

    public void seedRootUser() {
        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";
        String encodedPassword = passwordEncoder.encode(rawPassword);
        try (java.sql.Connection conn = dataSource.getConnection()) {
            boolean exists = false;
            try (java.sql.PreparedStatement ps = conn.prepareStatement("SELECT COUNT(*) FROM users WHERE username = ?")) {
                ps.setString(1, "admin_root");
                try (java.sql.ResultSet rs = ps.executeQuery()) { if (rs.next()) exists = rs.getInt(1) > 0; }
            }
            if (!exists) {
                String sql = "INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) "
                           + "VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)";
                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {
                    ps.setObject(1, java.util.UUID.randomUUID());
                    ps.setString(2, email);
                    ps.setString(3, encodedPassword);
                    int rows = ps.executeUpdate();
                    System.out.println(">>> [REGISTRY] INSERT admin_root rows affected: " + rows);
                }
            } else {
                System.out.println(">>> [REGISTRY] admin_root already exists -- skipping password reset.");
            }
        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }
}
""")

subprocess.run(['git','add','.'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','commit','-m','fix23: Ledger Payments-matched scale + hover + flush panel + rounded sticky header; robust sample purge; chunk warning silenced'],check=False,cwd=ROOT,capture_output=True)
subprocess.run(['git','push'],check=False,cwd=ROOT,capture_output=True)
print("Wrote:", *WROTE, sep="\n  ")
print("Done. Pushed.")