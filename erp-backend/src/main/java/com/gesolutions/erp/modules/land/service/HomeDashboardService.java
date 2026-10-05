// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/HomeDashboardService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditLog;
import com.gesolutions.erp.common.audit.AuditLogRepository;
import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.client.service.RecoveryStateService;
import com.gesolutions.erp.modules.finance.repository.ExpenseRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectType;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * fix181 (20.1 to 20.8, 12.5): THE HOME PAGE, built per rank on the server.
 * dashboardBlocks(rank) is the ONE list of what each rank sees; the answer carries only those blocks (money is never
 * sent to Manager or Secretary). The page draws whatever blocks arrive. Answers are kept for 60 seconds per rank.
 */
@Service
@RequiredArgsConstructor
public class HomeDashboardService {

    public static List<String> dashboardBlocks(Role rank) {
        return switch (rank) {
            case ROLE_SECRETARY -> List.of("workQueue", "dueCalls", "problems", "newProjects");
            case ROLE_MANAGER -> List.of("workQueue", "pipeline", "releaseReady", "problems", "receivables", "dueCalls", "newProjects");
            case ROLE_DIRECTOR -> List.of("money", "periods", "waitingForYou", "workQueue", "pipeline", "dueCalls", "newProjects", "recentActivity");
            case ROLE_ADMIN -> List.of("systemHealth", "money", "periods", "waitingForYou", "workQueue", "pipeline", "dueCalls", "newProjects", "recentActivity");
            default -> List.of();
        };
    }

    private static final List<String> HIDDEN_FROM_ACTIVITY = com.gesolutions.erp.common.audit.AuditActions.NOT_STAFF_WORK;   // 13.13: the shared code list

    private final LandProjectRepository projectRepository;
    private final PaymentRecordRepository paymentRepository;
    private final ExpenseRepository expenseRepository;
    private final AuditLogRepository auditRepository;
    private final UserRepository userRepository;
    private final RecoveryStateService recovery;
    private final WorkCountsService workCounts;
    private final BooksCheckService booksCheck;

    private final Map<Role, Object[]> cache = new ConcurrentHashMap<>();

    public Map<String, Object> home(Role rank) {
        Object[] hit = cache.get(rank);
        if (hit != null && System.currentTimeMillis() - (Long) hit[0] < 60_000L) {
            @SuppressWarnings("unchecked") Map<String, Object> m = (Map<String, Object>) hit[1];
            return m;
        }
        Map<String, Object> m = build(rank);
        cache.put(rank, new Object[]{System.currentTimeMillis(), m});
        return m;
    }

    /** Called after a change that moves the numbers (a payment, a status move...): the next answer is fresh. */
    public void forget() { cache.clear(); }

    @Transactional(readOnly = true)
    Map<String, Object> build(Role rank) {
        LocalDateTime now = LocalDateTime.now();
        List<String> blocks = dashboardBlocks(rank);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("rank", rank.name());
        out.put("rankLabel", rank.label());
        out.put("blocks", blocks);
        out.put("serverTime", now);

        List<LandProject> live = projectRepository.findAll();   // no deleted, no Pending
        Map<String, Object> wc = workCounts.counts();

        if (blocks.contains("workQueue")) {
            Map<String, Object> q = new LinkedHashMap<>();
            q.put("pending", wc.get("pending"));
            q.put("problems", wc.get("problems"));
            q.put("receivables", wc.get("receivables"));
            q.put("releaseReady", wc.get("releaseReady"));
            out.put("workQueue", q);
        }
        if (blocks.contains("dueCalls")) out.put("dueCalls", recovery.dueNowCached());
        if (blocks.contains("problems")) out.put("problems", wc.get("problems"));
        if (blocks.contains("receivables")) out.put("receivables", wc.get("receivables"));
        if (blocks.contains("pipeline")) out.put("pipeline", wc.get("byType"));
        if (blocks.contains("newProjects")) {
            // 20.9: by the day the project was ENTERED (created_at), not a typed start date or the title date
            LocalDateTime weekAgo = now.minusDays(7);
            out.put("newProjects", projectRepository.findAllIncludingPending().stream()
                    .filter(p -> p.getCreatedAt() != null && p.getCreatedAt().isAfter(weekAgo)).count());
        }
        if (blocks.contains("releaseReady")) {
            List<Map<String, Object>> list = new ArrayList<>();
            for (LandProject p : live) {
                if (p.releaseBlocker() != null) continue;
                if (list.size() >= 10) break;
                // fix182: the type and the first client, so the Dashboard chip says what it is
                Map<String, Object> r = new LinkedHashMap<>();
                r.put("id", p.getId());
                r.put("index", String.valueOf(p.getProjectIndex()));
                r.put("type", ProjectType.of(p).getLabel());
                var parties = p.billingParties();
                r.put("client", parties == null || parties.isEmpty() ? null : parties.iterator().next().getFullName());
                list.add(r);
            }
            out.put("releaseReady", Map.of("count", wc.get("releaseReady"), "first", list));
        }
        if (blocks.contains("money")) out.put("money", money(live, now));
        if (blocks.contains("periods")) {
            Map<String, Object> per = new LinkedHashMap<>();
            List<PaymentRecord> lines = paymentRepository.findAll();   // fix182: read once for both windows
            per.put("WEEK", period(lines, now.minusDays(7), now, "LAST 7 DAYS"));
            per.put("MONTH", period(lines, now.minusDays(30), now, "LAST 30 DAYS"));
            out.put("periods", per);
        }
        if (blocks.contains("waitingForYou")) {
            Map<String, Object> w = new LinkedHashMap<>();
            w.put("releaseReady", wc.get("releaseReady"));
            w.put("problems", wc.get("problems"));
            w.put("flaggedReceivableThisWeek", live.stream().filter(p -> p.isReceivable() && p.getReceivableStartDate() != null
                    && p.getReceivableStartDate().isAfter(now.minusDays(7))).count());
            w.put("booksMismatch", safeBooks());
            out.put("waitingForYou", w);
        }
        if (blocks.contains("recentActivity")) {
            List<Map<String, Object>> rows = new ArrayList<>();
            for (AuditLog a : auditRepository.findRecentExcept(HIDDEN_FROM_ACTIVITY, PageRequest.of(0, 8))) {
                Map<String, Object> r = new LinkedHashMap<>();
                r.put("id", a.getId()); r.put("action", a.getAction()); r.put("performedBy", a.getPerformedBy());
                r.put("timestamp", a.getTimestamp());
                String d = a.getDetails() == null ? "" : a.getDetails();
                r.put("details", d.length() > 160 ? d.substring(0, 160) + "..." : d);
                rows.add(r);
            }
            out.put("recentActivity", rows);
        }
        if (blocks.contains("systemHealth")) {
            Map<String, Object> h = new LinkedHashMap<>();
            h.put("failedLogins24h", auditRepository.countByActionInAndTimestampAfter(List.of(com.gesolutions.erp.common.audit.AuditActions.LOGIN_FAILED), now.minusHours(24)));
            h.put("jobFailures7d", auditRepository.countByActionInAndTimestampAfter(List.of(com.gesolutions.erp.common.audit.AuditActions.STORAGE_JOB_FAILED, com.gesolutions.erp.common.audit.AuditActions.AUTO_RECEIVABLE_FAILED), now.minusDays(7)));
            h.put("booksMismatch", safeBooks());
            h.put("accounts", userRepository.count());
            long admins = userRepository.countByRole(Role.ROLE_ADMIN);
            h.put("adminAccounts", admins);
            h.put("oneAdminWarning", admins > 1 ? "There is more than one Admin account. There must be exactly one." : null);
            h.put("auditLinesToday", auditRepository.countByTimestampAfter(now.toLocalDate().atStartOfDay()));
            out.put("systemHealth", h);
        }
        return out;
    }

    private long safeBooks() {
        try { return booksCheck.differences().size(); } catch (Exception e) { return -1; }
    }

    /** 12.5a, 20.4: title money and storage money apart; the bar never passes 100; arrears never below 0. */
    private Map<String, Object> money(List<LandProject> live, LocalDateTime now) {
        BigDecimal value = BigDecimal.ZERO, titleCollected = BigDecimal.ZERO, titleArrears = BigDecimal.ZERO;
        BigDecimal feesAccrued = BigDecimal.ZERO, feesCollected = BigDecimal.ZERO, feesUnpaid = BigDecimal.ZERO, kept = BigDecimal.ZERO;
        for (LandProject p : live) {
            if (p.getTotalCost() != null && p.getTotalCost().signum() > 0) value = value.add(p.getTotalCost());
            titleCollected = titleCollected.add(p.titlePaid());
            titleArrears = titleArrears.add(p.titleOwed());
            if (p.isReceivable()) {
                feesAccrued = feesAccrued.add(p.getStorageFeesAccumulated() == null ? BigDecimal.ZERO : p.getStorageFeesAccumulated());
                feesCollected = feesCollected.add(p.storagePaidSafe());
                feesUnpaid = feesUnpaid.add(p.storageUnpaid());
            } else {
                kept = kept.add(p.keptFees());
            }
        }
        double pct = value.signum() > 0 ? Math.min(100.0, titleCollected.multiply(BigDecimal.valueOf(100)).divide(value, 2, RoundingMode.HALF_UP).doubleValue()) : 0.0;
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("totalValue", value);
        m.put("titleCollected", titleCollected);
        m.put("titleArrears", titleArrears);
        m.put("collectionPercent", pct);
        m.put("storageFeesAccrued", feesAccrued);
        m.put("storageFeesCollected", feesCollected);
        m.put("storageFeesUnpaid", feesUnpaid);
        m.put("keptFees", kept);
        m.put("collectedThisMonth", paymentRepository.sumAllPaymentsSince(now.toLocalDate().withDayOfMonth(1).atStartOfDay()));
        List<Object[]> und = paymentRepository.undatedDeposits();
        m.put("undatedCount", und.isEmpty() ? 0 : ((Number) und.get(0)[0]).longValue());
        m.put("undatedSum", und.isEmpty() ? BigDecimal.ZERO : und.get(0)[1]);
        // 20.4c: the last 6 months with EVERY month present (a month with no payment is 0)
        Map<String, BigDecimal> byMonth = new LinkedHashMap<>();
        YearMonth first = YearMonth.from(now).minusMonths(5);
        for (int i = 0; i < 6; i++) byMonth.put(first.plusMonths(i).toString(), BigDecimal.ZERO);
        for (Object[] row : paymentRepository.monthlyRevenueSince(first.atDay(1).atStartOfDay())) {
            if (row[0] == null) continue;
            String key = String.valueOf(row[0]).substring(0, 7);
            if (byMonth.containsKey(key)) byMonth.put(key, row[1] == null ? BigDecimal.ZERO : new BigDecimal(row[1].toString()));
        }
        List<Map<String, Object>> trend = new ArrayList<>();
        byMonth.forEach((k, v) -> trend.add(Map.of("month", k, "amount", v)));
        m.put("trend", trend);
        return m;
    }

    /** 20.6: money in and out for a window; transactions = payment lines in it, a reversed pair counted as none. */
    private Map<String, Object> period(List<PaymentRecord> lines, LocalDateTime from, LocalDateTime to, String label) {
        BigDecimal in = paymentRepository.sumAllPaymentsSince(from);
        BigDecimal out = expenseRepository.sumBetween(from, to);
        Set<String> reversedIds = new HashSet<>();
        List<PaymentRecord> window = new ArrayList<>();
        for (PaymentRecord r : lines) {
            if (r.getNotes() != null && r.getNotes().startsWith("[REVERSAL OF ")) {
                int e = r.getNotes().indexOf(']');
                if (e > 13) reversedIds.add(r.getNotes().substring(13, e).trim());
            }
            if (r.getPaidOn() != null && !r.getPaidOn().isBefore(from) && !r.getPaidOn().isAfter(to)) window.add(r);
        }
        long tx = window.stream().filter(r -> !"REVERSAL".equals(r.getPaymentType()) && !reversedIds.contains(String.valueOf(r.getId()))).count();
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("label", label);
        m.put("revenue", in);
        m.put("expenses", out == null ? BigDecimal.ZERO : out);
        m.put("net", in.subtract(out == null ? BigDecimal.ZERO : out));
        m.put("transactions", tx);
        return m;
    }
}
