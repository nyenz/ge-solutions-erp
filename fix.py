# PATH: fix.py
import os

path = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"

if not os.path.isfile(path):
    print(f"MISSING: {path} not found")
else:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # VITAL: Normalize Windows CRLF (\r\n) to LF (\n) to guarantee 100% matching
    content = content.replace("\r\n", "\n")

    old_seed = """    @Transactional
    public void seedRootUser() {
        try {
            String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
            String password = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";

            java.util.Optional<User> existing = userRepository.findByUsername("admin_root");
            if (existing.isEmpty()) {
                User root = User.builder()
                        .id(UUID.randomUUID())
                        .username("admin_root")
                        .email(email)
                        .password(passwordEncoder.encode(password))
                        .role(Role.ROLE_ADMIN)
                        .isRoot(true)
                        .isActive(true)
                        .mustChangePassword(true)
                        .build();
                userRepository.save(root);
                System.out.println(">>> [REGISTRY] Master Founder Account Seeded with fallback default credentials.");
            } else {
                User root = existing.get();
                root.setPassword(passwordEncoder.encode(password));
                root.setMustChangePassword(true);
                root.setActive(true);
                userRepository.save(root);
                System.out.println(">>> [REGISTRY] Master Account found. Forced password reset to default for testing.");
            }
        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }"""

    new_seed = """    @Transactional
    public void seedRootUser() {
        try {
            String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : "test@gesolutions.com";
            String password = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : "TestPassword123";

            System.out.println(">>> [REGISTRY] Preparing to seed/reset 'admin_root' with password: '" + password + "'");

            java.util.Optional<User> existing = userRepository.findByUsername("admin_root");
            if (existing.isEmpty()) {
                User root = User.builder()
                        .id(UUID.randomUUID())
                        .username("admin_root")
                        .email(email)
                        .password(passwordEncoder.encode(password))
                        .role(Role.ROLE_ADMIN)
                        .isRoot(true)
                        .isActive(true)
                        .mustChangePassword(true)
                        .build();
                userRepository.saveAndFlush(root);
                System.out.println(">>> [REGISTRY] Master Founder Account Seeded with fallback default credentials.");
            } else {
                User root = existing.get();
                root.setPassword(passwordEncoder.encode(password));
                root.setMustChangePassword(true);
                root.setActive(true);
                userRepository.saveAndFlush(root);
                System.out.println(">>> [REGISTRY] Master Account found. Forced password reset to default for testing.");
            }
        } catch (Exception e) {
            System.err.println(">>> [REGISTRY] CRITICAL SEED/RESET FAULT:");
            e.printStackTrace();
        }
    }"""

    if old_seed in content:
        content = content.replace(old_seed, new_seed)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: Patched {path} successfully with forced flush logic.")
    else:
        print(f"SKIP: Target block already patched or missing in {path}")