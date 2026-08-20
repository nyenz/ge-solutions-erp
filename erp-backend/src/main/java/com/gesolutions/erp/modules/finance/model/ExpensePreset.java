// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/finance/model/ExpensePreset.java
package com.gesolutions.erp.modules.finance.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - EXPENSE PRESET (EXPENSES REBUILD)
 *
 * A quick-tap category button on the Expenses page (e.g. "Office",
 * "Fieldwork", "Land Office"). Any Manager+ user can create a new preset
 * instantly -- no approval step. This is the ONLY place a new category
 * name gets typed; every future expense against that category is then a
 * single tap, no typing.
 */
@Entity
@Table(name = "expense_presets")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExpensePreset {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "name", nullable = false, unique = true, length = 100)
    private String name;

    @Column(name = "created_by", length = 100)
    private String createdBy;

    @Builder.Default
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
