// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud, FiPlus, FiTrash2, FiSave } from 'react-icons/fi';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });

export default function IntakePage() {
    const navigate = useNavigate();
    const [saving, setSaving] = useState(false);
    const [projectId, setProjectId] = useState(null);
    const [projectIndex, setProjectIndex] = useState('');
    const [owners, setOwners] = useState([EMPTY_OWNER()]);

    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    const [templates, setTemplates] = useState([]);
    const [checkedStages, setCheckedStages] = useState({});
    const [isLegacy, setIsLegacy] = useState(false);

    const [titleId, setTitleId] = useState('');
    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [blockRoad, setBlockRoad] = useState('');

    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);

    const [fileQueue, setFileQueue] = useState([]);
    const [notes, setNotes] = useState('');

    const [toasts, setToasts] = useState([]);
    const toast = useCallback((msg, type='info') => {
        const id = Date.now();
        setToasts(p => [...p, {id, msg, type}]);
        setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 4000);
    }, []);

    useEffect(() => {
        stageTemplateService.getTemplate().then(t => setTemplates(t)).catch(() => {});
    }, []);

    const finalStageChecked = Object.keys(checkedStages).some(id => {
        const t = templates.find(x => x.id === id);
        return t && t.stageName === 'Registration and Title Issuance' && checkedStages[id];
    });

    const isSection5Unlocked = isLegacy || finalStageChecked;

    const handleLegacyPreset = () => {
        setIsLegacy(true);
        const allChecked = {};
        templates.forEach(t => { allChecked[t.id] = true; });
        setCheckedStages(allChecked);
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
        if (isSection5Unlocked) {
            if (!plotNumber.trim()) { toast('Plot Number is required when Legacy or Final Stage is checked.', 'error'); return; }
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
                owners: owners.map(o => ({
                    fullName: o.fullName.trim().toUpperCase(),
                    phone: o.phone.trim(),
                    email: o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address: o.address.trim(),
                })),
                selectedStages: Object.entries(checkedStages).filter(([_, v]) => v).map(([id]) => {
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

            if (isSection5Unlocked) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.blockRoad = blockRoad.trim().toUpperCase();
                payload.titleId = titleId.trim().toUpperCase();
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

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>New Land Project</h1>
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
                <h2 className={styles.sectionTitle}><FiFileText /> 1. Project Index</h2>
                <div className={styles.field}>
                    <label className={styles.label}>Project Index</label>
                    <input className={styles.input} value={projectIndex || 'Auto-generated on save'} disabled />
                </div>
            </section>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiUsers /> 2. Owners</h2>
                {owners.map((o, idx) => (
                    <div key={idx} className={styles.ownerRow}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                            <input className={styles.input} value={o.fullName} onChange={e => updateOwner(idx, 'fullName', e.target.value)} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>NIN</label>
                            <input className={styles.input} value={o.nationalId} onChange={e => updateOwner(idx, 'nationalId', e.target.value)} />
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

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiMap /> 3. Location</h2>
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
                        <label className={styles.label}>Area (Optional)</label>
                        <input className={styles.input} value={area} onChange={e => setArea(e.target.value)} />
                    </div>
                </div>
            </section>

            <section className={styles.section}>
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <h2 className={styles.sectionTitle} style={{borderBottom: 'none', paddingBottom: 0}}><FiCheckSquare /> 4. Stage Checklist</h2>
                    <button className={styles.legacyBtn} onClick={handleLegacyPreset}>Legacy Preset</button>
                </div>
                <div className={styles.stageList}>
                    {templates.map(t => (
                        <label key={t.id} className={`${styles.stageItem} ${checkedStages[t.id] ? styles.checked : ''}`}>
                            <input type="checkbox" className={styles.checkbox} checked={!!checkedStages[t.id]} 
                                onChange={e => setCheckedStages(p => ({...p, [t.id]: e.target.checked}))} />
                            <span className={styles.stageName}>{t.stageName}</span>
                        </label>
                    ))}
                </div>
            </section>

            {isSection5Unlocked && (
                <section className={styles.section} style={{border: '2px solid var(--orange)'}}>
                    <h2 className={styles.sectionTitle}><FiFileText /> 5. Title & Plot Details</h2>
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
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Area</label>
                            <input className={styles.input} value={area} onChange={e => setArea(e.target.value)} />
                        </div>
                    </div>
                </section>
            )}

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiDollarSign /> 6. Financials</h2>
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
                <div className={styles.financialsSummary}>
                    <div className={styles.finRow}><span>Total Cost</span><span>{Number(totalCost) || 0}</span></div>
                    <div className={styles.finRow}><span>Initial Payment</span><span>{Number(initialPayment) || 0}</span></div>
                    <div className={`${styles.finRow} ${styles.total}`}><span>Amount Owed</span><span>{amountOwed}</span></div>
                </div>
            </section>

            <section className={styles.section}>
                <h2 className={styles.sectionTitle}><FiUploadCloud /> 7. Documents & Notes</h2>
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