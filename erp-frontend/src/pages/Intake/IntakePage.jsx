// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiLock, FiEdit3, FiBookmark, FiX
} from 'react-icons/fi';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const PROJECT_TYPES = [
    { value: 'NEW_FOLDER',    label: 'New Folder',    icon: <FiFolderPlus aria-hidden="true" />, hint: 'No title yet -- opens a working folder' },
    { value: 'NEW_TITLE',     label: 'New Title',     icon: <FiFilePlus   aria-hidden="true" />,  hint: 'Title details are captured now' },
    { value: 'LEGACY_TITLE',  label: 'Legacy Title',  icon: <FiArchive    aria-hidden="true" />,  hint: 'Existing title being onboarded as a receivable' },
];

const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';

const loadPresets = () => {
    try {
        const raw = localStorage.getItem(PRESET_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
};

const savePresets = (presets) => {
    try { localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(presets)); } catch { /* no-op */ }
};

export default function IntakePage() {
    const navigate = useNavigate();
    const [saving, setSaving] = useState(false);
    const [projectIndex] = useState('');
    const [projectType, setProjectType] = useState('NEW_FOLDER');

    const [owners, setOwners] = useState([EMPTY_OWNER()]);

    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    const [templates, setTemplates] = useState([]);
    const [checkedStages, setCheckedStages] = useState({});
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [newStageCost, setNewStageCost] = useState('');

    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');

    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState(0);

    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');

    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type='info') => {
        const id = Date.now();
        setToasts(p => [...p, {id, msg, type}]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    const fetchTemplates = useCallback(() => {
        stageTemplateService.getTemplate().then(t => setTemplates(t || [])).catch(() => {});
    }, []);

    useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

    const sortedTemplates = useMemo(
        () => [...templates].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0)),
        [templates]
    );
    const firstStageId = sortedTemplates[0]?.id;
    const lastStageId = sortedTemplates[sortedTemplates.length - 1]?.id;

    // First and last stage are always part of the checklist and can't be
    // unchecked -- every project starts with the first stage and can't be
    // considered done until the last one. New/other stages default to
    // unchecked unless a preset or the Legacy type turns them all on.
    useEffect(() => {
        if (!sortedTemplates.length) return;
        setCheckedStages(prev => {
            const next = { ...prev };
            if (firstStageId && next[firstStageId] === undefined) next[firstStageId] = true;
            if (lastStageId && next[lastStageId] === undefined) next[lastStageId] = true;
            return next;
        });
    }, [sortedTemplates.length, firstStageId, lastStageId]);

    const finalStageChecked = lastStageId ? !!checkedStages[lastStageId] : false;
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleSectionVisible = isLegacy || titleAtIntake || finalStageChecked;

    const handleProjectTypeChange = (value) => {
        setProjectType(value);
        if (value === 'LEGACY_TITLE') {
            // Legacy onboarding: the record is already fully processed, so
            // every stage in the checklist is complete from day one.
            const allChecked = {};
            sortedTemplates.forEach(t => { allChecked[t.id] = true; });
            setCheckedStages(allChecked);
        }
    };

    const toggleStage = (id) => {
        if (id === firstStageId || id === lastStageId) return; // locked
        setCheckedStages(p => ({ ...p, [id]: !p[id] }));
    };

    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            const last = sortedTemplates[sortedTemplates.length - 1];
            // Insert the new stage just before the last (locked) stage,
            // pushing the last stage's position down by one so it stays last.
            const lastOrder = last?.displayOrder ?? sortedTemplates.length;
            if (last) {
                await stageTemplateService.updateTemplateStage(
                    last.id, last.stageName, last.defaultCost, lastOrder + 1
                );
            }
            const created = await stageTemplateService.addTemplateStage(
                newStageName.trim(),
                newStageCost ? Number(newStageCost) : 0,
                last ? lastOrder : undefined,
            );
            setNewStageName('');
            setNewStageCost('');
            setAddingStage(false);
            fetchTemplates();
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage added to checklist.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
        }
    };

    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const stageNames = sortedTemplates
            .filter(t => checkedStages[t.id])
            .map(t => t.stageName);
        const next = [...presets.filter(p => p.name !== presetName.trim()), { name: presetName.trim(), stageNames }];
        setPresets(next);
        savePresets(next);
        setPresetName('');
        setShowSavePreset(false);
        toast('Stage preset saved.', 'success');
    };

    const applyPreset = (name) => {
        if (!name) return;
        const preset = presets.find(p => p.name === name);
        if (!preset) return;
        const next = {};
        sortedTemplates.forEach(t => {
            next[t.id] = t.id === firstStageId || t.id === lastStageId || preset.stageNames.includes(t.stageName);
        });
        setCheckedStages(next);
    };

    const deletePreset = (name) => {
        const next = presets.filter(p => p.name !== name);
        setPresets(next);
        savePresets(next);
    };

    const updateOwner = (idx, field, val) => {
        setOwners(p => p.map((o, i) => i === idx ? {...o, [field]: val} : o));
    };

    const handleFileUpload = (e) => {
        const files = Array.from(e.target.files);
        setFileQueue(p => [...p, ...files]);
    };

    const handleSubmit = async () => {
        if (!district.trim() || !county.trim()) {
            toast('District and County are required.', 'error'); return;
        }
        for (let o of owners) {
            if (!o.nationalId.trim()) {
                toast('NIN is required for all owners.', 'error'); return;
            }
        }
        if (isTitleSectionVisible) {
            if (!plotNumber.trim()) { toast('Plot Number is required for a title record.', 'error'); return; }
            if (!area.trim()) { toast('Area is required for Title details.', 'error'); return; }
        }

        setSaving(true);
        try {
            const payload = {
                district: district.trim().toUpperCase(),
                county: county.trim().toUpperCase(),
                subCounty: subCounty.trim().toUpperCase(),
                parish: parish.trim().toUpperCase(),
                village: village.trim().toUpperCase(),
                area: area.trim(),
                totalCost: Number(totalCost) || 0,
                initialPayment: Number(initialPayment) || 0,
                isLegacy: isLegacy,
                titleAtIntake: titleAtIntake,
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(),
                    phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address: o.address.trim(),
                })),
                selectedStages: Object.entries(checkedStages).filter(([, v]) => v).map(([id]) => {
                    const t = templates.find(x => x.id === id);
                    return {
                        stageTemplateId: id,
                        stageName: t ? t.stageName : '',
                        isCustom: false,
                        isCompleted: true
                    };
                }),
                notes: notes.trim() ? [{ content: notes.trim() }] : [],
            };

            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
            }

            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.monthlyStorageFee = Number(monthlyStorageFee) || 0;
            }

            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Project registered successfully!', 'success');
            setTimeout(() => navigate('/land/projects'), 1500);
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
        } finally {
            setSaving(false);
        }
    };

    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));

    // Section numbers shift depending on whether Title Details is showing.
    let n = 0;
    const nIndex = ++n;
    const nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n;
    const nStages = ++n;
    const nFinancials = ++n;
    const nDocuments = ++n;
    const nNotes = ++n;

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button className={styles.btn} onClick={() => navigate(-1)}>Cancel</button>
                    <button className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> {saving ? 'Saving...' : 'Save Project'}
                    </button>
                </div>
            </header>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiHash /> {nIndex}. Project Index &amp; Type</h2>
                <div className={styles.field}>
                    <label className={styles.label}>Project Index</label>
                    <input className={styles.input} value={projectIndex || 'Auto-generated on save'} disabled />
                </div>
                <div className={styles.field}>
                    <label className={`${styles.label} ${styles.required}`}>Project Type</label>
                    <div className={styles.typeGroup}>
                        {PROJECT_TYPES.map(pt => (
                            <button
                                key={pt.value}
                                type="button"
                                className={`${styles.typeBtn} ${projectType === pt.value ? styles.typeBtnActive : ''}`}
                                onClick={() => handleProjectTypeChange(pt.value)}
                            >
                                {pt.icon}
                                <span>{pt.label}</span>
                            </button>
                        ))}
                    </div>
                    <p className={styles.typeHint}>{PROJECT_TYPES.find(pt => pt.value === projectType)?.hint}</p>
                </div>
            </section>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiUsers /> {nOwners}. Owners</h2>
                {owners.map((o, idx) => (
                    <div key={idx} className={styles.ownerRow}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>NIN</label>
                            <input className={styles.input} value={o.nationalId} onChange={e => updateOwner(idx, 'nationalId', e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                            <input className={styles.input} value={o.fullName} onChange={e => updateOwner(idx, 'fullName', e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Phone</label>
                            <input className={styles.input} value={o.phone} onChange={e => updateOwner(idx, 'phone', e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Email</label>
                            <input className={styles.input} value={o.email} onChange={e => updateOwner(idx, 'email', e.target.value)} />
                        </div>
                        <button className={styles.btn} onClick={() => setOwners(p => p.filter((_, i) => i !== idx))} disabled={owners.length === 1}>
                            <FiTrash2 />
                        </button>
                    </div>
                ))}
                <button className={styles.btn} onClick={() => setOwners(p => [...p, EMPTY_OWNER()])}>
                    <FiPlus /> Add joint owner
                </button>
            </section>

            {isTitleSectionVisible && (
                <section className={styles.section} style={{border: '2px solid var(--orange)'}}>
                    <h2 className={styles.sectionTitle}><FiFileText /> {nTitle}. Title &amp; Plot Details</h2>
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={styles.label}>Title ID</label>
                            <input className={styles.input} value={titleId} onChange={e => setTitleId(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Tenure</label>
                            <select className={styles.select} value={tenure} onChange={e => setTenure(e.target.value)}>
                                <option value="FREEHOLD">FREEHOLD</option>
                                <option value="MAILO">MAILO</option>
                                <option value="LEASEHOLD">LEASEHOLD</option>
                                <option value="CUSTOMARY">CUSTOMARY</option>
                            </select>
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                            <input className={styles.input} value={plotNumber} onChange={e => setPlotNumber(e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Block</label>
                            <input className={styles.input} value={blockRoad} onChange={e => setBlockRoad(e.target.value)} />
                        </div>
                    </div>
                </section>
            )}

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiMap /> {nLocation}. Location</h2>
                <div className={styles.grid3}>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>District</label>
                        <input className={styles.input} value={district} onChange={e => setDistrict(e.target.value)} />
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>County</label>
                        <input className={styles.input} value={county} onChange={e => setCounty(e.target.value)} />
                    </div>
                    <div className={styles.field}>
                        <label className={styles.label}>Sub-county</label>
                        <input className={styles.input} value={subCounty} onChange={e => setSubCounty(e.target.value)} />
                    </div>
                    <div className={styles.field}>
                        <label className={styles.label}>Parish</label>
                        <input className={styles.input} value={parish} onChange={e => setParish(e.target.value)} />
                    </div>
                    <div className={styles.field}>
                        <label className={styles.label}>Village</label>
                        <input className={styles.input} value={village} onChange={e => setVillage(e.target.value)} />
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${isTitleSectionVisible ? styles.required : ''}`}>Area{!isTitleSectionVisible ? ' (Optional)' : ''}</label>
                        <input className={styles.input} value={area} onChange={e => setArea(e.target.value)} />
                    </div>
                </div>
            </section>

            <section className={styles.section}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--gap-md)'}}>
                    <h2 className={styles.sectionTitle} style={{borderBottom: 'none', paddingBottom: 0}}><FiCheckSquare /> {nStages}. Stage Checklist</h2>
                    <div style={{display: 'flex', gap: 'var(--gap-md)', flexWrap: 'wrap', alignItems: 'center'}}>
                        {presets.length > 0 && (
                            <select className={styles.select} style={{width: 'auto'}} defaultValue=""
                                onChange={e => { applyPreset(e.target.value); e.target.value = ''; }}>
                                <option value="" disabled>Apply preset...</option>
                                {presets.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                            </select>
                        )}
                        <button className={styles.legacyBtn} onClick={() => setShowSavePreset(s => !s)}>
                            <FiBookmark /> Save as Preset
                        </button>
                        <button className={styles.legacyBtn} onClick={() => setAddingStage(s => !s)}>
                            <FiPlus /> Add Stage
                        </button>
                    </div>
                </div>

                {showSavePreset && (
                    <div className={styles.inlineAddRow}>
                        <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                        <button className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                        <button className={styles.btn} onClick={() => { setShowSavePreset(false); setPresetName(''); }}><FiX /></button>
                    </div>
                )}

                {addingStage && (
                    <div className={styles.inlineAddRow}>
                        <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                        <input className={styles.input} type="number" placeholder="Default cost" value={newStageCost} onChange={e => setNewStageCost(e.target.value)} style={{maxWidth: 160}} />
                        <button className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                        <button className={styles.btn} onClick={() => { setAddingStage(false); setNewStageName(''); setNewStageCost(''); }}><FiX /></button>
                    </div>
                )}

                <div className={styles.stageList}>
                    {sortedTemplates.map(t => {
                        const locked = t.id === firstStageId || t.id === lastStageId;
                        return (
                            <label key={t.id} className={`${styles.stageItem} ${checkedStages[t.id] ? styles.checked : ''} ${locked ? styles.stageLocked : ''}`}>
                                <input type="checkbox" className={styles.checkbox} checked={!!checkedStages[t.id]}
                                    disabled={locked}
                                    onChange={() => toggleStage(t.id)} />
                                <span className={styles.stageName}>{t.stageName}</span>
                                {locked && <span className={styles.lockedTag}><FiLock size={11} /> Required</span>}
                            </label>
                        );
                    })}
                </div>

                {presets.length > 0 && (
                    <div className={styles.presetList}>
                        {presets.map(p => (
                            <span key={p.name} className={styles.presetChip}>
                                {p.name}
                                <button className={styles.presetChipRemove} onClick={() => deletePreset(p.name)} aria-label={`Delete preset ${p.name}`}><FiX size={12} /></button>
                            </span>
                        ))}
                    </div>
                )}
            </section>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiDollarSign /> {nFinancials}. Financials</h2>
                <div className={styles.grid2}>
                    <div className={styles.field}>
                        <label className={styles.label}>Total Cost</label>
                        <input type="number" className={styles.input} value={totalCost} onChange={e => setTotalCost(e.target.value)} />
                    </div>
                    <div className={styles.field}>
                        <label className={styles.label}>Initial Payment</label>
                        <input type="number" className={styles.input} value={initialPayment} onChange={e => setInitialPayment(e.target.value)} />
                    </div>
                </div>

                {isLegacy && (
                    <>
                        <h3 className={styles.subheading}><FiArchive size={13} /> Legacy Storage Fees</h3>
                        <div className={styles.grid2}>
                            <div className={styles.field}>
                                <label className={styles.label}>Initial Storage Fee</label>
                                <input type="number" className={styles.input} value={initialStorageFee} onChange={e => setInitialStorageFee(e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Monthly Storage Fee</label>
                                <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => setMonthlyStorageFee(e.target.value)} placeholder="Leave blank for system default" />
                            </div>
                        </div>
                    </>
                )}

                <div className={styles.financialsSummary}>
                    <div className={styles.finRow}><span>Total Cost</span><span>{Number(totalCost) || 0}</span></div>
                    <div className={styles.finRow}><span>Initial Payment</span><span>{Number(initialPayment) || 0}</span></div>
                    {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}
                    <div className={`${styles.finRow} ${styles.total}`}><span>Amount Owed</span><span>{amountOwed}</span></div>
                </div>
            </section>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiUploadCloud /> {nDocuments}. Documents</h2>
                <label className={styles.dropzone}>
                    <FiUploadCloud size={24} />
                    <p>Click to upload documents</p>
                    <input type="file" multiple style={{display: 'none'}} onChange={handleFileUpload} />
                </label>
                <div className={styles.fileList}>
                    {fileQueue.map((f, i) => (
                        <div key={i} className={styles.fileItem}>
                            <span>{f.name}</span>
                            <button className={styles.btn} onClick={() => setFileQueue(p => p.filter((_, idx) => idx !== i))}><FiTrash2 /></button>
                        </div>
                    ))}
                </div>
            </section>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiEdit3 /> {nNotes}. Notes</h2>
                <div className={styles.field}>
                    <label className={styles.label}>Shared Project Notes</label>
                    <textarea className={styles.textarea} value={notes} onChange={e => setNotes(e.target.value)} />
                </div>
            </section>

            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles[t.type] || ''}`}>{t.msg}</div>
            ))}
        </div>
    );
}
