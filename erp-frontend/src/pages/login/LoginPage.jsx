// PATH: erp-frontend/src/pages/login/LoginPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import authService from '../../services/authService';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import { FiShield, FiEye, FiEyeOff, FiCheckCircle } from 'react-icons/fi';
import styles from './LoginPage.module.css';

const LoginPage = () => {
    const [creds, setCreds] = useState({ username: '', password: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(() => {
        // Check if we were redirected due to a session conflict
        const params = new URLSearchParams(window.location.search);
        if (params.get('reason') === 'session_conflict') {
            return 'SECURITY: Your session was terminated because this account logged in from another browser.';
        }
        if (params.get('reason') === 'idle_timeout') {
            return 'SESSION EXPIRED: You were logged out after 30 minutes of inactivity.';
        }
        return '';
    });
    
    // RECOVERY STATE
    const [isRecovering, setIsRecovering] = useState(false);
    const [recoveryEmail, setRecoveryEmail] = useState('');
    const [recoveryLoading, setRecoveryLoading] = useState(false);
    const [recoverySuccess, setRecoverySuccess] = useState('');

    const { login } = useAuth();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await authService.login(creds.username, creds.password);
            login(data);
        } catch (err) {
            setError(err.message === "IDENTIFICATION_FAILED" ? "WRONG CREDENTIALS" : err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRecovery = async () => {
        if (!recoveryEmail) return;
        setRecoveryLoading(true);
        setRecoverySuccess('');
        try {
            const msg = await authService.recoverPassword(recoveryEmail);
            setRecoverySuccess(msg);
            // Modal stays open to show the success message
        } catch (err) {
            alert(err.message);
        } finally {
            setRecoveryLoading(false);
        }
    };

    return (
        <div className={styles.pageWrapper}>
            <div className={styles.card}>
                <div className={`${styles.pins} ${styles.top}`}>{[...Array(6)].map((_, i) => <div key={i} className={styles.pin}></div>)}</div>
                <div className={`${styles.pins} ${styles.bottom}`}>{[...Array(6)].map((_, i) => <div key={i} className={styles.pin}></div>)}</div>
                
                <div className={styles.logoRow}>
                    <div className={styles.logoOuter}>
                        <div className={styles.logoPulse}></div>
                        <div className={styles.logoInner}>🌱</div>
                    </div>
                    <h1 className={styles.title}>Golden Seed</h1>
                    <p className={styles.subtitle}>Enterprise Portal</p>
                </div>

                <div className={styles.divider}><div className={styles.dot}></div></div>
                {error && <div className={styles.errorAlert}>{error}</div>}

                <form onSubmit={handleLogin} className={styles.form}>
                    <div className={styles.field}>
                        <label>USERNAME</label>
                        <input type="text" className={styles.input} value={creds.username} onChange={(e) => setCreds({...creds, username: e.target.value})} required autoComplete="username" />
                    </div>

                    <div className={styles.field}>
                        <label>PASSWORD</label>
                        <div className={styles.inputWrap}>
                            <input type={showPassword ? "text" : "password"} className={styles.input} value={creds.password} onChange={(e) => setCreds({...creds, password: e.target.value})} required autoComplete="current-password" />
                            <button type="button" className={styles.eyeBtn} onClick={() => setShowPassword(!showPassword)}><FiEye /></button>
                        </div>
                    </div>

                    <div className={styles.btnWrap}>
                        <HardwareButton type="submit" loading={loading} icon={FiShield}>Authorize</HardwareButton>
                    </div>
                </form>

                <div className={styles.footer}>
                    <button className={styles.lostBtn} onClick={() => { setIsRecovering(true); setRecoverySuccess(''); }}>Lost Master Key?</button>
                    <p className={styles.audit}>Logins are Audited for Accountability.</p>
                </div>
            </div>

            {/* MODAL: MASTER RECOVERY */}
            <HardwareModal isOpen={isRecovering} onClose={() => setIsRecovering(false)} title="MASTER RECOVERY">
                <div className={styles.modalBody}>
                    {recoverySuccess ? (
                        <div className={styles.successScreen}>
                            <FiCheckCircle size={50} color="#10b981" />
                            <p className={styles.successMsg}>{recoverySuccess}</p>
                            <HardwareButton onClick={() => setIsRecovering(false)}>Return to Login</HardwareButton>
                        </div>
                    ) : (
                        <>
                            <div className={styles.field}>
                                <label>Registered Owner Email</label>
                                <input type="email" className={styles.input} placeholder="admin@golden-seed.com" value={recoveryEmail} onChange={(e) => setRecoveryEmail(e.target.value)} />
                            </div>
                            <div className={styles.btnWrap}>
                                <HardwareButton loading={recoveryLoading} onClick={handleRecovery}>Transmit Reset</HardwareButton>
                            </div>
                        </>
                    )}
                </div>
            </HardwareModal>
        </div>
    );
};

export default LoginPage;