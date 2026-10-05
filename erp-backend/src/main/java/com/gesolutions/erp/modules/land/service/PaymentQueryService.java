// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/PaymentQueryService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.model.PaymentRecord;
import com.gesolutions.erp.modules.land.model.ProjectType;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * fix181 (12.4, 16.1 to 16.7, 16.10): THE payment list, used by the Payments page and the Reports PAYMENTS data.
 *  - one row per payment line with the facts that matter: purpose (allocation TITLE / STORAGE; old rows = TITLE), kind
 *    (OPENING_DEPOSIT, IN_RECEIVABLES, PAYMENT, REVERSAL), who paid (the client's CURRENT name), the project index and
 *    type, the receipt, reversed / reverses, the day paid and the entry time;
 *  - filtering, sorting and paging are done here; the totals are worked out for the SAME filters over every row (not
 *    just one page), and payments of deleted projects are never in a total;
 *  - three reads: the payment lines, their projects, their payers.
 */
@Service
@RequiredArgsConstructor
public class PaymentQueryService {

    public static final int MAX_PAGE = 200;

    private final PaymentRecordRepository paymentRepository;
    private final LandProjectRepository projectRepository;
    private final ClientRepository clientRepository;

    public record Filter(LocalDate from, LocalDate to, String tab, String projectType, String q,
                         boolean includeDeleted, boolean missingReceipt, String sort, String dir) {}

    public static String kindOf(PaymentRecord r) {
        if ("REVERSAL".equals(r.getPaymentType())) return "REVERSAL";
        if ("INITIAL_DEPOSIT".equals(r.getPaymentType())) return "OPENING_DEPOSIT";
        if ("RECEIVABLE_PARTIAL".equals(r.getPaymentType())) return "IN_RECEIVABLES";
        return "PAYMENT";
    }

    private static String allocationOf(PaymentRecord r) {
        return "STORAGE".equals(r.getAllocation()) ? "STORAGE" : "TITLE";
    }

    @Transactional(readOnly = true)
    public List<Map<String, Object>> rows(Filter f) {
        List<PaymentRecord> all = paymentRepository.findAll();
        Set<UUID> pids = all.stream().map(PaymentRecord::getProjectId).filter(Objects::nonNull).collect(Collectors.toSet());
        Map<UUID, LandProject> projects = new HashMap<>();
        for (LandProject p : projectRepository.findAllById(pids)) projects.put(p.getId(), p);
        Set<UUID> payerIds = all.stream().map(PaymentRecord::getPayerClientId).filter(Objects::nonNull).collect(Collectors.toSet());
        Map<UUID, Client> payers = new HashMap<>();
        for (Client c : clientRepository.findAllById(payerIds)) payers.put(c.getId(), c);

        // reversals: "[REVERSAL OF <id>] reason"
        Map<String, PaymentRecord> reversalOf = new HashMap<>();
        for (PaymentRecord r : all) {
            if (r.getNotes() != null && r.getNotes().startsWith("[REVERSAL OF ")) {
                int e = r.getNotes().indexOf(']');
                if (e > 13) reversalOf.put(r.getNotes().substring(13, e).trim(), r);
            }
        }
        Map<String, PaymentRecord> byId = new HashMap<>();
        for (PaymentRecord r : all) byId.put(String.valueOf(r.getId()), r);

        List<Map<String, Object>> out = new ArrayList<>();
        for (PaymentRecord r : all) {
            LandProject p = projects.get(r.getProjectId());
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", r.getId());
            m.put("projectId", r.getProjectId());
            m.put("projectIndex", p == null ? null : p.getProjectIndex());
            m.put("projectType", p == null ? null : ProjectType.of(p).name());
            m.put("projectTypeLabel", p == null ? null : ProjectType.of(p).getLabel());
            m.put("plotNumber", p == null || p.getLandTitle() == null ? null : p.getLandTitle().getPlotNumber());
            m.put("deleted", p != null && p.isDeleted());
            m.put("amountPaid", r.getAmountPaid());
            m.put("paymentType", r.getPaymentType());
            m.put("allocation", allocationOf(r));
            m.put("kind", kindOf(r));
            m.put("recordedBy", r.getRecordedBy());
            m.put("notes", r.getNotes());
            m.put("balanceAfter", r.getBalanceAfter());
            m.put("paidOn", r.getPaidOn());
            m.put("timestamp", r.getPaidOn() != null ? r.getPaidOn() : r.getTimestamp());   // old pages read this
            m.put("enteredAt", r.getTimestamp());
            // the time of day is real only when the money was taken when it was typed in (a past day is a 12:00 placeholder)
            m.put("timeKnown", r.getPaidOn() != null && r.getTimestamp() != null && r.getPaidOn().equals(r.getTimestamp()));
            Client payer = r.getPayerClientId() == null ? null : payers.get(r.getPayerClientId());
            String name = payer != null ? payer.getFullName() : r.getPayerName();
            m.put("clientName", name != null ? name : "Payer not recorded");
            m.put("ownerName", name != null ? name : "Payer not recorded");   // old field name, same value
            m.put("payerClientId", r.getPayerClientId());
            m.put("payerPhone", payer != null ? payer.getPhoneNumber() : null);
            m.put("hasReceipt", r.getReceiptDocumentId() != null);
            m.put("receiptDocumentId", r.getReceiptDocumentId());
            PaymentRecord rev = reversalOf.get(String.valueOf(r.getId()));
            m.put("reversed", rev != null);
            m.put("reversedBy", rev == null ? null : rev.getId());
            String origId = null;
            if (r.getNotes() != null && r.getNotes().startsWith("[REVERSAL OF ")) {
                int e = r.getNotes().indexOf(']');
                if (e > 13) origId = r.getNotes().substring(13, e).trim();
            }
            m.put("reversalOf", origId);
            PaymentRecord orig = origId == null ? null : byId.get(origId);
            m.put("reversalOfDate", orig == null ? null : (orig.getPaidOn() != null ? orig.getPaidOn() : orig.getTimestamp()));
            if (matches(m, f)) out.add(m);
        }
        sort(out, f);
        return out;
    }

    private static boolean matches(Map<String, Object> m, Filter f) {
        if (!f.includeDeleted() && Boolean.TRUE.equals(m.get("deleted"))) return false;
        String tab = f.tab() == null ? "ALL" : f.tab().toUpperCase(Locale.ROOT);
        switch (tab) {
            case "TITLE" -> { if (!"TITLE".equals(m.get("allocation"))) return false; }
            case "STORAGE" -> { if (!"STORAGE".equals(m.get("allocation"))) return false; }
            case "OPENING" -> { if (!"OPENING_DEPOSIT".equals(m.get("kind"))) return false; }
            case "REVERSALS" -> { if (!"REVERSAL".equals(m.get("kind"))) return false; }
            default -> { }
        }
        if (f.projectType() != null && !f.projectType().isBlank() && !f.projectType().equals(m.get("projectType"))) return false;
        if (f.missingReceipt() && (Boolean.TRUE.equals(m.get("hasReceipt")) || "REVERSAL".equals(m.get("kind")))) return false;
        LocalDateTime paid = (LocalDateTime) m.get("paidOn");
        if ((f.from() != null || f.to() != null) && paid == null) return false;   // undated rows only without a date filter
        if (f.from() != null && paid.toLocalDate().isBefore(f.from())) return false;
        if (f.to() != null && paid.toLocalDate().isAfter(f.to())) return false;
        if (f.q() != null && !f.q().isBlank()) {
            String t = f.q().toLowerCase(Locale.ROOT).trim();
            String digits = t.replaceAll("[^0-9]", "");
            StringBuilder hay = new StringBuilder();
            for (String k : List.of("projectIndex", "plotNumber", "clientName", "payerPhone", "recordedBy", "notes", "projectTypeLabel")) {
                Object v = m.get(k);
                if (v != null) hay.append(v).append(' ');
            }
            boolean amountHit = !digits.isEmpty() && digits.length() == t.replaceAll("[ ,]", "").length()
                    && m.get("amountPaid") instanceof BigDecimal a && a.abs().toBigInteger().toString().contains(digits);
            if (!hay.toString().toLowerCase(Locale.ROOT).contains(t) && !amountHit) return false;
        }
        return true;
    }

    private static void sort(List<Map<String, Object>> rows, Filter f) {
        String key = f.sort() == null ? "date" : f.sort();
        boolean asc = "asc".equalsIgnoreCase(f.dir());
        Comparator<Map<String, Object>> c = switch (key) {
            case "amount" -> Comparator.comparing(m -> (BigDecimal) m.get("amountPaid"), Comparator.nullsLast(Comparator.naturalOrder()));
            case "project" -> Comparator.comparing(m -> String.valueOf(m.get("projectIndex")));
            case "client" -> Comparator.comparing(m -> String.valueOf(m.get("clientName")).toLowerCase(Locale.ROOT));
            default -> Comparator.comparing(m -> (LocalDateTime) m.get("paidOn"), Comparator.nullsLast(Comparator.naturalOrder()));
        };
        if (!asc) c = c.reversed();
        if ("date".equals(key)) {
            // rows without a date always last, whatever the direction (16.4c)
            Comparator<Map<String, Object>> inner = c;
            c = (a, b) -> {
                boolean an = a.get("paidOn") == null, bn = b.get("paidOn") == null;
                if (an != bn) return an ? 1 : -1;
                return an ? 0 : inner.compare(a, b);
            };
        }
        rows.sort(c.thenComparing(m -> String.valueOf(m.get("id"))));
    }

    /** One page, plus how many rows there are in all. */
    public Map<String, Object> page(Filter f, int page, int size) {
        int s = Math.min(Math.max(size, 1), MAX_PAGE);
        int pg = Math.max(page, 0);
        List<Map<String, Object>> all = rows(f);
        int from = Math.min(pg * s, all.size());
        int to = Math.min(from + s, all.size());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("rows", all.subList(from, to));
        out.put("total", all.size());
        out.put("page", pg);
        out.put("size", s);
        return out;
    }

    /** The card numbers for the same filters: never a deleted project, reversals subtracted (net). */
    public Map<String, Object> totals(Filter f) {
        Filter live = new Filter(f.from(), f.to(), f.tab(), f.projectType(), f.q(), false, f.missingReceipt(), f.sort(), f.dir());
        BigDecimal title = BigDecimal.ZERO, storage = BigDecimal.ZERO, reversed = BigDecimal.ZERO, undatedSum = BigDecimal.ZERO;
        long undated = 0, count = 0;
        for (Map<String, Object> m : rows(live)) {
            BigDecimal a = m.get("amountPaid") instanceof BigDecimal b ? b : BigDecimal.ZERO;
            count++;
            if (m.get("paidOn") == null) { undated++; undatedSum = undatedSum.add(a); }
            if ("STORAGE".equals(m.get("allocation"))) storage = storage.add(a); else title = title.add(a);
            if ("REVERSAL".equals(m.get("kind"))) reversed = reversed.add(a.abs());
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("titleNet", title);
        out.put("storageNet", storage);
        out.put("reversed", reversed);
        out.put("net", title.add(storage));
        out.put("undatedCount", undated);
        out.put("undatedSum", undatedSum);
        out.put("rowCount", count);
        return out;
    }
}
