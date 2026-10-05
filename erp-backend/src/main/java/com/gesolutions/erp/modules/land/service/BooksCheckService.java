// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BooksCheckService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.land.model.LandProject;
import com.gesolutions.erp.modules.land.repository.LandProjectRepository;
import com.gesolutions.erp.modules.land.repository.PaymentRecordRepository;
import com.gesolutions.erp.modules.notification.service.NotificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * fix181 (16.12c): THE BOOKS CHECK. A project's amountPaid is a running total changed only by a payment, a reversal and
 * the intake; the Payments page adds up the payment LINES. This compares the two for every live project and lists the
 * ones that differ. It never changes a number (report only); a person decides what to do.
 * Runs every night at 01:00 (Kampala): one SYSTEM audit line and one alert to the Director and the Admin, only when
 * something differs.
 */
@Service
@RequiredArgsConstructor
public class BooksCheckService {

    private final LandProjectRepository projectRepository;
    private final PaymentRecordRepository paymentRepository;
    private final AuditService auditService;
    private final NotificationService notificationService;

    @Transactional(readOnly = true)
    public List<Map<String, Object>> differences() {
        Map<UUID, BigDecimal> lines = new HashMap<>();
        for (Object[] row : paymentRepository.sumPerProject()) {
            lines.put((UUID) row[0], row[1] == null ? BigDecimal.ZERO : new BigDecimal(row[1].toString()));
        }
        List<Map<String, Object>> out = new ArrayList<>();
        for (LandProject p : projectRepository.findAllIncludingPending()) {
            BigDecimal sum = lines.getOrDefault(p.getId(), BigDecimal.ZERO);
            BigDecimal paid = p.getAmountPaid() == null ? BigDecimal.ZERO : p.getAmountPaid();
            if (sum.compareTo(paid) == 0) continue;
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("projectId", p.getId());
            m.put("projectIndex", p.getProjectIndex());
            m.put("client", p.billingParties().stream().findFirst().map(c -> c.getFullName()).orElse("---"));
            m.put("sumOfLines", sum);
            m.put("amountPaid", paid);
            m.put("difference", paid.subtract(sum));
            out.add(m);
        }
        out.sort(Comparator.comparing(m -> String.valueOf(m.get("projectIndex"))));
        return out;
    }

    @Scheduled(cron = "0 0 1 * * *", zone = "Africa/Kampala")
    public void nightly() {
        List<Map<String, Object>> diff;
        try { diff = differences(); } catch (Exception e) { System.err.println(">>> [BOOKS] check failed: " + e.getMessage()); return; }
        if (diff.isEmpty()) return;
        StringBuilder which = new StringBuilder();
        for (Map<String, Object> m : diff) {
            if (which.length() > 0) which.append(", ");
            which.append("#").append(m.get("projectIndex")).append(" (").append(m.get("difference")).append(")");
        }
        auditService.logAction("BOOKS_MISMATCH", "SYSTEM: the books check found " + diff.size()
                + " project(s) where the payment lines and the amount paid differ: " + which + ". Nothing was changed.");
        notificationService.emitToAudience("BOOKS_MISMATCH",
                "The books check found " + diff.size() + " project(s) where the payments do not add up. Open Payments > BOOKS CHECK.",
                "SYSTEM", UUID.nameUUIDFromBytes("job|books-check".getBytes(StandardCharsets.UTF_8)));
    }
}
