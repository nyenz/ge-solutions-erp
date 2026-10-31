// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/archive/model/ArchivedItem.java
package com.gesolutions.erp.modules.archive.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * fix284 (B1, David): a document, a note or an expense that someone deleted. It is kept here for 90 days so a Director
 * can bring it back. The live tables stay exactly as they were: the item is copied here FIRST, then removed there, so
 * every list, total and report that reads the live tables is unchanged. A document's FILE stays in storage until this
 * row expires. Restoring puts the item back as a new live row; after 90 days a nightly job removes row and file.
 */
@Entity
@Table(name = "archived_items", indexes = {
    @Index(name = "idx_archived_deleted_at", columnList = "deleted_at"),
    @Index(name = "idx_archived_project", columnList = "project_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArchivedItem {

    public static final String DOCUMENT = "DOCUMENT";
    public static final String NOTE = "NOTE";
    public static final String EXPENSE = "EXPENSE";
    public static final int KEEP_DAYS = 90;

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    /** DOCUMENT, NOTE or EXPENSE */
    @Column(name = "kind", nullable = false, length = 12)
    private String kind;

    /** the id the item had while it was live */
    @Column(name = "original_id")
    private UUID originalId;

    @Column(name = "project_id")
    private UUID projectId;

    /** the words a person reads: the file name, the start of the note, "Fuel - UGX 50,000" */
    @Column(name = "label", nullable = false, length = 300)
    private String label;

    /** a second line: the category, or the project it belonged to */
    @Column(name = "detail", length = 300)
    private String detail;

    /** every field of the item as JSON text, enough to put it back */
    @Column(name = "snapshot", nullable = false, columnDefinition = "TEXT")
    private String snapshot;

    /** documents only: where the kept file is */
    @Column(name = "file_path", columnDefinition = "TEXT")
    private String filePath;

    @Column(name = "deleted_by", length = 100)
    private String deletedBy;

    @Builder.Default
    @Column(name = "deleted_at", nullable = false)
    private LocalDateTime deletedAt = LocalDateTime.now();

    @Column(name = "reason", columnDefinition = "TEXT")
    private String reason;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;
}
