// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java
package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.model.Client;
import com.gesolutions.erp.modules.client.repository.ClientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * GE SOLUTIONS - PHASE 2 IDENTITY LOOKUP
 *
 * Lets the frontend check a National ID (NIN) before or while a form is
 * being filled in, so staff can be warned about a likely typo (NIN already
 * registered to a different name) or have known details auto-filled
 * (NIN matches an existing person), per Section 17.3.
 */
@RestController
@RequestMapping("/api/v1/clients")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class ClientController {

    private final ClientRepository clientRepository;
    private final com.gesolutions.erp.modules.land.repository.LandProjectRepository projectRepository;
    private final com.gesolutions.erp.common.audit.AuditService auditService;

    @GetMapping("/lookup-nin")
    public ResponseEntity<Map<String, Object>> lookupByNin(@RequestParam String nin) {
        Map<String, Object> result = new HashMap<>();

        if (nin == null || nin.isBlank()) {
            result.put("exists", false);
            return ResponseEntity.ok(result);
        }

        return clientRepository.findByNationalId(nin.trim().toUpperCase())
                .map(c -> {
                    result.put("exists", true);
                    result.put("fullName", c.getFullName());
                    result.put("phoneNumber", c.getPhoneNumber());
                    result.put("email", c.getEmail());
                    result.put("homeAddress", c.getHomeAddress());
                    result.put("nationalId", c.getNationalId());
                    return ResponseEntity.ok(result);
                })
                .orElseGet(() -> {
                    result.put("exists", false);
                    return ResponseEntity.ok(result);
                });
    }

    /**
     * CLIENT DOSSIER: PORTFOLIO EDIT
     * Lets staff correct a client's own contact details straight from the
     * dossier page (full name, phone, email, home address). The National ID
     * is deliberately NOT editable here -- it is the identity anchor the
     * whole client record is keyed on (Phase 2/C, see Client.nationalId),
     * so changing it is a re-registration concern, not a portfolio edit.
     * Money figures (owed/paid/storage) are also out of scope: those are
     * derived from project payment records and are only ever changed by
     * recording an actual payment on the project (Digital Folder), never
     * typed in directly, so the ledger stays trustworthy.
     */
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    public ResponseEntity<Map<String, Object>> updateClient(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        Client c = clientRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Client not found"));
        // fix181 (11.1b): a Secretary may fix a client's details only while every project of that client is Pending
        if (isSecretary() && !onlyPending(c)) {
            throw new com.gesolutions.erp.common.exception.BusinessException("CLIENT_EDIT_BLOCKED: A Secretary can change a client only while every project of that client is Pending. Ask a Manager.");
        }

        // fix181 (13.6a): what each field was before, for the audit line
        String before = "name " + c.getFullName() + ", phone " + c.getPhoneNumber() + ", email " + c.getEmail() + ", address " + c.getHomeAddress();
        if (body.containsKey("fullName") && body.get("fullName") != null && !body.get("fullName").isBlank()) {
            c.setFullName(body.get("fullName").trim());
        }
        if (body.containsKey("phoneNumber") && body.get("phoneNumber") != null && !body.get("phoneNumber").isBlank()) {
            c.setPhoneNumber(com.gesolutions.erp.common.util.PhoneUtil.normalizeList(body.get("phoneNumber")));
        }
        if (body.containsKey("email")) {
            String email = body.get("email");
            c.setEmail(email == null || email.isBlank() ? null : email.trim());
        }
        if (body.containsKey("homeAddress")) {
            String addr = body.get("homeAddress");
            c.setHomeAddress(addr == null || addr.isBlank() ? null : addr.trim());
        }
        clientRepository.save(c);
        String after = "name " + c.getFullName() + ", phone " + c.getPhoneNumber() + ", email " + c.getEmail() + ", address " + c.getHomeAddress();
        if (!before.equals(after)) {
            auditService.logActionAfterCommit("CLIENT_UPDATED", "Client " + c.getId() + " (NIN " + c.getNationalId() + ") changed. Old: " + before + " -> New: " + after);
        }

        Map<String, Object> out = new HashMap<>();
        out.put("id", c.getId());
        out.put("fullName", c.getFullName());
        out.put("phoneNumber", c.getPhoneNumber());
        out.put("email", c.getEmail());
        out.put("homeAddress", c.getHomeAddress());
        return ResponseEntity.ok(out);
    }

    // ── fix181 (8.10b): correct a mistyped National ID, only while every project of that client is Pending ──
    @PutMapping("/{id}/nin")
    @PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
    @org.springframework.transaction.annotation.Transactional
    public ResponseEntity<Map<String, Object>> correctNin(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        Client c = clientRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Client not found"));
        String nin = body == null || body.get("nationalId") == null ? "" : body.get("nationalId").trim().toUpperCase(java.util.Locale.ROOT);
        if (nin.isEmpty()) {
            throw new com.gesolutions.erp.common.exception.BusinessException("NIN_REQUIRED: Type the correct National ID.");
        }
        if (!onlyPending(c)) {
            throw new com.gesolutions.erp.common.exception.BusinessException("NIN_CHANGE_BLOCKED: The National ID can only be corrected while every project of this client is Pending.");
        }
        if (nin.equals(c.getNationalId())) {
            return ResponseEntity.ok(Map.of("id", c.getId(), "nationalId", nin));
        }
        var other = clientRepository.findByNationalId(nin);
        if (other.isPresent() && !other.get().getId().equals(c.getId())) {
            throw new com.gesolutions.erp.common.exception.BusinessException("NIN_TAKEN: This National ID already belongs to another client ("
                    + other.get().getFullName() + "). Put that client on the project instead.");
        }
        String old = c.getNationalId();
        c.setNationalId(nin);
        clientRepository.save(c);
        auditService.logActionAfterCommit("CLIENT_NIN_CORRECTED", "National ID of " + c.getFullName() + " corrected from " + old + " to " + nin + ".");
        return ResponseEntity.ok(Map.of("id", c.getId(), "nationalId", nin));
    }

    private boolean onlyPending(Client c) {
        var ps = projectRepository.findAllOfPersonIncludingPending(c.getId());
        return !ps.isEmpty() && ps.stream().allMatch(com.gesolutions.erp.modules.land.model.LandProject::isPending);
    }

    private static boolean isSecretary() {
        var a = org.springframework.security.core.context.SecurityContextHolder.getContext().getAuthentication();
        return a != null && a.getAuthorities().stream().anyMatch(g -> "ROLE_SECRETARY".equals(g.getAuthority()));
    }
}
