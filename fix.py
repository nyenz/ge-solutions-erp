# PATH: fix.py
import os

path = "erp-backend/src/main/java/com/gesolutions/erp/config/JwtAuthenticationFilter.java"

if not os.path.isfile(path):
    print(f"MISSING: {path} not found")
else:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Normalize line endings
    content = content.replace("\r\n", "\n")

    old_block = """        jwt = authHeader.substring(7);
        username = jwtService.extractUsername(jwt);

        // 2. Validate Security Context and Perform Handshake
        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
            
            // PROVING non-nullity to the compiler to clear warnings
            // Validate session version — rejects tokens from older sessions
            Integer tokenSv = jwtService.extractClaim(jwt, claims -> {
                Object sv = claims.get("sv");
                return sv != null ? ((Number) sv).intValue() : null;
            });
            boolean sessionValid = userRepository.findByUsername(userDetails.getUsername())
                .map(u -> {
                    Integer dbSv = u.getSessionVersion();
                    if (dbSv == null) return false; // not yet set, reject until login
                    return tokenSv != null && tokenSv.equals(dbSv);
                })
                .orElse(false);

            if (jwtService.isTokenValid(jwt, Objects.requireNonNull(userDetails)) && sessionValid) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.getAuthorities()
                );
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                
                // AUTHORIZE OPERATOR SESSION
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }
        filterChain.doFilter(request, response);"""

    new_block = """        try {
            jwt = authHeader.substring(7);
            username = jwtService.extractUsername(jwt);

            // 2. Validate Security Context and Perform Handshake
            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UserDetails userDetails = this.userDetailsService.loadUserByUsername(username);
                
                Integer tokenSv = jwtService.extractClaim(jwt, claims -> {
                    Object sv = claims.get("sv");
                    return sv != null ? ((Number) sv).intValue() : null;
                });
                boolean sessionValid = userRepository.findByUsername(userDetails.getUsername())
                    .map(u -> {
                        Integer dbSv = u.getSessionVersion();
                        if (dbSv == null) return false; 
                        return tokenSv != null && tokenSv.equals(dbSv);
                    })
                    .orElse(false);

                if (jwtService.isTokenValid(jwt, Objects.requireNonNull(userDetails))) {
                    if (!sessionValid) {
                        // VITAL FIX: Force a 401 Unauthorized response for session conflicts
                        // This triggers the frontend Axios interceptor to instantly redirect to /login
                        response.setStatus(jakarta.servlet.http.HttpServletResponse.SC_UNAUTHORIZED);
                        response.setContentType("application/json");
                        response.getWriter().write("{\\"error\\": \\"SESSION_CONFLICT\\", \\"message\\": \\"Session expired on another device\\"}");
                        return;
                    }

                    UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                            userDetails,
                            null,
                            userDetails.getAuthorities()
                    );
                    authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                    
                    SecurityContextHolder.getContext().setAuthentication(authToken);
                }
            }
        } catch (Exception e) {
            // VITAL FIX: Catch ExpiredJwtException and force a 401 instead of crashing to a 500/403
            response.setStatus(jakarta.servlet.http.HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json");
            response.getWriter().write("{\\"error\\": \\"INVALID_TOKEN\\", \\"message\\": \\"Token expired or malformed\\"}");
            return;
        }
        filterChain.doFilter(request, response);"""

    if old_block in content:
        content = content.replace(old_block, new_block)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: Patched {path} with strict HTTP 401 responses for invalid/conflicting sessions.")
    elif new_block in content:
        print(f"SKIP: {path} is already patched.")
    else:
        print(f"FAIL: Target block not found in {path}")