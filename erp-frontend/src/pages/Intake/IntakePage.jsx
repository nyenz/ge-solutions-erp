// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useBlocker } from 'react-router-dom';
import { createPortal } from 'react-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiEdit3, FiBookmark, FiX, FiCopy, FiFile, FiEye, FiRefreshCw,
    FiCalendar
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareSelect from '../../components/common/HardwareSelect';
import BackToTopButton from '../../components/common/BackToTopButton';
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
const FINAL_STAGE = 'Registration and Title Issuance';

const DEFAULT_MONTHLY_STORAGE_FEE = 50000;

const todayISO = () => new Date().toISOString().slice(0, 10);
const todayDMY = () => {
    const d = new Date();
    return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
};
const formatDMY = (iso) => {
    if (!iso) return '';
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
};
const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';

const PRESET_STORAGE_KEY = 'geSolutions.intake.stagePresets';
const INDEX_CACHE_KEY = 'geSolutions.intake.nextIndexPreview';
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
    const [projectStartDate] = useState(todayISO);
    const [owners, setOwners] = useState([EMPTY_OWNER()]);

    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    const [masterTemplates, setMasterTemplates] = useState([]);
    const [stageList, setStageList] = useState(() => DEFAULT_STAGES.map(name => ({ id: null, name })));
    const [checked, setChecked] = useState({ [DEFAULT_STAGES[0]]: true });
    const [addingStage, setAddingStage] = useState(false);
    const [newStageName, setNewStageName] = useState('');
    const [insertAfterName, setInsertAfterName] = useState('');
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');
    const [titleIssueDate, setTitleIssueDate] = useState('');

    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [monthlyStorageFee, setMonthlyStorageFee] = useState(DEFAULT_MONTHLY_STORAGE_FEE);

    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');

    const [dirty, setDirty] = useState(false);
    const dirtyRef = useRef(false);
    const markDirty = useCallback(() => { dirtyRef.current = true; setDirty(true); }, []);

    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type = 'info') => {
        const id = Date.now() + Math.random();
        setToasts(p => [...p, { id, msg, type }]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    useEffect(() => {
        stageTemplateService.getTemplate().then(list => {
            const sorted = [...(list || [])].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0));
            const seen = new Set(); const uniq = [];
            sorted.forEach(t => {
                if (t.stageName && !seen.has(t.stageName)) { seen.add(t.stageName); uniq.push({ id: t.id, name: t.stageName }); }
            });
            setMasterTemplates(uniq);
        }).catch(() => {});
    }, []);

    useEffect(() => {
        let cancelled = false;
        try { const c = localStorage.getItem(INDEX_CACHE_KEY); if (c) setNextIndex(c); } catch {}
        const load = (attempt) => {
            landService.getNextIndex().then(idx => {
                if (cancelled) return;
                if (idx) { setNextIndex(idx); try { localStorage.setItem(INDEX_CACHE_KEY, idx); } catch {} }
            }).catch(() => {
                if (cancelled) return;
                if (attempt < 2) { setTimeout(() => load(attempt + 1), 2500); return; }
                let cached = null; try { cached = localStorage.getItem(INDEX_CACHE_KEY); } catch {}
                if (!cached) toast('Could not load the next index. Refresh to try again.', 'error');
            });
        };
        load(0);
        return () => { cancelled = true; };
    }, [toast]);

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

    useEffect(() => {
        const h = (e) => {
            if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; }
        };
        window.addEventListener('beforeunload', h);
        return () => window.removeEventListener('beforeunload', h);
    }, []);

    const blocker = useBlocker(dirty && !saving);

    useEffect(() => {
        if (blocker.state !== 'blocked') return;
        const onKeyDown = (e) => { if (e.key === 'Escape') blocker.reset(); };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [blocker]);

    const finalStageChecked = !!checked[FINAL_STAGE];
    const isLegacy = projectType === 'LEGACY_TITLE';
    const titleAtIntake = projectType === 'NEW_TITLE';
    const isTitleType = isLegacy || titleAtIntake;
    const isTitleSectionVisible = isTitleType || finalStageChecked;
    const showStages = !isTitleType;

    const handleProjectTypeChange = (value) => {
        setProjectType(value);
        markDirty();
        if (value === 'LEGACY_TITLE' || value === 'NEW_TITLE') {
            const all = {};
            stageList.forEach(s => { all[s.name] = true; });
            setChecked(all);
        } else {
            setChecked({ [stageList[0]?.name]: true });
        }
    };

    const toggleStage = (name) => {
        markDirty();
        setChecked(p => ({ ...p, [name]: !p[name] }));
    };

    const openInsertBelow = (name) => {
        setInsertAfterName(name);
        setAddingStage(true);
    };

    const handleAddStage = () => {
        const name = newStageName.trim();
        if (!name) { toast('Enter a stage name first.', 'error'); return; }
        if (stageList.some(s => s.name.toLowerCase() === name.toLowerCase())) {
            toast('That stage is already on the list.', 'error'); return;
        }
        let k;
        if (!stageList.length) k = 0;
        else {
            k = stageList.length - 1;
            const idx = stageList.findIndex(s => s.name === insertAfterName);
            if (idx >= 0) k = idx + 1;
            k = Math.min(Math.max(k, 1), Math.max(1, stageList.length - 1));
        }
        const next = [...stageList];
        next.splice(k, 0, { id: null, name });
        setStageList(next);
        setChecked(p => ({ ...p, [name]: true }));
        setNewStageName(''); setInsertAfterName(''); setAddingStage(false);
        markDirty();
        toast('Stage inserted.', 'success');
    };

    const handleDeleteStage = (name) => {
        setStageList(p => p.filter(s => s.name !== name));
        setChecked(p => { const n = { ...p }; delete n[name]; return n; });
        markDirty();
        toast('Stage removed.', 'success');
    };

    const handleRestoreDefaults = () => {
        setStageList(DEFAULT_STAGES.map(n => ({ id: null, name: n })));
        setChecked({ [DEFAULT_STAGES[0]]: true });
        setAddingStage(false); setNewStageName(''); setInsertAfterName('');
        markDirty();
        toast('Default stages restored.', 'success');
    };

    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const stageNames = stageList.filter(s => checked[s.name]).map(s => s.name);
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
        stageList.forEach(s => { next[s.name] = preset.stageNames.includes(s.name); });
        setChecked(next);
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

    const validate = () => {
        if (!district.trim()) { toast('District is required.', 'error'); return false; }
        if (!county.trim()) { toast('County is required.', 'error'); return false; }
        if (!subCounty.trim()) { toast('Sub-county is required.', 'error'); return false; }
        if (!parish.trim()) { toast('Parish is required.', 'error'); return false; }
        if (!village.trim()) { toast('Village is required.', 'error'); return false; }
        if (!area.trim()) { toast('Area is required.', 'error'); return false; }
        for (let i = 0; i < owners.length; i++) {
            const o = owners[i];
            if (!o.nationalId.trim()) { toast(`Owner ${i + 1}: NIN is required.`, 'error'); return false; }
            if (!o.fullName.trim()) { toast(`Owner ${i + 1}: Full Name is required.`, 'error'); return false; }
            if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }
        }
        if (isTitleSectionVisible) {
            if (!titleId.trim()) { toast('Title ID is required.', 'error'); return false; }
            if (!plotNumber.trim()) { toast('Plot Number is required.', 'error'); return false; }
            if (!blockRoad.trim()) { toast('Block is required.', 'error'); return false; }
            if (!titleIssueDate) { toast('Title Date is required.', 'error'); return false; }
        }
        if (!(Number(totalCost) > 0)) { toast('Total Cost must be greater than 0.', 'error'); return false; }
        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) {
            toast('Initial Payment is required (0 or more).', 'error'); return false; }
        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }
        return true;
    };

    const doSave = async () => {
        if (!validate()) return false;
        setSaving(true);
        try {
            let noteText = notes.trim();
            if (noteText && !/^\[\d{2}\/\d{2}\/\d{4}\]/.test(noteText)) {
                noteText = `[${todayDMY()}] ${noteText}`;
            }

            const payload = {
                district: district.trim().toUpperCase(),
                county: county.trim().toUpperCase(),
                subCounty: subCounty.trim().toUpperCase(),
                parish: parish.trim().toUpperCase(),
                village: village.trim().toUpperCase(),
                area: area.trim().toUpperCase(),
                totalCost: Number(totalCost) || 0,
                initialPayment: Number(initialPayment) || 0,
                isLegacy: isLegacy,
                titleAtIntake: titleAtIntake,
                projectStartDate: todayISO(),
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(),
                    phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address: o.address.trim(),
                })),
                selectedStages: stageList
                    .filter(s => checked[s.name])
                    .map(s => {
                        const m = masterTemplates.find(t => t.name === s.name);
                        return m
                            ? { stageTemplateId: m.id, stageName: s.name, isCustom: false, isCompleted: true }
                            : { stageName: s.name, isCustom: true, cost: 0, isCompleted: true };
                    }),
                notes: noteText ? [{ content: noteText }] : [],
            };

            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
                payload.titleIssueDate = titleIssueDate || null;
            }

            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.monthlyStorageFee = Number(monthlyStorageFee) || DEFAULT_MONTHLY_STORAGE_FEE;
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

    const handleDuplicate = async () => {
        const ok = await doSave();
        if (!ok) return;
        toast('Saved. Form duplicated for the next plot.', 'success');
        setProjectType('NEW_FOLDER');
        setTitleId(''); setTenure('FREEHOLD'); setPlotNumber(''); setBlockRoad(''); setTitleIssueDate('');
        setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0);
        setMonthlyStorageFee(DEFAULT_MONTHLY_STORAGE_FEE);
        setNotes('');
        setFileQueue(q => { q.forEach(x => URL.revokeObjectURL(x.url)); return []; });
        setStageList(DEFAULT_STAGES.map(n => ({ id: null, name: n })));
        setChecked({ [DEFAULT_STAGES[0]]: true });
        landService.getNextIndex().then(idx => {
            if (idx) { setNextIndex(idx); try { localStorage.setItem(INDEX_CACHE_KEY, idx); } catch {} }
        }).catch(() => {});
        window.scrollTo({ top: 0, behavior: 'smooth' });
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

    return (
        <div className={styles.container} ref={topRef}>
            <header className={styles.pageHeader}>
                <div className={styles.headerLeft}>
                    <h1 className={styles.title}>New Project</h1>
                    <p className={styles.subtitle}>Intake Form</p>
                </div>
                <div className={styles.actions}>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.cancelBtn}`} onClick={() => navigate(-1)}>Cancel</button>
                </div>
            </header>

            <div className={styles.sections}>

                <CollapsibleSection icon={<FiHash />} title={`${nIndex}. Entry Mode`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={styles.label}>Index</label>
                            <div className={styles.indexDisplay}>{nextIndex || 'Loading...'}</div>
                            <p className={styles.hint}>Next available index, assigned on save</p>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Date Started</label>
                            <div className={styles.indexDisplay}>{formatDMY(projectStartDate)}</div>
                            <p className={styles.hint}>Auto-generated with today's date</p>
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
                                <p className={styles.hint}>Multiple: separate with /</p>
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
                                <label className={`${styles.label} ${styles.required}`}>Block</label>
                                <input className={styles.input} value={blockRoad} onChange={e => { setBlockRoad(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Title Date</label>
                                <input type="date" className={styles.input} value={titleIssueDate} onChange={e => { setTitleIssueDate(e.target.value); markDirty(); }} />
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
                            <label className={`${styles.label} ${styles.required}`}>Sub-county</label>
                            <input className={styles.input} value={subCounty} onChange={e => { setSubCounty(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Parish</label>
                            <input className={styles.input} value={parish} onChange={e => { setParish(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Village</label>
                            <input className={styles.input} value={village} onChange={e => { setVillage(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Area</label>
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
                                <button type="button" className={styles.addBtn} onClick={handleRestoreDefaults}>
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
                                <button type="button" className={styles.xBtn} onClick={() => { setAddingStage(false); setNewStageName(''); setInsertAfterName(''); }} aria-label="Close"><FiX /></button>
                            </div>
                        )}
                        <div className={styles.stageList}>
                            {stageList.map((s, i) => {
                                const isLast = i === stageList.length - 1;
                                const isFirst = i === 0;
                                return (
                                    <label key={s.name} className={`${styles.stageItem} ${checked[s.name] ? styles.checked : ''}`}>
                                        <input type="checkbox" className={styles.checkbox} checked={!!checked[s.name]}
                                            onChange={() => toggleStage(s.name)} />
                                        <span className={styles.stageName}>{s.name}</span>
                                        <span className={styles.stageActions}>
                                            {!isLast && (
                                                <button
                                                    type="button"
                                                    className={styles.plusBtn}
                                                    title="Insert a stage below this one"
                                                    aria-label={`Insert stage below ${s.name}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(s.name); }}
                                                >
                                                    <FiPlus size={12} />
                                                </button>
                                            )}
                                            {!isLast && !isFirst && (
                                                <button
                                                    type="button"
                                                    className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeleteStage(s.name); }}
                                                    aria-label={`Delete stage ${s.name}`}
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
                                    <input type="number" className={styles.input} value={monthlyStorageFee} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} />
                                    <p className={styles.hint}>System default: {DEFAULT_MONTHLY_STORAGE_FEE.toLocaleString()}</p>
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
                <div className={styles.bottomBarRight}>
                    <button type="button" className={styles.addBtn} onClick={handleDuplicate} disabled={saving}>
                        <FiCopy /> Duplicate
                    </button>
                    <button type="button" className={`${styles.btn} ${styles.primary}`} disabled={saving} onClick={handleSubmit}>
                        <FiSave /> Save Project
                    </button>
                </div>
            </div>

            <BackToTopButton />

            {blocker.state === 'blocked' && typeof document !== 'undefined' && createPortal(
                <div className={styles.modalOverlay} onClick={() => blocker.reset()}>
                    <div className={styles.modalCard} onClick={e => e.stopPropagation()}>
                        <h3 className={styles.modalTitle}>Unsaved work</h3>
                        <p className={styles.modalText}>
                            You have unsaved information on this form. Save before leaving?
                        </p>
                        <div className={styles.modalBtns}>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} onClick={() => blocker.proceed()}>Leave</button>
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
                        <p className={styles.modalHint}>Click outside or press Esc to keep editing</p>
                    </div>
                </div>,
                document.body
            )}

            {typeof document !== 'undefined' && createPortal(
                <div className={styles.toastStack} role="region" aria-label="Notifications" aria-live="polite">
                    {toasts.map(t => (
                        <div key={t.id} className={`${styles.toast} ${styles['toast_' + (t.type || 'info')]}`}>{t.msg}</div>
                    ))}
                </div>,
                document.body
            )}
        </div>
    );
}
