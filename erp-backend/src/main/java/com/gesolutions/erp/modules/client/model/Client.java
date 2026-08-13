// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/client/model/Client.java
package com.gesolutions.erp.modules.client.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.time.Month;
import java.util.UUID;

/**
 * GE SOLUTIONS - HUMAN IDENTITY REGISTRY
 *
 * PHASE 2: Identity is now anchored on National ID (NIN), not phone number.
 * Phone number is still required as a contact field, but is no longer
 * enforced as unique at the database level -- joint owners or family
 * members may legitimately share one phone.
 *
 * Physically manages the "Recovery Cool-Down" logic:
 * - 14-Day Interval Check
 * - 2-Call Per Month Handbrake
 */
@Entity
@Table(name = "clients", indexes = {
    @Index(name = "idx_client_phone", columnList = "phone_number"),
    @Index(name = "idx_client_nin", columnList = "national_id"),
    @Index(name = "idx_client_last_call", columnList = "last_contacted_at")
})
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class Client {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    // NOTE: unique=true intentionally removed in Phase 2 -- see DataInitializer
    // migration that drops the old DB-level unique constraint on this column.
    @Column(name = "phone_number", nullable = false, length = 50)
    private String phoneNumber;

    /**
     * NATIONAL ID (NIN) -- THE REAL IDENTITY ANCHOR (Phase 2)
     * Mandatory for every project owner going forward. Unique at the DB level
     * (see DataInitializer). Legacy client rows created before Phase 2 may
     * have this blank until next edited.
     */
    @Column(name = "national_id", length = 100)
    private String nationalId;

    @Column(name = "home_address", columnDefinition = "TEXT")
    private String homeAddress;

    @Column(name = "email")
    private String email;

    /* --- RECOVERY ARCHITECTURE (THE 2-14 RULE) --- */

    @Column(name = "last_contacted_at")
    private LocalDateTime lastContactedAt;

    /**
     * THE MONTHLY COUNTER
     * Physically counts successful interactions in the current month.
     */
    @Builder.Default
    @Column(name = "monthly_contact_count", nullable = false)
    private Integer monthlyContactCount = 0;

    /**
     * RELIABILITY METER (0-100)
     * Decreases on defaults, increases on successful calls and payments.
     */
    @Builder.Default
    @Column(name = "reliability_score", nullable = false)
    private Double reliabilityScore = 100.0;

    /**
     * HARDWARE LOGIC: Contact Suppression Check
     * This method tells the system if the counter needs to be reset 
     * before a new call is logged.
     */
    public boolean shouldResetMonthlyCounter() {
        if (lastContactedAt == null) return true;
        
        Month currentMonth = LocalDateTime.now().getMonth();
        int currentYear = LocalDateTime.now().getYear();
        
        return lastContactedAt.getMonth() != currentMonth || lastContactedAt.getYear() != currentYear;
    }
}
