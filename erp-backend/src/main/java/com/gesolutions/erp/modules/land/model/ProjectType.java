// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/ProjectType.java
package com.gesolutions.erp.modules.land.model;

import java.util.List;

/**
 * fix180: the eight project types picked on New Project. Each type decides
 * (1) whether the Title Details panel is shown (ALWAYS, OPTIONAL = staff switch it on, NEVER) and
 * (2) its own ordered default status list (seeded into status_templates per type, see StatusTemplateService).
 * Stored on LandProject.projectType as the enum name. This is the ONE place the list lives on the server;
 * the page copy is erp-frontend/src/constants/projectTypes.js (keep the two in step).
 */
public enum ProjectType {

    FRESH_SURVEY("Fresh Survey", TitleMode.NEVER, List.of(
            "Field Measurement", "Invoice / Contract Number", "Area Land Committee", "Physical Planning Consent",
            "Board Minute", "Instruction to Survey", "Job Record Jacket (JRJ)", "Deed Plan", "Offer Letter",
            "Forwarding Letter", "Titled")),
    SUBDIVISION("Subdivision", TitleMode.ALWAYS, List.of(
            "Field Measurement", "Invoice / Contract Number", "Consent for Subdivision", "Physical Planning Consent",
            "Instruction to Survey", "Job Record Jacket (JRJ)", "Deed Plan", "Titled")),
    LEGACY_TITLES("Legacy Titles", TitleMode.ALWAYS, List.of(
            "Invoice / Contract Number", "Titled")),
    TRANSFER_OF_TITLE("Transfer of Title", TitleMode.ALWAYS, List.of(
            "Invoice / Contract Number", "Transfer Form", "Stamp Duty", "Titled")),
    BOUNDARY_OPENING("Boundary Opening", TitleMode.ALWAYS, List.of(
            "Field Measurement", "Invoice / Contract Number", "Survey Report")),
    TOPOGRAPHIC_SURVEY("Topographic Survey", TitleMode.OPTIONAL, List.of(
            "Field Measurement", "Invoice / Contract Number", "Survey Report")),
    RESURVEY("Resurvey", TitleMode.ALWAYS, List.of(
            "Field Measurement", "Invoice / Contract Number", "Area Land Committee", "Physical Planning Consent",
            "Board Minute", "Instruction to Survey", "Job Record Jacket (JRJ)", "Deed Plan", "Titled")),
    SPECIAL_PROJECTS("Special Projects", TitleMode.NEVER, List.of(
            "Contract", "Field Measurement", "Progressive Reports", "Progressive Invoice", "Final Reports",
            "Final Invoices"));

    public enum TitleMode { ALWAYS, OPTIONAL, NEVER }

    private final String label;
    private final TitleMode titleMode;
    private final List<String> defaultStatuses;

    ProjectType(String label, TitleMode titleMode, List<String> defaultStatuses) {
        this.label = label;
        this.titleMode = titleMode;
        this.defaultStatuses = defaultStatuses;
    }

    public String getLabel() { return label; }
    public TitleMode getTitleMode() { return titleMode; }
    public List<String> getDefaultStatuses() { return defaultStatuses; }

    /** True when a project of this type carries Title Details (for OPTIONAL: only when staff switched it on). */
    public boolean showsTitle(boolean optionalSwitchedOn) {
        return titleMode == TitleMode.ALWAYS || (titleMode == TitleMode.OPTIONAL && optionalSwitchedOn);
    }

    /** Lenient lookup: enum name or label, any case. Unknown or blank = null. */
    public static ProjectType from(String code) {
        if (code == null || code.isBlank()) return null;
        String c = code.trim();
        for (ProjectType t : values()) {
            if (t.name().equalsIgnoreCase(c) || t.label.equalsIgnoreCase(c)) return t;
        }
        return null;
    }

    /** The type of a stored project. Projects saved before fix180 have none: Legacy Title entries read as LEGACY_TITLES, the rest as FRESH_SURVEY. */
    public static ProjectType of(LandProject p) {
        ProjectType t = p == null ? null : from(p.getProjectType());
        if (t != null) return t;
        return p != null && p.isLegacy() ? LEGACY_TITLES : FRESH_SURVEY;
    }
}
