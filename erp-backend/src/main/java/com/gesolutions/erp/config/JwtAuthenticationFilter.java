// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/JwtAuthenticationFilter.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.repository.UserRepository;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Objects;

/**
 * GE SOLUTIONS - JWT BOUNCER
 * Extracts the digital signature from the header to verify the operator's identity.
 * Physically removes 'Null type safety' warnings via strict validation.
 */
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;
    private final UserRepository userRepository;

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain
    ) throws ServletException, IOException {
        
        final String authHeader = request.getHeader("Authorization");
        final String jwt;
        final String username;

        // 1. Validate Header Integrity
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        try {
            jwt = authHeader.substring(7);
            username = jwtService.extractUsername(jwt);

            // 2. Validate Security Context and Perform Handshake
            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
                
                Integer tokenSv = jwtService.extractClaim(jwt, claims -> {
                    Object sv = claims.get("sv");
                    return sv != null ? ((Number) sv).intValue() : null;
                });
                com.gesolutions.erp.modules.auth.model.User account = userRepository.findByUsername(userDetails.getUsername()).orElse(null);
                boolean sessionValid = account != null && account.getSessionVersion() != null
                        && tokenSv != null && tokenSv.equals(account.getSessionVersion());

                if (jwtService.isTokenValid(jwt, Objects.requireNonNull(userDetails))) {
                    if (!sessionValid) {
                        // another sign-in, a sign-out, a key change, a suspension or a rank change ended this session
                        writeError(response, 401, "SESSION_CONFLICT", "This session was ended. Sign in again.");
                        return;
                    }
                    // fix181: a suspended account stops at once, not when its token runs out
                    if (!userDetails.isEnabled()) {
                        writeError(response, 401, "ACCOUNT_SUSPENDED", "This account is suspended.");
                        return;
                    }
                    // fix181: a temporary key only opens the key change; everything else waits until it is changed
                    if (account.isMustChangePassword() && !lockedAllowed(request.getRequestURI())) {
                        writeError(response, 403, "PASSWORD_CHANGE_REQUIRED", "Change your temporary key first (Settings > Security).");
                        return;
                    }

                    UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                            userDetails,
                            null,
                            userDetails.getAuthorities()
                    );
                    authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

                    SecurityContextHolder.getContext().setAuthentication(authToken);
                }
            }
        } catch (Exception e) {
            // VITAL FIX: Catch ExpiredJwtException and force a 401 instead of crashing to a 500/403
            writeError(response, 401, "INVALID_TOKEN", "Your sign-in expired. Sign in again.");
            return;
        }
        filterChain.doFilter(request, response);
    }

    /** Paths a person with a temporary key may still call. */
    static boolean lockedAllowed(String uri) {
        return uri != null && (uri.startsWith("/api/v1/auth/") || uri.equals("/api/v1/profile/change-password")
                || uri.equals("/api/v1/profile/me"));
    }

    private static void writeError(HttpServletResponse response, int status, String code, String message) throws IOException {
        response.setStatus(status);
        response.setContentType("application/json");
        response.getWriter().write("{\"error\": \"" + code + "\", \"message\": \"" + message + "\"}");
    }
}