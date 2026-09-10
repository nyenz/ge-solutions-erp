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
    public ResponseEntity<Map<String, Object>> updateClient(@PathVariable UUID id, @RequestBody Map<String, String> body) {
        Client c = clientRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Client not found"));

        if (body.containsKey("fullName") && body.get("fullName") != null && !body.get("fullName").isBlank()) {
            c.setFullName(body.get("fullName").trim());
        }
        if (body.containsKey("phoneNumber") && body.get("phoneNumber") != null && !body.get("phoneNumber").isBlank()) {
            c.setPhoneNumber(body.get("phoneNumber").trim());
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

        Map<String, Object> out = new HashMap<>();
        out.put("id", c.getId());
        out.put("fullName", c.getFullName());
        out.put("phoneNumber", c.getPhoneNumber());
        out.put("email", c.getEmail());
        out.put("homeAddress", c.getHomeAddress());
        return ResponseEntity.ok(out);
    }
}
