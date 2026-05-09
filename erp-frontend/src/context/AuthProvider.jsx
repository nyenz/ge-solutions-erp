// PATH: erp-frontend/src/context/AuthProvider.jsx
import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { AuthContext } from './AuthContext';

// Generate a unique session ID for this browser tab/window
const generateSessionId = () => Math.random().toString(36).slice(2) + Date.now().toString(36);

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => localStorage.getItem('gs_token'));
    const [user, setUser] = useState(() => {
        const storedUser = localStorage.getItem('gs_user');
        try { return storedUser ? JSON.parse(storedUser) : null; } catch { return null; }
    });

    // This tab's unique session ID — stored in sessionStorage (tab-only, not shared)
    const tabSessionId = useRef(
        sessionStorage.getItem('gs_tab_session') || (() => {
            const id = generateSessionId();
            sessionStorage.setItem('gs_tab_session', id);
            return id;
        })()
    );

    const login = useCallback((authData) => {
        if (authData?.token && authData?.user) {
            const sessionId = generateSessionId();
            // Store the new session ID in localStorage so other tabs can detect it
            localStorage.setItem('gs_active_session', sessionId);
            // Update this tab's session reference
            sessionStorage.setItem('gs_tab_session', sessionId);
            tabSessionId.current = sessionId;

            setToken(authData.token);
            setUser(authData.user);
            localStorage.setItem('gs_token', authData.token);
            localStorage.setItem('gs_user', JSON.stringify(authData.user));
        }
    }, []);

    const logout = useCallback(() => {
        setToken(null);
        setUser(null);
        sessionStorage.removeItem('gs_tab_session');
        localStorage.clear();
        window.location.href = '/login';
    }, []);

    // Listen for storage events — fires when ANOTHER tab changes localStorage
    useEffect(() => {
        if (!token) return; // Not logged in, nothing to check

        // Set the active session when this tab first loads with a valid token
        // (handles page refresh — we re-assert our session)
        const currentGlobalSession = localStorage.getItem('gs_active_session');
        const mySession = sessionStorage.getItem('gs_tab_session');

        // If there's a global session and it doesn't match ours, we were logged out
        if (currentGlobalSession && mySession && currentGlobalSession !== mySession) {
            console.warn('[GS-ERP] Session conflict detected — logging out this tab.');
            setToken(null);
            setUser(null);
            sessionStorage.removeItem('gs_tab_session');
            // Don't clear localStorage — the new session owns it
            window.location.href = '/login?reason=session_conflict';
            return;
        }

        const handleStorageChange = (e) => {
            // Another tab changed gs_active_session — means someone logged in elsewhere
            if (e.key === 'gs_active_session') {
                const newSession = e.newValue;
                const mySession = sessionStorage.getItem('gs_tab_session');
                if (newSession && mySession && newSession !== mySession) {
                    console.warn('[GS-ERP] New login detected in another tab — logging out this session.');
                    setToken(null);
                    setUser(null);
                    sessionStorage.removeItem('gs_tab_session');
                    window.location.href = '/login?reason=session_conflict';
                }
            }
            // Another tab cleared the token (logout)
            if (e.key === 'gs_token' && !e.newValue) {
                setToken(null);
                setUser(null);
                sessionStorage.removeItem('gs_tab_session');
                window.location.href = '/login';
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, [token]);

    const contextValue = useMemo(() => ({
        user, token, login, logout,
        isAuthenticated: !!token,
        isRoot: user?.isRoot || false
    }), [user, token, login, logout]);

    return (
        <AuthContext.Provider value={contextValue}>
            {children}
        </AuthContext.Provider>
    );
};