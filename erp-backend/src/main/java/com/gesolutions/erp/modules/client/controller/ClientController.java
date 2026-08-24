// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/ClientController.java
package com.gesolutions.erp.modules.client.controller;

import com.gesolutions.erp.modules.client.repository.ClientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

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
}
