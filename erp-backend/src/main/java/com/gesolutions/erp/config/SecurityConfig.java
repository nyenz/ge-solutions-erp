// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/SecurityConfig.java
package com.gesolutions.erp.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

/**
 * NYENZ ERP - INDUSTRIAL SECURITY HUB (V1.2 - PRODUCTION READY)
 * 
 * Physically defines the digital perimeter. 
 * Features: Multi-origin CORS support, Stateless JWT sessions, and Method Gating.
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity // CRITICAL: Enables @PreAuthorize role-gating on methods
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtAuthFilter;
    private final AuthenticationProvider authenticationProvider;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // 1. ATTACH MULTI-ENVIRONMENT CORS
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                
                // 2. DISABLE CSRF (Stateless JWTs do not require session cookies)
                .csrf(AbstractHttpConfigurer::disable)
                
                // 3. DEFINE ACCESS PERIMETERS
                .authorizeHttpRequests(auth -> auth
                        // Public Gateway: Login and Recovery
                        .requestMatchers("/api/v1/auth/**").permitAll()
                        
                        // The Digital Vault: Allows image/PDF streaming
                        .requestMatchers("/api/v1/vault/**").permitAll()
                        
                        // Secured Perimeter: Requires valid JWT
                        .anyRequest().authenticated()
                )
                
                // 4. SESSION ARCHITECTURE
                .sessionManagement(session -> session
                        .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                )
                
                // 5. ATTACH HARDWARE PROVIDERS
                .authenticationProvider(authenticationProvider)
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * CORS MASTER PROTOCOL
     * Connects multiple potential frontends (React Local, Mobile PWA, Production Domain)
     * to the Spring Boot Backend.
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        
        // --- ALLOWED ORIGINS (THE ACCESS LIST) ---
        configuration.setAllowedOrigins(List.of(
            "http://localhost:5173",    // Local Development
            "http://127.0.0.1:5173",   // Local IP Dev
            "http://localhost",         // Production Docker Local
            "https://ge-solutions.com" // PLACEHOLDER: Replace with your real domain
        ));
        
        // Allow all industrial HTTP verbs
        configuration.setAllowedMethods(Arrays.asList(
            "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
        ));
        
        // Define allowed hardware headers
        configuration.setAllowedHeaders(Arrays.asList(
            "Authorization", 
            "Content-Type", 
            "Cache-Control",
            "X-Requested-With"
        ));
        
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L); // Cache CORS pre-flight for 1 hour for performance

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}