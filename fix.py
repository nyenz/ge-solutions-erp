import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK  {label}")
    else:
        print(f"MISSING  {label}")

# PATH: erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java
fp = 'erp-backend/src/main/java/com/gesolutions/erp/config/DataInitializer.java'

old = '''        try {
            entityManager.createNativeQuery(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL"
            ).executeUpdate();
            System.out.println(">>> [DB_SCHEMA] session_version column verified.");
        } catch (Exception e) {
            System.out.println(">>> [DB_SCHEMA] session_version already exists or skipped: " + e.getMessage());
        }'''

new = '''        try {
            entityManager.createNativeQuery(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 0 NOT NULL"
            ).executeUpdate();
            System.out.println(">>> [DB_SCHEMA] session_version column verified.");
        } catch (Exception e) {
            System.out.println(">>> [DB_SCHEMA] session_version already exists or skipped: " + e.getMessage());
        }

        // Fix missing columns in land_projects that Hibernate DDL auto=update missed
        String[] landProjectMigrations = {
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_paused BOOLEAN NOT NULL DEFAULT FALSE",
            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS storage_fee_override NUMERIC(15,2)",
        };
        for (String sql : landProjectMigrations) {
            try {
                entityManager.createNativeQuery(sql).executeUpdate();
                System.out.println(">>> [DB_SCHEMA] OK: " + sql.substring(0, 60));
            } catch (Exception e) {
                System.out.println(">>> [DB_SCHEMA] Skipped: " + e.getMessage());
            }
        }'''

patch(fp, old, new, "DataInitializer: add missing land_projects columns")

print("\nDone.")
print("git add -A && git commit -m 'fix: add missing storage_paused and storage_fee_override columns' && git push")