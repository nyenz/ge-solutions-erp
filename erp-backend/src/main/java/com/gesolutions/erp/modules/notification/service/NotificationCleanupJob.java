// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/notification/service/NotificationCleanupJob.java
package com.gesolutions.erp.modules.notification.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.modules.notification.repository.NotificationReadRepository;
import com.gesolutions.erp.modules.notification.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/** fix181 (14.8): bell alerts (and their read markers) older than 90 days are removed every night at 02:30. */
@Service
@RequiredArgsConstructor
public class NotificationCleanupJob {

    public static final int KEEP_DAYS = 90;

    private final NotificationRepository notifications;
    private final NotificationReadRepository reads;
    private final AuditService auditService;

    @Scheduled(cron = "0 30 2 * * *", zone = "Africa/Kampala")
    @Transactional
    public void cleanup() {
        int n = notifications.deleteOlderThan(LocalDateTime.now().minusDays(KEEP_DAYS));
        int r = reads.deleteOrphans();
        if (n > 0) {
            auditService.logActionAfterCommit("NOTIFICATIONS_CLEANED", "SYSTEM: " + n + " bell alert(s) older than " + KEEP_DAYS
                    + " days removed (" + r + " read marker(s)).");
        }
    }
}
