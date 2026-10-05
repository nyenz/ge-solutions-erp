package com.gesolutions.erp.common.audit;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.*;

/**
 * fix181 (13.13, 13.14): every code a logAction / logActionAs / logActionAfterCommit / reportFailures call writes must
 * be in AuditActions (the one shared list); the Audit page catalog is checked against it by the front-end build script.
 */
public class AuditActionsTest {

    private static final Pattern CALL = Pattern.compile("logAction(As|AfterCommit)?\\s*\\(|reportFailures\\s*\\(");
    private static final Pattern CODE = Pattern.compile("\"([A-Z][A-Z0-9_]{2,})\"");

    @Test
    public void everyWrittenCodeIsInTheSharedList() throws IOException {
        Set<String> unknown = new TreeSet<>();
        try (Stream<Path> files = Files.walk(Paths.get("src/main/java"))) {
            for (Path f : files.filter(p -> p.toString().endsWith(".java") && !p.endsWith("ScenarioSeeder.java")).toList()) {
                List<String> lines = Files.readAllLines(f);
                for (int i = 0; i < lines.size(); i++) {
                    Matcher m = CALL.matcher(lines.get(i));
                    if (!m.find()) continue;
                    String text = lines.get(i).substring(m.start());
                    if (!lines.get(i).trim().endsWith(";") && i + 1 < lines.size()) text += " " + lines.get(i + 1);
                    text = text.split(";")[0];
                    Matcher c = CODE.matcher(text);
                    while (c.find()) if (!AuditActions.ALL.contains(c.group(1))) unknown.add(c.group(1) + " (" + f.getFileName() + ")");
                }
            }
        }
        assertTrue(unknown.isEmpty(), "audit codes missing from AuditActions: " + unknown);
    }

    @Test
    public void oldCodesAreNotAlsoCurrent() {
        for (String c : AuditActions.OLD) assertFalse(AuditActions.ALL.contains(c), c + " is listed as both old and current");
    }
}
