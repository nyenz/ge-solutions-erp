import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import styles from './ClientPortfolioPage.module.css';

const API = import.meta.env?.VITE_API_URL || '';

const fmt = (n) => Number(n || 0).toLocaleString();

const pct = (owed, paid) => {
  const total = Number(owed || 0) + Number(paid || 0);
  if (!total) return 0;
  return Math.round((Number(paid || 0) / total) * 100);
};

export default function ClientPortfolioPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [dossier, setDossier]   = useState(null);
  const [loading, setLoading]   = useState(true);
  const [editing, setEditing]   = useState(null);   // plot id currently being edited
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving]     = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/api/clients/${id}/dossier`);
      setDossier(r.data);
    } catch (e) {
      console.error('[portfolio] load failed', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);

  const projects = useMemo(
    () => groupByProject(dossier?.plots || []),
    [dossier]
  );

  const startEdit = (plot) => {
    setEditing(plot.id);
    setEditForm({
      index:    plot.projectIndex ?? '',
      district: plot.district     ?? '',
      owed:     plot.owed         ?? 0,
      paid:     plot.paid         ?? 0,
      storage:  plot.storage      ?? 0,
      titled:     !!plot.titled,
      receivable: !!plot.receivable,
    });
  };

  const cancelEdit = () => { setEditing(null); setEditForm({}); };

  const saveEdit = async (plotId) => {
    setSaving(true);
    try {
      await axios.patch(`${API}/api/clients/${id}/plots/${plotId}`, {
        projectIndex: editForm.index,
        district:     editForm.district,
        owed:         Number(editForm.owed || 0),
        paid:         Number(editForm.paid || 0),
        storage:      Number(editForm.storage || 0),
        titled:       editForm.titled,
        receivable:   editForm.receivable,
      });
      await load();
      cancelEdit();
    } catch (e) {
      console.error('[portfolio] save failed', e);
      alert('Failed to save. Check console / API endpoint.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className={styles.page}><div className={styles.loading}>Loading portfolio…</div></div>;
  }
  if (!dossier) {
    return <div className={styles.page}><div className={styles.empty}>No dossier found.</div></div>;
  }

  return (
    <div className={styles.page}>

      {/* IDENTITY -------------------------------------------------- */}
      <section className={styles.card}>
        <header className={styles.cardHeader}>
          <h2>Client Identity</h2>
          <span className={styles.muted}>#{dossier.clientNo || dossier.id}</span>
        </header>
        <div className={styles.grid}>
          <Field label="Full Name"  value={dossier.fullName || dossier.name} />
          <Field label="Phone"      value={dossier.phone} />
          <Field label="Email"      value={dossier.email} />
          <Field label="Type"       value={dossier.clientType} />
          <Field label="Status"     value={dossier.status} />
          <Field label="Joined"     value={(dossier.createdAt || '').slice(0, 10)} />
        </div>
      </section>

      {/* TOTALS ---------------------------------------------------- */}
      <section className={styles.card}>
        <header className={styles.cardHeader}>
          <h2>Portfolio Totals</h2>
          <span className={styles.muted}>
            {projects.length} project{projects.length === 1 ? '' : 's'}
          </span>
        </header>
        <div className={styles.totalsGrid}>
          <Total label="Total Owed"    value={fmt(dossier.totalOwed)}    tone="warn" />
          <Total label="Total Paid"    value={fmt(dossier.totalPaid)}    tone="good" />
          <Total label="Storage Fees"  value={fmt(dossier.totalStorage)} />
          <Total label="Recovery %"    value={`${pct(dossier.totalOwed, dossier.totalPaid)}%`} tone="good" />
        </div>
      </section>

      {/* PROJECTS -------------------------------------------------- */}
      <section className={styles.card}>
        <header className={styles.cardHeader}>
          <h2>Projects &amp; Indexes</h2>
        </header>

        {projects.length === 0 && (
          <div className={styles.empty}>No projects linked to this client.</div>
        )}

        {projects.map((p) => (
          <div key={p.projectId ?? 'orphan'} className={styles.projectBlock}>
            <div className={styles.projectHead}>
              <div>
                <h3 className={styles.projectTitle}>
                  {p.projectName || `Project ${p.projectIndex ?? '—'}`}
                </h3>
                <span className={styles.muted}>
                  Project Index: {p.projectIndex ?? '—'} &middot; {p.plots.length} plot{p.plots.length === 1 ? '' : 's'}
                </span>
              </div>
              <span className={p.isJoint ? styles.badgeJoint : styles.badgeIndividual}>
                {p.isJoint ? 'JOINT' : 'INDIVIDUAL'}
              </span>
            </div>

            <div className={styles.totalsGridSmall}>
              <Total label="Owed"        value={fmt(p.owed)}    tone="warn" />
              <Total label="Paid"        value={fmt(p.paid)}    tone="good" />
              <Total label="Storage"     value={fmt(p.storage)} />
              <Total label="Recovery %"  value={`${pct(p.owed, p.paid)}%`} tone="good" />
            </div>

            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Index</th>
                  <th>District</th>
                  <th>Status</th>
                  <th className={styles.right}>Owed</th>
                  <th className={styles.right}>Paid</th>
                  <th className={styles.right}>Storage</th>
                  <th className={styles.right}>Recovery&nbsp;%</th>
                  <th className={styles.right}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {p.plots.map((plot) => {
                  const isEdit = editing === plot.id;
                  return (
                    <tr key={plot.id} className={isEdit ? styles.rowEditing : ''}>
                      <td>
                        {isEdit
                          ? <input className={styles.input} value={editForm.index}
                                   onChange={(e) => setEditForm((f) => ({ ...f, index: e.target.value }))} />
                          : (plot.projectIndex ?? '—')}
                      </td>
                      <td>
                        {isEdit
                          ? <input className={styles.input} value={editForm.district}
                                   onChange={(e) => setEditForm((f) => ({ ...f, district: e.target.value }))} />
                          : (plot.district || '—')}
                      </td>
                      <td>
                        <span className={
                          plot.titled ? styles.dotGood
                          : plot.receivable ? styles.dotWarn
                          : styles.dotNeutral
                        }>
                          {plot.titled ? 'TITLED' : plot.receivable ? 'RECEIVABLE' : 'FOLDER'}
                        </span>
                      </td>
                      <td className={styles.right}>
                        {isEdit
                          ? <input type="number" className={styles.inputSm} value={editForm.owed}
                                   onChange={(e) => setEditForm((f) => ({ ...f, owed: e.target.value }))} />
                          : fmt(plot.owed)}
                      </td>
                      <td className={styles.right}>
                        {isEdit
                          ? <input type="number" className={styles.inputSm} value={editForm.paid}
                                   onChange={(e) => setEditForm((f) => ({ ...f, paid: e.target.value }))} />
                          : fmt(plot.paid)}
                      </td>
                      <td className={styles.right}>
                        {isEdit
                          ? <input type="number" className={styles.inputSm} value={editForm.storage}
                                   onChange={(e) => setEditForm((f) => ({ ...f, storage: e.target.value }))} />
                          : fmt(plot.storage)}
                      </td>
                      <td className={styles.right}>{pct(plot.owed, plot.paid)}%</td>
                      <td className={styles.right}>
                        {isEdit ? (
                          <div className={styles.actions}>
                            <button className={styles.btnSave} disabled={saving} onClick={() => saveEdit(plot.id)}>
                              {saving ? '…' : 'Save'}
                            </button>
                            <button className={styles.btnGhost} onClick={cancelEdit}>Cancel</button>
                          </div>
                        ) : (
                          <div className={styles.actions}>
                            <button className={styles.btnEdit} onClick={() => startEdit(plot)}>Edit</button>
                            <button className={styles.btnGhost} onClick={() => navigate(`/folder/${plot.projectId}`)}>
                              Open
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}
      </section>

      {/* CALL LOG -------------------------------------------------- */}
      <section className={styles.card}>
        <header className={styles.cardHeader}>
          <h2>Call Log</h2>
        </header>
        {(!dossier.calls || dossier.calls.length === 0) && (
          <div className={styles.empty}>No calls logged.</div>
        )}
        {dossier.calls?.map((c, i) => (
          <div key={i} className={styles.callRow}>
            <span className={styles.callDate}>{(c.date || '').slice(0, 10) || '—'}</span>
            <span className={styles.callNote}>{c.note || c.summary || '—'}</span>
          </div>
        ))}
      </section>

    </div>
  );
}

/* ---------------- helpers ---------------- */

function Field({ label, value }) {
  return (
    <div className={styles.field}>
      <span className={styles.fieldLabel}>{label}</span>
      <span className={styles.fieldValue}>{value || '—'}</span>
    </div>
  );
}

function Total({ label, value, tone }) {
  return (
    <div className={styles.total}>
      <span className={styles.totalLabel}>{label}</span>
      <span className={`${styles.totalValue} ${tone ? styles['tone_' + tone] : ''}`}>{value}</span>
    </div>
  );
}

function groupByProject(plots) {
  const map = new Map();
  plots.forEach((p) => {
    const key = p.projectId ?? '__orphan__';
    if (!map.has(key)) {
      map.set(key, {
        projectId:    p.projectId,
        projectIndex: p.projectIndex,
        projectName:  p.projectName,
        isJoint:      !!(p.isJoint || p.joint),
        plots:        [],
        owed:         0,
        paid:         0,
        storage:      0,
      });
    }
    const g = map.get(key);
    g.plots.push(p);
    g.owed    += Number(p.owed    || 0);
    g.paid    += Number(p.paid    || 0);
    g.storage += Number(p.storage || 0);
    if (p.isJoint || p.joint) g.isJoint = true;
    if (!g.projectIndex && p.projectIndex) g.projectIndex = p.projectIndex;
    if (!g.projectName  && p.projectName)  g.projectName  = p.projectName;
  });
  return Array.from(map.values());
}
