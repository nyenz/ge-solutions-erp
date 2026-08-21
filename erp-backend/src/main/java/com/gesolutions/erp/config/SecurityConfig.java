// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/SecurityConfig.java
package com.gesolutions.erp.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

import java.util.Arrays;
import java.util.List;

/**
 * GOLDEN SEED ERP - MASTER SECURITY CONFIG (V3.0 - CLOUD STABLE)
 *
 * The CORS filter runs at the HIGHEST possible priority, before any
 * JWT checking. This means the browser's "preflight" OPTIONS request
 * (which has no token) gets a green light immediately.
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtAuthFilter;
    private final AuthenticationProvider authenticationProvider;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .authorizeHttpRequests(auth -> auth
                        // The browser sends an OPTIONS "preflight" before every real request.
                        // We must allow it without a token, or the login itself never happens.
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .requestMatchers("/api/v1/auth/**").permitAll()
                        .requestMatchers("/api/v1/vault/**").permitAll()
                        .anyRequest().authenticated()
                )
                .sessionManagement(session -> session
                        .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                )
                .authenticationProvider(authenticationProvider)
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * THE MASTER CORS GATE
     *
     * This @Bean with @Order(HIGHEST_PRECEDENCE) is a separate filter that
     * runs BEFORE Spring Security even wakes up. It handles the browser
     * handshake directly, so no CORS errors ever reach your login screen.
     */
    @Bean
    @Order(Ordered.HIGHEST_PRECEDENCE)
    public CorsFilter corsFilter() {
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        CorsConfiguration config = new CorsConfiguration();

        config.setAllowCredentials(true);

        // ── THE COMPLETE TRUSTED LIST ──
        // VITAL FIX: 'golden-seed.onrender.com' was MISSING from this list.
        // That single omission caused every browser login to fail with a
        // "Network Error" even though Postman (which ignores CORS) worked fine.
        config.setAllowedOrigins(List.of(
            "http://localhost",
            "http://localhost:5173",
            "http://localhost:80",
            "http://127.0.0.1",
            "https://golden-seed.onrender.com",       // ← YOUR ACTUAL FRONTEND URL
            "https://ge-solutions-ui.onrender.com"    // ← kept as backup
        ));

        config.setAllowedHeaders(Arrays.asList(
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Requested-With",
            "Cache-Control",
            "Origin"
        ));

        config.setAllowedMethods(Arrays.asList(
            "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
        ));

        // Tells the browser it can cache the CORS handshake result for 1 hour.
        // This reduces the number of preflight requests and speeds up your app.
        config.setMaxAge(3600L);

        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }
}