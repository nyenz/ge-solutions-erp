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

        jwt = authHeader.substring(7);
        username = jwtService.extractUsername(jwt);

        // 2. Validate Security Context and Perform Handshake
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
            
            // PROVING non-nullity to the compiler to clear warnings
            // Validate session version — rejects tokens from older sessions
            Integer tokenSv = jwtService.extractClaim(jwt, claims -> {
                Object sv = claims.get("sv");
                return sv != null ? ((Number) sv).intValue() : null;
            });
            boolean sessionValid = userRepository.findByUsername(userDetails.getUsername())
                .map(u -> {
                    Integer dbSv = u.getSessionVersion();
                    if (dbSv == null) return false; // not yet set, reject until login
                    return tokenSv != null && tokenSv.equals(dbSv);
                })
                .orElse(false);

            if (jwtService.isTokenValid(jwt, Objects.requireNonNull(userDetails)) && sessionValid) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.getAuthorities()
                );
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                
                // AUTHORIZE OPERATOR SESSION
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }
        filterChain.doFilter(request, response);
    }
}