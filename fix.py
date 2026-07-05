# PATH: fix.py
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
        print(f"FAIL: {label}")

# ROOT CAUSE FOUND:
# Nowhere in application.properties or application-test.properties was
# spring.servlet.multipart.max-file-size or max-request-size ever set.
# Spring Boot's silent DEFAULT is max-file-size=1MB and max-request-size=10MB.
# That means ANY scan over ~1MB (a normal phone photo) was being rejected by
# MaxUploadSizeExceededException -- even though GlobalExceptionHandler's
# error message claimed "File size exceeds 50MB limit." The message was a lie
# because the real ceiling was never configured to match it.
#
# FIX: explicitly set the limits everywhere so the real ceiling matches the
# promised ceiling, and raise the per-file limit to 50MB (best practical
# limit for scanned title documents/photos) with a generous total-request
# ceiling since Intake can upload several scans at once. Also add a
# file-size-threshold so large files spill to disk instead of being held
# fully in memory (protects the 384MB heap configured in render.yaml).

# ── 1. PROD CONFIG: application.properties ──
PROD_PATH = "erp-backend/src/main/resources/application.properties"
OLD_PROD = """# STARTUP SPEED -- reduce Hibernate scan time
spring.jpa.properties.hibernate.temp.use_jdbc_metadata_defaults=false
spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect
spring.jpa.properties.hibernate.jdbc.lob.non_contextual_creation=true
"""
NEW_PROD = """# STARTUP SPEED -- reduce Hibernate scan time
spring.jpa.properties.hibernate.temp.use_jdbc_metadata_defaults=false
spring.jpa.database-platform=org.hibernate.dialect.PostgreSQLDialect
spring.jpa.properties.hibernate.jdbc.lob.non_contextual_creation=true

# FILE UPLOAD LIMITS
# VITAL FIX: Spring Boot's silent default is 1MB per file / 10MB per request
# if these are never set. That was the real cause of the "file too big" error
# firing on files well under 50MB -- the code promised 50MB but never
# configured it. These values are now the single source of truth and match
# the error message in GlobalExceptionHandler exactly.
spring.servlet.multipart.max-file-size=50MB
spring.servlet.multipart.max-request-size=250MB
spring.servlet.multipart.file-size-threshold=2KB
"""
patch(PROD_PATH, OLD_PROD, NEW_PROD, "PATCH 1/3: application.properties multipart limits")

# ── 2. TEST CONFIG: application-test.properties ──
TEST_PATH = "erp-backend/src/main/resources/application-test.properties"
OLD_TEST = """ADMIN_EMAIL=test@gesolutions.com
ADMIN_DEFAULT_PASSWORD=TestPassword123
MAIL_USERNAME=test@gmail.com
MAIL_PASSWORD=testpassword
"""
NEW_TEST = """ADMIN_EMAIL=test@gesolutions.com
ADMIN_DEFAULT_PASSWORD=TestPassword123
MAIL_USERNAME=test@gmail.com
MAIL_PASSWORD=testpassword

# FILE UPLOAD LIMITS (kept identical to production so test behavior matches reality)
spring.servlet.multipart.max-file-size=50MB
spring.servlet.multipart.max-request-size=250MB
spring.servlet.multipart.file-size-threshold=2KB
"""
patch(TEST_PATH, OLD_TEST, NEW_TEST, "PATCH 2/3: application-test.properties multipart limits")

# ── 3. ERROR MESSAGE: GlobalExceptionHandler.java ──
GEH_PATH = "erp-backend/src/main/java/com/gesolutions/erp/common/exception/GlobalExceptionHandler.java"
OLD_GEH = """    // --- 4. DIGITAL VAULT FAULTS ---
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleFileSizeLimit(MaxUploadSizeExceededException ex) {
        System.err.println(">>> [HARDWARE_LIMIT]: Upload exceeded 50MB threshold.");
        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "VAULT_CAPACITY_EXCEEDED", "File size exceeds 50MB limit.");
    }"""
NEW_GEH = """    // --- 4. DIGITAL VAULT FAULTS ---
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleFileSizeLimit(MaxUploadSizeExceededException ex) {
        // VITAL FIX: message now reflects the ACTUAL configured limits in
        // application.properties (50MB per file, 250MB per full upload batch),
        // instead of the old hardcoded text that did not match reality.
        System.err.println(">>> [HARDWARE_LIMIT]: Upload exceeded configured size threshold. " + ex.getMessage());
        return buildResponse(HttpStatus.PAYLOAD_TOO_LARGE, "VAULT_CAPACITY_EXCEEDED",
            "File too large. Each file must be under 50MB, and the total of all files in one upload must be under 250MB.");
    }"""
patch(GEH_PATH, OLD_GEH, NEW_GEH, "PATCH 3/3: GlobalExceptionHandler accurate error message")

print("")
print("DONE. After this: git add -A && git commit -m 'fix: configure real 50MB/250MB upload limits (was silently 1MB/10MB)' && git push")
print("Then wait for Render to redeploy the backend before testing uploads again.")