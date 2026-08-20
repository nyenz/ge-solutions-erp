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

    /**
     * DISCOVERY: GET STALE CALL LIST
     * Returns all proprietors who haven't been contacted in 14 days 
     * and have not exceeded their 2-call monthly limit.
     */
    @Transactional(readOnly = true)
    public List<Client> getStaleRecoveryList() {
        return clientRepository.findStaleClientsForRecovery();
    }

    /**
     * SENSOR: NOTIFICATION COUNT
     * Powers the header bell icon.
     */
    @Transactional(readOnly = true)
    public long getRecoveryTaskCount() {
        return clientRepository.countTotalStaleClients();
    }

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
        
        auditService.logAction("RECOVERY_SYNC", 
            "Call logged for " + client.getFullName() + ". Monthly count: " + client.getMonthlyContactCount() + "/2");
    }

    /**
     * INTAKE: FIND OR CREATE
     * Standard industrial deduplication based on Phone Number.
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
                    auditService.logAction("CLIENT_ARCHIVE", "New identity registered: " + fullName);
                    return saved;
                });
    }

    /**
     * PHASE 2: NIN-BASED IDENTITY LOOKUP
     * Finds an existing person by their National ID (NIN), or creates a new one.
     * Per business rule (Section 17.3): if a person's NIN changes, they are
     * treated as a brand new person record -- this method never merges by
     * name or phone, only ever by NIN.
     */
    @Transactional
    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {
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
            String existingName = existing.get().getFullName() == null ? "" : existing.get().getFullName().trim();
            String typedName = fullName == null ? "" : fullName.trim();
            if (!existingName.equalsIgnoreCase(typedName)) {
                throw new BusinessException("NIN_NAME_MISMATCH: This NIN is already registered to '"
                        + existingName + "', but you entered '" + typedName
                        + "'. Confirm this is the same person before continuing, or check the NIN for a typo.");
            }
            return existing.get();
        }

        Client newClient = Client.builder()
                .fullName(fullName)
                .phoneNumber(phone)
                .nationalId(normalizedNin)
                .email(email)
                .monthlyContactCount(0)
                .reliabilityScore(100.0)
                .build();

        Client saved = clientRepository.save(newClient);
        auditService.logAction("CLIENT_ARCHIVE",
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