// PATH: erp-frontend/src/context/AuthProvider.jsx
import React, { useState, useCallback, useMemo } from 'react';
import { AuthContext } from './AuthContext';
import api from '../api/axios';

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => localStorage.getItem('gs_token'));
    const [user, setUser] = useState(() => {
        const stored = localStorage.getItem('gs_user');
        try { return stored ? JSON.parse(stored) : null; } catch { return null; }
    });

    const login = useCallback((authData) => {
        if (authData?.token && authData?.user) {
            setToken(authData.token);
            setUser(authData.user);
            localStorage.setItem('gs_token', authData.token);
            localStorage.setItem('gs_user', JSON.stringify(authData.user));
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
