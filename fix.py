import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    count = content.count(old)
    if count == 1:
        content = content.replace(old, new)
        write(path, content)
        print('OK: ' + label)
    elif count == 0:
        print('MISSING (not found): ' + label)
    else:
        print('MISSING (found ' + str(count) + ' times, expected 1): ' + label)

def remove_file(path, label):
    if os.path.exists(path):
        os.remove(path)
        print('OK (deleted): ' + label)
    else:
        print('MISSING (already gone): ' + label)


# ============================================================
# FIX 1 + 4: FolderPage.jsx -- crash on titleless projects,
# plus the missing FOLDER/TITLED status tag (Section 18.9.4)
# ============================================================

FP = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

patch(FP,
'''                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT ID:</strong> {project.landTitle.plotNumber}</span>
                    <span><strong>TENURE:</strong> {project.landTitle.tenure}</span>
                    {project.landTitle.district && <span><strong>DISTRICT:</strong> {project.landTitle.district}</span>}
                    <span><strong>STATUS:</strong> {project.status}</span>''',
'''                <div className={styles.printDossierMeta}>
                    <span><strong>PLOT ID:</strong> {project.landTitle?.plotNumber || project.projectIndex}</span>
                    {project.landTitle?.tenure && <span><strong>TENURE:</strong> {project.landTitle.tenure}</span>}
                    {project.district && <span><strong>DISTRICT:</strong> {project.district}</span>}
                    <span><strong>STATUS:</strong> {project.status}</span>''',
'FolderPage.jsx print-dossier header no longer crashes on a titleless project')

patch(FP,
'''            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle.plotNumber}</h1>
                    <div className={styles.metaLine}>
                        {project.landTitle?.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.landTitle.projectIndex}
                            </span>
                        )}''',
'''            <header className={styles.terminalHeader}>
                <div className={styles.idPlate}>
                    <h1>{project.landTitle?.plotNumber || project.projectIndex || 'UNTITLED'}</h1>
                    <div className={styles.metaLine}>
                        {project.projectIndex && (
                            <span className={`${styles.metaTag} ${styles.tagBlue}`}>
                                PROJECT #{project.projectIndex}
                            </span>
                        )}
                        <span className={`${styles.metaTag} ${project.landTitle ? styles.tagGreen : styles.tagOrange}`}>
                            {project.landTitle ? 'TITLED' : 'FOLDER'}
                        </span>''',
'FolderPage.jsx terminal header no longer crashes, plus adds the FOLDER/TITLED status tag')


# ============================================================
# FIX 5: physicalBoxNumber -- restore the field that Phase D
# accidentally deleted (it was confused with the new titleId
# field). Now optional, same bucket as volume/folio/instrumentNo.
# ============================================================

patch(FP,
'''                    titleId:           data.project?.landTitle?.titleId           || '',
                    totalCost:         String(data.project?.totalCost             || 0),''',
'''                    titleId:           data.project?.landTitle?.titleId           || '',
                    physicalBoxNumber: data.project?.landTitle?.physicalBoxNumber || '',
                    totalCost:         String(data.project?.totalCost             || 0),''',
'FolderPage.jsx edit buffer: restore physicalBoxNumber')

patch(FP,
'''                                            <div className={styles.inputGrid3}>
                                                <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>DATE OF SURVEY</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        value={buffer.surveyDate || ''}
                                                        onChange={e => touchedSetBuffer({...buffer, surveyDate: e.target.value})} />
                                                </div>
                                            </div>''',
'''                                            <div className={styles.inputGrid3}>
                                                <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>DATE OF SURVEY</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        value={buffer.surveyDate || ''}
                                                        onChange={e => touchedSetBuffer({...buffer, surveyDate: e.target.value})} />
                                                </div>
                                                <SmartInput label="BOX NUMBER" value={buffer.physicalBoxNumber} showCaps onChange={e => touchedSetBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />
                                            </div>''',
'FolderPage.jsx edit form: restore physicalBoxNumber input field')

patch(FP,
'''                                                    ['INSTRUMENT',   project.landTitle.instrumentNo],
                                                    ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
                                                ].map(([l,v],i) => (''',
'''                                                    ['INSTRUMENT',   project.landTitle.instrumentNo],
                                                    ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
                                                    ['BOX NUMBER',   project.landTitle.physicalBoxNumber || '---'],
                                                ].map(([l,v],i) => (''',
'FolderPage.jsx read-only details table: restore BOX NUMBER row')


# ============================================================
# FIX 2 + 4: LedgerPage.jsx -- search/display were still reading
# projectIndex/district/county off the deprecated LandTitle
# location instead of LandProject, breaking search and display
# for every folder-only project. Also adds the missing status tag.
# ============================================================

LP = 'erp-frontend/src/pages/Ledger/LedgerPage.jsx'

patch(LP,
'''    const fields = [
        proj.landTitle?.plotNumber,
        proj.landTitle?.projectIndex,
        proj.landTitle?.district,
        proj.landTitle?.county,
        proj.landTitle?.blockRoad,
        proj.landTitle?.tenure,''',
'''    const fields = [
        proj.landTitle?.plotNumber,
        proj.projectIndex,
        proj.district,
        proj.county,
        proj.landTitle?.blockRoad,
        proj.landTitle?.tenure,
        proj.landTitle?.titleId,''',
'LedgerPage.jsx search: read projectIndex/district/county from LandProject, not the deprecated LandTitle copy')

patch(LP,
'''                                        aria-label={`Record: ${proj.landTitle?.plotNumber}`}''',
'''                                        aria-label={`Record: ${proj.landTitle?.plotNumber || proj.projectIndex}`}''',
'LedgerPage.jsx row aria-label: fall back to projectIndex for folder-only rows')

patch(LP,
'''                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || '---'}</strong>
                                                    {proj.landTitle?.projectIndex && (
                                                        <span className={styles.districtTag}> #{proj.landTitle.projectIndex}</span>
                                                    )}
                                                    <div>
                                                        {proj.landTitle?.tenure && (
                                                            <span className={styles.tenureTag}>{proj.landTitle.tenure}</span>
                                                        )}
                                                        {proj.landTitle?.district && (
                                                            <span className={styles.districtTag}>{proj.landTitle.district}</span>
                                                        )}
                                                    </div>
                                                </div>''',
'''                                                <div>
                                                    <strong>{proj.landTitle?.plotNumber || proj.projectIndex || '---'}</strong>
                                                    {proj.projectIndex && (
                                                        <span className={styles.districtTag}> #{proj.projectIndex}</span>
                                                    )}
                                                    <div>
                                                        <span className={proj.landTitle ? styles.tagPaid : styles.tagStandard}>
                                                            {proj.landTitle ? 'TITLED' : 'FOLDER'}
                                                        </span>
                                                        {proj.landTitle?.tenure && (
                                                            <span className={styles.tenureTag}>{proj.landTitle.tenure}</span>
                                                        )}
                                                        {proj.district && (
                                                            <span className={styles.districtTag}>{proj.district}</span>
                                                        )}
                                                    </div>
                                                </div>''',
'LedgerPage.jsx row display: fix broken data source for folder-only rows + add FOLDER/TITLED status tag')


# ============================================================
# FIX 3: IntakePage.jsx -- Area could pass validation but never
# actually get saved, because the form validated one state
# variable (titleArea) but sent a different one (area) to the
# server. Fix: collapse to a single "area" value used throughout,
# matching Section 18.4/18.9 (area lives ONLY on LandProject,
# never duplicated).
# ============================================================

IP = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

patch(IP,
'''    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');
    const [titleArea, setTitleArea] = useState('');''',
'''    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');''',
'IntakePage.jsx: remove the duplicate titleArea state that could silently lose the entered value')

patch(IP,
'''    useEffect(() => {
        if (area) setTitleArea(area);
    }, [area]);

''',
'',
'IntakePage.jsx: remove the now-unnecessary one-way area->titleArea sync effect')

patch(IP,
'''            if (!titleArea.trim()) { toast('Area is required for Title details.', 'error'); return; }''',
'''            if (!area.trim()) { toast('Area is required for Title details.', 'error'); return; }''',
'IntakePage.jsx: validate the real area value that actually gets saved')

patch(IP,
'''                            <label className={`${styles.label} ${styles.required}`}>Area</label>
                            <input className={styles.input} value={titleArea} onChange={e => setTitleArea(e.target.value)} />''',
'''                            <label className={`${styles.label} ${styles.required}`}>Area</label>
                            <input className={styles.input} value={area} onChange={e => setArea(e.target.value)} />''',
'IntakePage.jsx: Section 5 Area input now edits the one true area value, not a throwaway copy')


# ============================================================
# FIX 5 (backend side): physicalBoxNumber restore
# ============================================================

LT = 'erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/LandTitle.java'

patch(LT,
'''@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id")
})''',
'''@Table(name = "land_titles", indexes = {
    @Index(name = "idx_plot_registry", columnList = "plot_number"),
    @Index(name = "idx_title_id", columnList = "title_id"),
    @Index(name = "idx_physical_archive", columnList = "physical_box_number")
})''',
'LandTitle.java: restore physical_box_number index')

patch(LT,
'''    @Column(name = "block_road", length = 100)
    private String blockRoad;''',
'''    @Column(name = "block_road", length = 100)
    private String blockRoad;

    /**
     * PHYSICAL ARCHIVE LOGISTICS
     * Which physical box in the office holds this title's paperwork.
     * Restored after being accidentally deleted in Phase D -- previously
     * mandatory, now OPTIONAL, since a folder-only project has no title
     * yet and therefore nothing physical to file. Set once the physical
     * document actually arrives, same bucket as volume/folio/instrumentNo.
     */
    @Column(name = "physical_box_number", length = 100)
    private String physicalBoxNumber;''',
'LandTitle.java: restore physicalBoxNumber field')

LER = 'erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java'

patch(LER,
'''    private String volume;
    private String folio;
    private String instrumentNo;''',
'''    private String volume;
    private String folio;
    private String instrumentNo;
    private String physicalBoxNumber;''',
'LandEntryRequest.java: restore physicalBoxNumber field')

LS = 'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java'

patch(LS,
'''                    .volume(request.getVolume())
                    .folio(request.getFolio())
                    .instrumentNo(request.getInstrumentNo())
                    .surveyDate(request.getSurveyDate())
                    // Kept in sync on the deprecated LandTitle column too,''',
'''                    .volume(request.getVolume())
                    .folio(request.getFolio())
                    .instrumentNo(request.getInstrumentNo())
                    .surveyDate(request.getSurveyDate())
                    .physicalBoxNumber(request.getPhysicalBoxNumber())
                    // Kept in sync on the deprecated LandTitle column too,''',
'LandService.java atomicIntake(): restore physicalBoxNumber on new-title creation')

patch(LS,
'''                    .volume(request.getVolume())
                    .folio(request.getFolio())
                    .instrumentNo(request.getInstrumentNo())
                    .surveyDate(request.getSurveyDate())
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : java.time.LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
            project.setLandTitle(title);
        } else if (title != null) {
            title.setTitleId(request.getTitleId());
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlockRoad(request.getBlockRoad());
            title.setDistrict(request.getDistrict());
            title.setCounty(request.getCounty());
            title.setVolume(request.getVolume());
            title.setFolio(request.getFolio());
            title.setInstrumentNo(request.getInstrumentNo());
            title.setSurveyDate(request.getSurveyDate());
        }''',
'''                    .volume(request.getVolume())
                    .folio(request.getFolio())
                    .instrumentNo(request.getInstrumentNo())
                    .surveyDate(request.getSurveyDate())
                    .physicalBoxNumber(request.getPhysicalBoxNumber())
                    .projectStartDate(request.getProjectStartDate() != null ? request.getProjectStartDate() : java.time.LocalDate.now())
                    .titleIssueDate(request.getTitleIssueDate())
                    .build();
            project.setLandTitle(title);
        } else if (title != null) {
            title.setTitleId(request.getTitleId());
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlockRoad(request.getBlockRoad());
            title.setDistrict(request.getDistrict());
            title.setCounty(request.getCounty());
            title.setVolume(request.getVolume());
            title.setFolio(request.getFolio());
            title.setInstrumentNo(request.getInstrumentNo());
            title.setSurveyDate(request.getSurveyDate());
            title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());
        }''',
'LandService.java updateProjectFull(): restore physicalBoxNumber on both create-on-edit and update paths')


# ============================================================
# FIX 6 (bonus, found during this same audit): RecoveryController
# builds a PlotSummary by calling plot.getLandTitle().getPlotNumber()
# and .getSurveyDate() with NO null check -- this will throw a
# NullPointerException (500 error, page fails to load) the moment a
# folder-only project with recovery activity shows up in the
# Recovery Portal. Not caused by Phase D -- this became reachable
# the moment Phase A made landTitle nullable, and nobody had
# audited RecoveryController for it until now.
# ============================================================

RC = 'erp-backend/src/main/java/com/gesolutions/erp/modules/client/controller/RecoveryController.java'

patch(RC,
'''                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()
                        .projectId(plot.getId())
                        .plotNumber(plot.getLandTitle().getPlotNumber())
                        .isReceivable(plot.isReceivable())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr)
                        .surveyDate(plot.getLandTitle().getSurveyDate())
                        .ownershipType(ownershipType)''',
'''                RecoveryTaskDTO.PlotSummary.PlotSummaryBuilder summaryBuilder = RecoveryTaskDTO.PlotSummary.builder()
                        .projectId(plot.getId())
                        .plotNumber(plot.getLandTitle() != null ? plot.getLandTitle().getPlotNumber() : plot.getProjectIndex())
                        .physicalBoxNumber(plot.getLandTitle() != null ? plot.getLandTitle().getPhysicalBoxNumber() : null)
                        .isReceivable(plot.isReceivable())
                        .lastInteractionNote(lastNote)
                        .paymentHealthBadge(badge)
                        .lastPaymentDate(lastPaymentStr)
                        .surveyDate(plot.getLandTitle() != null ? plot.getLandTitle().getSurveyDate() : null)
                        .ownershipType(ownershipType)''',
'RecoveryController.java: null-guard landTitle access (was an unguarded NPE risk for folder-only projects) + restore physicalBoxNumber')

RTD = 'erp-backend/src/main/java/com/gesolutions/erp/modules/client/dto/RecoveryTaskDTO.java'

patch(RTD,
'''    public static class PlotSummary {
        private UUID projectId;
        private String plotNumber;
        private boolean isReceivable;''',
'''    public static class PlotSummary {
        private UUID projectId;
        private String plotNumber;
        private String physicalBoxNumber;
        private boolean isReceivable;''',
'RecoveryTaskDTO.java: restore physicalBoxNumber field')

RP = 'erp-frontend/src/pages/Recovery/RecoveryPortal.jsx'

patch(RP,
'''                                                <div className={styles.plotSubCardHeader}>
                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>
                                                </div>''',
'''                                                <div className={styles.plotSubCardHeader}>
                                                    <strong className={styles.plotSubCardTitle}>{p.plotNumber}</strong>
                                                    {p.physicalBoxNumber && <span className={styles.plotSubCardBox}>BOX: {p.physicalBoxNumber}</span>}
                                                </div>''',
'RecoveryPortal.jsx: restore physicalBoxNumber display')


# ============================================================
# FIX 7: ProjectResponse.java is dead code -- it was updated in
# Phases D and E but nothing in the backend actually constructs
# or returns it (the real /ledger endpoint returns Page<LandProject>
# directly). Deleting it rather than leaving unused, misleading
# code behind.
# ============================================================

remove_file(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectResponse.java',
    'ProjectResponse.java: removed dead/unused DTO')


# ============================================================
# Commit and push automatically -- PERMANENT RULE, Section 3
# ============================================================

import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m',
    'Phase G: fix audit findings -- FolderPage/Recovery crash on titleless '
    'projects, Ledger search/display reading stale LandTitle location, '
    'Intake area data-loss bug, restore accidentally-deleted physicalBoxNumber, '
    'add missing Folder/Titled status tag, remove dead ProjectResponse.java'])
subprocess.run(['git', 'push'])