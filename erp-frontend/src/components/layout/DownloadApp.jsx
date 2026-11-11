// PATH: erp-frontend/src/components/layout/DownloadApp.jsx
// fix293 (David): the "Download app" button in the top bar. Puts the Golden Seed icon on the phone or laptop, straight
// from this page (no Play Store or App Store), and the app keeps updating by itself. Hidden once the app is installed.
// When the browser can install it, its own popup opens; otherwise (iPhone, or the browser is not ready yet) a sheet
// shows the steps for each kind of device.
import React, { useEffect, useState } from 'react';
import { FiDownload, FiSmartphone, FiMonitor } from 'react-icons/fi';
import HardwareModal from '../common/HardwareModal';
import { isInstalled, canPrompt, promptInstall, onInstallChange, deviceKind } from '../../utils/installApp';
import styles from './Header.module.css';

const STEPS = [
    { key: 'android', icon: FiSmartphone, title: 'Android phone (Chrome)', text: 'Tap the menu ⋮ at the top right, then Install app or Add to Home screen.' },
    { key: 'ios', icon: FiSmartphone, title: 'iPhone or iPad (Safari)', text: 'Open this page in Safari. Tap the Share button, then Add to Home Screen.' },
    { key: 'laptop', icon: FiMonitor, title: 'Laptop (Chrome or Edge)', text: 'Click the install icon at the right end of the address bar, or the menu ⋮ then Install Golden Seed.' },
];

export default function DownloadApp() {
    const [, bump] = useState(0);
    const [help, setHelp] = useState(false);
    useEffect(() => onInstallChange(() => bump((n) => n + 1)), []);
    if (isInstalled()) return null;

    const mine = deviceKind();
    const steps = [...STEPS].sort((a, b) => (a.key === mine ? -1 : b.key === mine ? 1 : 0));   // this device's steps first

    const press = async () => {
        if (canPrompt()) {
            const r = await promptInstall();
            if (r !== 'none') { bump((n) => n + 1); return; }
        }
        setHelp(true);
    };

    return (
        <>
            <button type="button" className={styles.downloadBtn} onClick={press} title="Put the Golden Seed app on this device" aria-label="Download the app">
                <FiDownload aria-hidden="true" /><span className={styles.downloadLbl}>Download app</span>
            </button>
            <HardwareModal isOpen={help} onClose={() => setHelp(false)} title="DOWNLOAD THE APP">
                <p className={styles.dlLead}>The app installs straight from this page. No Play Store or App Store is needed, and it updates by itself.</p>
                <div className={styles.dlSteps}>
                    {steps.map((s) => (
                        <div key={s.key} className={`${styles.dlStep} ${s.key === mine ? styles.dlStepMine : ''}`}>
                            <s.icon className={styles.dlIcon} aria-hidden="true" />
                            <div>
                                <strong className={styles.dlTitle}>{s.title}{s.key === mine ? ' (this device)' : ''}</strong>
                                <span className={styles.dlText}>{s.text}</span>
                            </div>
                        </div>
                    ))}
                </div>
                <p className={styles.dlFoot}>The Golden Seed icon then appears with your other apps. You sign in the same way, and everything stays the same.</p>
            </HardwareModal>
        </>
    );
}
