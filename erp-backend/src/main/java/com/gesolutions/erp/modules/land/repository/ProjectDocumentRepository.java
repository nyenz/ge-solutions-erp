// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/ProjectDocumentRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.ProjectDocument;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

/**
 * THE DIGITAL ARCHIVE REPOSITORY
 * 
 * Manages the persistence of metadata for scanned land documents.
 * This repository keeps the database lightweight by storing paths to files 
 * on the physical server disk rather than storing the actual binaries.
 */
@Repository
public interface ProjectDocumentRepository extends JpaRepository<ProjectDocument, UUID> {

    /**
     * Retrieves all scans and files associated with a specific Plot/Project.
     * Used in the Project Profile Page to display the digital history.
     * 
     * @param projectId The unique ID of the land project.
     * @return A list of documents (Deed plans, Title scans, etc.).
     */
    List<ProjectDocument> findByProjectId(UUID projectId);

    /**
     * Retrieves documents of a specific type for a project.
     * Useful for finding "Title Scans" specifically during final release.
     */
    List<ProjectDocument> findByProjectIdAndFileType(UUID projectId, String fileType);

    /**
     * Audit Support: Find documents uploaded by a specific staff member.
     */
    List<ProjectDocument> findByUploadedBy(String uploadedBy);
}