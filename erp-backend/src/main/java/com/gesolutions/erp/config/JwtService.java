// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/JwtService.java
package com.gesolutions.erp.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders; // VITAL IMPORT
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import java.security.Key;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

@Service
public class JwtService {

    @Value("${ge.solutions.jwt.secret}")
    private String secretKey;

    @Value("${ge.solutions.jwt.expiration}")
    private long jwtExpiration;

    public String extractUsername(String token) { return extractClaim(token, Claims::getSubject); }
    public <T> T extractClaim(String token, Function<Claims, T> cr) { return cr.apply(extractAllClaims(token)); }
    public String generateToken(UserDetails ud) { return generateToken(new HashMap<>(), ud); }

    public String generateToken(Map<String, Object> extra, UserDetails ud) {
        return Jwts.builder()
                .setClaims(extra)
                .setSubject(ud.getUsername())
                .setIssuedAt(new Date(System.currentTimeMillis()))
                .setExpiration(new Date(System.currentTimeMillis() + jwtExpiration))
                .signWith(getSignInKey(), SignatureAlgorithm.HS256)
                .compact();
    }

    public boolean isTokenValid(String token, UserDetails ud) {
        final String username = extractUsername(token);
        return (username.equals(ud.getUsername())) && !isTokenExpired(token);
    }

    private boolean isTokenExpired(String token) { return extractExpiration(token).before(new Date()); }
    private Date extractExpiration(String token) { return extractClaim(token, Claims::getExpiration); }

    private Claims extractAllClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(getSignInKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }

    private Key getSignInKey() {
        // VITAL FIX: We now explicitly DECODE the Base64 secret you provided
        // This stops the 500 System Critical Error in Linux/Render
        byte[] keyBytes = Decoders.BASE64.decode(secretKey);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}