// PATH: erp-frontend/src/pages/Guide/GuidePage.jsx
// fix231 (David): the GUIDE page -- an auto-playing, step-by-step guide per rank and per task, made of real pictures of
// this app (recorded on demo data by e2e/guide.mjs). The player itself is public/guide/index.html (the same file is the
// shareable guide), shown here full size and opened on the tasks of the person's own rank.
import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { roleFlags } from '../../utils/roles';
import styles from './GuidePage.module.css';

const rankOf = (f) => (f.isEmployee ? 'Employee' : f.isOwnerLevel ? 'Director' : f.isManager ? 'Manager' : 'Secretary');

const GuidePage = () => {
    const { user } = useAuth();
    const f = roleFlags(user);
    const src = '/guide/index.html?role=' + encodeURIComponent(rankOf(f));
    return (
        <div className={styles.wrap}>
            <iframe className={styles.frame} src={src} title="Golden Seed guide: how to use the system, step by step" />
        </div>
    );
};

export default GuidePage;
