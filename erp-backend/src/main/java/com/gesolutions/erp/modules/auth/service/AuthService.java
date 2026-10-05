// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/AuthService.java
package com.gesolutions.erp.modules.auth.service;

import com.gesolutions.erp.modules.auth.dto.LoginRequest;
import com.gesolutions.erp.modules.auth.dto.LoginResponse;
import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * GOLDEN SEED ERP - SIGN-IN (fix181)
 *
 * The username is trimmed and matched without caring about capital letters (phone keyboards turn "mary" into "Mary").
 * The key is checked FIRST; only a person who typed the right key is told that the account is suspended or that the
 * temporary key has expired (a stranger with a wrong key learns nothing). Every failure is a BusinessException (HTTP
 * 400), never 401: the page treats 401 as "signed out" and would reload the sign-in screen on every wrong key.
 */
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserDetailsService userDetailsService;
    private final UserRepository userRepository;
    private final JwtService jwtService;
    private final AuditService auditService;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public LoginResponse authenticate(LoginRequest request, String ip) {
        String typed = request.getUsername() == null ? "" : request.getUsername().trim();
        User user = userRepository.findByUsernameIgnoreCase(typed).orElse(null);
        if (user == null || request.getPassword() == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BusinessException("IDENTIFICATION_FAILED: Wrong username or key.");
        }
        if (!user.isActive()) {
            throw new BusinessException("ACCOUNT_SUSPENDED: This account is suspended. Ask the Director.");
        }
        if (user.isMustChangePassword() && user.getTempKeyExpiresAt() != null && user.getTempKeyExpiresAt().isBefore(LocalDateTime.now())) {
            throw new BusinessException("KEY_EXPIRED: This temporary key has expired. Ask the Director for a new key.");
        }

        // a new session signs out every other device of this account (one account, one device at a time)
        user.bumpSessionVersion();
        userRepository.save(user);

        LoginResponse response = buildResponse(user);
        auditService.logActionAs(user.getUsername(), "LOGIN_SUCCESS",
                "Operator session established: " + user.getUsername() + " from IP " + ip);
        return response;
    }

    /** A token plus the user block the page keeps (also used after the own key change). */
    public LoginResponse buildResponse(User user) {
        final UserDetails userDetails = userDetailsService.loadUserByUsername(user.getUsername());
        java.util.Map<String, Object> extraClaims = new java.util.HashMap<>();
        extraClaims.put("sv", user.getSessionVersion());
        String token = jwtService.generateToken(extraClaims, userDetails);
        return LoginResponse.builder()
                .token(token)
                .user(LoginResponse.UserData.builder()
                        .id(user.getId())
                        .username(user.getUsername())
                        .role(user.getRole())
                        .isRoot(user.isRoot())
                        .mustChangePassword(user.isMustChangePassword())
                        .build())
                .build();
    }

    /** fix181: SIGN OUT on the server, so a copied token stops working too. */
    @Transactional
    public void logout(String username) {
        userRepository.findByUsername(username).ifPresent(u -> {
            u.bumpSessionVersion();
            userRepository.save(u);
        });
    }
}
