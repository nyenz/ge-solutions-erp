// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DashboardController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.auth.model.Role;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.modules.land.service.HomeDashboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/dashboard")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DashboardController {

    private final UserRepository userRepository;
    private final HomeDashboardService homeDashboardService;

    /**
     * fix181 (20.1): THE home page answer -- only the blocks of the caller's rank (HomeDashboardService.dashboardBlocks).
     * Money is never sent to Manager or Secretary. The old /summary and /director answers were removed in Step 5
     * (12.5c, 13.7): they loaded the whole audit table into memory and sent raw audit text to every rank.
     */
    @GetMapping("/home")
    public Map<String, Object> home() {
        String name = SecurityContextHolder.getContext().getAuthentication().getName();
        User u = userRepository.findByUsername(name).orElseThrow();
        return homeDashboardService.home(u.isRoot() ? Role.ROLE_ADMIN : u.getRole());
    }
}
