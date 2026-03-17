// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/audit/AuditLog.java
package com.gesolutions.erp.common.audit;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "audit_logs")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class AuditLog {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    private String action;
    
    @Column(columnDefinition = "TEXT")
    private String details;

    private String performedBy;
    private LocalDateTime timestamp;
}
