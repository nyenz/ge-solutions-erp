// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/service/ClientService.java
package com.gesolutions.erp.modules.client.service;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * GE SOLUTIONS - CLIENT MANAGEMENT ENGINE
 * 
 * Physically enforces the 2-14 recovery protocol:
 * - Resets monthly call counters on new calendar months.
 * - Caps interactions at 2 per month to prevent harassment.
 * - Identifies "Stale" assets for the Recovery Hub.
 */
@Service
@RequiredArgsConstructor
public class ClientService {

    private final ClientRepository clientRepository;
    private final AuditService auditService;
    private final com.gesolutions.erp.modules.notification.service.NotificationService notificationService;

    /**
     * RECOVERY ACTION: LOG CONTACT
     * physically increments the counter and resets the 14-day clock.
     * Enforces the Monthly Reset "Handbrake".
     */
    @Transactional
    public void logManagerContact(UUID clientId) {
        Client client = clientRepository.findById(clientId)
                .orElseThrow(() -> new BusinessException("IDENTITY_FAULT: Client record missing."));

        // 1. MONTHLY RESET HANDBRAKE
        // If the last call was in a different month, reset counter to 0
        if (client.shouldResetMonthlyCounter()) {
            client.setMonthlyContactCount(0);
        }

        // 2. INCREMENT AND TIMESTAMP
        client.setMonthlyContactCount(client.getMonthlyContactCount() + 1);
        client.setLastContactedAt(LocalDateTime.now());
        
        // 3. RELIABILITY ADJUSTMENT
        // Reward the client score for picking up/being reachable
        double newScore = Math.min(100.0, client.getReliabilityScore() + 1.5);
        client.setReliabilityScore(newScore);

        clientRepository.save(client);
        
        auditService.logActionAfterCommit("RECOVERY_SYNC", 
            "Call logged for " + client.getFullName() + ". Monthly count: " + client.getMonthlyContactCount() + "/2");
    }

    /**
     * INTAKE: FIND OR CREATE (LEGACY, PHONE-BASED)
     * Standard industrial deduplication based on Phone Number.
     * DEPRECATED since PHASE C (Section 18.4/18.10): national_id is now
     * NOT NULL at the DB level, and this method never sets it, so calling
     * it would now fail with a DB integrity violation. Confirmed unused --
     * no call sites anywhere in the codebase. Left in place rather than
     * deleted since nothing calls it and this phase is scoped to the NIN
     * constraint itself; use findOrCreateClientByNin() for anything new.
     */
    @Transactional
    public Client findOrCreateClient(String fullName, String phone, String email) {
        return clientRepository.findByPhoneNumber(phone)
                .orElseGet(() -> {
                    Client newClient = Client.builder()
                            .fullName(fullName)
                            .phoneNumber(phone)
                            .email(email)
                            .monthlyContactCount(0)
                            .reliabilityScore(100.0)
                            .build();
                    
                    Client saved = clientRepository.save(newClient);
                    auditService.logActionAfterCommit("CLIENT_ARCHIVE", "New identity registered: " + fullName);
                    return saved;
                });
    }

    /**
     * NIN-BASED IDENTITY LOOKUP
     * Finds an existing person by their National ID (NIN), or creates a new one.
     * Per business rule (Section 17.3): if a person's NIN changes, they are
     * treated as a brand new person record -- this method never merges by
     * name or phone, only ever by NIN.
     * PHASE C (Section 18.4/18.10): the blank-NIN check and the
     * NIN_NAME_MISMATCH guard below were already correct -- they did not
     * rely on the column being optional. What changed is that
     * Client.nationalId is now a genuinely enforced NOT NULL + UNIQUE
     * column underneath this method (see DataInitializer), instead of the
     * soft convention it used to be.
     */
    @Transactional
    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {
        // fix139: one standard phone format (blank is only tolerated for an existing client)
        String cleanPhone = (phone == null || phone.isBlank()) ? null
                : com.gesolutions.erp.common.util.PhoneUtil.normalizeList(phone);
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
            // fix181 (11.11): repeated spaces do not make a different name (the order of the words still matters)
            String existingName = existing.get().getFullName() == null ? "" : existing.get().getFullName().trim().replaceAll("\\s+", " ");
            String typedName = fullName == null ? "" : fullName.trim().replaceAll("\\s+", " ");
            if (!existingName.equalsIgnoreCase(typedName)) {
                // fix181 (8.10a): an Employee never reads another person's name back from a NIN
                var auth = org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication();
                boolean employee = auth != null && auth.getAuthorities().stream().anyMatch(a -> "ROLE_EMPLOYEE".equals(a.getAuthority()));
                if (employee) {
                    // the office hears once a day per person that a field entry is stuck (no names in the alert)
                    if (notificationService != null) notificationService.emitNow("NIN_CONFLICT",
                            "An employee could not save a project: a National ID is already registered under another name. Please check.",
                            "CLIENT", existing.get().getId());
                    throw new BusinessException("NIN_CONFLICT: This National ID is already registered under a different name. Check the NIN, or ask a Secretary.");
                }
                throw new BusinessException("NIN_NAME_MISMATCH: This NIN is already registered to '"
                        + existingName + "', but you entered '" + typedName
                        + "'. Confirm this is the same person before continuing, or check the NIN for a typo.");
            }
            return existing.get();
        }

        Client newClient = Client.builder()
                .fullName(fullName)
                .phoneNumber(cleanPhone != null ? cleanPhone
                        : com.gesolutions.erp.common.util.PhoneUtil.normalizeList(phone))
                .nationalId(normalizedNin)
                .email(email)
                .monthlyContactCount(0)
                .reliabilityScore(100.0)
                .build();

        Client saved = clientRepository.save(newClient);
        auditService.logActionAfterCommit("CLIENT_ARCHIVE",
            "New identity registered via NIN: " + fullName + " (" + normalizedNin + ")");
        return saved;
    }

    /**
     * SYSTEM UTILITY: ADJUST RELIABILITY
     * Manually adjusted by financial events (e.g., missed payments lower score).
     */
    @Transactional
    public void adjustReliability(UUID clientId, double delta) {
        Client client = clientRepository.findById(clientId).orElseThrow();
        double updated = Math.max(0.0, Math.min(100.0, client.getReliabilityScore() + delta));
        client.setReliabilityScore(updated);
        clientRepository.save(client);
    }
}