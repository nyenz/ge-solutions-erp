// PATH: erp-frontend/src/components/common/DocParts.jsx
// fix179: ONE shared document section design for the Folder page and the Intake page.
//   DocList     the dark inset plane that holds the groups (Folder look)
//   DocGroup    orange uppercase type heading + count (Folder look)
//   DocRow      icon, plain name (no white bar), meta, View (Intake look), delete / LOCKED
//   DocDropzone big upload zone when empty, slim "Add more documents" bar once files exist (Intake look)
// Pages pass their own copy-in props only; the look lives here so the two pages can never drift apart again.
import React from 'react';
import { FiFileText, FiEye, FiTrash2, FiUploadCloud } from 'react-icons/fi';
import { DOC_KINDS_TEXT } from '../../utils/imageShrink';
import s from './DocParts.module.css';

export function DocList({ capped = false, className = '', children }) {
    return <div className={`${s.list} ${capped ? s.listCapped : ''} ${className}`.trim()}>{children}</div>;
}

export function DocGroup({ label, count, children }) {
    return (
        <>
            <div className={s.groupLabel}>{label}{count != null && <span className={s.groupCount}>{count}</span>}</div>
            {children}
        </>
    );
}

export function DocRow({ name, meta, metaTitle, onView, onDelete, deleteTitle, locked = false, lockTitle, className = '' }) {
    return (
        <div className={`${s.row} ${className}`.trim()}>
            <FiFileText className={s.icon} aria-hidden="true" />
            <span className={s.name} title={name}>{name}</span>
            {meta ? <span className={s.meta} title={metaTitle}>{meta}</span> : null}
            <span className={s.actions}>
                <button type="button" className={s.btn} onClick={onView} aria-label={'View ' + name} title={'View ' + name}>
                    <FiEye size={12} aria-hidden="true" /> View
                </button>
                {onDelete && (
                    <button type="button" className={`${s.btn} ${s.btnDel}`} onClick={onDelete} aria-label={'Delete ' + name} title={deleteTitle || 'Delete this document'}>
                        <FiTrash2 size={12} aria-hidden="true" />
                    </button>
                )}
                {locked && <span className={s.lock} title={lockTitle}>LOCKED</span>}
            </span>
        </div>
    );
}

export function DocDropzone({ compact = false, required = false, onClick, className = '', title }) {
    const act = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick && onClick(); } };
    return (
        <div className={`${s.zone} ${compact ? s.zoneCompact : ''} ${className}`.trim()} onClick={onClick} onKeyDown={act} role="button" tabIndex={0} title={title}>
            <span className={s.zoneIcon}><FiUploadCloud size={compact ? 13 : 18} aria-hidden="true" /></span>
            {compact ? (
                <span className={s.zoneTitle}>Add more documents</span>
            ) : (
                <>
                    <span className={s.zoneTitle}>Click to upload{required && <span className={s.req}>*</span>}</span>
                    <span className={s.zoneSub}>{required ? 'Required - ' : ''}{DOC_KINDS_TEXT}, up to 50 MB each</span>
                </>
            )}
        </div>
    );
}
