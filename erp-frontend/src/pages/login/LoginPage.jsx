// PATH: erp-frontend/src/pages/login/LoginPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import authService from '../../services/authService';
import api from '../../api/axios';
import { errorText } from '../../utils/errorText';
import HardwareButton from '../../components/common/HardwareButton';
import HardwareModal from '../../components/common/HardwareModal';
import { FiShield, FiEye, FiEyeOff, FiInfo } from 'react-icons/fi';
import styles from './LoginPage.module.css';

const LoginPage = () => {
    // ALL useState hooks must come before any conditional returns (React rules)
    const [creds, setCreds] = useState({ username: '', password: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('reason') === 'session_conflict') {
            return 'You were signed out: this account signed in somewhere else, signed out, or its key or rank was changed.';
        }
        if (params.get('reason') === 'session_expired') {
            return 'Your sign-in expired. Please sign in again.';
        }
        if (params.get('reason') === 'suspended') {
            return 'This account is suspended. Ask the Director.';
        }
        if (params.get('reason') === 'other_account') {
            return 'Another account signed in on this device. Sign in again.';
        }
        if (params.get('reason') === 'idle_timeout') {
            return 'You were signed out after 30 minutes without use.';
        }
        return '';
    });
    const [isRecovering, setIsRecovering] = useState(false);
    const { login } = useAuth();

    // fix181 (15.2l): no fixed 900 ms wait. Ask the server if it is awake; the "waking up" screen shows only while that
    // call has taken more than a second (this also wakes a sleeping server early, so the first sign-in is faster).
    const [waking, setWaking] = useState(false);
    useEffect(() => {
        let done = false;
        const slow = setTimeout(() => { if (!done) setWaking(true); }, 1000);
        api.get('/auth/health', { timeout: 65000 })
            .catch(() => { /* a dead server shows its error when the person signs in */ })
            .finally(() => { done = true; clearTimeout(slow); setWaking(false); });
        return () => { done = true; clearTimeout(slow); };
    }, []);

    if (waking) {
        return (
            <div className={styles.appLoadScreen}>
                <div className={styles.loadLogo}>
                    <div className={styles.loadPulseOuter} />
                    <div className={styles.loadPulseInner}>
                        <span className={styles.loadEmoji}>🌱</span>
                    </div>
                </div>
                <div className={styles.loadBarWrap}>
                    <div className={styles.loadBar} />
                </div>
                <p className={styles.loadLabel}>GOLDEN SEED ERP</p>
                <p className={styles.loadSub}>The server is waking up, up to 60 seconds on the free plan...</p>
                <button type="button" className={styles.lostBtn} onClick={() => setWaking(false)}>Show the sign-in form now</button>
            </div>
        );
    }

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const data = await authService.login(creds.username.trim(), creds.password);
            login(data);
        } catch (err) {
            // fix181 (15.2c): read the code before the colon and show its plain sentence (utils/errorText.js)
            const msg = err.message || '';
            if (msg === 'SERVER_STARTING_UP') setError('The server is waking up (up to 60 seconds on the free plan). Wait a moment and try again.');
            else if (!msg || msg === 'Network Error' || msg === 'COMMUNICATION_FAULT') setError('Could not reach the server. Check the internet and try again.');
            else setError(errorText({ response: { status: 400, data: { message: msg } } }));
        } finally {
            setLoading(false);
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
                        <label htmlFor="login-username">USERNAME</label>
                        {/* fix181 (15.2d): phones must not capitalise, correct or add a space to the username */}
                        <input id="login-username" name="username" type="text" className={styles.input} value={creds.username}
                            onChange={(e) => setCreds({...creds, username: e.target.value})} onBlur={() => setCreds(c => ({ ...c, username: c.username.trim() }))}
                            required autoComplete="username" autoCapitalize="none" autoCorrect="off" spellCheck={false} />
                    </div>

                    <div className={styles.field}>
                        <label htmlFor="login-password">PASSWORD</label>
                        <div className={styles.inputWrap}>
                            <input id="login-password" name="password" type={showPassword ? "text" : "password"} className={styles.input} value={creds.password} onChange={(e) => setCreds({...creds, password: e.target.value})} required autoComplete="current-password" />
                            <button type="button" className={styles.eyeBtn} onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide the key' : 'Show the key'}>{showPassword ? <FiEyeOff /> : <FiEye />}</button>
                        </div>
                    </div>

                    <div className={styles.btnWrap}>
                        <HardwareButton type="submit" loading={loading} icon={FiShield}>Authorize</HardwareButton>
                    </div>
                </form>

                <div className={styles.footer}>
                    <button type="button" className={styles.lostBtn} onClick={() => setIsRecovering(true)}>Forgot your key?</button>
                    <p className={styles.audit}>Logins are Audited for Accountability.</p>
                </div>
            </div>

            {/* fix181 (15.3, owner choice B): email recovery is off; nobody's key can be reset from this page */}
            <HardwareModal isOpen={isRecovering} onClose={() => setIsRecovering(false)} title="FORGOT YOUR KEY?">
                <div className={styles.modalBody}>
                    <div className={styles.successScreen}>
                        <div className={styles.successIconWrap}><FiInfo size={28} color="#38bdf8" /></div>
                        <p className={styles.successMsg}>
                            Staff: ask the Director to reset your key.<br />
                            Director: ask the Admin.<br />
                            Admin: use the owner recovery.
                        </p>
                        <div className={styles.btnWrap} style={{ marginTop: '10px' }}>
                            <HardwareButton onClick={() => setIsRecovering(false)}>Back to sign in</HardwareButton>
                        </div>
                    </div>
                </div>
            </HardwareModal>
        </div>
    );
};

export default LoginPage;