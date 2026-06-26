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

    # ── PATCH 1 ──────────────────────────────────────────────────────────────
    # Replace userRepository.save(root) with userRepository.saveAndFlush(root)
    # in BOTH branches of seedRootUser() so Hibernate is forced to flush the
    # dirty state to the database immediately, regardless of AOP proxy state.
    # This fixes the "password never committed" bug when CommandLineRunner
    # bypasses the Spring @Transactional proxy via local self-invocation.
    # ─────────────────────────────────────────────────────────────────────────

    old_seed = (
        "    @Transactional\n"
        "    public void seedRootUser() {\n"
        "        try {\n"
        "            String email = (adminEmail != null && !adminEmail.isBlank()) ? adminEmail : \"test@gesolutions.com\";\n"
        "            String password = (adminDefaultPassword != null && !adminDefaultPassword.isBlank()) ? adminDefaultPassword : \"TestPassword123\";\n"
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
        "                userRepository.save(root);\n"
        "                System.out.println(\">>> [REGISTRY] Master Founder Account Seeded with fallback default credentials.\");\n"
        "            } else {\n"
        "                User root = existing.get();\n"
        "                root.setPassword(passwordEncoder.encode(password));\n"
        "                root.setMustChangePassword(true);\n"
        "                root.setActive(true);\n"
        "                userRepository.save(root);\n"
        "                System.out.println(\">>> [REGISTRY] Master Account found. Forced password reset to default for testing.\");\n"
        "            }\n"
        "        } catch (Exception e) {\n"
        "            System.err.println(\">>> [REGISTRY] CRITICAL SEED/RESET FAULT:\");\n"
        "            e.printStackTrace();\n"
        "        }\n"
        "    }"
    )

    new_seed = (
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

    if old_seed in content:
        content = content.replace(old_seed, new_seed)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: Patched {path} -- replaced save() with saveAndFlush() in both branches.")
    elif new_seed in content:
        print(f"SKIP: {path} already contains saveAndFlush -- patch already applied, no action needed.")
    else:
        # Fallback: try a simpler targeted replacement in case whitespace varies
        changed = content
        changed = changed.replace(
            "                userRepository.save(root);\n"
            "                System.out.println(\">>> [REGISTRY] Master Founder Account Seeded",
            "                userRepository.saveAndFlush(root);\n"
            "                System.out.println(\">>> [REGISTRY] Master Founder Account Seeded"
        )
        changed = changed.replace(
            "                userRepository.save(root);\n"
            "                System.out.println(\">>> [REGISTRY] Master Account found",
            "                userRepository.saveAndFlush(root);\n"
            "                System.out.println(\">>> [REGISTRY] Master Account found"
        )
        if changed != content:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(changed)
            print(f"OK: Patched {path} via fallback targeted replacement.")
        else:
            print(f"SKIP: Target block not found in {path} -- file may already be fully patched or has unexpected formatting.")
            print("      Verify manually that seedRootUser() uses saveAndFlush() in both branches.")