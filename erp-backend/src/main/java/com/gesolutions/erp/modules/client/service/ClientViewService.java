// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/service/ClientViewService.java
package com.gesolutions.erp.modules.client.service;

import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.model.RecoveryNote;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectType;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * fix181 (Sections 5, 6, 11.7 to 11.10): the CLIENT LEDGER and the CLIENT PORTFOLIO (dossier), built once.
 *  - Every rule comes from the shared places: Recovery state / last payment / graduation delay (RecoveryStateService),
 *    critical, billed, paid, owed, kept fees (LandProject). The pages stop working these out themselves.
 *  - Pending projects are never counted; a client whose projects are ALL Pending is flagged pendingOnly (5.8).
 *  - Day counts come from the server (11.9).
 *  - Money fields are sent only to the Director and the Admin (5.9, owner default a): the pages already hid them from
 *    Manager and Secretary, now the server does not send them either.
 *  - One read for the clients, one for the projects, one for the notes (11.10).
 */
@Service
@RequiredArgsConstructor
public class ClientViewService {

    private static final List<String> MONEY_KEYS = List.of("owed", "paid", "billed", "titlePaid", "storage", "storageFees",
            "storagePaid", "storageUnpaid", "keptFees", "paidByThisClient", "payments", "totals");

    private final ClientRepository clientRepo;
    private final LandProjectRepository projectRepo;
    private final PaymentRecordRepository paymentRepo;
    private final RecoveryStateService recovery;

    private static boolean seesMoney() {
        var a = SecurityContextHolder.getContext().getAuthentication();
        return a != null && a.getAuthorities().stream().anyMatch(g -> "ROLE_DIRECTOR".equals(g.getAuthority()) || "ROLE_ADMIN".equals(g.getAuthority()));
    }

    private static Long days(LocalDateTime t, LocalDateTime now) {
        return t == null ? null : Math.max(0, ChronoUnit.DAYS.between(t.toLocalDate(), now.toLocalDate()));
    }

    // ── one project row (the same on both pages) ─────────────────────────────
    private Map<String, Object> projectRow(LandProject p, RecoveryStateService.Snapshot snap, LocalDateTime now) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("projectId", p.getId());
        row.put("index", p.getProjectIndex());
        row.put("plot", p.getLandTitle() == null ? null : p.getLandTitle().getPlotNumber());
        row.put("district", p.getDistrict());
        row.put("subCounty", p.getSubCounty());
        row.put("projectType", ProjectType.of(p).name());
        row.put("projectTypeLabel", ProjectType.of(p).getLabel());
        row.put("receivable", p.isReceivable());
        row.put("titled", p.getLandTitle() != null);              // kept for old pages
        row.put("hasTitleDetails", p.getLandTitle() != null);     // 11.8: the honest name
        row.put("released", p.getLandTitle() != null && p.getLandTitle().isReleased());
        row.put("problem", p.isProblem());
        row.put("status", p.getStatus());
        row.put("legacy", p.isLegacy());
        row.put("critical", p.isCritical());
        row.put("recoveryState", recovery.projectState(snap, p, now));
        row.put("graduatedAt", p.getGraduatedAt());
        row.put("recoveryStartsOn", RecoveryStateService.inGraduationDelay(p, now)
                ? p.getGraduatedAt().plusMonths(RecoveryStateService.GRADUATION_DELAY_MONTHS).toLocalDate() : null);
        row.put("lastPayment", p.getLastPaymentDate());
        row.put("daysSincePayment", days(p.getLastPaymentDate(), now));
        row.put("parentProjectId", p.getParentProjectId());
        row.put("parentSubdivisionNo", p.getParentSubdivisionNo());
        row.put("subdivisionCount", p.getSubdivisionCount());
        // money (taken out again for Manager and Secretary)
        row.put("billed", p.billed());
        row.put("paid", p.paidTowardBilled());
        row.put("titlePaid", p.titlePaid());
        row.put("storageFees", nz(p.getStorageFeesAccumulated()));
        row.put("storage", nz(p.getStorageFeesAccumulated()));
        row.put("storagePaid", p.storagePaidSafe());
        row.put("storageUnpaid", p.storageUnpaid());
        row.put("keptFees", p.keptFees());
        row.put("owed", p.owedNow());
        return row;
    }

    private static BigDecimal nz(BigDecimal v) { return v == null ? BigDecimal.ZERO : v; }

    private static BigDecimal sum(List<Map<String, Object>> rows, String key) {
        BigDecimal t = BigDecimal.ZERO;
        for (Map<String, Object> r : rows) if (r.get(key) instanceof BigDecimal b) t = t.add(b);
        return t;
    }

    private static void stripMoney(Map<String, Object> m) {
        for (String k : MONEY_KEYS) m.remove(k);
        Object plots = m.get("plots");
        if (plots instanceof List<?> l) for (Object o : l) if (o instanceof Map<?, ?> r) {
            @SuppressWarnings("unchecked") Map<String, Object> rr = (Map<String, Object>) r;
            for (String k : MONEY_KEYS) rr.remove(k);
        }
    }

    /** The client-level fields shared by the ledger row and the dossier. */
    private void clientSummary(Map<String, Object> m, Client c, List<LandProject> ps, List<RecoveryNote> ns,
                               List<Map<String, Object>> rows, boolean hasPending, LocalDateTime now) {
        m.put("plotCount", ps.size());
        m.put("pendingOnly", ps.isEmpty() && hasPending);   // 5.8: a field entry only, not "no projects"
        m.put("owed", sum(rows, "owed"));
        m.put("paid", sum(rows, "paid"));
        m.put("billed", sum(rows, "billed"));
        m.put("storage", sum(rows, "storageFees"));
        m.put("storagePaid", sum(rows, "storagePaid"));
        m.put("storageUnpaid", sum(rows, "storageUnpaid"));
        m.put("keptFees", sum(rows, "keptFees"));
        m.put("criticalCount", rows.stream().filter(r -> Boolean.TRUE.equals(r.get("critical"))).count());
        // plain yes/no flags (no amounts), so every rank can filter: owing, paid up, fees kept (11.3), receivables
        BigDecimal owedAll = sum(rows, "owed"), keptAll = sum(rows, "keptFees");
        m.put("owing", owedAll.signum() > 0);
        m.put("feesKept", keptAll.signum() > 0);
        m.put("paidUp", !ps.isEmpty() && owedAll.signum() == 0 && keptAll.signum() == 0);
        m.put("receivableCount", rows.stream().filter(r -> Boolean.TRUE.equals(r.get("receivable"))).count());
        m.put("recoveryState", recovery.qualifies(ps, now) ? recovery.state(ps, ns, now) : null);
        LocalDateTime last = recovery.lastPayment(ps, now);
        m.put("lastPaymentAt", last);
        m.put("daysSincePayment", days(last, now));
        // 6.8 / 11.1c: every unpaid project is still inside its first month -> the dot shows NEW, not red
        boolean owing = false, owingOutsideDelay = false;
        LocalDate startsOn = null;
        for (LandProject p : ps) {
            if (p.owedNow().signum() <= 0) continue;
            owing = true;
            if (RecoveryStateService.inGraduationDelay(p, now)) {
                LocalDate d = p.getGraduatedAt().plusMonths(RecoveryStateService.GRADUATION_DELAY_MONTHS).toLocalDate();
                if (startsOn == null || d.isBefore(startsOn)) startsOn = d;
            } else owingOutsideDelay = true;
        }
        m.put("newProjectOnly", owing && !owingOutsideDelay && last == null);
        m.put("recoveryStartsOn", owing && !owingOutsideDelay ? startsOn : null);
        m.put("lastContact", c.getLastContactedAt());
        m.put("daysSinceContact", days(c.getLastContactedAt(), now));
        m.put("lastTag", ns.isEmpty() ? null : ns.get(0).getTag());
        m.put("lastTone", ns.isEmpty() ? null : ns.get(0).getTone());
        // fix181 (9.6): missed calls in the last 30 days, counted per day (the Recovery rule), for the reports
        m.put("missedCallDays30", recovery.miss30(ns, now));
    }

    // ── CLIENT LEDGER ───────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public List<Map<String, Object>> ledger() {
        LocalDateTime now = LocalDateTime.now();
        RecoveryStateService.Snapshot snap = recovery.load();
        Set<UUID> withPending = new HashSet<>();
        for (LandProject p : projectRepo.findAllIncludingPending()) {
            if (!p.isPending()) continue;
            for (Client c : p.getClients()) withPending.add(c.getId());
            for (Client c : p.getProprietors()) withPending.add(c.getId());
        }
        boolean money = seesMoney();
        List<Map<String, Object>> out = new ArrayList<>();
        for (Client c : clientRepo.findAll()) {
            List<LandProject> ps = snap.projectsOf(c.getId());
            List<RecoveryNote> ns = snap.notesOf(c.getId());
            List<Map<String, Object>> rows = new ArrayList<>();
            for (LandProject p : ps) rows.add(projectRow(p, snap, now));
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", c.getId());
            m.put("name", c.getFullName());
            m.put("nin", c.getNationalId());
            m.put("phone", c.getPhoneNumber());
            m.put("email", c.getEmail());
            m.put("reliability", c.getReliabilityScore());
            m.put("plots", rows);
            clientSummary(m, c, ps, ns, rows, withPending.contains(c.getId()), now);
            if (!money) stripMoney(m);
            out.add(m);
        }
        out.sort((a, b) -> String.valueOf(a.get("name")).compareToIgnoreCase(String.valueOf(b.get("name"))));
        return out;
    }

    // ── CLIENT PORTFOLIO (dossier) ──────────────────────────────────────────

    @Transactional(readOnly = true)
    public Map<String, Object> dossier(UUID id) {
        LocalDateTime now = LocalDateTime.now();
        Client c = clientRepo.findById(id).orElseThrow(() -> new BusinessException("CLIENT_NOT_FOUND: No such client."));
        List<LandProject> ps = projectRepo.findByBillingClient(id);   // Pending and deleted left out by the query
        RecoveryStateService.Snapshot snap = recovery.load();
        List<RecoveryNote> ns = snap.notesOf(id);
        boolean hasPending = projectRepo.findAllOfPersonIncludingPending(id).stream().anyMatch(LandProject::isPending);

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", c.getId());
        out.put("name", c.getFullName());
        out.put("nin", c.getNationalId());
        out.put("phone", c.getPhoneNumber());
        out.put("email", c.getEmail());
        out.put("address", c.getHomeAddress());
        out.put("reliability", c.getReliabilityScore());
        out.put("monthlyContacts", c.getMonthlyContactCount());

        List<Map<String, Object>> rows = new ArrayList<>();
        for (LandProject p : ps) {
            Map<String, Object> row = projectRow(p, snap, now);
            Set<Client> owners = p.billingParties();
            row.put("ownershipType", owners != null && owners.size() > 1 ? "JOINT" : "SOLO");
            List<Map<String, Object>> co = new ArrayList<>();
            if (owners != null) for (Client o : owners) {
                if (o == null || o.getId() == null || id.equals(o.getId())) continue;
                co.add(Map.of("clientId", o.getId(), "fullName", o.getFullName()));
            }
            row.put("coOwners", co);
            // 6.2: subdivision links
            if (p.getParentProjectId() != null) {
                projectRepo.findById(p.getParentProjectId()).ifPresent(par -> row.put("parentProjectIndex", par.getProjectIndex()));
            }
            if (ProjectType.of(p) == ProjectType.SUBDIVISION) {
                List<Map<String, Object>> kids = new ArrayList<>();
                for (LandProject t : projectRepo.findTransfersOf(p.getId())) {
                    kids.add(Map.of("projectId", t.getId(), "index", String.valueOf(t.getProjectIndex()),
                            "plotNo", t.getParentSubdivisionNo() == null ? 0 : t.getParentSubdivisionNo(),
                            "released", t.getLandTitle() != null && t.getLandTitle().isReleased()));
                }
                row.put("transfers", kids);
            }
            // 4.7, 6.1, 11.7: the payments, who paid (current name), reversals marked
            List<PaymentRecord> lines = paymentRepo.findByProjectIdOrderByTimestampDesc(p.getId());
            Set<String> reversed = new HashSet<>();
            for (PaymentRecord r : lines) {
                if (r.getNotes() != null && r.getNotes().startsWith("[REVERSAL OF ")) {
                    int e = r.getNotes().indexOf(']');
                    if (e > 13) reversed.add(r.getNotes().substring(13, e).trim());
                }
            }
            Map<UUID, Client> people = new HashMap<>();
            if (owners != null) for (Client o : owners) people.put(o.getId(), o);
            List<Map<String, Object>> pays = new ArrayList<>();
            BigDecimal mine = BigDecimal.ZERO;
            for (PaymentRecord r : lines) {
                Map<String, Object> pm = new LinkedHashMap<>();
                pm.put("id", r.getId());
                pm.put("amount", r.getAmountPaid());
                pm.put("paidOn", r.getPaidOn());
                pm.put("enteredAt", r.getTimestamp());
                pm.put("allocation", r.getAllocation());
                pm.put("type", r.getPaymentType());
                pm.put("payerClientId", r.getPayerClientId());
                Client payer = r.getPayerClientId() == null ? null : people.computeIfAbsent(r.getPayerClientId(), k -> clientRepo.findById(k).orElse(null));
                pm.put("payerName", payer != null ? payer.getFullName() : (r.getPayerName() != null ? r.getPayerName() : "payer not recorded"));
                boolean isReversal = "REVERSAL".equals(r.getPaymentType());
                boolean wasReversed = reversed.contains(String.valueOf(r.getId()));
                pm.put("reversal", isReversal);
                pm.put("reversed", wasReversed);
                pays.add(pm);
                if (!isReversal && !wasReversed && id.equals(r.getPayerClientId()) && r.getAmountPaid() != null) mine = mine.add(r.getAmountPaid());
            }
            row.put("payments", pays);
            row.put("paidByThisClient", mine);
            rows.add(row);
        }
        out.put("plots", rows);
        clientSummary(out, c, ps, ns, rows, hasPending, now);
        Map<String, Object> totals = new LinkedHashMap<>();
        for (String k : List.of("owed", "paid", "billed", "storage", "storagePaid", "storageUnpaid", "keptFees")) totals.put(k, out.get(k));
        out.put("totals", totals);

        List<Map<String, Object>> notes = new ArrayList<>();
        for (RecoveryNote n : ns) {
            Map<String, Object> nm = new LinkedHashMap<>();
            nm.put("id", n.getId()); nm.put("tag", n.getTag()); nm.put("tone", n.getTone()); nm.put("text", n.getText());
            nm.put("author", n.getAuthor() == null ? null : n.getAuthor().getUsername());
            nm.put("createdAt", n.getCreatedAt());
            notes.add(nm);
        }
        out.put("notes", notes);
        if (!seesMoney()) stripMoney(out);
        return out;
    }
}
