// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/PendingProjectDTO.java
package com.gesolutions.erp.modules.land.dto;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * fix181 (8.8): what an Employee (and the Pending view) receives about a project. On purpose it has NO money:
 * no price, nothing paid, no fees, no balance, no payment lines. PendingProjectDTOTest checks the JSON.
 */
@Data
@Builder
public class PendingProjectDTO {
    private UUID id;
    private String projectIndex;
    private String projectType;
    private boolean pending;
    private boolean rejected;
    private String rejectedReason;
    private LocalDateTime startedAt;
    private LocalDateTime enteredAt;
    private String enteredBy;
    private Long ageDays;
    // location
    private String district;
    private String county;
    private String subCounty;
    private String parish;
    private String village;
    private String area;
    private LocalDate projectStartDate;
    // title details
    private boolean titleDetailsEnabled;
    private Integer subdivisionCount;
    private String plotNumber;
    private String block;
    private String tenure;
    private BigDecimal areaHectares;
    private String volume;
    private String folio;
    private LocalDate titleIssueDate;
    // fix199 (test note 9): the parts the office saved while Pending. totalCost is filled ONLY for the office
    // (PendingProjectService.viewOwn); an Employee sees just priceSet.
    private String invoiceNumber;
    private String contractNumber;
    private boolean priceSet;
    @com.fasterxml.jackson.annotation.JsonInclude(com.fasterxml.jackson.annotation.JsonInclude.Include.NON_NULL)
    private BigDecimal totalCost;   // left out of the JSON entirely for an Employee (PendingWorkflowTest checks the words)
    // people
    private List<Person> clients;
    private List<Person> owners;
    private List<Neighbor> neighbors;
    private List<String> clientNames;

    public record Person(UUID id, String fullName, String phone, String nationalId, String email, String address) {}
    public record Neighbor(String fullName, String phone, String side, String plotNumber, String notes) {}
}
