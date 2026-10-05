package com.gesolutions.erp.modules.admin;

import com.gesolutions.erp.modules.admin.controller.SystemAdminController;
import jakarta.persistence.CollectionTable;
import jakarta.persistence.Entity;
import jakarta.persistence.JoinTable;
import jakarta.persistence.Table;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.core.type.filter.AnnotationTypeFilter;

import java.lang.reflect.Field;
import java.util.Set;
import java.util.TreeSet;

import static org.junit.jupiter.api.Assertions.assertTrue;

/** fix181 (14.4g, 15.5a): every table of an entity is either wiped or kept on purpose; a new table must be placed. */
public class WipeTableListTest {

    @Test
    public void everyEntityTableIsPlaced() throws Exception {
        ClassPathScanningCandidateComponentProvider scan = new ClassPathScanningCandidateComponentProvider(false);
        scan.addIncludeFilter(new AnnotationTypeFilter(Entity.class));
        Set<String> tables = new TreeSet<>();
        for (BeanDefinition bd : scan.findCandidateComponents("com.gesolutions.erp")) {
            Class<?> c = Class.forName(bd.getBeanClassName());
            Table t = c.getAnnotation(Table.class);
            tables.add(t != null && !t.name().isEmpty() ? t.name() : c.getSimpleName().toLowerCase());
            for (Field f : c.getDeclaredFields()) {
                JoinTable jt = f.getAnnotation(JoinTable.class);
                if (jt != null && !jt.name().isEmpty()) tables.add(jt.name());
                CollectionTable ct = f.getAnnotation(CollectionTable.class);
                if (ct != null && !ct.name().isEmpty()) tables.add(ct.name());
            }
        }
        assertTrue(tables.size() > 15, "the scan found too few tables: " + tables);
        Set<String> missing = new TreeSet<>();
        for (String t : tables) {
            if (!SystemAdminController.TABLES_TO_WIPE.contains(t) && !SystemAdminController.KEPT_ON_PURPOSE.contains(t)) missing.add(t);
        }
        assertTrue(missing.isEmpty(), "Put these tables in TABLES_TO_WIPE or KEPT_ON_PURPOSE: " + missing);
        assertTrue(SystemAdminController.KEPT_ON_PURPOSE.contains("users"), "staff accounts are kept (14.4a B)");
        assertTrue(SystemAdminController.KEPT_ON_PURPOSE.contains("audit_logs"), "the audit trail is never wiped (14.4b)");
    }
}
