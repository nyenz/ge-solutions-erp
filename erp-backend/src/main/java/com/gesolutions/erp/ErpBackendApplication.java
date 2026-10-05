// PATH: erp-backend/src/main/java/com/gesolutions/erp/ErpBackendApplication.java
package com.gesolutions.erp;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class ErpBackendApplication {

    /** fix181: the business runs on Uganda time. Every LocalDateTime.now() (locks, "today", nightly jobs) uses this zone. */
    public static final String ZONE = "Africa/Kampala";

    public static void main(String[] args) {
        java.util.TimeZone.setDefault(java.util.TimeZone.getTimeZone(ZONE));
        SpringApplication.run(ErpBackendApplication.class, args);
    }
}