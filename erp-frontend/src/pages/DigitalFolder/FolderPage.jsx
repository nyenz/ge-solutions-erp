// PATH: erp-frontend/src/pages/DigitalFolder/FolderPage.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  FiMap, FiUsers, FiDollarSign, FiCheckSquare, FiUploadCloud, FiEdit3,
  FiTrash2, FiSave, FiX, FiFileText, FiArchive, FiEye, FiAlertOctagon, FiHome
} from 'react-icons/fi';
import CollapsibleSection from '../../components/ui/CollapsibleSection';
import HardwareSelect from '../../components/common/HardwareSelect';
import BackToTopButton from '../../components/common/BackToTopButton';
import landService from '../../services/landService';
import stageTemplateService from '../../services/stageTemplateService';
import recoveryService from '../../services/recoveryService';
import istyles from '../Intake/IntakePage.module.css';
import styles from './FolderPage.module.css';

const fmt = (n) => Number(n || 0).toLocaleString();
const TENURES = ['FREEHOLD', 'MAILO', 'LEASEHOLD', 'CUSTOMARY'];

export default function FolderPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ROLE_ADMIN' || user?.role === 'ROLE_DIRECTOR' || user?.isRoot;
  const [binder, setBinder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [buffer, setBuffer] = useState(null);
  const [stages, setStages] = useState([]);
  const [payOpen, setPayOpen] = useState(false);
  const [payAmount, setPayAmount] = useState('');
  const [payType, setPayType] = useState('TITLE');
  const [noteOpen, setNoteOpen] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [noteEditId, setNoteEditId] = useState(null);
  const [toasts, setToasts] = useState([]);
  const fileRef = useRef(null);
  const toast = useCallback((m, t = 'info') => { const id = Date.now()+Math.random(); setToasts(p => [...p, { id, m, t }]); setTimeout(() => setToasts(p => p.filter(x => x.id !== id)), 4000); }, []);

  const load = useCallback(async () => {
    try {
      const d = await landService.getDeepBinder(id);
      setBinder(d);
      const p = d.project;
      setBuffer({
        plotNumber: p.landTitle?.plotNumber || '', tenure: p.landTitle?.tenure || 'FREEHOLD',
        blockRoad: p.landTitle?.blockRoad || '', titleId: p.landTitle?.titleId || '',
        titleIssueDate: p.landTitle?.titleIssueDate || '',
        district: p.district || '', county: p.county || '', subCounty: p.subCounty || '',
        parish: p.parish || '', village: p.village || '', area: p.area || '',
        totalCost: String(p.totalCost || 0), initialPayment: String(p.amountPaid || 0),
        isLegacy: !!p.isLegacy,
        owners: (p.proprietors || []).map(o => ({ fullName: o.fullName||'', phone: o.phoneNumber||'', nationalId: o.nationalId||'', email: o.email||'', address: o.homeAddress||'' })),
      });
    } catch { toast('Could not load record', 'error'); }
    finally { setLoading(false); }
  }, [id, toast]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { stageTemplateService.getProjectStages(id).then(s => setStages(s || [])).catch(() => {}); }, [id, isEditing]);

  const p = binder?.project;
  if (loading || !p || !buffer) return <div className={istyles.container}><p className={istyles.hint}>Loading record…</p></div>;

  const isReceivable = !!p.isReceivable;
  const hasTitle = !!p.landTitle;
  const totalValue = Number(p.totalCost || 0);
  const paid = Number(p.amountPaid || 0);
  const storageFees = Number(p.storageFeesAccumulated || 0);
  const titleDebt = Math.max(0, totalValue - paid);
  const totalOwed = isReceivable ? titleDebt + storageFees : titleDebt;
  const set = (k, v) => setBuffer(b => ({ ...b, [k]: v }));

  const commit = async () => {
    setCommitting(true);
    try {
      await landService.updateMasterFolder(id, { ...buffer, totalCost: Number(buffer.totalCost)||0, initialPayment: Number(buffer.initialPayment)||0 });
      setIsEditing(false); toast('Changes saved', 'success'); await load();
    } catch (e) { toast('SAVE FAILED: ' + (e.response?.data?.message || e.message), 'error'); }
    finally { setCommitting(false); }
  };

  const recordPayment = async () => {
    if (!payAmount || Number(payAmount) <= 0) { toast('Enter a valid amount', 'error'); return; }
    try {
      await recoveryService.recordPayment(id, payAmount, payType === 'STORAGE' ? `[STORAGE FEE PAYMENT]` : '');
      setPayOpen(false); setPayAmount(''); toast('Payment recorded', 'success'); await load();
    } catch (e) { toast('PAYMENT FAILED: ' + (e.response?.data?.message || e.message), 'error'); }
  };

  const saveNote = async () => {
    if (!noteText.trim()) return;
    try {
      if (noteEditId) await landService.editStandaloneNote(noteEditId, noteText);
      else await landService.addStandaloneNote(id, noteText);
      setNoteOpen(false); setNoteText(''); setNoteEditId(null); toast('Note saved', 'success'); await load();
    } catch { toast('Note save failed', 'error'); }
  };

  const badge = (label, cls) => <span className={`${istyles.stageName} ${cls}`}>{label}</span>;

  return (
    <div className={istyles.container}>
      <header className={istyles.pageHeader}>
        <div className={istyles.headerLeft}>
          <h1 className={istyles.title}>{p.landTitle?.plotNumber || `#${p.projectIndex}`}</h1>
          <p className={istyles.subtitle}>Project Folder — {p.status}</p>
        </div>
        <div className={istyles.actions}>
          <span className={istyles.stageName}>{hasTitle ? (buffer.isLegacy ? 'LEGACY' : 'TITLED') : 'FOLDER'}</span>
          {isReceivable && <span className={istyles.cancelBtn} style={{padding:'4px 10px',borderRadius:6}}>RECEIVABLES</span>}
          {!isEditing && <button className={`${istyles.btn} ${istyles.primary}`} onClick={() => setIsEditing(true)}><FiEdit3 /> Edit</button>}
          {isEditing && (<>
            <button className={`${istyles.btn} ${istyles.cancelBtn}`} onClick={() => { setIsEditing(false); load(); }}>Cancel</button>
            <button className={`${istyles.btn} ${istyles.primary}`} onClick={commit} disabled={committing}><FiSave /> Save</button>
          </>)}
        </div>
      </header>

      <div className={istyles.sections}>
        <CollapsibleSection icon={<FiMap />} title="1. Details">
          <div className={istyles.grid3}>
            <div className={istyles.field}><label className={`${istyles.label} ${istyles.required}`}>District</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.district} onChange={e => set('district', e.target.value)} /></div>
            <div className={istyles.field}><label className={`${istyles.label} ${istyles.required}`}>County</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.county} onChange={e => set('county', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Sub-county</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.subCounty} onChange={e => set('subCounty', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Parish</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.parish} onChange={e => set('parish', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Village</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.village} onChange={e => set('village', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Area</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.area} onChange={e => set('area', e.target.value)} /></div>
          </div>
          <h3 className={istyles.subheading}><FiFileText size={13} /> Title {hasTitle ? '' : '(add details to upgrade folder → title)'}</h3>
          <div className={istyles.grid3}>
            <div className={istyles.field}><label className={istyles.label}>Title ID</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.titleId} onChange={e => set('titleId', e.target.value)} /></div>
            <HardwareSelect label="Tenure" options={TENURES} value={buffer.tenure} onChange={v => isEditing && set('tenure', v)} />
            <div className={istyles.field}><label className={istyles.label}>Plot Number</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.plotNumber} onChange={e => set('plotNumber', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Block</label>
              <input className={istyles.input} disabled={!isEditing} value={buffer.blockRoad} onChange={e => set('blockRoad', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Title Date</label>
              <input type="date" className={istyles.input} disabled={!isEditing} value={buffer.titleIssueDate} onChange={e => set('titleIssueDate', e.target.value)} /></div>
            <div className={istyles.field}><label className={istyles.label}>Legacy</label>
              <HardwareSelect options={['NO', 'YES']} value={buffer.isLegacy ? 'YES' : 'NO'} onChange={v => isEditing && set('isLegacy', v === 'YES')} /></div>
          </div>
        </CollapsibleSection>

        <CollapsibleSection icon={<FiUsers />} title="2. Owners">
          {buffer.owners.map((o, i) => (
            <div key={i} className={istyles.ownerRow}>
              <div className={istyles.field}><label className={istyles.label}>NIN</label><input className={istyles.input} disabled={!isEditing} value={o.nationalId} onChange={e => { const os=[...buffer.owners]; os[i].nationalId=e.target.value; set('owners',os); }} /></div>
              <div className={istyles.field}><label className={istyles.label}>Full Name</label><input className={istyles.input} disabled={!isEditing} value={o.fullName} onChange={e => { const os=[...buffer.owners]; os[i].fullName=e.target.value; set('owners',os); }} /></div>
              <div className={istyles.field}><label className={istyles.label}>Phone</label><input className={istyles.input} disabled={!isEditing} value={o.phone} onChange={e => { const os=[...buffer.owners]; os[i].phone=e.target.value; set('owners',os); }} /></div>
              <div className={istyles.field}><label className={istyles.label}>Email</label><input className={istyles.input} disabled={!isEditing} value={o.email} onChange={e => { const os=[...buffer.owners]; os[i].email=e.target.value; set('owners',os); }} /></div>
            </div>
          ))}
        </CollapsibleSection>

        <CollapsibleSection icon={<FiDollarSign />} title="3. Financials">
          <div className={istyles.financialsSummary}>
            <div className={istyles.finRow}><span>Plot Value</span><span>UGX {fmt(totalValue)}</span></div>
            <div className={istyles.finRow}><span>Paid</span><span>UGX {fmt(paid)}</span></div>
            <div className={istyles.finRow}><span>Title Debt</span><span>UGX {fmt(titleDebt)}</span></div>
            {isReceivable && <div className={istyles.finRow}><span>+ Storage Fees</span><span style={{color:'#ef4444'}}>UGX {fmt(storageFees)}</span></div>}
            <div className={`${istyles.finRow} ${istyles.total}`}><span>Total Owed</span><span>UGX {fmt(totalOwed)}</span></div>
          </div>
          {isAdmin && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
              <button className={`${istyles.btn} ${istyles.primary}`} onClick={() => setPayOpen(true)}><FiDollarSign /> Record Payment</button>
              {!isReceivable && <button className={`${istyles.btn} ${istyles.cancelBtn}`} onClick={async () => { await recoveryService.moveToReceivable(id); toast('Moved to receivables', 'warn'); load(); }}><FiAlertOctagon /> To Receivables</button>}
              {isReceivable && <button className={`${istyles.btn} ${istyles.primary}`} onClick={async () => { await recoveryService.exitReceivable(id, false); toast('Exited receivables', 'success'); load(); }}><FiHome /> Exit Receivables</button>}
            </div>
          )}
        </CollapsibleSection>

        <CollapsibleSection icon={<FiCheckSquare />} title="4. Stages">
          {stages.map(s => (
            <label key={s.id} className={istyles.stageItem}>
              <input type="checkbox" className={istyles.checkbox} checked={!!s.isCompleted} disabled={!isEditing}
                onChange={async () => { await stageTemplateService.toggleStageCompletion(id, s.id, !s.isCompleted); stageTemplateService.getProjectStages(id).then(setStages); }} />
              <span className={istyles.stageName}>{s.stageName}</span>
            </label>
          ))}
        </CollapsibleSection>

        <CollapsibleSection icon={<FiUploadCloud />} title={`5. Documents (${(binder.documents||[]).length})`}>
          {(binder.documents||[]).map((d, i) => (
            <div key={i} className={istyles.fileItem}>
              <span className={istyles.fileMeta}><span className={istyles.fileName}>{d.fileName}</span></span>
              <span className={istyles.fileActions}>
                <button className={`${istyles.btn} ${istyles.small}`} onClick={() => window.open(d.filePath, '_blank')}><FiEye size={12} /> View</button>
                {isEditing && <button className={`${istyles.btn} ${istyles.small} ${istyles.deleteBtn}`} onClick={async () => { await landService.deleteDocument(d.id); load(); }}><FiTrash2 size={12} /></button>}
              </span>
            </div>
          ))}
          {isEditing && <button className={istyles.addBtn} onClick={() => fileRef.current?.click()}><FiUploadCloud /> Upload</button>}
          <input ref={fileRef} type="file" multiple style={{ display: 'none' }} onChange={async e => { if (e.target.files?.length) { await landService.addExtraDocuments(id, Array.from(e.target.files)); load(); } }} />
        </CollapsibleSection>

        <CollapsibleSection icon={<FiEdit3 />} title={`6. Notes (${(binder.notes||[]).length})`}>
          {(binder.notes||[]).map((n, i) => (
            <div key={i} className={istyles.fileItem}>
              <span className={istyles.fileMeta}><span className={istyles.fileName}>{n.notes}</span></span>
              {isEditing && <span className={istyles.fileActions}>
                <button className={`${istyles.btn} ${istyles.small}`} onClick={() => { setNoteEditId(n.id); setNoteText(n.notes); setNoteOpen(true); }}><FiEdit3 size={12} /></button>
                <button className={`${istyles.btn} ${istyles.small} ${istyles.deleteBtn}`} onClick={async () => { await landService.deleteStandaloneNote(n.id); load(); }}><FiTrash2 size={12} /></button>
              </span>}
            </div>
          ))}
          <button className={istyles.addBtn} onClick={() => { setNoteEditId(null); setNoteText(''); setNoteOpen(true); }}><FiEdit3 /> Add Note</button>
        </CollapsibleSection>
      </div>

      {/* NOTE MODAL: only X + Save (no redundant Cancel) */}
      {noteOpen && createPortal(
        <div className={istyles.modalOverlay} onClick={() => setNoteOpen(false)}>
          <div className={istyles.modalCard} onClick={e => e.stopPropagation()}>
            <h3 className={istyles.modalTitle}>Add Note</h3>
            <textarea className={istyles.textarea} value={noteText} onChange={e => setNoteText(e.target.value)} />
            <div className={istyles.modalBtns}>
              <button className={`${istyles.btn} ${istyles.deleteBtn}`} onClick={() => setNoteOpen(false)} aria-label="Close"><FiX /></button>
              <button className={`${istyles.btn} ${istyles.primary}`} onClick={saveNote}><FiSave /> Save Entry</button>
            </div>
          </div>
        </div>, document.body)}

      {/* PAYMENT MODAL */}
      {payOpen && createPortal(
        <div className={istyles.modalOverlay} onClick={() => setPayOpen(false)}>
          <div className={istyles.modalCard} onClick={e => e.stopPropagation()}>
            <h3 className={istyles.modalTitle}>Record Payment</h3>
            <HardwareSelect label="Type" options={['TITLE', 'STORAGE']} value={payType} onChange={setPayType} />
            <input type="number" className={istyles.input} placeholder="Amount (UGX)" value={payAmount} onChange={e => setPayAmount(e.target.value)} />
            <div className={istyles.modalBtns}>
              <button className={`${istyles.btn} ${istyles.deleteBtn}`} onClick={() => setPayOpen(false)} aria-label="Close"><FiX /></button>
              <button className={`${istyles.btn} ${istyles.primary}`} onClick={recordPayment}><FiSave /> Confirm</button>
            </div>
          </div>
        </div>, document.body)}

      {typeof document !== 'undefined' && createPortal(
        <div className={istyles.toastStack}>{toasts.map(t => <div key={t.id} className={`${istyles.toast} ${istyles['toast_' + t.t]}`}>{t.m}</div>)}</div>, document.body)}

      <BackToTopButton />
    </div>
  );
}