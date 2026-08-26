// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useBlocker } from 'react-router-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiEdit3, FiBookmark, FiX, FiCopy, FiArrowUp, FiFile, FiEye, FiRefreshCw,
    FiCalendar
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareSelect from '../../components/common/HardwareSelect';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

const PROJECT_TYPES = [
    { value: 'NEW_FOLDER',   label: 'New Folder',   icon: <FiFolderPlus aria-hidden="true" />, hint: 'No title yet' },
    { value: 'NEW_TITLE',    label: 'New Title',    icon: <FiFilePlus aria-hidden="true" />,   hint: 'Title captured now' },
    { value: 'LEGACY_TITLE', label: 'Legacy Title', icon: <FiArchive aria-hidden="true" />,    hint: 'Existing title, receivable' },
];

const TENURE_OPTIONS = ['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY'];

const DEFAULT_STAGES = [
    'Field Work',
    'Deed Plan',
    'LC Inspection',
    'District Land Board Approval',
    'Tax Assessment and Stamp Duty',
    'Registration and Title Issuance',
];

const todayISO = () => new Date().toISOString().slice(0, 10);
const todayDMY = () => {
    const d = new Date();
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
};
const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';

const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';
const loadPresets = () => {
    try {
        const raw = localStorage.getItem(PRESET_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch { return []; }
};
const savePresets = (presets) => {
    try { localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(presets)); } catch {}
};

export default function IntakePage() {
    const navigate = useNavigate();
    const topRef = useRef(null);
    const fileInputRef = useRef(null);
    const [saving, setSaving] = useState(false);
    const [nextIndex, setNextIndex] = useState('');
    const [projectType, setProjectType] = useState('NEW_FOLDER');
    const [projectStartDate, setProjectStartDate] = useState(todayISO);
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
    const [insertAfterId, setInsertAfterId] = useState('');
    const [restoring, setRestoring] = useState(false);
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');
    const [titleIssueDate, setTitleIssueDate] = useState('');
    const [volume, setVolume] = useState('');
    const [folio, setFolio] = useState('');
    const [instrumentNo, setInstrumentNo] = useState('');
    const [physicalBoxNumber, setPhysicalBoxNumber] = useState('');
    const [surveyDate, setSurveyDate] = useState('');

    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState(0);

    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');

    const [dirty, setDirty] = useState(false);
    const dirtyRef = useRef(false);
    const markDirty = useCallback(() => { dirtyRef.current = true; setDirty(true); }, []);

    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type = 'info') => {
        const id = Date.now();
        setToasts(p => [...p, { id, msg, type }]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    const fetchTemplates = useCallback(() => {
        stageTemplateService.getTemplate().then(t => setTemplates(t || [])).catch(() => {});
    }, []);
    useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

    useEffect(() => {
        landService.getNextIndex().then(idx => setNextIndex(idx || '')).catch(() => {});
    }, []);

    // STANDARD: sidebar auto-collapses once the user starts working on the form
    const collapsedOnce = useRef(false);
    useEffect(() => {
        const el = topRef.current;
        if (!el) return;
        const handler = () => {
            if (collapsedOnce.current) return;
            collapsedOnce.current = true;
            const aside = document.querySelector('aside');
            const toggle = document.querySelector('[class*="sidebarToggle"]');
            if (aside && toggle && aside.getBoundingClientRect().width > 120) {
                toggle.click();
            }
        };
        el.addEventListener('focusin', handler);
        el.addEventListener('input', handler);
        el.addEventListener('click', handler);
        return () => {
            el.removeEventListener('focusin', handler);
            el.removeEventListener('input', handler);
            el.removeEventListener('click', handler);
        };
    }, []);

    // STANDARD: warn before closing the tab with unsaved work
    useEffect(() => {
        const h = (e) => {
            if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; }
        };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, []);

    // Warn before navigating away inside the app with unsaved work
    const blocker = useBlocker(dirty && !saving);

    const sortedTemplates = useMemo(
        () => [...templates].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0)),
        [templates]
    );
    const firstStageId = sortedTemplates[0]?.id;
    const lastStageId = sortedTemplates[sortedTemplates.length - 1]?.id;

    useEffect(() => {
        if (!sortedTemplates.length) return;
        setCheckedStages(prev => {
            const next = { ...prev };
            if (firstStageId && next[firstStageId] === undefined) next[firstStageId] = true;
            return next;
        });
    }, [sortedTemplates.length, firstStageId]);

    const finalStageChecked = lastStageId ? !!checkedStages[lastStageId] : false;
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleType = isLegacy || titleAtIntake;
    const isTitleSectionVisible = isTitleType || finalStageChecked;
    const showStages = !isTitleType;

    const allStagesChecked = () => {
        const all = {};
        sortedTemplates.forEach(t => { all[t.id] = true; });
        return all;
    };
    const defaultStages = () => {
        const d = {};
        if (firstStageId) d[firstStageId] = true;
        return d;
    };

    const handleProjectTypeChange = (value) => {
        setProjectType(value);
        markDirty();
        if (value === 'LEGACY_TITLE' || value === 'NEW_TITLE') {
            setCheckedStages(allStagesChecked());
        } else {
            setCheckedStages(defaultStages());
        }
    };

    const toggleStage = (id) => {
        markDirty();
        setCheckedStages(p => ({ ...p, [id]: !p[id] }));
    };

    // one parallel wave of order updates = fast, no lag
    const renumber = (ordered) => Promise.all(
        ordered.map((t, i) =>
            t?.id ? stageTemplateService.updateTemplateStage(t.id, t.stageName, t.defaultCost || 0, i + 1) : null
        )
    );

    const openInsertBelow = (stageId) => {
        setInsertAfterId(stageId);
        setAddingStage(true);
    };

    const handleAddStage = async () => {
        if (!newStageName.trim()) { toast('Enter a stage name first.', 'error'); return; }
        try {
            let k = sortedTemplates.length - 1; // default: just before last
            const idx = sortedTemplates.findIndex(t => t.id === insertAfterId);
            if (idx >= 0) k = idx + 1; // appears directly under the clicked stage
            k = Math.min(Math.max(k, 1), Math.max(1, sortedTemplates.length - 1));

            const created = await stageTemplateService.addTemplateStage(newStageName.trim(), 0);
            const item = { id: created?.id, stageName: newStageName.trim(), defaultCost: 0 };
            const next = sortedTemplates.filter(t => t.id !== created?.id);
            next.splice(k, 0, item);
            await renumber(next);

            setNewStageName('');
            setInsertAfterId('');
            setAddingStage(false);
            fetchTemplates();
            if (created?.id) setCheckedStages(p => ({ ...p, [created.id]: true }));
            toast('Stage inserted.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not add stage.', 'error');
        }
    };

    const handleDeleteStage = async (id) => {
        try {
            await stageTemplateService.deleteTemplateStage(id);
            setCheckedStages(p => { const n = { ...p }; delete n[id]; return n; });
            fetchTemplates();
            toast('Stage removed.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Could not delete stage.', 'error');
        }
    };

    const handleRestoreDefaults = async () => {
        setRestoring(true);
        try {
            const keep = sortedTemplates.filter(t => DEFAULT_STAGES.includes(t.stageName));
            await Promise.all(
                sortedTemplates
                    .filter(t => !DEFAULT_STAGES.includes(t.stageName))
                    .map(t => stageTemplateService.deleteTemplateStage(t.id))
            );
            const have = new Set(keep.map(t => t.stageName));
            const added = [];
            for (const name of DEFAULT_STAGES) {
                if (!have.has(name)) {
                    const c = await stageTemplateService.addTemplateStage(name, 0);
                    added.push({ id: c?.id, stageName: name, defaultCost: 0 });
                }
            }
            const byName = {};
            [...keep, ...added].forEach(t => { byName[t.stageName] = t; });
            await renumber(DEFAULT_STAGES.map(name => byName[name]).filter(Boolean));
            fetchTemplates();
            toast('Default stages restored.', 'success');
        } catch (err) {
            toast(err.response?.data?.message || 'Restore failed.', 'error');
        } finally {
            setRestoring(false);
        }
    };

    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const stageNames = sortedTemplates.filter(t => checkedStages[t.id]).map(t => t.stageName);
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
            next[t.id] = preset.stageNames.includes(t.stageName);
        });
        setCheckedStages(next);
        markDirty();
    };

    const deletePreset = (name) => {
        const next = presets.filter(p => p.name !== name);
        setPresets(next);
        savePresets(next);
    };

    const updateOwner = (idx, field, val) => {
        markDirty();
        setOwners(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o));
    };

    const handleFileUpload = (e) => {
        const items = Array.from(e.target.files).map(f => ({
            name: f.name, size: f.size, file: f, url: URL.createObjectURL(f),
        }));
        if (items.length) {
            setFileQueue(p => [...p, ...items]);
            markDirty();
        }
        e.target.value = '';
    };

    const removeFile = (i) => {
        setFileQueue(p => {
            URL.revokeObjectURL(p[i].url);
            return p.filter((_, idx) => idx !== i);
        });
    };

    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();

    const scrollTop = () => topRef.current && topRef.current.scrollIntoView({ behavior: 'smooth' });

    // ---- validation shared by Save and Duplicate ----
    const validate = () => {
        if (!district.trim() || !county.trim()) {
            toast('District and County are required.', 'error'); return false;
        }
        for (let i = 0; i < owners.length; i++) {
            const o = owners[i];
            if (!o.nationalId.trim()) { toast(`Owner ${i + 1}: NIN is required.`, 'error'); return false; }
            if (!o.fullName.trim()) { toast(`Owner ${i + 1}: Full Name is required.`, 'error'); return false; }
            if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }
        }
        if (isTitleSectionVisible) {
            if (!titleId.trim()) { toast('Title ID is required for a title record.', 'error'); return false; }
            if (!plotNumber.trim()) { toast('Plot Number is required for a title record.', 'error'); return false; }
            if (!area.trim()) { toast('Area is required for Title details.', 'error'); return false; }
        }
        if (!(Number(totalCost) > 0)) { toast('Total Cost must be greater than 0.', 'error'); return false; }
        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) {
            toast('Initial Payment is required (0 or more).', 'error'); return false;
        }
        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }
        return true;
    };

    // ---- the actual save (no navigation) ----
    const doSave = async () => {
        if (!validate()) return false;
        setSaving(true);
        try {
            let noteText = notes.trim();
            if (noteText && !/^\[\d{2}\/\d{2}\/\d{4}\]/.test(noteText)) {
                noteText = `[${todayDMY()}] ${noteText}`; // STANDARD: notes carry their date
            }

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
                projectStartDate: projectStartDate || todayISO(),
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(),
                    phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address: o.address.trim(),
                })),
                selectedStages: Object.entries(checkedStages)
                    .filter(([id, v]) => v && templates.some(t => t.id === id))
                    .map(([id]) => {
                        const t = templates.find(x => x.id === id);
                        return {
                            stageTemplateId: id,
                            stageName: t ? t.stageName : '',
                            isCustom: false,
                            isCompleted: true
                        };
                    }),
                notes: noteText ? [{ content: noteText }] : [],
            };

            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
                payload.titleIssueDate = titleIssueDate || null;
                payload.volume = volume.trim().toUpperCase();
                payload.folio = folio.trim().toUpperCase();
                payload.instrumentNo = instrumentNo.trim().toUpperCase();
                payload.physicalBoxNumber = physicalBoxNumber.trim().toUpperCase();
                payload.surveyDate = surveyDate || null;
            }

            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.monthlyStorageFee = Number(monthlyStorageFee) || 0;
            }

            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file));
            dirtyRef.current = false;
            setDirty(false);
            return true;
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
            return false;
        } finally {
            setSaving(false);
        }
    };

    const handleSubmit = async () => {
        const ok = await doSave();
        if (ok) {
            toast('Project registered successfully!', 'success');
            setTimeout(() => navigate('/land/projects'), 1200);
        }
    };

    // Duplicate = SAVE the current form first (same validations/warnings),
    // then carry owners + location into a fresh form.
    const handleDuplicate = async () => {
        const ok = await doSave();
        if (!ok) return;
        toast('Saved. Form duplicated for the next plot.', 'success');
        setProjectType('NEW_FOLDER');
        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');
        setVolume(''); setFolio(''); setInstrumentNo(''); setPhysicalBoxNumber(''); setSurveyDate('');
        setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setMonthlyStorageFee(0);
        setNotes('');
        setFileQueue(q => { q.forEach(x => URL.revokeObjectURL(x.url)); return []; });
        setCheckedStages(defaultStages());
        setProjectStartDate(todayISO);
        landService.getNextIndex().then(idx => setNextIndex(idx || '')).catch(() => {});
        scrollTop();
    };

    const amountOwed = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));

    let n = 0;
    const nIndex = ++n;
    const nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n;
    const nStages = showStages ? ++n : null;
    const nFinancials = ++n;
    const nDocuments = ++n;
    const nNotes = ++n;

    const insertAfterName = sortedTemplates.find(t => t.id === insertAfterId)?.stageName;

    return (
        <div className={styles.container} ref={topRef}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button className={styles.btn} onClick={() => navigate(-1)}>Cancel</button>
                </div>
            </header>

            <div className={styles.sections}>

                <CollapsibleSection icon={<FiHash />} title={`${nIndex}. Entry Mode`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={styles.label}>Index</label>
                            <input className={`${styles.input} ${styles.indexValue}`} value={nextIndex} placeholder="--" disabled />
                            <p className={styles.hint}>Next available index, assigned on save</p>
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Date Started</label>
                            <input type="date" className={styles.input} value={projectStartDate} onChange={e => { setProjectStartDate(e.target.value); markDirty(); }} />
                            <p className={styles.hint}>Auto-filled with today. Edit if started earlier.</p>
                        </div>
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>Type</label>
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
                </CollapsibleSection>

                <CollapsibleSection icon={<FiUsers />} title={`${nOwners}. Owners`}>
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
                                <label className={`${styles.label} ${styles.required}`}>Phone</label>
                                <input className={styles.input} value={o.phone} onChange={e => updateOwner(idx, 'phone', e.target.value)} placeholder="0700 000 000 / 0788 000 000" />
                                <p className={styles.hint}>Multiple numbers: separate with /</p>
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Email</label>
                                <input className={styles.input} value={o.email} onChange={e => updateOwner(idx, 'email', e.target.value)} />
                            </div>
                            <button
                                type="button"
                                className={`${styles.btn} ${styles.deleteBtn}`}
                                onClick={() => setOwners(p => p.filter((_, i) => i !== idx))}
                                disabled={owners.length === 1}
                                aria-label="Remove owner"
                            >
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                    <button type="button" className={styles.addBtn} onClick={() => { setOwners(p => [...p, EMPTY_OWNER()]); markDirty(); }}>
                        <FiPlus /> Add Owner
                    </button>
                </CollapsibleSection>

                {isTitleSectionVisible && (
                    <CollapsibleSection icon={<FiFileText />} title={`${nTitle}. Title Details`} accent>
                        <div className={styles.grid3}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Title ID</label>
                                <input className={styles.input} value={titleId} onChange={e => { setTitleId(e.target.value); markDirty(); }} />
                            </div>
                            <HardwareSelect
                                label="Tenure"
                                required
                                options={TENURE_OPTIONS}
                                value={tenure}
                                onChange={(v) => { setTenure(v); markDirty(); }}
                            />
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                                <input className={styles.input} value={plotNumber} onChange={e => { setPlotNumber(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Block</label>
                                <input className={styles.input} value={blockRoad} onChange={e => { setBlockRoad(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Title Date</label>
                                <input type="date" className={styles.input} value={titleIssueDate} onChange={e => { setTitleIssueDate(e.target.value); markDirty(); }} />
                                <p className={styles.hint}>Leave blank if not yet received.</p>
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Volume</label>
                                <input className={styles.input} value={volume} onChange={e => { setVolume(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Folio</label>
                                <input className={styles.input} value={folio} onChange={e => { setFolio(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Instrument No.</label>
                                <input className={styles.input} value={instrumentNo} onChange={e => { setInstrumentNo(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Physical Box Number</label>
                                <input className={styles.input} value={physicalBoxNumber} onChange={e => { setPhysicalBoxNumber(e.target.value); markDirty(); }} />
                                <p className={styles.hint}>Set once the physical document arrives.</p>
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Survey Date</label>
                                <input type="date" className={styles.input} value={surveyDate} onChange={e => { setSurveyDate(e.target.value); markDirty(); }} />
                            </div>
                        </div>
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiMap />} title={`${nLocation}. Location`}>
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>District</label>
                            <input className={styles.input} value={district} onChange={e => { setDistrict(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>County</label>
                            <input className={styles.input} value={county} onChange={e => { setCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Sub-county</label>
                            <input className={styles.input} value={subCounty} onChange={e => { setSubCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Parish</label>
                            <input className={styles.input} value={parish} onChange={e => { setParish(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Village</label>
                            <input className={styles.input} value={village} onChange={e => { setVillage(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${isTitleSectionVisible ? styles.required : ''}`}>Area{!isTitleSectionVisible ? ' (Optional)' : ''}</label>
                            <input className={styles.input} value={area} onChange={e => { setArea(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                </CollapsibleSection>

                {showStages && (
                    <CollapsibleSection
                        icon={<FiCheckSquare />}
                        title={`${nStages}. Stages`}
                        right={
                            <div style={{ display: 'flex', gap: 'var(--gap-md)', flexWrap: 'wrap', alignItems: 'center' }}>
                                {presets.length > 0 && (
                                    <HardwareSelect
                                        compact
                                        placeholder="Apply preset..."
                                        value=""
                                        options={presets.map(p => p.name)}
                                        onChange={applyPreset}
                                    />
                                )}
                                <button type="button" className={styles.addBtn} onClick={() => setShowSavePreset(s => !s)}>
                                    <FiBookmark /> Save Preset
                                </button>
                                <button type="button" className={styles.addBtn} onClick={() => { setAddingStage(s => !s); setInsertAfterId(''); }}>
                                    <FiPlus /> Add Stage
                                </button>
                                <button type="button" className={styles.addBtn} disabled={restoring} onClick={handleRestoreDefaults}>
                                    <FiRefreshCw /> Restore Defaults
                                </button>
                            </div>
                        }
                    >
                        {showSavePreset && (
                            <div className={styles.inlineAddRow}>
                                <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setShowSavePreset(false); setPresetName(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        {addingStage && (
                            <div className={styles.inlineAddRow}>
                                <span className={styles.insertCtx}>
                                    {insertAfterName ? `Insert under: ${insertAfterName}` : 'Insert before last stage'}
                                </span>
                                <input className={styles.input} placeholder="New stage name" value={newStageName} onChange={e => setNewStageName(e.target.value)} />
                                <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleAddStage}>Add</button>
                                <button type="button" className={styles.xBtn} onClick={() => { setAddingStage(false); setNewStageName(''); setInsertAfterId(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        <div className={styles.stageList}>
                            {sortedTemplates.map((t, i) => {
                                const isLast = t.id === lastStageId;
                                return (
                                    <label key={t.id} className={`${styles.stageItem} ${checkedStages[t.id] ? styles.checked : ''}`}>
                                        <input type="checkbox" className={styles.checkbox} checked={!!checkedStages[t.id]}
                                            onChange={() => toggleStage(t.id)} />
                                        <span className={styles.stageName}>{t.stageName}</span>
                                        <span className={styles.stageActions}>
                                            {!isLast && (
                                                <button
                                                    type="button"
                                                    className={styles.plusBtn}
                                                    title="Insert a stage below this one"
                                                    aria-label={`Insert stage below ${t.stageName}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(t.id); }}
                                                >
                                                    <FiPlus size={12} />
                                                </button>
                                            )}
                                            {!isLast && t.id !== firstStageId && (
                                                <button
                                                    type="button"
                                                    className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeleteStage(t.id); }}
                                                    aria-label={`Delete stage ${t.stageName}`}
                                                >
                                                    <FiTrash2 size={12} />
                                                </button>
                                            )}
                                        </span>
                                    </label>
                                );
                            })}
                        </div>
                        {presets.length > 0 && (
                            <div className={styles.presetList}>
                                {presets.map(p => (
                                    <span key={p.name} className={styles.presetChip}>
                                        {p.name}
                                        <button
                                            type="button"
                                            className={styles.presetChipRemove}
                                            onClick={() => deletePreset(p.name)}
                                            aria-label={`Delete preset ${p.name}`}
                                        >
                                            <FiX size={12} />
                                        </button>
                                    </span>
                                ))}
                            </div>
                        )}
                    </CollapsibleSection>
                )}

                <CollapsibleSection icon={<FiDollarSign />} title={`${nFinancials}. Financials`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Total Cost</label>
                            <input type="number" className={styles.input} value={totalCost} onChange={e => { setTotalCost(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Initial Payment</label>
                            <input type="number" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />
                        </div>
                    </div>
                    {isLegacy && (
                        <>
                            <h3 className={styles.subheading}><FiArchive size={13} /> Storage Fees</h3>
                            <div className={styles.grid2}>
                                <div className={styles.field}>
                                    <label className={styles.label}>Initial Storage Fee</label>
                                    <input type="number" className={styles.input} value={initialStorageFee} onChange={e => { setInitialStorageFee(e.target.value); markDirty(); }} />
                                </div>
                                <div className={styles.field}>
                                    <label className={styles.label}>Monthly Storage Fee</label>
                                    <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} placeholder="System default" />
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
                </CollapsibleSection>

                <div className={styles.splitRow}>
                    <CollapsibleSection icon={<FiUploadCloud />} title={`${nDocuments}. Documents`}>
                        <div
                            className={styles.dropzone}
                            onClick={triggerFileInput}
                            role="button"
                            tabIndex={0}
                            onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); triggerFileInput(); } }}
                        >
                            <span className={styles.dropzoneIcon}><FiUploadCloud size={18} /></span>
                            <span className={styles.dropzoneTitle}>Click to upload<span className={styles.reqMark}>*</span></span>
                            <span className={styles.dropzoneSub}>Required - PDF, images, any file</span>
                        </div>
                        <input ref={fileInputRef} type="file" multiple onChange={handleFileUpload} style={{ display: 'none' }} />
                        <div className={styles.fileList}>
                            {fileQueue.map((f, i) => (
                                <div key={i} className={styles.fileItem}>
                                    <span className={styles.fileMeta}>
                                        <FiFile className={styles.fileIcon} size={14} />
                                        <span className={styles.fileName}>{f.name}</span>
                                        <span className={styles.fileSize}>{fmtSize(f.size)}</span>
                                    </span>
                                    <span className={styles.fileActions}>
                                        <a className={`${styles.btn} ${styles.small}`} href={f.url} target="_blank" rel="noreferrer" aria-label={`View ${f.name}`}>
                                            <FiEye size={12} /> View
                                        </a>
                                        <button
                                            type="button"
                                            className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                            onClick={() => removeFile(i)}
                                            aria-label={`Remove ${f.name}`}
                                        >
                                            <FiTrash2 size={12} />
                                        </button>
                                    </span>
                                </div>
                            ))}
                        </div>
                    </CollapsibleSection>

                    <CollapsibleSection icon={<FiEdit3 />} title={`${nNotes}. Notes`}>
                        <div className={styles.notesWrap}>
                            <span className={styles.noteDateChip}><FiCalendar size={11} /> {todayDMY()}</span>
                            <textarea className={styles.textarea} value={notes} onChange={e => { setNotes(e.target.value); markDirty(); }} placeholder="Shared project notes - visible to all staff on the folder page..." />
                            <p className={styles.hint}>Saved with today's date as an intake note.</p>
                        </div>
                    </CollapsibleSection>
                </div>

            </div>

            <div className={styles.bottomBar}>
                <button type="button" className={styles.topBtn} onClick={scrollTop} aria-label="Back to top">
                    <FiArrowUp />
                </button>
                <div className={styles.bottomBarRight}>
                    <button type="button" className={styles.addBtn} onClick={handleDuplicate} disabled={saving}>
                        <FiCopy /> Duplicate
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save Project
                    </button>
                </div>
            </div>

            {blocker.state === 'blocked' && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalCard}>
                        <h3 className={styles.modalTitle}>Unsaved work</h3>
                        <p className={styles.modalText}>
                            You have unsaved information on this form. Do you want to save it before leaving?
                        </p>
                        <div className={styles.modalBtns}>
                            <button type="button" className={styles.btn} onClick={() => blocker.reset()}>Stay</button>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} onClick={() => blocker.proceed()}>Leave without saving</button>
                            <button
                                type="button"
                                className={`${styles.btn} ${styles.primary}`}
                                onClick={async () => {
                                    const ok = await doSave();
                                    if (ok) blocker.proceed(); else blocker.reset();
                                }}
                            >
                                <FiSave /> Save & Leave
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {toasts.map(t => (
                <div key={t.id} className={`${styles.toast} ${styles[t.type] || ''}`}>{t.msg}</div>
            ))}
        </div>
    );
}
