package com.gesolutions.erp.config;

import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * fix284 (B5): the REAL server must never run with the public fallback secrets that are written in
 * application.properties (they are on GitHub, so anyone can read them).
 *
 * The guard is on when the demo data is switched OFF (= a real server) and the database is not the in-memory test
 * database. It refuses to start the app (the update script then puts the previous version back) if the login-signing
 * key, the starting owner key or the database password is still the public fallback or empty.
 * The practice (DEMO) copy has demo data on, so it is not affected. The real server sets all three in
 * /opt/ges/infra/.env, so nothing changes for it.
 */
@Component
public class StartupSecretGuard {

    static final String PUBLIC_JWT_SECRET = "YTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=";
    static final String PUBLIC_ADMIN_KEY = "TestPassword123";
    static final String PUBLIC_DB_PASSWORD = "able1212";

    @Value("${ge.solutions.seed-demo-data:true}") private boolean seedDemoData;
    @Value("${spring.datasource.url:}") private String datasourceUrl;
    @Value("${ge.solutions.jwt.secret:}") private String jwtSecret;
    @Value("${ADMIN_DEFAULT_PASSWORD:}") private String adminDefaultPassword;
    @Value("${spring.datasource.password:}") private String dbPassword;

    @PostConstruct
    void check() {
        List<String> problems = problems(seedDemoData, datasourceUrl, jwtSecret, adminDefaultPassword, dbPassword);
        if (problems.isEmpty()) return;
        String msg = "This server is set up as a REAL server (demo data is off) but it still uses public default secrets: "
                + String.join("; ", problems)
                + ". Set your own values in /opt/ges/infra/.env (deploy.sh makes them for you) and start again.";
        System.err.println(">>> [BOOT] FATAL STARTUP ERROR: " + msg);
        throw new IllegalStateException(msg);
    }

    /** The list of what is wrong. Empty when the guard is off or everything is fine. Static so a test can call it. */
    static List<String> problems(boolean seedDemoData, String url, String jwt, String adminKey, String dbPass) {
        List<String> out = new ArrayList<>();
        boolean testDatabase = url != null && url.startsWith("jdbc:h2:");
        if (seedDemoData || testDatabase) return out;
        if (blank(jwt) || PUBLIC_JWT_SECRET.equals(jwt.trim())) out.add("the login signing key (GE_SOLUTIONS_JWT_SECRET)");
        if (blank(adminKey) || PUBLIC_ADMIN_KEY.equals(adminKey.trim())) out.add("the starting owner key (ADMIN_DEFAULT_PASSWORD)");
        if (blank(dbPass) || PUBLIC_DB_PASSWORD.equals(dbPass.trim())) out.add("the database password (SPRING_DATASOURCE_PASSWORD)");
        return out;
    }

    private static boolean blank(String s) { return s == null || s.trim().isEmpty(); }
}
