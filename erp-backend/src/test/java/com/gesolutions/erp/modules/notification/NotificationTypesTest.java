package com.gesolutions.erp.modules.notification;

import com.gesolutions.erp.modules.notification.service.NotificationTypes;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

/** fix181 (17.2): the one alert list is complete, never addresses the Employee, and the page catalog knows every type. */
public class NotificationTypesTest {

    @Test
    public void noAudienceContainsTheEmployeeOrAll() {
        for (NotificationTypes.Type t : NotificationTypes.all().values()) {
            assertFalse(t.audience().isEmpty(), t.code() + " has no audience");
            assertFalse(t.audience().contains("ROLE_EMPLOYEE"), t.code() + " must not go to the Employee");
            assertFalse(t.audience().contains("ALL"), t.code() + " must not use ALL");
        }
    }

    @Test
    public void adminGetsOnlySystemStaffAndBooksCheck() {
        for (NotificationTypes.Type t : NotificationTypes.all().values()) {
            if (!t.audience().contains("ROLE_ADMIN")) continue;
            boolean allowed = t.group() == NotificationTypes.Group.SYSTEM || t.group() == NotificationTypes.Group.STAFF
                    || t.code().equals("BOOKS_MISMATCH") || t.code().equals("PROJECT_DELETED");
            assertTrue(allowed, t.code() + " should not go to the Admin");
        }
    }

    @Test
    public void everyTypeIsInThePageCatalog() throws Exception {
        Path catalog = Path.of("..", "erp-frontend", "src", "components", "common", "notificationCatalog.js");
        if (!Files.exists(catalog)) return;   // backend built on its own
        String js = Files.readString(catalog);
        for (String code : NotificationTypes.all().keySet()) {
            assertTrue(js.contains(code + ":"), code + " is missing from notificationCatalog.js");
        }
    }
}
