#!/usr/bin/env python3
import os
import subprocess

def patch_file(path, old, new):
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        return
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    if old not in content:
        print(f"MISSING in {path}: {old[:50]}...")
        return
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

# 1. ProjectResponse.java
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/ProjectResponse.java",
    "    private UUID projectId;\n    private String plotNumber;\n    private String physicalBoxNumber;",
    "    private UUID projectId;\n    private String plotNumber;\n    private String titleStatus;\n    private String subCounty;\n    private String parish;\n    private String village;\n    private String titleId;"
)

# 2. LandService.java (updateProjectFull)
patch_file(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java",
    """        // PHASE B (Section 18.9.1): landTitle can now be null (a
        // titleless "folder" stage project). Skip the title-field
        // setters entirely when there is no title yet -- everything
        // else on this project (owners, cost, legacy flag) still
        // updates normally below. Real create-a-title-on-edit logic
        // is Phase D/E's job, not this phase's.
        if (title != null) {
            title.setPlotNumber(request.getPlotNumber());
            title.setTenure(request.getTenure());
            title.setBlockRoad(request.getBlockRoad());
            title.setDistrict(request.getDistrict());
            title.setCounty(request.getCounty());
            title.setVolume(request.getVolume());
            title.setFolio(request.getFolio());
            title.setInstrumentNo(request.getInstrumentNo());
            title.setPhysicalBoxNumber(request.getPhysicalBoxNumber());
            title.setSurveyDate(request.getSurveyDate());
        }""",
    """        // PHASE E (Section 18.9.4): Create LandTitle on edit if title fields
        // are provided but no title exists yet. Otherwise update existing title.
        boolean hasTitleFields = request.getPlotNumber() != null && !request.getPlotNumber().isBlank();
        if (title == null && hasTitleFields) {
            title = LandTitle.builder()
                    .titleId(request.getTitleId())
                    .tenure(request.getTenure() != null && !request.getTenure().isBlank() ? request.getTenure() : "FREEHOLD")
                    .plotNumber(request.getPlotNumber())
                    .blockRoad(request.getBlockRoad())
                    .district(request.getDistrict())
                    .county(request.getCounty())
                    .volume(request.getVolume())
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
        }

        // Save location fields on LandProject (Phase A/E)
        project.setDistrict(request.getDistrict());
        project.setCounty(request.getCounty());
        project.setSubCounty(request.getSubCounty());
        project.setParish(request.getParish());
        project.setVillage(request.getVillage());
        project.setArea(request.getArea());"""
)

# 3. FolderPage.jsx - Header
patch_file(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """<header className={styles.terminalHeader}>
<div className={styles.idPlate}>
<h1>{project.landTitle.plotNumber}</h1>
<div className={styles.metaLine}>
{project.landTitle?.projectIndex && (
<span className={`${styles.metaTag} ${styles.tagBlue}`}>
PROJECT #{project.landTitle.projectIndex}
</span>
)}""",
    """<header className={styles.terminalHeader}>
<div className={styles.idPlate}>
<h1>{project.landTitle?.plotNumber || project.projectIndex || 'UNREGISTERED PLOT'}</h1>
<div className={styles.metaLine}>
{(project.projectIndex || project.landTitle?.projectIndex) && (
<span className={`${styles.metaTag} ${styles.tagBlue}`}>
PROJECT #{project.projectIndex || project.landTitle?.projectIndex}
</span>
)}
<span className={styles.metaTag} style={{ background: project.landTitle ? 'rgba(139,92,246,0.2)' : 'rgba(238,140,58,0.2)', color: project.landTitle ? '#a78bfa' : '#EE8C3A', borderColor: project.landTitle ? 'rgba(139,92,246,0.4)' : 'rgba(238,140,58,0.4)' }}>
{project.landTitle ? 'TITLED' : 'FOLDER'}
</span>"""
)

# 4. FolderPage.jsx - Buffer initialization
patch_file(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """                    plotNumber:        data.project?.landTitle?.plotNumber        || '',
                    tenure:            data.project?.landTitle?.tenure            || 'MAILO',
                    blockRoad:         data.project?.landTitle?.blockRoad         || '',
                    district:          data.project?.landTitle?.district          || '',
                    county:            data.project?.landTitle?.county            || '',
                    volume:            data.project?.landTitle?.volume            || '',
                    folio:             data.project?.landTitle?.folio             || '',
                    instrumentNo:      data.project?.landTitle?.instrumentNo      || '',
                    surveyDate:        data.project?.landTitle?.surveyDate         || '',""",
    """                    plotNumber:        data.project?.landTitle?.plotNumber        || '',
                    tenure:            data.project?.landTitle?.tenure            || 'MAILO',
                    blockRoad:         data.project?.landTitle?.blockRoad         || '',
                    district:          data.project?.district                     || '',
                    county:            data.project?.county                       || '',
                    subCounty:         data.project?.subCounty                    || '',
                    parish:            data.project?.parish                       || '',
                    village:           data.project?.village                      || '',
                    area:              data.project?.area                         || '',
                    volume:            data.project?.landTitle?.volume            || '',
                    folio:             data.project?.landTitle?.folio             || '',
                    instrumentNo:      data.project?.landTitle?.instrumentNo      || '',
                    surveyDate:        data.project?.landTitle?.surveyDate         || '',
                    titleId:           data.project?.landTitle?.titleId           || '',"""
)

# 5. FolderPage.jsx - OVERVIEW tab body
patch_file(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """                            {isEditing ? (
                                <>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                        <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\D/g,'')})} />
                                        <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\D/g,'')})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <div className={styles.hwInputWrap}>
                                            <div className={styles.inputLabelRow}><label>DATE OF SURVEY</label></div>
                                            <input type="date" className={styles.hwInput}
                                                value={buffer.surveyDate || ''}
                                                onChange={e => touchedSetBuffer({...buffer, surveyDate: e.target.value})} />
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className={styles.readOnlyGrid}>
                                    {[
                                        ['PLOT ID',      project.landTitle.plotNumber],
                                        ['TENURE',       project.landTitle.tenure],
                                        ['DISTRICT',     project.landTitle.district],
                                        ['COUNTY',       project.landTitle.county],
                                        ['BLOCK / ROAD', project.landTitle.blockRoad],
                                        ['VOLUME',       project.landTitle.volume],
                                        ['FOLIO',        project.landTitle.folio],
                                        ['INSTRUMENT',   project.landTitle.instrumentNo],
                                        ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
                                    ].map(([l,v],i) => (
                                        <div key={i} className={styles.specItem}>
                                            <span className={styles.specLabel}>{l}</span>
                                            <span className={styles.specValue}>{v || '---'}</span>
                                        </div>
                                    ))}
                                </div>
                            )}""",
    """                            {isEditing ? (
                                <>
                                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 4 }}>LOCATION (Always visible)</div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="DISTRICT" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />
                                        <SmartInput label="COUNTY" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />
                                        <SmartInput label="SUB-COUNTY" value={buffer.subCounty} showCaps onChange={e => touchedSetBuffer({...buffer, subCounty: e.target.value.toUpperCase()})} />
                                    </div>
                                    <div className={styles.inputGrid3}>
                                        <SmartInput label="PARISH" value={buffer.parish} showCaps onChange={e => touchedSetBuffer({...buffer, parish: e.target.value.toUpperCase()})} />
                                        <SmartInput label="VILLAGE" value={buffer.village} showCaps onChange={e => touchedSetBuffer({...buffer, village: e.target.value.toUpperCase()})} />
                                        <SmartInput label="AREA" value={buffer.area} onChange={e => touchedSetBuffer({...buffer, area: e.target.value})} />
                                    </div>
                                    {project.landTitle && (
                                        <>
                                            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 16, borderTop: '1px solid rgba(139,92,246,0.3)', paddingTop: 12 }}>TITLE & PLOT DETAILS</div>
                                            <div className={styles.inputGrid3}>
                                                <SmartInput ref={firstInputRef} label="PLOT ID" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />
                                                <SmartSelect label="TENURE" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />
                                                <SmartInput label="TITLE ID" value={buffer.titleId} showCaps onChange={e => touchedSetBuffer({...buffer, titleId: e.target.value.toUpperCase()})} />
                                            </div>
                                            <div className={styles.inputGrid3}>
                                                <SmartInput label="BLOCK / ROAD" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />
                                                <SmartInput label="INSTRUMENT NO." value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />
                                                <SmartInput label="VOLUME" value={buffer.volume} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\D/g,'')})} />
                                            </div>
                                            <div className={styles.inputGrid3}>
                                                <SmartInput label="FOLIO" value={buffer.folio} inputMode="numeric" hint="Numbers only" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\D/g,'')})} />
                                                <div className={styles.hwInputWrap}>
                                                    <div className={styles.inputLabelRow}><label>DATE OF SURVEY</label></div>
                                                    <input type="date" className={styles.hwInput}
                                                        value={buffer.surveyDate || ''}
                                                        onChange={e => touchedSetBuffer({...buffer, surveyDate: e.target.value})} />
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </>
                            ) : (
                                <>
                                    <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 4 }}>LOCATION</div>
                                    <div className={styles.readOnlyGrid}>
                                        {[
                                            ['DISTRICT',     project.district],
                                            ['COUNTY',       project.county],
                                            ['SUB-COUNTY',   project.subCounty],
                                            ['PARISH',       project.parish],
                                            ['VILLAGE',      project.village],
                                            ['AREA',         project.area],
                                        ].map(([l,v],i) => (
                                            <div key={i} className={styles.specItem}>
                                                <span className={styles.specLabel}>{l}</span>
                                                <span className={styles.specValue}>{v || '---'}</span>
                                            </div>
                                        ))}
                                    </div>
                                    {project.landTitle && (
                                        <>
                                            <div style={{ fontFamily: "'DM Sans',sans-serif", fontSize: 10, fontWeight: 900, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8, marginTop: 16, borderTop: '1px solid rgba(139,92,246,0.3)', paddingTop: 12 }}>TITLE & PLOT DETAILS</div>
                                            <div className={styles.readOnlyGrid}>
                                                {[
                                                    ['PLOT ID',      project.landTitle.plotNumber],
                                                    ['TENURE',       project.landTitle.tenure],
                                                    ['TITLE ID',     project.landTitle.titleId],
                                                    ['BLOCK / ROAD', project.landTitle.blockRoad],
                                                    ['VOLUME',       project.landTitle.volume],
                                                    ['FOLIO',        project.landTitle.folio],
                                                    ['INSTRUMENT',   project.landTitle.instrumentNo],
                                                    ['SURVEY DATE',  project.landTitle.surveyDate || '---'],
                                                ].map(([l,v],i) => (
                                                    <div key={i} className={styles.specItem}>
                                                        <span className={styles.specLabel}>{l}</span>
                                                        <span className={styles.specValue}>{v || '---'}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </>
                                    )}
                                </>
                            )}"""
)

# Git commit and push
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'Phase E: Folder page additive display + status tag + ProjectResponse update'])
subprocess.run(['git', 'push'])