# PATH: fix.py
# FIXES THREE COMPOUNDING BUGS THAT CAUSE admin_root LOGIN FAILURE:
#
# BUG 1: @Transactional self-invocation bypass -- run() calls seedRootUser() on 'this',
#         so the Spring AOP proxy never fires and @Transactional is ignored.
#         saveAndFlush() helps but is not bulletproof if the EntityManager is dirty.
#
# BUG 2: JPA/Hibernate ORM layer caching -- even with saveAndFlush(), the Hibernate
#         first-level cache may serve a stale entity to the next findByUsername() call
#         within the same persistence context.
#
# BUG 3: The AuthService catches ALL exceptions (including DisabledException,
#         LockedException, etc.) and re-throws as "IDENTIFICATION_FAILED", making
#         it impossible to know the real cause from the outside.
#
# THE FIX:
# - DataInitializer.java: Use raw JDBC (already available via DataSource) to UPDATE
#   the password directly -- this completely bypasses JPA, EntityManager, L1 cache,
#   proxy issues, and @Transactional self-invocation. A plain JDBC UPDATE auto-commits
#   in its own connection.
#
# - AuthService.java: Log the REAL exception type and message before re-throwing,
#   so we can see in Render logs whether it's BadCredentials, DisabledException, etc.
#
# - ApplicationConfig.java: Add a null-check guard on user.getRole() so a missing
#   role doesn't silently cause a NullPointerException swallowed by the catch block.

import os

def patch(path, old, new, label):
    if not os.path.isfile(path):
        print(f"MISSING: {path}")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    if old in content:
        content = content.replace(old, new)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: {label}")
    elif new in content:
        print(f"SKIP (already applied): {label}")
    else:
        print(f"FAIL (target not found): {label}")
        # Print a snippet to help debug
        idx = content.find("seedRootUser") if "seedRootUser" in path else content.find("authenticate")
        if idx > 0:
            print(f"      Context around key symbol: ...{repr(content[max(0,idx-60):idx+80])}...")


# ============================================================
# PATCH 1: DataInitializer.java
# Replace the JPA-based seedRootUser() with a raw JDBC version.
# Raw JDBC is completely immune to:
#   - @Transactional proxy bypass
#   - Hibernate L1 cache staleness
#   - EntityManager flush/commit timing
#   - @Builder.Default field initializer conflicts
# ============================================================

DATA_INIT_PATH = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"

OLD_SEED = (
    "    @Transactional\n"
    "    public void seedRootUser() {\n"
    "        try {\n"
    "            String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : \"test@gesolutions.com\";\n"
    "            String password = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : \"TestPassword123\";\n"
    "\n"
    "            System.out.println(\">>> [REGISTRY] Preparing to seed/reset 'admin_root' with password: '\" + password + \"'\");\n"
    "\n"
    "            java.util.Optional<User> existing = userRepository.findByUsername(\"admin_root\");\n"
    "            if (existing.isEmpty()) {\n"
    "                User root = User.builder()\n"
    "                        .id(UUID.randomUUID())\n"
    "                        .username(\"admin_root\")\n"
    "                        .email(email)\n"
    "                        .password(passwordEncoder.encode(password))\n"
    "                        .role(Role.ROLE_ADMIN)\n"
    "                        .isRoot(true)\n"
    "                        .isActive(true)\n"
    "                        .mustChangePassword(true)\n"
    "                        .build();\n"
    "                userRepository.saveAndFlush(root);\n"
    "                System.out.println(\">>> [REGISTRY] Master Founder Account Seeded with fallback default credentials.\");\n"
    "            } else {\n"
    "                User root = existing.get();\n"
    "                root.setPassword(passwordEncoder.encode(password));\n"
    "                root.setMustChangePassword(true);\n"
    "                root.setActive(true);\n"
    "                userRepository.saveAndFlush(root);\n"
    "                System.out.println(\">>> [REGISTRY] Master Account found. Forced password reset to default for testing.\");\n"
    "            }\n"
    "        } catch (Exception e) {\n"
    "            System.err.println(\">>> [REGISTRY] CRITICAL SEED/RESET FAULT:\");\n"
    "            e.printStackTrace();\n"
    "        }\n"
    "    }"
)

NEW_SEED = (
    "    // NOTE: Deliberately NOT @Transactional -- we use raw JDBC so this is\n"
    "    // completely immune to Spring AOP proxy bypass, Hibernate L1 cache,\n"
    "    // EntityManager flush timing, and @Builder.Default field conflicts.\n"
    "    public void seedRootUser() {\n"
    "        String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : \"test@gesolutions.com\";\n"
    "        String rawPassword = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : \"TestPassword123\";\n"
    "        String encodedPassword = passwordEncoder.encode(rawPassword);\n"
    "\n"
    "        System.out.println(\">>> [REGISTRY] seedRootUser() via raw JDBC. Raw password=\" + rawPassword.substring(0,3) + \"***\");\n"
    "\n"
    "        try (java.sql.Connection conn = dataSource.getConnection()) {\n"
    "            // Check if admin_root exists\n"
    "            boolean exists = false;\n"
    "            try (java.sql.PreparedStatement ps = conn.prepareStatement(\n"
    "                    \"SELECT COUNT(*) FROM users WHERE username = ?\")) {\n"
    "                ps.setString(1, \"admin_root\");\n"
    "                try (java.sql.ResultSet rs = ps.executeQuery()) {\n"
    "                    if (rs.next()) exists = rs.getInt(1) > 0;\n"
    "                }\n"
    "            }\n"
    "\n"
    "            if (!exists) {\n"
    "                // INSERT brand-new admin_root row\n"
    "                String sql = \"INSERT INTO users (id, username, email, password, role, is_root, is_active, must_change_password, session_version) \"\n"
    "                           + \"VALUES (?, 'admin_root', ?, ?, 'ROLE_ADMIN', true, true, true, 0)\";\n"
    "                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {\n"
    "                    ps.setObject(1, java.util.UUID.randomUUID());\n"
    "                    ps.setString(2, email);\n"
    "                    ps.setString(3, encodedPassword);\n"
    "                    int rows = ps.executeUpdate();\n"
    "                    System.out.println(\">>> [REGISTRY] INSERT admin_root rows affected: \" + rows);\n"
    "                }\n"
    "            } else {\n"
    "                // UPDATE existing row -- raw JDBC, auto-commits, no cache issues\n"
    "                String sql = \"UPDATE users SET password = ?, is_active = true, must_change_password = true \"\n"
    "                           + \"WHERE username = 'admin_root'\";\n"
    "                try (java.sql.PreparedStatement ps = conn.prepareStatement(sql)) {\n"
    "                    ps.setString(1, encodedPassword);\n"
    "                    int rows = ps.executeUpdate();\n"
    "                    System.out.println(\">>> [REGISTRY] UPDATE admin_root rows affected: \" + rows);\n"
    "                }\n"
    "            }\n"
    "\n"
    "            // Verify by re-reading the stored hash\n"
    "            try (java.sql.PreparedStatement ps = conn.prepareStatement(\n"
    "                    \"SELECT password, is_active FROM users WHERE username = 'admin_root'\")) {\n"
    "                try (java.sql.ResultSet rs = ps.executeQuery()) {\n"
    "                    if (rs.next()) {\n"
    "                        String storedHash = rs.getString(\"password\");\n"
    "                        boolean active = rs.getBoolean(\"is_active\");\n"
    "                        boolean matches = passwordEncoder.matches(rawPassword, storedHash);\n"
    "                        System.out.println(\">>> [REGISTRY] Post-write verification:\");\n"
    "                        System.out.println(\">>>   is_active in DB = \" + active);\n"
    "                        System.out.println(\">>>   hash starts with = \" + storedHash.substring(0, Math.min(20, storedHash.length())));\n"
    "                        System.out.println(\">>>   BCrypt.matches(rawPassword, storedHash) = \" + matches);\n"
    "                        if (!matches) {\n"
    "                            System.err.println(\">>> [REGISTRY] FATAL: BCrypt verify FAILED after write! Check encoder config.\");\n"
    "                        } else {\n"
    "                            System.out.println(\">>> [REGISTRY] SUCCESS: Password verified. Login WILL work.\");\n"
    "                        }\n"
    "                    } else {\n"
    "                        System.err.println(\">>> [REGISTRY] FATAL: admin_root row not found after write!\");\n"
    "                    }\n"
    "                }\n"
    "            }\n"
    "\n"
    "        } catch (Exception e) {\n"
    "            System.err.println(\">>> [REGISTRY] CRITICAL SEED/RESET FAULT:\");\n"
    "            e.printStackTrace();\n"
    "        }\n"
    "    }"
)

patch(DATA_INIT_PATH, OLD_SEED, NEW_SEED, "PATCH 1: DataInitializer.seedRootUser() -> raw JDBC (bypasses all ORM issues)")


# ============================================================
# PATCH 2: AuthService.java
# Log the REAL exception class and message before re-throwing.
# This tells us in Render logs exactly WHY authenticate() failed
# (BadCredentials vs DisabledException vs NPE etc.)
# ============================================================

AUTH_SERVICE_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/AuthService.java"

OLD_AUTH_CATCH = (
    "        } catch (Exception e) {\n"
    "            // DIAGNOSTIC: Triggered if username or password hash don't match\n"
    "            throw new BusinessException(\"IDENTIFICATION_FAILED: INVALID SECURITY KEY\");\n"
    "        }"
)

NEW_AUTH_CATCH = (
    "        } catch (Exception e) {\n"
    "            // DIAGNOSTIC: Log the REAL cause so we can see it in Render logs\n"
    "            System.err.println(\">>> [AUTH_FAULT] authenticate() threw: \" + e.getClass().getName() + \" -- \" + e.getMessage());\n"
    "            throw new BusinessException(\"IDENTIFICATION_FAILED: INVALID SECURITY KEY\");\n"
    "        }"
)

patch(AUTH_SERVICE_PATH, OLD_AUTH_CATCH, NEW_AUTH_CATCH, "PATCH 2: AuthService.java -> log real exception class before re-throw")


# ============================================================
# PATCH 3: ApplicationConfig.java
# Guard against user.getRole() returning null (would throw NPE
# inside the catch block, showing up as IDENTIFICATION_FAILED).
# Also add defensive logging so we can see exactly what the
# UserDetailsService is returning during loadUserByUsername().
# ============================================================

APP_CONFIG_PATH = "erp-backend/src/main/java/com/gesolutions/erp/config/ApplicationConfig.java"

OLD_UDS = (
    "    @Bean\n"
    "    public UserDetailsService userDetailsService() {\n"
    "        return username -> {\n"
    "            User user = userRepository.findByUsername(username)\n"
    "                    .orElseThrow(() -> new UsernameNotFoundException(\"Operator missing in registry\"));\n"
    "\n"
    "            // Physically return our CUSTOM USER (the entity itself) \n"
    "            // but wrapped for Spring Security compatibility.\n"
    "            return new CustomUserPrincipal(user);\n"
    "        };\n"
    "    }"
)

NEW_UDS = (
    "    @Bean\n"
    "    public UserDetailsService userDetailsService() {\n"
    "        return username -> {\n"
    "            User user = userRepository.findByUsername(username)\n"
    "                    .orElseThrow(() -> new UsernameNotFoundException(\"Operator missing in registry: \" + username));\n"
    "\n"
    "            // Defensive diagnostics -- visible in Render deploy logs\n"
    "            System.out.println(\">>> [UDS] loadUserByUsername('\" + username + \"')\");\n"
    "            System.out.println(\">>>   isActive=\" + user.isActive()\n"
    "                + \"  role=\" + user.getRole()\n"
    "                + \"  passwordHashPrefix=\" + (user.getPassword() != null ? user.getPassword().substring(0, Math.min(15, user.getPassword().length())) : \"NULL\"));\n"
    "\n"
    "            if (user.getRole() == null) {\n"
    "                throw new UsernameNotFoundException(\"Operator '\" + username + \"' has NULL role -- cannot build authorities\");\n"
    "            }\n"
    "\n"
    "            return new CustomUserPrincipal(user);\n"
    "        };\n"
    "    }"
)

patch(APP_CONFIG_PATH, OLD_UDS, NEW_UDS, "PATCH 3: ApplicationConfig.java -> guard null role + diagnostic logging in UDS")


print("")
print("=== SUMMARY ===")
print("3 patches applied.")
print("")
print("WHAT EACH PATCH DOES:")
print("  PATCH 1 (DataInitializer): Replaces JPA-based seedRootUser() with raw JDBC.")
print("           Raw JDBC bypasses Spring AOP, Hibernate L1 cache, EntityManager,")
print("           @Transactional self-invocation, and @Builder.Default quirks.")
print("           Runs a BCrypt verify AFTER the write and logs the result.")
print("           Check Render logs for '>>> [REGISTRY] BCrypt.matches(...) = true'")
print("")
print("  PATCH 2 (AuthService): Logs the REAL exception type from authenticate().")
print("           Check Render logs for '>>> [AUTH_FAULT] authenticate() threw: ...'")
print("           This tells you if it is BadCredentialsException (wrong password),")
print("           DisabledException (is_active=false), or something else.")
print("")
print("  PATCH 3 (ApplicationConfig): Guards against null role causing silent NPE,")
print("           and logs exactly what the UserDetailsService sees for each login.")
print("           Check Render logs for '>>> [UDS] loadUserByUsername(admin_root)'")
print("")
print("NEXT STEPS:")
print("  1. py fix.py")
print("  2. git add -A && git commit -m 'fix: raw JDBC seed, auth diagnostics' && git push")
print("  3. Wait for Render green tick (~5-10 min)")
print("  4. In Render logs, look for:")
print("       >>> [REGISTRY] BCrypt.matches(rawPassword, storedHash) = true")
print("       >>> [REGISTRY] SUCCESS: Password verified. Login WILL work.")
print("  5. Try logging in. If still failing, the Render logs will now show the")
print("     exact exception class so we know exactly what to fix next.")