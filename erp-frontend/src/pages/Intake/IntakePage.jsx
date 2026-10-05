// PATH: erp-frontend/src/pages/Intake/IntakePage.jsx
import { roleFlags } from '../../utils/roles';
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useBlocker, useSearchParams } from 'react-router-dom';
import { createPortal } from 'react-dom';
import {
    FiUsers, FiMap, FiCheckSquare, FiFileText, FiDollarSign, FiUploadCloud,
    FiPlus, FiTrash2, FiSave, FiHash, FiFolderPlus, FiFilePlus, FiArchive,
    FiEdit3, FiBookmark, FiX, FiCopy, FiRefreshCw, FiCalendar, FiGrid, FiLink
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareDatePicker from '../../components/common/HardwareDatePicker';
import HardwareSelect from '../../components/common/HardwareSelect';
import HardwareModal from '../../components/common/HardwareModal';
import HardwareModalSelect from '../../components/common/HardwareModalSelect';
import modalStyles from '../../components/common/HardwareModal.module.css';
import BackToTopButton from '../../components/common/BackToTopButton';
import landService from '../../services/landService';
import { normalizePhones } from '../../utils/phone';
import statusTemplateService from '../../services/statusTemplateService';
import { useAuth } from '../../hooks/useAuth';
import { PROJECT_TYPES, showsTitle } from '../../constants/projectTypes';
import { DocList, DocGroup, DocRow, DocDropzone } from '../../components/common/DocParts';
import styles from './IntakePage.module.css';

const EMPTY_OWNER = () => ({ fullName: '', phone: '', email: '', nationalId: '', address: '' });
const EMPTY_NEIGHBOR = () => ({ fullName: '', phone: '', side: '', plotNumber: '' });
// fix180: the eight project types. Title Details follow the type (shared list in constants/projectTypes.js).
const TYPE_ICONS = { FRESH_SURVEY: <FiFolderPlus aria-hidden="true" />, SUBDIVISION: <FiGrid aria-hidden="true" />, LEGACY_TITLES: <FiArchive aria-hidden="true" />,
    TRANSFER_OF_TITLE: <FiLink aria-hidden="true" />, BOUNDARY_OPENING: <FiMap aria-hidden="true" />, TOPOGRAPHIC_SURVEY: <FiMap aria-hidden="true" />,
    RESURVEY: <FiRefreshCw aria-hidden="true" />, SPECIAL_PROJECTS: <FiFilePlus aria-hidden="true" /> };
const TYPE_HINTS = {
    FRESH_SURVEY: 'New survey, no title yet', SUBDIVISION: 'One title split into plots; each plot can be transferred later',
    LEGACY_TITLES: 'Existing title, receivable', TRANSFER_OF_TITLE: 'Title moving to a new owner', BOUNDARY_OPENING: 'Re-open the boundaries of a titled plot',
    TOPOGRAPHIC_SURVEY: 'Title Details optional', RESURVEY: 'Survey a titled plot again', SPECIAL_PROJECTS: 'Contract work, no title',
};
const TENURE_OPTIONS = ['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY'];
const sameRows = (a, b) => JSON.stringify(a) === JSON.stringify(b);
// fix173: the default monthly storage fee is read from the server (landService.getStorageFeeDefault); no copy of it lives here.
const todayISO = () => new Date().toISOString().slice(0, 10);
const todayDMY = () => { const d = new Date(); return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`; };
const fmtSize = (b) => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
// fix175: same file rules as the Folder page
const SCAN_EXT = ['pdf', 'jpg', 'jpeg', 'png', 'webp'];
const fileExt = (name) => { const m = String(name || '').toLowerCase().match(/[.]([a-z0-9]{1,6})$/); return m ? m[1] : ''; };
// fix172: today as yyyy-mm-dd in the user's own time zone (todayISO above is UTC and can be yesterday early in the morning)
const localISO = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
// fix172: whole 30-day months between an "in receivables since" date (yyyy-mm-dd) and today, the same count the nightly fee job uses
const monthsSince = (iso) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
    if (!m) return 0;
    const start = new Date(+m[1], +m[2] - 1, +m[3]);
    const t = new Date();
    const today = new Date(t.getFullYear(), t.getMonth(), t.getDate());
    return Math.max(0, Math.floor(Math.round((today - start) / 86400000) / 30));
};
const PRESET_STORAGE_KEY = 'geSolutions.intake.statusPresets';
const INDEX_CACHE_KEY = 'geSolutions.intake.nextIndexPreview';
const loadPresets = () => { try { const r = localStorage.getItem(PRESET_STORAGE_KEY); return r ? JSON.parse(r) : []; } catch { return []; } };
const savePresets = (p) => { try { localStorage.setItem(PRESET_STORAGE_KEY, JSON.stringify(p)); } catch {} };

export default function IntakePage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { user } = useAuth();
    // fix180: only Admin, Manager and Director can add a status (Secretary is data entry only; the server checks too)
    const canAddStatus = roleFlags(user).canAddStatus;
    const topRef = useRef(null);
    const fileInputRef = useRef(null);
    const [saving, setSaving] = useState(false);
    const [nextIndex, setNextIndex] = useState('');
    const [projectType, setProjectType] = useState('FRESH_SURVEY');
    const [titleSwitch, setTitleSwitch] = useState(false);          // fix180: Topographic Survey only
    const [subdivisionCount, setSubdivisionCount] = useState('');   // fix180: Subdivision only
    const [transferFrom, setTransferFrom] = useState(null);         // fix180: { id, index, plot } when transferring a subdivision plot
    const [projectStartDate, setProjectStartDate] = useState(todayISO);
    // ENTRY DATE: automatic, never editable -- the day this intake was
    // actually keyed into the system. Kept separate from Date Started
    // above, which is when fieldwork began and can be backdated by the
    // operator (e.g. entering a project two days after it started).
    const [entryDate] = useState(todayDMY);
    // fix180: CLIENTS first, then OWNERS. Owners start as a copy of the clients and follow them until staff change an owner.
    const [clients, setClients] = useState([EMPTY_OWNER()]);
    const [owners, setOwners] = useState([EMPTY_OWNER()]);
    const [ownersLinked, setOwnersLinked] = useState(true);
    const [neighbors, setNeighbors] = useState([]);
    const [district, setDistrict] = useState('');
    const [county, setCounty] = useState('');
    const [subCounty, setSubCounty] = useState('');
    const [parish, setParish] = useState('');
    const [village, setVillage] = useState('');
    const [area, setArea] = useState('');

    // Statuses are LOCAL-ONLY: edits never touch the master template, so the list resets to the project type's
    // list whenever the type changes or the form is opened unsaved.
    const [masterTemplates, setMasterTemplates] = useState([]);
    const [statusList, setStatusList] = useState([]);
    const [checked, setChecked] = useState({});
    const [addingStatus, setAddingStatus] = useState(false);
    const [newStatusName, setNewStatusName] = useState('');
    const [insertAfterName, setInsertAfterName] = useState('');
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState('');
    const [showSavePreset, setShowSavePreset] = useState(false);

    const [tenure, setTenure] = useState('FREEHOLD');
    const [plotNumber, setPlotNumber] = useState('');
    const [block, setBlock] = useState('');
    const [areaHectares, setAreaHectares] = useState('');   // fix180: required with Title Details
    const [volume, setVolume] = useState('');
    const [folio, setFolio] = useState('');
    const [titleIssueDate, setTitleIssueDate] = useState('');
    const [totalCost, setTotalCost] = useState(0);
    const [initialPayment, setInitialPayment] = useState(0);
    const [initialStorageFee, setInitialStorageFee] = useState(0);
    const [initialStorageFeePaid, setInitialStorageFeePaid] = useState(0);   // fix171
    const [lastPaidDate, setLastPaidDate] = useState('');           // fix172: optional, empty = paid today
    const [receivablesSince, setReceivablesSince] = useState('');   // fix172: optional, Legacy Title only
    const [titlePayerIdx, setTitlePayerIdx] = useState('');         // fix172: which client (row number) paid the initial payment
    const [feesPayerIdx, setFeesPayerIdx] = useState('');           // fix172: which client paid the storage fees
    // fix173: blank = follow the system default (nothing is stored on the project); a typed rate is that project's own rate
    const [monthlyStorageFee, setMonthlyStorageFee] = useState('');
    const [systemFee, setSystemFee] = useState(0);
    useEffect(() => { landService.getStorageFeeDefault().then(setSystemFee).catch(() => {}); }, []);
    const [fileQueue, setFileQueue] = useState([]);
    // fix174: document types = the Folder page classifications (PAYMENT_RECEIPT is filed by the payment window, never at intake)
    const [docCats, setDocCats] = useState([]);
    useEffect(() => { landService.getDocumentCategories().then(setDocCats).catch(() => {}); }, []);
    const catChoices = useMemo(() => docCats.filter(c => c.code !== 'PAYMENT_RECEIPT'), [docCats]);
    const catOptions = useMemo(() => catChoices.map(c => ({ value: c.code, label: c.label })), [catChoices]);
    const [uploadDraft, setUploadDraft] = useState(null); // fix175: { batch, error, files: [{ file, category }] }
    const [newCatOpen, setNewCatOpen] = useState(false);
    const [newCatName, setNewCatName] = useState('');
    const [catBusy, setCatBusy] = useState(false);
    const [previewFile, setPreviewFile] = useState(null);
    // fix176: preview window is sized to the document (portrait / landscape) and always fits the screen
    const openPreview = async (f) => {
        const isPdf = fileExt(f.name) === 'pdf';
        let ratio = 0.707; // A4 portrait fallback
        try {
            if (isPdf) {
                const txt = new TextDecoder('latin1').decode(await f.file.arrayBuffer());
                const mb = txt.match(/\/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*\]/);
                if (mb) {
                    let w = Math.abs(mb[3] - mb[1]); let h = Math.abs(mb[4] - mb[2]);
                    const rot = txt.match(/\/Rotate\s+(-?\d+)/);
                    if (rot && Math.abs(parseInt(rot[1], 10)) % 180 === 90) { const t = w; w = h; h = t; }
                    if (w > 0 && h > 0) ratio = w / h;
                }
            } else {
                ratio = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im.naturalWidth / im.naturalHeight); im.onerror = rej; im.src = f.url; });
            }
        } catch (err) { /* keep the portrait default */ }
        ratio = Math.min(4, Math.max(0.25, ratio || 0.707));
        setPreviewFile({ ...f, isPdf, ratio });
    };
    useEffect(() => {
        if (!previewFile) return undefined;
        const onKey = (e) => { if (e.key === 'Escape') setPreviewFile(null); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [previewFile]);
    const catLabelOf = (code) => { const c = docCats.find(x => x.code === code); return c ? c.label : ''; };
    // fix179: queued files grouped by document type (same grouping as the Folder page), keeping each file's queue index
    const queueGroups = (() => {
        const g = new Map();
        fileQueue.forEach((f, i) => { const k = f.category || '__NONE__'; if (!g.has(k)) g.set(k, []); g.get(k).push({ f, i }); });
        const rank = (k) => { if (k === '__NONE__') return 9999; const x = docCats.findIndex(c => c.code === k); return x < 0 ? 9000 : x; };
        return [...g.entries()].sort((p, q) => rank(p[0]) - rank(q[0]));
    })();
    const catCodeOf = (label) => { const c = catChoices.find(x => x.label === label); return c ? c.code : ''; };
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
    // fix173: a monthly fee of 0 or less is not allowed at intake. It becomes the system default and the user is told.
    const feeOrDefault = (v) => { const n = Number(v); return n > 0 ? n : systemFee; };
    const fixFeeBox = () => {
        if (monthlyStorageFee === '' || monthlyStorageFee === null || Number(monthlyStorageFee) > 0) return;
        setMonthlyStorageFee(systemFee > 0 ? String(systemFee) : '');
        toast('Monthly Storage Fee must be more than 0, so the system default' + (systemFee > 0 ? ' (UGX ' + systemFee.toLocaleString() + ')' : '') + ' is used instead.', 'info');
    };

    // fix180: each project type has its own status list. Legacy Titles arrive with every status done (the title exists);
    // every other type with the first status done.
    const loadTypeStatuses = useCallback((type) => {
        statusTemplateService.getTemplate(type).then(list => {
            const sorted = [...(list || [])].sort((a, b) => (a.displayOrder ?? 0) - (b.displayOrder ?? 0));
            const seen = new Set(); const uniq = [];
            sorted.forEach(t => { if (t.statusName && !seen.has(t.statusName)) { seen.add(t.statusName); uniq.push({ id: t.id, name: t.statusName }); } });
            setMasterTemplates(uniq);
            setStatusList(uniq.map(t => ({ id: t.id, name: t.name })));
            const c = {};
            uniq.forEach((t, i) => { if (i === 0 || type === 'LEGACY_TITLES') c[t.name] = true; });
            setChecked(c);
        }).catch(() => { setMasterTemplates([]); setStatusList([]); setChecked({}); });
    }, []);
    useEffect(() => { loadTypeStatuses(projectType); }, [projectType, loadTypeStatuses]);

    // fix180: TRANSFER of a subdivision plot (opened from the subdivision's folder page): the type is Transfer of Title and
    // the Clients and Owners are copied from the subdivision. Title Details, Neighbors and everything else start blank.
    useEffect(() => {
        const from = searchParams.get('transferFrom');
        const plot = parseInt(searchParams.get('plot') || '', 10);
        if (!from || !(plot > 0)) return;
        landService.getDeepBinder(from).then(data => {
            const p = data && data.project;
            if (!p) return;
            const toRow = (c) => ({ fullName: c.fullName || '', phone: c.phoneNumber || '', email: c.email || '', nationalId: c.nationalId || '', address: c.homeAddress || '' });
            const cl = (p.clients && p.clients.length ? p.clients : (p.proprietors || [])).map(toRow);
            const ow = (p.proprietors || []).map(toRow);
            setProjectType('TRANSFER_OF_TITLE');
            if (cl.length) setClients(cl);
            if (ow.length) { setOwners(ow); setOwnersLinked(sameRows(ow, cl)); }
            setTransferFrom({ id: p.id, index: p.projectIndex, plot });
        }).catch(() => toast('Could not load the subdivision project. Open the transfer again from its folder page.', 'error'));
    }, [searchParams, toast]);

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

    /* This page used to fake a click on the sidebar's own toggle button the
       first time you touched the form, as a one-off workaround so the panel
       wasn't eating width while you filled this in. The sidebar now collapses
       itself on any nav click, on every page, so the page-local version of
       the same behaviour was just a second way of doing the same thing. */

    useEffect(() => {
        const h = (e) => { if (dirtyRef.current) { e.preventDefault(); e.returnValue = ''; } };
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

    const firstStatusName = statusList[0]?.name;
    const isLegacy = projectType === 'LEGACY_TITLES';
    // fix180: Title Details are shown by project type (Topographic Survey: only when switched on)
    const isTitleSectionVisible = showsTitle(projectType, titleSwitch);
    const isSubdivision = projectType === 'SUBDIVISION';

    const handleProjectTypeChange = (value) => {
        if (transferFrom && value !== 'TRANSFER_OF_TITLE') { toast('A subdivision plot is transferred with a Transfer of Title project.', 'error'); return; }
        setProjectType(value); markDirty();
        if (value !== 'TOPOGRAPHIC_SURVEY') setTitleSwitch(false);
        setAddingStatus(false); setNewStatusName(''); setInsertAfterName('');
    };
    // The first status is mandatory (every project passes through it before intake).
    const toggleStatus = (name) => {
        if (name === firstStatusName) return;
        markDirty(); setChecked(p => ({ ...p, [name]: !p[name] }));
    };

    const openInsertBelow = (name) => { setInsertAfterName(name); setAddingStatus(true); };
    const handleAddStatus = () => {
        if (!canAddStatus) { toast('Only an Admin, Manager or Director can add a status.', 'error'); return; }
        const name = newStatusName.trim();
        if (!name) { toast('Enter a status name first.', 'error'); return; }
        if (statusList.some(s => s.name.toLowerCase() === name.toLowerCase())) { toast('That status is already on the list.', 'error'); return; }
        let k = statusList.length;
        const idx = statusList.findIndex(s => s.name === insertAfterName);
        if (idx >= 0) k = idx + 1;
        k = Math.max(k, 1);
        const next = [...statusList]; next.splice(k, 0, { id: null, name });
        setStatusList(next); setChecked(p => ({ ...p, [name]: false }));
        setNewStatusName(''); setInsertAfterName(''); setAddingStatus(false);
        markDirty(); toast('Status inserted.', 'success');
    };
    const handleDeleteStatus = (name) => {
        setStatusList(p => p.filter(s => s.name !== name));
        setChecked(p => { const n = { ...p }; delete n[name]; return n; });
        markDirty(); toast('Status removed.', 'success');
    };
    const handleRestoreDefaults = () => {
        loadTypeStatuses(projectType);
        setAddingStatus(false); setNewStatusName(''); setInsertAfterName('');
        markDirty(); toast('Default statuses restored.', 'success');
    };
    const handleSavePreset = () => {
        if (!presetName.trim()) { toast('Name the preset first.', 'error'); return; }
        const statusNames = statusList.filter(s => checked[s.name]).map(s => s.name);
        const next = [...presets.filter(p => p.name !== presetName.trim()), { name: presetName.trim(), statusNames }];
        setPresets(next); savePresets(next); setPresetName(''); setShowSavePreset(false);
        toast('Status preset saved.', 'success');
    };
    const applyPreset = (name) => {
        const preset = presets.find(p => p.name === name);
        if (!preset) return;
        const names = preset.statusNames || [];
        const next = {}; statusList.forEach((s, i) => { next[s.name] = i === 0 || names.includes(s.name); });
        setChecked(next); markDirty();
    };
    const deletePreset = (name) => { setPresets(presets.filter(p => p.name !== name)); savePresets(presets.filter(p => p.name !== name)); };

    // fix180: CLIENTS. While the owners are still linked, every client change is copied into the owners.
    const changeClients = (fn) => {
        const next = fn(clients);
        setClients(next);
        if (ownersLinked) setOwners(next.map(c => ({ ...c })));
        markDirty();
    };
    const updateClient = (idx, field, val) => changeClients(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o));
    // OWNERS: the first change unlinks them from the clients (they are then edited on their own)
    const updateOwner = (idx, field, val) => { markDirty(); setOwnersLinked(false); setOwners(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o)); };
    const copyClientsToOwners = () => { setOwners(clients.map(c => ({ ...c }))); setOwnersLinked(true); markDirty(); };
    const updateNeighbor = (idx, field, val) => { markDirty(); setNeighbors(p => p.map((o, i) => i === idx ? { ...o, [field]: val } : o)); };
    // fix175: picking files opens the same UPLOAD DOCUMENTS popup the Folder page uses; files join the list only once each has a type
    const handleFileUpload = (e) => {
        const picked = Array.from(e.target.files || []);
        e.target.value = '';
        if (!picked.length) return;
        const ok = []; const bad = [];
        picked.forEach(f => {
            if (!SCAN_EXT.includes(fileExt(f.name))) bad.push(f.name + ' (use PDF, JPG, PNG or WEBP)');
            else if (!f.size) bad.push(f.name + ' (the file is empty)');
            else if (f.size > 50 * 1024 * 1024) bad.push(f.name + ' (over 50 MB)');
            else ok.push(f);
        });
        if (bad.length) toast('NOT ADDED: ' + bad.join('; '), 'error');
        if (!ok.length) return;
        setUploadDraft({ batch: '', error: '', files: ok.map(file => ({ file, category: '' })) });
    };
    const removeFile = (i) => setFileQueue(p => { URL.revokeObjectURL(p[i].url); return p.filter((_, idx) => idx !== i); });
    const triggerFileInput = () => fileInputRef.current && fileInputRef.current.click();
    const closeUploadDraft = () => { setUploadDraft(null); setNewCatOpen(false); setNewCatName(''); };
    const setBatchCategory = (code) => setUploadDraft(d => d && ({ ...d, error: '', batch: code, files: d.files.map(f => ({ ...f, category: code })) }));
    const setDraftFileCategory = (i, code) => setUploadDraft(d => d && ({ ...d, error: '', files: d.files.map((f, j) => (j === i ? { ...f, category: code } : f)) }));
    const handleAddCategory = async () => {
        const name = newCatName.trim();
        if (name.length < 2 || catBusy) return;
        setCatBusy(true);
        try {
            const cat = await landService.addDocumentCategory(name);
            setDocCats(await landService.getDocumentCategories());
            setNewCatName(''); setNewCatOpen(false);
            setUploadDraft(d => d && ({ ...d, error: '', batch: d.batch || cat.code, files: d.files.map(f => (f.category ? f : { ...f, category: cat.code })) }));
            toast('Category "' + cat.label + '" ready', 'success');
        } catch (err) { setUploadDraft(d => d && ({ ...d, error: 'COULD NOT ADD CATEGORY: ' + ((err && err.response && err.response.data && (err.response.data.message || err.response.data.error)) || (err && err.message) || 'unknown error') })); } finally { setCatBusy(false); }
    };
    const confirmUploadDraft = () => {
        if (!uploadDraft) return;
        if (uploadDraft.files.some(f => !f.category)) { setUploadDraft(d => d && ({ ...d, error: 'PICK A CATEGORY FOR EVERY FILE.' })); return; }
        const items = uploadDraft.files.map(({ file, category }) => ({ name: file.name, size: file.size, file, url: URL.createObjectURL(file), category }));
        setFileQueue(p => [...p, ...items]); markDirty();
        closeUploadDraft();
    };

    const validate = () => {
        if (!district.trim()) { toast('District is required.', 'error'); return false; }
        if (!county.trim()) { toast('County is required.', 'error'); return false; }
        if (!subCounty.trim()) { toast('Sub-county is required.', 'error'); return false; }
        if (!parish.trim()) { toast('Parish is required.', 'error'); return false; }
        if (!village.trim()) { toast('Village is required.', 'error'); return false; }
        if (!area.trim()) { toast('Area is required.', 'error'); return false; }
        const checkPeople = (rows, what) => {
            for (let i = 0; i < rows.length; i++) {
                const o = rows[i];
                if (!o.nationalId.trim()) { toast(`${what} ${i + 1}: NIN is required.`, 'error'); return false; }
                if (!o.fullName.trim()) { toast(`${what} ${i + 1}: Full Name is required.`, 'error'); return false; }
                if (!o.phone.trim()) { toast(`${what} ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }
                const ph = normalizePhones(o.phone);
                if (!ph.ok) { toast(`${what} ${i + 1}: ${ph.error}`, 'error'); return false; }
            }
            return true;
        };
        if (!checkPeople(clients, 'Client') || !checkPeople(owners, 'Owner')) return false;
        for (let i = 0; i < neighbors.length; i++) {
            const nb = neighbors[i];
            if (!nb.fullName.trim()) { toast(`Neighbor ${i + 1}: Name is required (or remove the row).`, 'error'); return false; }
            if (nb.phone.trim() && !normalizePhones(nb.phone).ok) { toast(`Neighbor ${i + 1}: ${normalizePhones(nb.phone).error}`, 'error'); return false; }
        }
        if (isSubdivision && !(Number(subdivisionCount) >= 1 && Number.isInteger(Number(subdivisionCount)))) { toast('Enter the number of subdivisions (plots) being created.', 'error'); return false; }
        if (isTitleSectionVisible) {
            if (!plotNumber.trim()) { toast('Plot Number is required.', 'error'); return false; }
            if (!block.trim()) { toast('Block is required.', 'error'); return false; }
            if (!(Number(areaHectares) > 0)) { toast('Area (hectares) is required and must be more than 0.', 'error'); return false; }
            if (!titleIssueDate) { toast('Title Date is required.', 'error'); return false; }
        }
        if (!(Number(totalCost) > 0)) { toast('Total Cost must be greater than 0.', 'error'); return false; }
        if (initialPayment === '' || initialPayment === null || Number(initialPayment) < 0) { toast('Initial Payment is required (0 or more).', 'error'); return false; }
        // fix171: the same checks the server makes, so the message shows before anything is sent
        if (Number(initialPayment) > Number(totalCost)) { toast('Initial Payment cannot be more than the Total Cost.', 'error'); return false; }
        // fix172: the optional dates, and which owner paid the intake money
        const paidAny = (Number(initialPayment) || 0) > 0 || (isLegacy && (Number(initialStorageFeePaid) || 0) > 0);
        if (lastPaidDate && lastPaidDate > localISO()) { toast('Date Last Paid cannot be in the future.', 'error'); return false; }
        if (lastPaidDate && !paidAny) { toast('Date Last Paid needs a payment amount. Enter the payment, or clear the date.', 'error'); return false; }
        if (isLegacy && receivablesSince && receivablesSince > localISO()) { toast('In Receivables Since cannot be in the future.', 'error'); return false; }
        if (clients.length > 1) {
            if ((Number(initialPayment) || 0) > 0 && titlePayerIdx === '') { toast('Pick which client paid the Initial Payment.', 'error'); return false; }
            if (isLegacy && (Number(initialStorageFeePaid) || 0) > 0 && feesPayerIdx === '') { toast('Pick which client paid the Storage Fees Already Paid.', 'error'); return false; }
        }
        if (isLegacy) {
            fixFeeBox();   // fix173: 0 or negative monthly fee -> default, with a message
            const feeCharged = Number(initialStorageFee) || 0;
            const feePaid = Number(initialStorageFeePaid) || 0;
            if (feeCharged < 0 || feePaid < 0) { toast('Storage fees cannot be negative.', 'error'); return false; }
            if (!Number.isInteger(feePaid)) { toast('Storage Fees Already Paid: whole shillings only.', 'error'); return false; }
            const backlogNow = receivablesSince ? monthsSince(receivablesSince) * feeOrDefault(monthlyStorageFee) : 0;
            if (feePaid > feeCharged + backlogNow) { toast('Storage Fees Already Paid cannot be more than the fees charged (Initial Storage Fee plus the backlog fees).', 'error'); return false; }
            if (Number(initialPayment) >= Number(totalCost) && (feeCharged > 0 || feePaid > 0 || receivablesSince)) {
                toast('The title work is already fully paid, so this project will not be in receivables and cannot carry storage fees. Clear the storage fee boxes and the In Receivables Since date.', 'error'); return false;
            }
        }
        if (fileQueue.length === 0) { toast('At least one document is required.', 'error'); return false; }
        if (fileQueue.some(q => !q.category)) { toast('Pick a document type for every file.', 'error'); return false; }   // fix174
        return true;
    };

    const personOut = (o) => ({
        fullName: o.fullName.trim().toUpperCase(), phone: normalizePhones(o.phone).value || o.phone.trim(),
        email: o.email.trim().toLowerCase(), nationalId: o.nationalId.trim().toUpperCase(), address: o.address.trim(),
    });
    const doSave = async () => {
        if (!validate()) return false;
        setSaving(true);
        try {
            let noteText = notes.trim();
            if (noteText && !/^\[\d{2}\/\d{2}\/\d{4}\]/.test(noteText)) noteText = `[${todayDMY()}] ${noteText}`;
            const payload = {
                district: district.trim().toUpperCase(), county: county.trim().toUpperCase(),
                subCounty: subCounty.trim().toUpperCase(), parish: parish.trim().toUpperCase(),
                village: village.trim().toUpperCase(), area: area.trim().toUpperCase(),
                totalCost: Number(totalCost) || 0, initialPayment: Number(initialPayment) || 0,
                projectType, titleDetailsEnabled: projectType === 'TOPOGRAPHIC_SURVEY' && titleSwitch,
                isLegacy, projectStartDate: projectStartDate || todayISO(),
                clients: clients.map(personOut),
                owners: owners.map(personOut),
                neighbors: neighbors.filter(nb => nb.fullName.trim()).map(nb => ({
                    fullName: nb.fullName.trim().toUpperCase(), phone: nb.phone.trim() ? (normalizePhones(nb.phone).value || nb.phone.trim()) : '',
                    side: nb.side.trim().toUpperCase(), plotNumber: nb.plotNumber.trim().toUpperCase(),
                })),
                // Every status on the list is sent, not just the checked ones -- an unchecked status is still real
                // work ahead on this project, and the folder page needs it as a pending row.
                selectedStatuses: statusList.map(s => {
                    const m = masterTemplates.find(t => t.name === s.name);
                    const isCompleted = !!checked[s.name];
                    return m
                        ? { statusTemplateId: m.id, statusName: s.name, isCustom: false, isCompleted }
                        : { statusName: s.name, isCustom: true, cost: 0, isCompleted };
                }),
                notes: noteText ? [{ content: noteText }] : [],
            };
            if (isTitleSectionVisible) {
                payload.plotNumber = plotNumber.trim().toUpperCase();
                payload.tenure = tenure;
                payload.block = block.trim().toUpperCase();
                payload.areaHectares = Number(areaHectares);
                payload.volume = volume.trim().toUpperCase();
                payload.folio = folio.trim().toUpperCase();
                payload.titleIssueDate = titleIssueDate || null;
            }
            if (isSubdivision) payload.subdivisionCount = Number(subdivisionCount);
            if (transferFrom) { payload.parentProjectId = transferFrom.id; payload.parentSubdivisionNo = transferFrom.plot; }
            if (isLegacy) {
                payload.isStartAsReceivable = true;
                payload.initialStorageFee = Number(initialStorageFee) || 0;
                payload.initialStorageFeePaid = Number(initialStorageFeePaid) || 0;
                // fix173: send a rate only when one was typed that differs from the system default, so a project entered at the
                // default keeps FOLLOWING the default (before, every Legacy project was saved with its own copy of 50,000)
                const typedFee = Number(monthlyStorageFee) || 0;
                if (typedFee > 0 && typedFee !== systemFee) payload.monthlyStorageFee = typedFee;
            }
            // fix172: the optional dates, and which client paid the intake money (sent as that client's NIN)
            if (lastPaidDate) payload.lastPaidDate = lastPaidDate;
            if (isLegacy && receivablesSince) payload.receivablesSince = receivablesSince;
            const ninOf = (idx) => (idx !== '' && clients[idx]) ? clients[idx].nationalId.trim().toUpperCase() : '';
            if ((Number(initialPayment) || 0) > 0 && ninOf(titlePayerIdx)) payload.initialPaymentPayerNin = ninOf(titlePayerIdx);
            if (isLegacy && (Number(initialStorageFeePaid) || 0) > 0 && ninOf(feesPayerIdx)) payload.initialStorageFeePaidPayerNin = ninOf(feesPayerIdx);
            await landService.createAtomicEntry(payload, fileQueue.map(q => q.file), fileQueue.map(q => q.category));
            dirtyRef.current = false; setDirty(false);
            return true;
        } catch (err) {
            toast(err.response?.data?.message || 'Save failed', 'error');
            return false;
        } finally { setSaving(false); }
    };

    const handleSubmit = async () => {
        const ok = await doSave();
        if (ok) {
            toast('Project registered successfully!', 'success');
            // fix180: a transfer goes back to the subdivision it came from
            setTimeout(() => navigate(transferFrom ? '/folder/' + transferFrom.id : '/land/projects'), 1200);
        }
    };

    const handleDuplicate = async () => {
        const ok = await doSave();
        if (!ok) return;
        toast('Saved. Form duplicated for the next plot.', 'success');
        // fix180: the type, clients, owners and location stay (the next plot is usually the same job); title, neighbors,
        // money, files and notes start blank. A subdivision transfer cannot be duplicated onto the same plot.
        setProjectStartDate(todayISO()); setTransferFrom(null);
        setTenure('FREEHOLD'); setPlotNumber(''); setBlock(''); setAreaHectares(''); setVolume(''); setFolio(''); setTitleIssueDate('');
        setNeighbors([]); setSubdivisionCount('');
        setTotalCost(0); setInitialPayment(0); setInitialStorageFee(0); setInitialStorageFeePaid(0); setMonthlyStorageFee('');
        setLastPaidDate(''); setReceivablesSince(''); setTitlePayerIdx(''); setFeesPayerIdx('');   // fix172
        setNotes(''); setFileQueue(q => { q.forEach(x => URL.revokeObjectURL(x.url)); return []; });
        loadTypeStatuses(projectType);
        landService.getNextIndex().then(idx => { if (idx) { setNextIndex(idx); try { localStorage.setItem(INDEX_CACHE_KEY, idx); } catch {} } }).catch(() => {});
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // fix171: Amount Owed now includes the storage fees still unpaid (Legacy Title only, and only while the title work is not fully paid)
    const titleLeft = Math.max(0, (Number(totalCost) || 0) - (Number(initialPayment) || 0));
    // fix172: backlog fees = whole 30-day months since the In Receivables Since date x the monthly fee (only while the title work is not fully paid)
    const backlogMonths = isLegacy && titleLeft > 0 && receivablesSince ? monthsSince(receivablesSince) : 0;
    const backlogRate = feeOrDefault(monthlyStorageFee);
    const backlogFees = backlogMonths * backlogRate;
    const feesCharged = isLegacy ? Math.max(0, Number(initialStorageFee) || 0) + backlogFees : 0;
    const feesPaidNow = Math.min(feesCharged, Math.max(0, Number(initialStorageFeePaid) || 0));
    const amountOwed = titleLeft + (titleLeft > 0 ? feesCharged - feesPaidNow : 0);
    // fix172: removing a client must not leave a payer pointing at the wrong person
    const removeClient = (idx) => {
        changeClients(p => p.filter((_, i) => i !== idx));
        const shift = (cur) => (cur === '' || cur === idx ? '' : cur > idx ? cur - 1 : cur);
        setTitlePayerIdx(shift); setFeesPayerIdx(shift);
    };
    const removeOwner = (idx) => { setOwnersLinked(false); setOwners(p => p.filter((_, i) => i !== idx)); markDirty(); };
    const ownerLabels = clients.map((o, i) => (i + 1) + '. ' + (o.fullName.trim() ? o.fullName.trim().toUpperCase() : 'CLIENT ' + (i + 1)));
    const pickOwner = (setter) => (label) => { setter(ownerLabels.indexOf(label)); markDirty(); };
    const titlePaidNow = (Number(initialPayment) || 0) > 0;
    const feesPaidEntered = isLegacy && (Number(initialStorageFeePaid) || 0) > 0;
    let n = 0;
    const nIndex = ++n, nClients = ++n, nOwners = ++n;
    const nTitle = isTitleSectionVisible ? ++n : null;
    const nLocation = ++n, nNeighbors = ++n, nStatuses = ++n;
    const nFinancials = ++n, nDocuments = ++n, nNotes = ++n;
    // one Client / Owner row (same fields for both panels)
    const personRow = (o, idx, onChange, onRemove, canRemove, what) => (
        <div key={idx} className={styles.ownerRow}>
            <div className={styles.field}>
                <label className={`${styles.label} ${styles.required}`}>NIN</label>
                <input className={styles.input} value={o.nationalId} onChange={e => onChange(idx, 'nationalId', e.target.value)} />
            </div>
            <div className={styles.field}>
                <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                <input className={styles.input} value={o.fullName} onChange={e => onChange(idx, 'fullName', e.target.value)} />
            </div>
            <div className={styles.field}>
                <label className={`${styles.label} ${styles.required}`}>Phone</label>
                <input className={styles.input} value={o.phone} onChange={e => onChange(idx, 'phone', e.target.value)} onBlur={e => { const r = normalizePhones(e.target.value); if (r.ok && r.value !== e.target.value) onChange(idx, 'phone', r.value); }} placeholder="07XX XXX XXX / 07XX XXX XXX" />
                <p className={styles.hint}>Multiple: separate with /</p>
            </div>
            <div className={styles.field}>
                <label className={styles.label}>Email</label>
                <input className={styles.input} value={o.email} onChange={e => onChange(idx, 'email', e.target.value)} />
            </div>
            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`}
                onClick={() => onRemove(idx)} disabled={!canRemove} aria-label={'Remove ' + what}>
                <FiTrash2 />
            </button>
        </div>
    );

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
                    <div className={styles.grid3}>
                        <div className={styles.field}>
                            <label className={styles.label}>Index</label>
                            <div className={styles.indexDisplay}>{nextIndex || 'Loading...'}</div>
                            <p className={styles.hint}>Next available index, assigned on save</p>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Entry Date</label>
                            <div className={styles.indexDisplay}>{entryDate}</div>
                            <p className={styles.hint}>Automatically recorded when this is saved</p>
                        </div>
                        <div className={styles.field}>
                            <label className={styles.label}>Date Started</label>
                            <HardwareDatePicker block className={styles.input} value={projectStartDate} ariaLabel="Date started" onChange={v => { setProjectStartDate(v); markDirty(); }} />
                            <p className={styles.hint}>Defaults to today, edit if work started earlier</p>
                        </div>
                    </div>
                    <div className={styles.field}>
                        <label className={`${styles.label} ${styles.required}`}>Project Type</label>
                        <div className={styles.typeGroup} role="radiogroup" aria-label="Project type">
                            {PROJECT_TYPES.map(pt => (
                                <button key={pt.value} type="button" role="radio" aria-checked={projectType === pt.value}
                                    className={`${styles.typeBtn} ${projectType === pt.value ? styles.typeBtnActive : ''}`}
                                    disabled={!!transferFrom && pt.value !== 'TRANSFER_OF_TITLE'}
                                    onClick={() => handleProjectTypeChange(pt.value)}>
                                    {TYPE_ICONS[pt.value]}<span>{pt.label}</span>
                                </button>
                            ))}
                        </div>
                        <p className={styles.typeHint}>{TYPE_HINTS[projectType]}</p>
                    </div>
                    {transferFrom && (
                        <div className={styles.transferBanner} role="status">
                            <FiLink aria-hidden="true" /> Transfer of plot {transferFrom.plot} of subdivision #{transferFrom.index}. Clients and Owners were copied; Title Details and Neighbors start blank.
                        </div>
                    )}
                    {projectType === 'TOPOGRAPHIC_SURVEY' && (
                        <label className={styles.toggleRow}>
                            <input type="checkbox" className={styles.checkbox} checked={titleSwitch} onChange={e => { setTitleSwitch(e.target.checked); markDirty(); }} />
                            Add Title Details to this Topographic Survey
                        </label>
                    )}
                    {isSubdivision && (
                        <div className={styles.grid3}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Number of Subdivisions</label>
                                <input type="number" min="1" max="1000" step="1" className={styles.input} value={subdivisionCount} onChange={e => { setSubdivisionCount(e.target.value); markDirty(); }} />
                                <p className={styles.hint}>How many plots this subdivision creates. Each plot can be transferred later from the folder page.</p>
                            </div>
                        </div>
                    )}
                </CollapsibleSection>

                <CollapsibleSection icon={<FiUsers />} title={`${nClients}. Clients`}>
                    <p className={styles.linkNote}>The people who brought the work and pay for it. Recovery calls the clients.</p>
                    {clients.map((o, idx) => personRow(o, idx, updateClient, removeClient, clients.length > 1, 'client'))}
                    <button type="button" className={styles.addBtn} onClick={() => changeClients(p => [...p, EMPTY_OWNER()])}>
                        <FiPlus /> Add Client
                    </button>
                </CollapsibleSection>

                <CollapsibleSection icon={<FiUser />} title={`${nOwners}. Owners`}>
                    <div className={styles.linkNote}>
                        {ownersLinked
                            ? <span>The owners are a copy of the clients and follow them. Change any owner field to edit the owners on their own.</span>
                            : <><span>The owners are edited on their own.</span>
                                <button type="button" className={styles.clearLink} onClick={copyClientsToOwners}>Copy from clients again</button></>}
                    </div>
                    {owners.map((o, idx) => personRow(o, idx, updateOwner, removeOwner, owners.length > 1, 'owner'))}
                    <button type="button" className={styles.addBtn} onClick={() => { setOwnersLinked(false); setOwners(p => [...p, EMPTY_OWNER()]); markDirty(); }}>
                        <FiPlus /> Add Owner
                    </button>
                </CollapsibleSection>

                {isTitleSectionVisible && (
                    <CollapsibleSection icon={<FiFileText />} title={`${nTitle}. Title Details`} accent>
                        <div className={styles.grid3}>
                            <HardwareSelect label="Tenure" required options={TENURE_OPTIONS} value={tenure} onChange={(v) => { setTenure(v); markDirty(); }} />
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Plot Number</label>
                                <input className={styles.input} value={plotNumber} onChange={e => { setPlotNumber(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Block</label>
                                <input className={styles.input} value={block} onChange={e => { setBlock(e.target.value); markDirty(); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Area (hectares)</label>
                                <input type="number" min="0" step="0.0001" className={styles.input} value={areaHectares} onChange={e => { setAreaHectares(e.target.value); markDirty(); }} />
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
                                <label className={`${styles.label} ${styles.required}`}>Title Date</label>
                                <HardwareDatePicker block className={styles.input} value={titleIssueDate} ariaLabel="Title date" onChange={v => { setTitleIssueDate(v); markDirty(); }} />
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

                <CollapsibleSection icon={<FiUsers />} title={`${nNeighbors}. Neighbors`}>
                    {neighbors.length === 0 && <p className={styles.linkNote}>No neighbors added. Add the people whose land borders this plot.</p>}
                    {neighbors.map((nb, idx) => (
                        <div key={idx} className={`${styles.ownerRow} ${styles.neighborRow}`}>
                            <div className={styles.field}>
                                <label className={`${styles.label} ${styles.required}`}>Full Name</label>
                                <input className={styles.input} value={nb.fullName} onChange={e => updateNeighbor(idx, 'fullName', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Phone</label>
                                <input className={styles.input} value={nb.phone} onChange={e => updateNeighbor(idx, 'phone', e.target.value)} onBlur={e => { const r = normalizePhones(e.target.value); if (e.target.value.trim() && r.ok && r.value !== e.target.value) updateNeighbor(idx, 'phone', r.value); }} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Side</label>
                                <input className={styles.input} value={nb.side} placeholder="e.g. North" onChange={e => updateNeighbor(idx, 'side', e.target.value)} />
                            </div>
                            <div className={styles.field}>
                                <label className={styles.label}>Their Plot</label>
                                <input className={styles.input} value={nb.plotNumber} onChange={e => updateNeighbor(idx, 'plotNumber', e.target.value)} />
                            </div>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} aria-label="Remove neighbor"
                                onClick={() => { setNeighbors(p => p.filter((_, i) => i !== idx)); markDirty(); }}>
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                    <button type="button" className={styles.addBtn} onClick={() => { setNeighbors(p => [...p, EMPTY_NEIGHBOR()]); markDirty(); }}>
                        <FiPlus /> Add Neighbor
                    </button>
                </CollapsibleSection>

                <CollapsibleSection icon={<FiCheckSquare />} title={`${nStatuses}. Statuses`}
                    right={
                        <div style={{ display: 'flex', gap: 'var(--gap-md)', flexWrap: 'wrap', alignItems: 'center' }}>
                            {presets.length > 0 && (
                                <HardwareSelect compact placeholder="Apply preset..." value="" options={presets.map(p => p.name)} onChange={applyPreset} />
                            )}
                            <button type="button" className={styles.addBtn} onClick={() => setShowSavePreset(s => !s)}>
                                <FiBookmark /> Save Preset
                            </button>
                            <button type="button" className={styles.addBtn} onClick={handleRestoreDefaults}>
                                <FiRefreshCw /> Restore Defaults
                            </button>
                        </div>
                    }>
                    {showSavePreset && (
                        <div className={styles.inlineAddRow}>
                            <input className={styles.input} placeholder="Preset name" value={presetName} onChange={e => setPresetName(e.target.value)} />
                            <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleSavePreset}>Save</button>
                            <button type="button" className={styles.xBtn} onClick={() => { setShowSavePreset(false); setPresetName(''); }} aria-label="Close"><FiX /></button>
                        </div>
                    )}
                    {addingStatus && canAddStatus && (
                        <div className={styles.inlineAddRow}>
                            <span className={styles.insertCtx}>{insertAfterName ? `Insert under: ${insertAfterName}` : 'Add at the end'}</span>
                            <input className={styles.input} placeholder="New status name" value={newStatusName} onChange={e => setNewStatusName(e.target.value)} />
                            <button type="button" className={`${styles.btn} ${styles.primary}`} onClick={handleAddStatus}>Add</button>
                            <button type="button" className={styles.xBtn} onClick={() => { setAddingStatus(false); setNewStatusName(''); setInsertAfterName(''); }} aria-label="Close"><FiX /></button>
                        </div>
                    )}
                    <p className={styles.hint}>The {PROJECT_TYPES.find(pt => pt.value === projectType)?.label} status list. Tick what is already done.{canAddStatus ? '' : ' Only an Admin, Manager or Director can add a status.'}</p>
                    <div className={styles.statusList}>
                        {statusList.length === 0 && <p className={styles.hint}>Loading the status list...</p>}
                        {statusList.map((s) => {
                            const isFirst = s.name === firstStatusName;
                            return (
                                <label key={s.name} className={`${styles.statusItem} ${checked[s.name] ? styles.checked : ''}`}>
                                    <input type="checkbox" className={styles.checkbox} checked={!!checked[s.name]}
                                        disabled={isFirst}
                                        title={isFirst ? 'Always required before intake' : undefined}
                                        onChange={() => toggleStatus(s.name)} />
                                    <span className={styles.statusName}>{s.name}{isFirst ? ' (required)' : ''}</span>
                                    <span className={styles.statusActions}>
                                        {canAddStatus && (
                                            <button type="button" className={styles.plusBtn} title="Insert a status below this one"
                                                aria-label={`Insert status below ${s.name}`}
                                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); openInsertBelow(s.name); }}>
                                                <FiPlus size={12} />
                                            </button>
                                        )}
                                        {!isFirst && (
                                            <button type="button" className={`${styles.btn} ${styles.small} ${styles.deleteBtn}`}
                                                onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleDeleteStatus(s.name); }}
                                                aria-label={`Delete status ${s.name}`}>
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
                                    <button type="button" className={styles.presetChipRemove} onClick={() => deletePreset(p.name)} aria-label={`Delete preset ${p.name}`}>
                                        <FiX size={12} />
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                </CollapsibleSection>

                <CollapsibleSection icon={<FiDollarSign />} title={`${nFinancials}. Financials`}>
                    <div className={styles.grid2}>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>Total Cost</label>
                            <input type="number" className={styles.input} value={totalCost} onChange={e => { setTotalCost(e.target.value); markDirty(); }} />
                        </div>
                        <div className={styles.field}>
                            <label className={`${styles.label} ${styles.required}`}>{isLegacy ? 'Initial Payment (Title Work)' : 'Initial Payment'}</label>
                            <input type="number" min="0" className={styles.input} value={initialPayment} onChange={e => { setInitialPayment(e.target.value); markDirty(); }} />
                            {isLegacy && <p className={styles.hint}>Money paid toward the title work only. Storage fees already paid go in the Storage Fees box below.</p>}
                        </div>
                    </div>
                    {(titlePaidNow || feesPaidEntered) && (
                        <div className={styles.grid2}>
                            {clients.length > 1 && titlePaidNow && (
                                <div className={styles.field}>
                                    <HardwareSelect label="Initial Payment Paid By" required placeholder="Choose the client" options={ownerLabels} value={ownerLabels[titlePayerIdx] || ''} onChange={pickOwner(setTitlePayerIdx)} />
                                    <p className={styles.hint}>The client who paid the title work money. Each client's payments are tracked on a joint project.</p>
                                </div>
                            )}
                            <div className={styles.field}>
                                <label className={styles.label}>Date Last Paid</label>
                                <HardwareDatePicker block className={styles.input} value={lastPaidDate} ariaLabel="Date last paid" onChange={v => { setLastPaidDate(v); markDirty(); }} />
                                {lastPaidDate && <button type="button" className={styles.clearLink} onClick={() => { setLastPaidDate(''); markDirty(); }}>Clear date</button>}
                                <p className={styles.hint}>Optional. The day the client last paid. Left empty it counts as paid today, which locks recovery calls for 30 days.</p>
                            </div>
                        </div>
                    )}
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
                                    <input type="number" className={styles.input} value={monthlyStorageFee} placeholder={systemFee ? String(systemFee) : ''} onChange={e => { setMonthlyStorageFee(e.target.value); markDirty(); }} onBlur={fixFeeBox} />
                                    <p className={styles.hint}>System default: {systemFee ? systemFee.toLocaleString() : '...'}. Leave blank to use it. 0 or less is not allowed and turns into the default.</p>
                                </div>
                                <div className={styles.field}>
                                    <label className={styles.label}>Storage Fees Already Paid</label>
                                    <input type="number" min="0" className={styles.input} value={initialStorageFeePaid} onChange={e => { setInitialStorageFeePaid(e.target.value); markDirty(); }} />
                                    <p className={styles.hint}>Part of the fees charged (Initial Storage Fee plus backlog fees) that the client has already paid. Counted toward the fees, not the title work. It only counts as a recent payment if you set a Date Last Paid.</p>
                                </div>
                                {clients.length > 1 && feesPaidEntered && (
                                    <div className={styles.field}>
                                        <HardwareSelect label="Storage Fees Paid By" required placeholder="Choose the client" options={ownerLabels} value={ownerLabels[feesPayerIdx] || ''} onChange={pickOwner(setFeesPayerIdx)} />
                                        <p className={styles.hint}>The client who paid these storage fees.</p>
                                    </div>
                                )}
                                <div className={styles.field}>
                                    <label className={styles.label}>In Receivables Since</label>
                                    <HardwareDatePicker block className={styles.input} value={receivablesSince} ariaLabel="In receivables since" onChange={v => { setReceivablesSince(v); markDirty(); }} />
                                    {receivablesSince && <button type="button" className={styles.clearLink} onClick={() => { setReceivablesSince(''); markDirty(); }}>Clear date</button>}
                                    <p className={styles.hint}>
                                        Optional. If this project was already unpaid before today, pick the day it went into receivables.{' '}
                                        {backlogMonths > 0
                                            ? `${backlogMonths} month(s) x UGX ${backlogRate.toLocaleString()} = UGX ${backlogFees.toLocaleString()} backlog fees are added now. If you already typed those months into Initial Storage Fee, lower it so they are not counted twice.`
                                            : 'Fees are counted from that date. Empty = counted from today.'}
                                    </p>
                                </div>
                            </div>
                        </>
                    )}
                    <div className={styles.financialsSummary}>
                        <div className={styles.finRow}><span>Total Cost</span><span>{Number(totalCost) || 0}</span></div>
                        <div className={styles.finRow}><span>{isLegacy ? 'Initial Payment (Title Work)' : 'Initial Payment'}</span><span>{Number(initialPayment) || 0}</span></div>
                        {isLegacy && <div className={styles.finRow}><span>Initial Storage Fee</span><span>{Number(initialStorageFee) || 0}</span></div>}
                        {isLegacy && backlogMonths > 0 && <div className={styles.finRow}><span>Backlog Storage Fees ({backlogMonths} mo)</span><span>{backlogFees}</span></div>}
                        {isLegacy && <div className={styles.finRow}><span>Storage Fees Already Paid</span><span>{Number(initialStorageFeePaid) || 0}</span></div>}
                        <div className={`${styles.finRow} ${styles.total}`}><span>Amount Owed</span><span>{amountOwed}</span></div>
                    </div>
                </CollapsibleSection>

                <div className={styles.splitRow}>
                    <CollapsibleSection icon={<FiUploadCloud />} title={`${nDocuments}. Documents`}>
                        {fileQueue.length > 0 && (
                            <DocList>
                                {queueGroups.map(([cat, items]) => (
                                    <DocGroup key={cat} label={cat === '__NONE__' ? 'NO TYPE' : (catLabelOf(cat) || cat)} count={items.length}>
                                        {items.map(({ f, i }) => (
                                            <DocRow key={i} name={f.name} meta={fmtSize(f.size)} onView={() => openPreview(f)} onDelete={() => removeFile(i)} deleteTitle={'Remove ' + f.name} />
                                        ))}
                                    </DocGroup>
                                ))}
                            </DocList>
                        )}
                        <DocDropzone compact={fileQueue.length > 0} required onClick={triggerFileInput} />
                        <input ref={fileInputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={handleFileUpload} style={{ display: 'none' }} />
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

            <HardwareModal isOpen={!!uploadDraft} lockBackdrop onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
                {uploadDraft && (<>
                    <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>CATEGORY FOR ALL {uploadDraft.files.length} FILE(S)</label>
                        <HardwareModalSelect value={uploadDraft.batch} options={catOptions} onChange={setBatchCategory} placeholder="Choose category" emptyText="No categories available" ariaLabel="Category for all files" /></div>
                    <div className={styles.upFileList}>{uploadDraft.files.map((f, i) => (<div key={i} className={styles.upFileRow}>
                        <span className={styles.upFileName} title={f.file.name}>{f.file.name}</span>
                        <HardwareModalSelect compact className={styles.upFileSelect} value={f.category} options={catOptions} onChange={code => setDraftFileCategory(i, code)} placeholder="Category" emptyText="No categories available" ariaLabel={'Category for ' + f.file.name} /></div>))}</div>
                    {newCatOpen ? (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NEW CATEGORY NAME</label>
                        <input type="text" className={modalStyles.modalInput} value={newCatName} maxLength={120} placeholder="e.g. Survey Report" onChange={e => setNewCatName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleAddCategory(); }} />
                        <div className={styles.upCatActions}>
                            <button type="button" className={styles.upBtn} onClick={handleAddCategory} disabled={catBusy || newCatName.trim().length < 2}>SAVE CATEGORY</button>
                            <button type="button" className={styles.upBtn} onClick={() => { setNewCatOpen(false); setNewCatName(''); }}>CLOSE</button>
                        </div></div>)
                        : (<button type="button" className={styles.upBtn} onClick={() => setNewCatOpen(true)} title="Add a category that is not in the list yet">+ NEW CATEGORY</button>)}
                    {uploadDraft.error && <div className={styles.upErr} role="alert">{uploadDraft.error}</div>}
                    <div className={modalStyles.modalFooter}>
                        <button type="button" className={modalStyles.modalBtnPrimary} onClick={confirmUploadDraft}>ADD</button>
                    </div>
                </>)}
            </HardwareModal>
            {previewFile && typeof document !== 'undefined' && createPortal(
                <div className={styles.pvOverlay} onClick={() => setPreviewFile(null)} role="dialog" aria-modal="true" aria-label={previewFile.name}>
                    <div className={styles.pvPanel} onClick={e => e.stopPropagation()}>
                        <header className={styles.pvHead}>
                            <span className={styles.pvTitle} title={previewFile.name}>{previewFile.name}</span>
                            <span className={styles.pvTag}>{previewFile.ratio >= 1 ? 'Landscape' : 'Portrait'}</span>
                            <button type="button" className={modalStyles.closeBtn} onClick={() => setPreviewFile(null)} aria-label="Close preview" title="Close"><FiX aria-hidden="true" /></button>
                        </header>
                        <div className={styles.pvStage} style={{ '--pv-ratio': previewFile.ratio }}>
                            {previewFile.isPdf
                                ? <iframe className={styles.pvMedia} src={previewFile.url} title={previewFile.name} />
                                : <img className={`${styles.pvMedia} ${styles.pvImg}`} src={previewFile.url} alt={previewFile.name} />}
                        </div>
                    </div>
                </div>, document.body)}
            {blocker.state === 'blocked' && typeof document !== 'undefined' && createPortal(
                <div className={styles.modalOverlay} onClick={() => blocker.reset()}>
                    <div className={styles.modalCard} onClick={e => e.stopPropagation()}>
                        <h3 className={styles.modalTitle}>Unsaved work</h3>
                        <p className={styles.modalText}>You have unsaved information on this form. Save before leaving?</p>
                        <div className={styles.modalBtns}>
                            <button type="button" className={`${styles.btn} ${styles.deleteBtn}`} onClick={() => blocker.proceed()}>Leave</button>
                            <button type="button" className={`${styles.btn} ${styles.primary}`}
                                onClick={async () => { const ok = await doSave(); if (ok) blocker.proceed(); else blocker.reset(); }}>
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
