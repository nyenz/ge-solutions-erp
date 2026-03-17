// PATH: erp-frontend/src/context/AuthProvider.jsx
import React, { useState, useCallback, useMemo } from 'react';
import { AuthContext } from './AuthContext';

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(() => localStorage.getItem('gs_token'));
    const [user, setUser] = useState(() => {
        const storedUser = localStorage.getItem('gs_user');
        try { return storedUser ? JSON.parse(storedUser) : null; } catch { return null; }
    });

    const login = useCallback((authData) => {
        if (authData?.token && authData?.user) {
            setToken(authData.token);
            setUser(authData.user);
            localStorage.setItem('gs_token', authData.token);
            localStorage.setItem('gs_user', JSON.stringify(authData.user));
        }
    }, []);

    const logout = useCallback(() => {
        setToken(null);
        setUser(null);
        localStorage.clear(); // PURGE ALL KEYS
        window.location.href = '/login';
    }, []);

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