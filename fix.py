import os

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if old not in content:
        print(f"MISSING patch target in: {path}")
        return
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content.replace(old, new, 1))
    print(f"OK (patched): {path}")

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. LandTitle.java — add surveyDate field
# ============================================================
patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'model', 'LandTitle.java'),
    '// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java\npackage com.gesolutions.erp.modules.land.model;\n\nimport jakarta.persistence.*;\nimport lombok.*;\nimport java.time.LocalDateTime;\nimport java.util.UUID;',
    '// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java\npackage com.gesolutions.erp.modules.land.model;\n\nimport jakarta.persistence.*;\nimport lombok.*;\nimport java.time.LocalDate;\nimport java.time.LocalDateTime;\nimport java.util.UUID;'
)

patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'model', 'LandTitle.java'),
    '    @Builder.Default\n    @Column(name = "is_released", nullable = false)\n    private boolean isReleased = false;',
    '    @Column(name = "survey_date")\n    private LocalDate surveyDate;\n\n    @Builder.Default\n    @Column(name = "is_released", nullable = false)\n    private boolean isReleased = false;'
)

# ============================================================
# 2. LandEntryRequest.java — add surveyDate field
# ============================================================
patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'dto', 'LandEntryRequest.java'),
    'import com.fasterxml.jackson.annotation.JsonProperty;\nimport lombok.*;\nimport java.math.BigDecimal;\nimport java.util.ArrayList;\nimport java.util.List;\nimport java.util.UUID;',
    'import com.fasterxml.jackson.annotation.JsonProperty;\nimport lombok.*;\nimport java.math.BigDecimal;\nimport java.time.LocalDate;\nimport java.util.ArrayList;\nimport java.util.List;\nimport java.util.UUID;'
)

patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'dto', 'LandEntryRequest.java'),
    '    private String instrumentNo;\n    private String physicalBoxNumber;',
    '    private String instrumentNo;\n    private String physicalBoxNumber;\n    private LocalDate surveyDate;'
)

# ============================================================
# 3. RecoveryTaskDTO.PlotSummary — add surveyDate
# ============================================================
patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'client', 'dto', 'RecoveryTaskDTO.java'),
    'import lombok.*;\nimport java.math.BigDecimal;\nimport java.util.List;\nimport java.util.UUID;',
    'import lombok.*;\nimport java.math.BigDecimal;\nimport java.time.LocalDate;\nimport java.util.List;\nimport java.util.UUID;'
)

patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'client', 'dto', 'RecoveryTaskDTO.java'),
    '        private String lastPaymentDate;\n        private String lastInteractionNote;',
    '        private String lastPaymentDate;\n        private String lastInteractionNote;\n        private LocalDate surveyDate;'
)

# ============================================================
# 4. LandService.java — map surveyDate in atomicIntake and updateProjectFull
# ============================================================
patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'service', 'LandService.java'),
    '        LandTitle title = LandTitle.builder()\n                .tenure(request.getTenure())\n                .plotNumber(request.getPlotNumber())\n                .physicalBoxNumber(request.getPhysicalBoxNumber())\n                .district(request.getDistrict())\n                .blockRoad(request.getBlockRoad())\n                .county(request.getCounty())\n                .volume(request.getVolume())\n                .folio(request.getFolio())\n                .instrumentNo(request.getInstrumentNo())\n                .build();',
    '        LandTitle title = LandTitle.builder()\n                .tenure(request.getTenure())\n                .plotNumber(request.getPlotNumber())\n                .physicalBoxNumber(request.getPhysicalBoxNumber())\n                .district(request.getDistrict())\n                .blockRoad(request.getBlockRoad())\n                .county(request.getCounty())\n                .volume(request.getVolume())\n                .folio(request.getFolio())\n                .instrumentNo(request.getInstrumentNo())\n                .surveyDate(request.getSurveyDate())\n                .build();'
)

patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'land', 'service', 'LandService.java'),
    '        title.setPlotNumber(request.getPlotNumber());\n        title.setTenure(request.getTenure());\n        title.setBlockRoad(request.getBlockRoad());\n        title.setDistrict(request.getDistrict());\n        title.setCounty(request.getCounty());\n        title.setVolume(request.getVolume());\n        title.setFolio(request.getFolio());\n        title.setInstrumentNo(request.getInstrumentNo());\n        title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());',
    '        title.setPlotNumber(request.getPlotNumber());\n        title.setTenure(request.getTenure());\n        title.setBlockRoad(request.getBlockRoad());\n        title.setDistrict(request.getDistrict());\n        title.setCounty(request.getCounty());\n        title.setVolume(request.getVolume());\n        title.setFolio(request.getFolio());\n        title.setInstrumentNo(request.getInstrumentNo());\n        title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());\n        title.setSurveyDate(request.getSurveyDate());'
)

# ============================================================
# 5. RecoveryController.java — pass surveyDate into PlotSummary builder
# ============================================================
patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'modules', 'client', 'controller', 'RecoveryController.java'),
    '                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()\n                        .projectId(plot.getId())\n                        .plotNumber(plot.getLandTitle().getPlotNumber())\n                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())\n                        .isBacklog(plot.isBacklog())\n                        .lastInteractionNote(lastNote)\n                        .paymentHealthBadge(badge)\n                        .lastPaymentDate(lastPaymentStr);',
    '                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()\n                        .projectId(plot.getId())\n                        .plotNumber(plot.getLandTitle().getPlotNumber())\n                        .physicalBoxNumber(plot.getLandTitle().getPhysicalBoxNumber())\n                        .isBacklog(plot.isBacklog())\n                        .lastInteractionNote(lastNote)\n                        .paymentHealthBadge(badge)\n                        .lastPaymentDate(lastPaymentStr)\n                        .surveyDate(plot.getLandTitle().getSurveyDate());'
)

# ============================================================
# 6. DataInitializer.java — add migration for survey_date column
# ============================================================
patch(
    os.path.join(BASE, 'erp-backend', 'src', 'main', 'java', 'com', 'gesolutions', 'erp', 'config', 'DataInitializer.java'),
    '            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",',
    '            "ALTER TABLE land_projects ADD COLUMN IF NOT EXISTS backlog_start_override TIMESTAMP",\n            "ALTER TABLE land_titles ADD COLUMN IF NOT EXISTS survey_date DATE",'
)

# ============================================================
# 7. IntakePage.jsx — add surveyDate state + date input in backlog section
# ============================================================
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx'),
    "    const [monthlyStorageFee, setMonthlyStorageFee] = useState('50000');\n    const [initialStorageFee, setInitialStorageFee] = useState('');",
    "    const [monthlyStorageFee, setMonthlyStorageFee] = useState('50000');\n    const [initialStorageFee, setInitialStorageFee] = useState('');\n    const [surveyDate,        setSurveyDate]        = useState('');"
)

# isDirty: add surveyDate check
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx'),
    "        if (initialStorageFee !== '') return true;\n        if (fileQueue.length > 0) return true;",
    "        if (initialStorageFee !== '') return true;\n        if (surveyDate !== '') return true;\n        if (fileQueue.length > 0) return true;"
)

# handleDuplicatePlot payload — add surveyDate
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx'),
    "                isStartAsBacklog: isBacklog,\n                isLegacy: false,\n                owners: owners.map(o => ({",
    "                isStartAsBacklog: isBacklog,\n                surveyDate: surveyDate || undefined,\n                isLegacy: false,\n                owners: owners.map(o => ({"
)

# handleSubmit payload — add surveyDate (second occurrence, after monthlyStorageFee line)
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx'),
    "                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,\n                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,\n                isLegacy: false, // Always false for new plots - legacy is a historical flag only",
    "                monthlyStorageFee: isBacklog ? (Number(monthlyStorageFee) || 50000) : undefined,\n                initialStorageFee: isBacklog ? (Number(initialStorageFee) || 0) : undefined,\n                surveyDate: surveyDate || undefined,\n                isLegacy: false, // Always false for new plots - legacy is a historical flag only"
)

# Add date input inside backlogFeeConfig section — after backlogFeeConfigTitle
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Intake', 'IntakePage.jsx'),
    "                                    <div className={styles.backlogFeeConfigTitle}>\n                                        BACKLOG FEE CONFIGURATION\n                                    </div>\n                                    <div className={styles.grid2} style={{marginBottom: 0}}>",
    "                                    <div className={styles.backlogFeeConfigTitle}>\n                                        BACKLOG FEE CONFIGURATION\n                                    </div>\n                                    <div className={styles.grid2} style={{marginBottom: 12}}>\n                                        <div className={styles.inputWrap}>\n                                            <div className={styles.labelRow}>\n                                                <label className={styles.fieldLabel}>DATE OF SURVEY</label>\n                                            </div>\n                                            <input\n                                                type=\"date\"\n                                                className={styles.hwInput}\n                                                value={surveyDate}\n                                                onChange={e => setSurveyDate(e.target.value)}\n                                            />\n                                        </div>\n                                    </div>\n                                    <div className={styles.grid2} style={{marginBottom: 0}}>"
)

# ============================================================
# 8. FolderPage.jsx — show/edit surveyDate in Overview tab
# ============================================================
# In buffer initialisation, add surveyDate
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.jsx'),
    "                    physicalBoxNumber: data.project?.landTitle?.physicalBoxNumber || '',\n                    totalCost:         String(data.project?.totalCost             || 0),",
    "                    physicalBoxNumber: data.project?.landTitle?.physicalBoxNumber || '',\n                    surveyDate:        data.project?.landTitle?.surveyDate         || '',\n                    totalCost:         String(data.project?.totalCost             || 0),"
)

# In handleCommit, pass surveyDate (it's already spread via ...buffer so nothing needed)

# In the edit mode inputGrid3 for plot details — add surveyDate after instrumentNo row
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.jsx'),
    "                                    <div className={styles.inputGrid3}>\n                                        <SmartInput label=\"INSTRUMENT NO.\" value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />\n                                        <SmartInput label=\"VOLUME\" value={buffer.volume} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />\n                                        <SmartInput label=\"FOLIO\" value={buffer.folio} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />\n                                    </div>",
    "                                    <div className={styles.inputGrid3}>\n                                        <SmartInput label=\"INSTRUMENT NO.\" value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />\n                                        <SmartInput label=\"VOLUME\" value={buffer.volume} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />\n                                        <SmartInput label=\"FOLIO\" value={buffer.folio} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />\n                                    </div>\n                                    <div className={styles.inputGrid3}>\n                                        <div className={styles.hwInputWrap}>\n                                            <div className={styles.inputLabelRow}><label>DATE OF SURVEY</label></div>\n                                            <input type=\"date\" className={styles.hwInput}\n                                                value={buffer.surveyDate || ''}\n                                                onChange={e => touchedSetBuffer({...buffer, surveyDate: e.target.value})} />\n                                        </div>\n                                    </div>"
)

# In the read-only grid for Overview tab — add SURVEY DATE row
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'DigitalFolder', 'FolderPage.jsx'),
    "                                        ['INSTRUMENT',   project.landTitle.instrumentNo],\n                                    ].map(([l,v],i) => (",
    "                                        ['INSTRUMENT',   project.landTitle.instrumentNo],\n                                        ['SURVEY DATE',  project.landTitle.surveyDate || '---'],\n                                    ].map(([l,v],i) => ("
)

# ============================================================
# 9. RecoveryPortal.jsx — show surveyDate in expanded backlog plot card
# ============================================================
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.jsx'),
    "                                <div className={styles.plotSubCardHeader}>\n                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>\n                                                    <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber || '---'}</span>\n                                                </div>",
    "                                <div className={styles.plotSubCardHeader}>\n                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>\n                                                    <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber || '---'}</span>\n                                                </div>\n                                                {p.isBacklog && p.surveyDate && (\n                                                    <div className={styles.surveyDateRow}>\n                                                        SURVEYED: <strong>{p.surveyDate}</strong>\n                                                    </div>\n                                                )}"
)

# Add surveyDateRow CSS to RecoveryPortal.module.css
patch(
    os.path.join(BASE, 'erp-frontend', 'src', 'pages', 'Recovery', 'RecoveryPortal.module.css'),
    ".plotSubCard:last-child { margin-bottom: 0; }",
    ".plotSubCard:last-child { margin-bottom: 0; }\n\n.surveyDateRow {\n    font-family: 'DM Sans', sans-serif;\n    font-size: clamp(8px, 0.85vw, 10px);\n    font-weight: 800;\n    color: rgba(255, 255, 255, 0.4);\n    text-transform: uppercase;\n    letter-spacing: 1px;\n    margin-bottom: clamp(8px, 1vw, 11px);\n    display: flex;\n    align-items: center;\n    gap: 6px;\n}\n.surveyDateRow strong {\n    font-family: 'Space Mono', monospace;\n    font-weight: 900;\n    color: rgba(255, 255, 255, 0.75);\n    font-size: clamp(9px, 0.9vw, 11px);\n    letter-spacing: 0.5px;\n}"
)

print("\n=== ALL DONE ===")