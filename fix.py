#!/usr/bin/env python3
"""
fix_robust.py -- Applies the definitive fixes using minimal, guaranteed anchors.
Avoids "anchor not found" errors by using regex for repetitive blocks.
"""
import os
import re
import subprocess

def process_file(path, modifications, regex_mods=None):
    if not os.path.exists(path):
        print(f"❌ MISSING FILE: {path}")
        return False
        
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    original_content = content
    all_ok = True
    
    # String replacements
    for desc, old, new in modifications:
        if new in content:
            print(f"✅ {desc} (already applied)")
            continue
        if old not in content:
            print(f"❌ {desc} (anchor not found)")
            all_ok = False
            continue
            
        content = content.replace(old, new, 1)
        print(f"🔧 {desc}")
        
    # Regex replacements
    if regex_mods:
        for desc, pattern, repl, check_str in regex_mods:
            if check_str in content:
                print(f"✅ {desc} (already applied)")
                continue
            new_content, count = re.subn(pattern, repl, content, flags=re.DOTALL)
            if count == 0:
                print(f"❌ {desc} (regex pattern not found)")
                all_ok = False
            else:
                content = new_content
                print(f"🔧 {desc} ({count} matches)")
        
    if content != original_content:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            
    return all_ok

# --- DataInitializer.java ---
di_path = "erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java"
di_mods = [
    (
        "Add phone constraint sweep & title_id nullable migration",
        '            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",\n',
        '            "ALTER TABLE clients DROP CONSTRAINT IF EXISTS clients_phone_number_key",\n'
        '            // FIX: Sweep for any Hibernate-generated unique constraint on phone_number\n'
        '            "DO $$ DECLARE cname text; BEGIN " +\n'
        '                "SELECT tc.constraint_name INTO cname FROM information_schema.table_constraints tc " +\n'
        '                "JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name " +\n'
        '                "WHERE tc.table_name = \'clients\' AND tc.constraint_type = \'UNIQUE\' AND ccu.column_name = \'phone_number\' LIMIT 1; " +\n'
        '                "IF cname IS NOT NULL THEN EXECUTE \'ALTER TABLE clients DROP CONSTRAINT \' || quote_ident(cname); END IF; " +\n'
        '                "END $$",\n'
        '            // FIX: Ensure title_id is nullable for Folder-type projects\n'
        '            "ALTER TABLE land_projects ALTER COLUMN title_id DROP NOT NULL",\n'
    ),
    (
        "Add verifyTitleIdNullable() call and method",
        '        } catch (Exception e) {\n'
        '            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());\n'
        '        }\n'
        '    }\n',
        '        } catch (Exception e) {\n'
        '            System.err.println(">>> [DB_SCHEMA] Migration warning: " + e.getMessage());\n'
        '        }\n'
        '\n'
        '        // FIX: verify title_id is actually nullable after migrations\n'
        '        verifyTitleIdNullable();\n'
        '    }\n'
        '\n'
        '    private void verifyTitleIdNullable() {\n'
        '        try (Connection conn = dataSource.getConnection();\n'
        '             Statement stmt = conn.createStatement()) {\n'
        '            boolean nullable = false;\n'
        '            try (java.sql.ResultSet rs = stmt.executeQuery(\n'
        '                    "SELECT is_nullable FROM information_schema.columns " +\n'
        '                    "WHERE table_name = \'land_projects\' AND column_name = \'title_id\'")) {\n'
        '                if (rs.next()) nullable = "YES".equalsIgnoreCase(rs.getString(1));\n'
        '            }\n'
        '            if (!nullable) {\n'
        '                System.out.println(">>> [DB_SCHEMA] title_id is still NOT NULL -- forcing fix now.");\n'
        '                stmt.execute("ALTER TABLE land_projects ALTER COLUMN title_id DROP NOT NULL");\n'
        '                try (java.sql.ResultSet rs2 = stmt.executeQuery(\n'
        '                        "SELECT is_nullable FROM information_schema.columns " +\n'
        '                        "WHERE table_name = \'land_projects\' AND column_name = \'title_id\'")) {\n'
        '                    nullable = rs2.next() && "YES".equalsIgnoreCase(rs2.getString(1));\n'
        '                }\n'
        '            }\n'
        '            if (nullable) {\n'
        '                System.out.println(">>> [DB_SCHEMA] VERIFIED: land_projects.title_id is nullable. Folder projects can save.");\n'
        '            } else {\n'
        '                System.err.println(">>> [DB_SCHEMA] CRITICAL: land_projects.title_id is STILL NOT NULL after force-fix.");\n'
        '            }\n'
        '        } catch (Exception e) {\n'
        '            System.err.println(">>> [DB_SCHEMA] CRITICAL: could not verify title_id nullability: " + e.getMessage());\n'
        '        }\n'
        '    }\n'
    ),
    (
        "Update seed completion log",
        '            System.out.println(">>> [SAMPLE] Seeded 7 sample projects (district = SAMPLE DATA).");\n',
        '            long saved = ids.stream().filter(java.util.Objects::nonNull).count();\n'
        '            System.out.println(">>> [SAMPLE] Seeded " + saved + " of 7 sample projects (district = SAMPLE DATA).");\n'
    ),
    (
        "Add trySeed method definition",
        '        } catch (Exception e) {\n'
        '            System.err.println(">>> [SAMPLE] seed failed (non-fatal): " + e.getMessage());\n'
        '        }\n'
        '    }\n',
        '        } catch (Exception e) {\n'
        '            System.err.println(">>> [SAMPLE] seed failed (non-fatal): " + e.getMessage());\n'
        '        }\n'
        '    }\n'
        '\n'
        '    private java.util.UUID trySeed(String label, java.util.concurrent.Callable<java.util.UUID> supplier) {\n'
        '        try {\n'
        '            return supplier.call();\n'
        '        } catch (Exception e) {\n'
        '            System.err.println(">>> [SAMPLE] " + label + " failed (skipped): " + e.getMessage());\n'
        '            return null;\n'
        '        }\n'
        '    }\n'
    )
]

di_regex = [
    (
        "Wrap seedOne calls in trySeed()",
        r'ids\.add\(seedOne\("SAMPLE-00(\d)",(.*?)idByName\)\);',
        r'ids.add(trySeed("SAMPLE-00\1", () -> seedOne("SAMPLE-00\1",\2idByName)));',
        'trySeed("SAMPLE-001"'
    )
]

# --- LandService.java ---
ls_path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java"
ls_mods = [
    (
        "Add @Transactional to atomicIntake",
        '    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {\n',
        '    @Transactional(rollbackFor = Exception.class)\n'
        '    public LandProject atomicIntake(LandEntryRequest request, MultipartFile[] scans) throws Exception {\n'
    )
]

print("=== Applying robust fixes ===")
ok1 = process_file(di_path, di_mods, di_regex)
ok2 = process_file(ls_path, ls_mods)

if not (ok1 and ok2):
    print("\n❌ One or more fixes failed to apply. Check the output above.")
    exit(1)

print("\n✅ All fixes applied successfully!")
subprocess.run(["git", "add", "-A"], check=False)
subprocess.run(["git", "commit", "-m", "fix: robust application of phone sweep, title_id nullable, transactional intake, and resilient seeding"], check=False)
subprocess.run(["git", "push"], check=False)
print("\nDone. Pushed to remote. Check Render logs for 'VERIFIED: land_projects.title_id is nullable'.")