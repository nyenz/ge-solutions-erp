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
 * NYENZ ERP - MASTER SECURITY CONFIG (V2.0 - FINAL CLOUD GATE)
 * 
 * Physically prioritizes CORS handshaking to prevent 403 Preflight errors.
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
                // 1. ACTIVATE CORS FIRST (This kills the Red Error)
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                
                // 2. DISABLE CSRF for Stateless API
                .csrf(AbstractHttpConfigurer::disable)
                
                // 3. AUTHORIZE PUBLIC & PRIVATE ROUTES
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/api/v1/auth/**").permitAll()
                        .requestMatchers("/api/v1/vault/**").permitAll()
                        // Ensure OPTIONS requests (CORS Preflight) are always allowed
                        .requestMatchers(org.springframework.http.HttpMethod.OPTIONS, "/**").permitAll()
                        .anyRequest().authenticated()
                )
                
                // 4. STATELSS SESSIONS
                .sessionManagement(session -> session
                        .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
                )
                
                .authenticationProvider(authenticationProvider)
                .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        
        // ── THE MASTER TRUST LIST ──
        config.setAllowedOrigins(List.of(
            "http://localhost",
            "http://localhost:5173",
            "https://golden-seed.onrender.com" // OLD
        ));
        
        // Allow all industrial standard verbs
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        
        // VITAL: Explicitly allow the headers your app uses
        config.setAllowedHeaders(Arrays.asList(
            "Authorization", 
            "Content-Type", 
            "Cache-Control", 
            "X-Requested-With"
        ));
        
        config.setAllowCredentials(true);
        config.setMaxAge(3600L); // Keep the handshake alive for 1 hour

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}