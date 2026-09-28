// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/DocumentCategory.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - DOCUMENT CATEGORY (fix136)
 *
 * The catalog a document is filed under: Application Forms, Offer Letters,
 * Forwarding Letters, Deed Plan, Copy of Title, Payment Receipts, plus any
 * category a Secretary / Manager / Admin / Director adds at upload time.
 *
 * code  = stable machine key stored on project_documents.category
 * label = what people read
 */
@Entity
@Table(name = "document_categories", uniqueConstraints = {
    @UniqueConstraint(name = "uq_document_category_code", columnNames = "code")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DocumentCategory {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "code", nullable = false, length = 60)
    private String code;

    @Column(name = "label", nullable = false, length = 120)
    private String label;

    @Builder.Default
    @Column(name = "built_in", nullable = false)
    private boolean builtIn = false;

    /** Built-ins are 1..6 in the order the office files them; custom ones sort after. */
    @Builder.Default
    @Column(name = "sort_order", nullable = false)
    private int sortOrder = 100;

    @Column(name = "created_by", length = 100)
    private String createdBy;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
