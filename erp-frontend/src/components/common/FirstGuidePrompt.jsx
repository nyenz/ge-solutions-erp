// PATH: erp-frontend/src/components/common/FirstGuidePrompt.jsx
// fix262 (David): a new account is offered the short guide of its own rank at its first visit, with a SKIP. Either
// answer is saved on the server, so it is never offered again (on any device). Not shown while the key must be changed.
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FiPlayCircle } from 'react-icons/fi';
import HardwareModal from './HardwareModal';
import api from '../../api/axios';
import { useAuth } from '../../hooks/useAuth';
import styles from './FirstGuidePrompt.module.css';

const FirstGuidePrompt = () => {
    const { user, updateSession } = useAuth();
    const navigate = useNavigate();
    const { pathname } = useLocation();
    const [closed, setClosed] = useState(false);
    const open = !!(user && user.showGuide && !user.mustChangePassword && !closed && pathname !== '/guide');

    const answer = (watch) => {
        setClosed(true);
        updateSession({ user: { ...user, showGuide: false } });
        api.post('/profile/guide-seen').catch(() => { /* asked again next time if this did not reach the server */ });
        if (watch) navigate('/guide');
    };

    return (
        <HardwareModal isOpen={open} onClose={() => answer(false)} title="WELCOME TO GOLDEN SEED">
            <p className={styles.text}>
                New here? A short guide plays the main tasks of your work step by step, with pictures of this system.
                It takes a few minutes. You can open it again any time from GUIDE in the menu.
            </p>
            <div className={styles.row}>
                <button type="button" className={styles.watch} onClick={() => answer(true)}><FiPlayCircle aria-hidden="true" /> WATCH THE GUIDE</button>
                <button type="button" className={styles.skip} onClick={() => answer(false)}>SKIP</button>
            </div>
        </HardwareModal>
    );
};

export default FirstGuidePrompt;
