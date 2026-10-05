// PATH: erp-frontend/src/context/AuthProvider.jsx
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { AuthContext } from './AuthContext';
import api, { markActivity } from '../api/axios';
import { forget as forgetPageCache } from '../utils/pageCache';

// fix181 (14.2d): the username inside the token (the "sub" claim); null when it cannot be read
const tokenUser = (t) => {
    try { return JSON.parse(atob(String(t).split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).sub || null; } catch { return null; }
};
const readUser = () => { try { return JSON.parse(localStorage.getItem('gs_user') || 'null'); } catch { return null; } };

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => {
        const t = localStorage.getItem('gs_token');
        const u = readUser();
        // fix181 (14.2d): the saved user must be the person inside the token; otherwise start signed out
        if (t && (!u || (tokenUser(t) && String(tokenUser(t)).toLowerCase() !== String(u.username || '').toLowerCase()))) {
            localStorage.removeItem('gs_token'); localStorage.removeItem('gs_user');
            return null;
        }
        return t;
    });
    const [user, setUser] = useState(() => (localStorage.getItem('gs_token') ? readUser() : null));

    // fix181 (14.2a): ONE account per browser. Another tab signing in as someone else (or signing out) ends this tab's
    // session too, so nothing this tab sends is saved under the other person's name.
    useEffect(() => {
        const onStorage = (e) => {
            if (e.key !== 'gs_token' && e.key !== 'gs_user' && e.key !== null) return;
            const t = localStorage.getItem('gs_token');
            const u = readUser();
            const mine = String(user?.username || '').toLowerCase();
            if (!t || !u) {
                if (user) { setToken(null); setUser(null); window.location.href = '/login'; }
                return;
            }
            if (!user) { setToken(t); setUser(u); return; }   // e.g. this tab was on the login page
            if (String(u.username || '').toLowerCase() !== mine) {
                setToken(null); setUser(null);
                window.location.href = '/login?reason=other_account';
                return;
            }
            setToken(t); setUser(u);   // same person, new token (own key change in the other tab)
        };
        window.addEventListener('storage', onStorage);
        return () => window.removeEventListener('storage', onStorage);
    }, [user]);

    // fix181 (15.2g): refresh the saved user from the server once per start (a changed rank or a cleared
    // "must change key" shows without signing out)
    useEffect(() => {
        if (!localStorage.getItem('gs_token')) return;
        api.get('/profile/me').then(res => {
            const me = res.data || {};
            const cur = readUser() || {};
            if (cur.username && me.username && cur.username.toLowerCase() !== String(me.username).toLowerCase()) return;
            const next = { ...cur, username: me.username ?? cur.username, role: me.role ?? cur.role, isRoot: !!me.isRoot,
                mustChangePassword: !!me.mustChangePassword, email: me.email ?? cur.email };
            localStorage.setItem('gs_user', JSON.stringify(next));
            setUser(next);
        }).catch(() => { /* the 401/403 handler in axios.js deals with a dead session */ });
    }, []);

    const login = useCallback((authData) => {
        if (authData?.token && authData?.user) {
            forgetPageCache();   // fix182: never show one person's cached lists to the next
            setToken(authData.token);
            setUser(authData.user);
            localStorage.setItem('gs_token', authData.token);
            localStorage.setItem('gs_user', JSON.stringify(authData.user));
            markActivity(true);
            // the appearance choices are per person (15.1i): tell PreferencesProvider who is here now
            window.dispatchEvent(new Event('gs-user-changed'));
        }
    }, []);

    // fix181: take a fresh token + user from the server (after the own key change) without signing out
    const updateSession = useCallback((authData) => {
        if (authData?.token) { setToken(authData.token); localStorage.setItem('gs_token', authData.token); }
        if (authData?.user) { setUser(authData.user); localStorage.setItem('gs_user', JSON.stringify(authData.user)); }
    }, []);

    const logout = useCallback(() => {
        // fix181: end the session on the server too (best effort: a sleeping server must not block the sign out)
        try { api.post('/auth/logout').catch(() => {}); } catch { /* ignore */ }
        setToken(null);
        setUser(null);
        localStorage.removeItem('gs_token');
        localStorage.removeItem('gs_user');
        window.location.href = '/login';
    }, []);

    const contextValue = useMemo(() => ({
        user, token, login, logout, updateSession,
        isAuthenticated: !!token,
        isRoot: user?.isRoot || false
    }), [user, token, login, logout, updateSession]);

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};
