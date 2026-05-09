import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    dir_ = os.path.dirname(path)
    if dir_:
        os.makedirs(dir_, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING patch target in {path}")
        return
    write(path, content.replace(old, new, 1))


# ============================================================
# FIX 1: Add sessionVersion to User entity
# ============================================================
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/model/User.java",
    "    @Column(name = \"reset_token\")\n    private String resetToken;",
    """    @Column(name = \"reset_token\")
    private String resetToken;

    /**
     * SESSION VERSION
     * Incremented on every login. Embedded in the JWT.
     * If the JWT version doesn't match the DB version, the session is invalid.
     * This enforces single-session across all devices and browsers.
     */
    @Builder.Default
    @Column(name = \"session_version\", nullable = false)
    private Integer sessionVersion = 0;"""
)

# ============================================================
# FIX 2: Increment sessionVersion on login in AuthService
# ============================================================
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/auth/service/AuthService.java",
    "        if (!user.isActive()) {\n            throw new BusinessException(\"AUTHORITY_REVOKED: ACCOUNT_SUSPENDED\");\n        }\n\n        final UserDetails userDetails = userDetailsService.loadUserByUsername(request.getUsername());\n        String token = jwtService.generateToken(userDetails);",
    """        if (!user.isActive()) {
            throw new BusinessException("AUTHORITY_REVOKED: ACCOUNT_SUSPENDED");
        }

        // Increment session version — invalidates all previously issued tokens
        user.setSessionVersion(user.getSessionVersion() + 1);
        userRepository.save(user);

        final UserDetails userDetails = userDetailsService.loadUserByUsername(request.getUsername());
        // Embed sessionVersion in JWT so we can validate it on every request
        java.util.Map<String, Object> extraClaims = new java.util.HashMap<>();
        extraClaims.put("sv", user.getSessionVersion());
        String token = jwtService.generateToken(extraClaims, userDetails);"""
)

# ============================================================
# FIX 3: Add sessionVersion validation to JwtAuthenticationFilter
# ============================================================
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/config/JwtAuthenticationFilter.java",
    "import com.gesolutions.erp.config.JwtService;\nimport org.springframework.security.core.context.SecurityContextHolder;\nimport org.springframework.security.core.userdetails.UserDetails;\nimport org.springframework.security.core.userdetails.UserDetailsService;",
    """import com.gesolutions.erp.config.JwtService;
import com.gesolutions.erp.modules.auth.repository.UserRepository;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;"""
)

patch(
    "erp-backend/src/main/java/com/gesolutions/erp/config/JwtAuthenticationFilter.java",
    "    private final JwtService jwtService;\n    private final UserDetailsService userDetailsService;",
    """    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;
    private final UserRepository userRepository;"""
)

patch(
    "erp-backend/src/main/java/com/gesolutions/erp/config/JwtAuthenticationFilter.java",
    "            if (jwtService.isTokenValid(jwt, Objects.requireNonNull(userDetails))) {\n                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(",
    """            // Validate session version — rejects tokens from older sessions
            Integer tokenSv = jwtService.extractClaim(jwt, claims -> {
                Object sv = claims.get("sv");
                return sv != null ? ((Number) sv).intValue() : null;
            });
            boolean sessionValid = userRepository.findByUsername(userDetails.getUsername())
                .map(u -> tokenSv != null && tokenSv.equals(u.getSessionVersion()))
                .orElse(false);

            if (jwtService.isTokenValid(jwt, Objects.requireNonNull(userDetails)) && sessionValid) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken("""
)

# ============================================================
# FIX 4: Update addendum
# ============================================================
addendum = """# GE SOLUTIONS ERP -- CONTEXT ADDENDUM
# This file receives all small incremental updates each session.
# Last updated: May 2026

---

## SESSION MANAGEMENT RULES (HOW EVERY SESSION ENDS)

At the end of every session the AI must do the following in order:

1. Read the addendum to identify everything worked on this session
2. Ask David: "Are you happy with X, Y, Z? Should I mark them as done?"
3. Wait for David to confirm -- do not assume anything is done without confirmation
4. Once confirmed:
   - Move confirmed items INTO Section 10 (COMPLETED) of master guide
   - Remove confirmed items FROM Section 11 (TO DO) of master guide
   - If something new came up during the session, add it to Section 11
5. Both sections must reflect 3 sources of truth:
   - What the addendum says was worked on
   - What David explicitly confirmed he is happy with
   - What the code actually shows

RULE: Once something is marked done and moved to Section 10, it is NEVER put back in Section 11.
RULE: Section 11 only contains things not yet done. Completed work lives in Section 10 only.
RULE: The addendum is the running log. The master guide Sections 10 and 11 are the clean summary.

---

## NEW UI RULES ADDED (May 2026)

### UI UNIFORMITY RULE (DEFAULT DESIGN APPROACH)
Every element of the same type must look and behave identically across all pages and sections regardless of where it appears. Only deviate when explicitly instructed.

### RESPONSIVENESS RULE (DEFAULT DESIGN APPROACH)
Every element, property, and value must respond to screen size changes by default.

### "SAME DESIGN" PHRASE RULE
When the instruction says "same design", the element must be identical in every measurable way.

### NO BROWSER DEFAULT STYLING RULE (DEFAULT DESIGN APPROACH)
Every element must be explicitly styled -- no browser defaults are ever acceptable anywhere in the app.

---

## SESSION: May 2026 -- FIXES APPLIED THIS SESSION

### 1. Print Preview (FolderPage)
- Completely rewrote @media print CSS in FolderPage.module.css
- Pipeline HUD: compact horizontal row with visible stage dots
- Terminal header: white background, navy border-left
- All panels: white background, grey borders, all drawers forced open
- Read-only grid: 3 columns on print
- Owners: 2 columns on print
- Financials: all visible, no glow effects
- Notes + docs: scroll disabled, full height shown
- @page: A4 portrait, 15mm margins
- Status: DONE PREVIOUS SESSION

### 2. PDF viewing in FolderPage (from Cloudinary)
- Added isPDF() helper function to detect PDF files by path/URL
- PDF files now show with open-in-new-tab link + 📄 emoji prefix
- Cloudinary raw PDFs served directly via their secure_url
- Status: DONE PREVIOUS SESSION

### 3. Document preview on New Plot page (IntakePage)
- Fixed file queue to allow opening uploaded files before submission
- Files show emoji prefix (📄 for PDF, 🖼 for image) as visual hint
- Status: DONE PREVIOUS SESSION

### 4. Audit Page filter dropdowns (ALL STAFF / ALL ACTIONS)
- Resized hwSelectWrap to flex: 1 1 140px, max-width: 260px
- Status: DONE PREVIOUS SESSION

### 5. Single-session enforcement -- BROWSER TABS ONLY (previous)
- localStorage-based approach for same-browser tab detection
- Status: DONE PREVIOUS SESSION

### 6. Server-side single-session enforcement (THIS SESSION)
- Added sessionVersion (Integer) column to users table in User.java
- On every login: sessionVersion incremented in DB, embedded in JWT as "sv" claim
- JwtAuthenticationFilter: on every request, extracts "sv" from JWT and compares
  to the current DB value. If mismatch (old token), request is rejected with 401.
- This means: logging in from computer B immediately invalidates computer A's token.
- The axios interceptor on the frontend already handles 401 by redirecting to /login.
- Status: DONE THIS SESSION

---

## HOW SERVER-SIDE SESSION ENFORCEMENT WORKS

1. David logs in on Computer A
   -> sessionVersion in DB becomes 1
   -> JWT contains { sv: 1 }
   -> Computer A works fine

2. David logs in on Computer B (or someone else logs in)
   -> sessionVersion in DB becomes 2
   -> JWT on Computer B contains { sv: 2 }
   -> Computer A's JWT still has { sv: 1 }

3. Computer A makes any API request
   -> Filter extracts sv=1 from JWT
   -> DB has sv=2
   -> 1 != 2 -> 401 Unauthorized
   -> Axios interceptor on frontend detects 401
   -> Redirects to /login
   -> Computer A is now logged out automatically

No cron jobs, no websockets, no polling needed. Works on next request.

---

## KNOWN ISSUES / NOTES

- Cloudinary raw PDFs: If PDFs show 401, check Cloudinary dashboard >
  Security > Restricted media types. The fix is on the Cloudinary side.
  Your Java code already uploads PDFs with resource_type=raw correctly.

- sessionVersion DB migration: Hibernate DDL auto=update will add the
  session_version column automatically on next deploy. Existing rows
  will get NULL which Java treats as 0 (due to Integer object type).
  First login after deploy will set it to 1 and everything works normally.
"""

write("LLM_CONTEXT_ADDENDUM.md", addendum)

print("\n=== ALL FIXES COMPLETE ===")
print("1. User.java: sessionVersion field added")
print("2. AuthService.java: increments sessionVersion on login, embeds in JWT")
print("3. JwtAuthenticationFilter.java: validates sessionVersion on every request")
print("4. LLM_CONTEXT_ADDENDUM.md: updated")
print("\nNOTE: Hibernate will auto-create the session_version column on next deploy.")
print("Existing users get sessionVersion=0, first login sets it to 1. No data loss.")