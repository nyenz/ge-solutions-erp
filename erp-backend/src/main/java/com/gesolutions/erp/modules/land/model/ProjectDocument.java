// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectDocument.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - DIGITAL ASSET VAULT
 * Stores metadata and location paths for title scans and IDs.
 * Physically anchors the physical paper to the digital archive.
 */
@Entity
@Table(name = "project_documents", indexes = {
    @Index(name = "idx_doc_project", columnList = "project_id")
})
@Getter 
@Setter 
@NoArgsConstructor 
@AllArgsConstructor 
@Builder
public class ProjectDocument {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "project_id", nullable = false)
    private UUID projectId;

    @Column(name = "file_name", nullable = false)
    private String fileName;

    /**
     * ASSET CATEGORY: 
     * e.g., DEED_PLAN, TITLE_CERT, NIN_SCAN, PROBLEM_PROOF
     */
    @Column(name = "file_type", length = 100)
    private String fileType;

    /**
     * STORAGE ANCHOR: 
     * The physical path on Local Disk or a Cloud Bucket URL.
     */
    @Column(name = "file_path", nullable = false, columnDefinition = "TEXT")
    private String filePath;

    /**
     * TACTICAL NOTES: 
     * Specific intelligence related to THIS physical file.
     */
    @Column(name = "internal_notes", columnDefinition = "TEXT")
    private String internalNotes;

    @Column(name = "uploaded_by", length = 100)
    private String uploadedBy;

    @Builder.Default
    @Column(name = "uploaded_at", updatable = false)
    private LocalDateTime uploadedAt = LocalDateTime.now();
}