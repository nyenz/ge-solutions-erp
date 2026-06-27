// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/ApplicationConfig.java
package com.gesolutions.erp.config;

import com.gesolutions.erp.modules.auth.model.User;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Collections;

@Configuration
@RequiredArgsConstructor
public class ApplicationConfig {

    private final UserRepository userRepository;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * CUSTOM IDENTITY RETRIEVAL
     * FIXED: Maps the 'isRoot' property into the CustomPrincipal so 
     * @PreAuthorize can read it without crashing (solves 500 Core Error).
     */
    @Bean
    public UserDetailsService userDetailsService() {
        return username -> {
            User user = userRepository.findByUsername(username)
                    .orElseThrow(() -> new UsernameNotFoundException("Operator missing in registry: " + username));

            // Defensive diagnostics -- visible in Render deploy logs
            System.out.println(">>> [UDS] loadUserByUsername('" + username + "')");
            System.out.println(">>>   isActive=" + user.isActive()
                + "  role=" + user.getRole()
                + "  passwordHashPrefix=" + (user.getPassword() != null ? user.getPassword().substring(0, Math.min(15, user.getPassword().length())) : "NULL"));

            if (user.getRole() == null) {
                throw new UsernameNotFoundException("Operator '" + username + "' has NULL role -- cannot build authorities");
            }

            return new CustomUserPrincipal(user);
        };
    }

    @Bean
    public AuthenticationProvider authenticationProvider() {
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider();
        authProvider.setUserDetailsService(userDetailsService());
        authProvider.setPasswordEncoder(passwordEncoder());
        return authProvider;
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    /**
     * INNER CLASS: CUSTOM PRINCIPAL
     * Acts as the bridge between the Database User and the Security Bouncer.
     */
    public static class CustomUserPrincipal extends org.springframework.security.core.userdetails.User {
        private final boolean isRoot;

        public CustomUserPrincipal(User user) {
            super(user.getUsername(), user.getPassword(), user.isActive(), 
                  true, true, true, 
                  Collections.singletonList(new SimpleGrantedAuthority(user.getRole().name())));
            this.isRoot = user.isRoot();
        }

        public boolean isRoot() {
            return isRoot;
        }
    }
}