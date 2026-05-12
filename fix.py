import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new, label=""):
    content = read(path)
    if old not in content:
        print(f"MISSING ({label or path}): target string not found")
        return
    write(path, content.replace(old, new, 1))
    print(f"OK patch ({label or path})")


# ================================================================
# FIX: AuthProvider.jsx
#
# PROBLEM:
#   The current code uses localStorage to detect when ANY account
#   logs in from another tab/browser and then kicks out the current
#   session. This breaks multi-user scenarios where David logs in
#   on Computer A and a staff member logs in on Computer B.
#
# ROOT CAUSE:
#   localStorage is SHARED across all browser sessions on the same
#   machine (same origin). But more importantly, the 'storage' event
#   fires across ALL tabs on the same browser — and the gs_active_session
#   key was being set on EVERY login, kicking out everyone.
#
# SOLUTION:
#   Remove the browser-tab single-session enforcement entirely.
#   The server-side sessionVersion (already implemented in the JWT
#   filter) correctly handles the real security requirement:
#   - Same USERNAME logs in from Computer B -> Computer A gets 401
#     on next request -> axios interceptor redirects to /login.
#   - DIFFERENT users on different computers -> no conflict at all.
#
# The ?reason=session_conflict URL param handling is kept so existing
# bookmarks/redirects don't break, but it now shows a cleaner message.
# ================================================================

NEW_AUTH_PROVIDER = '''\
// PATH: erp-frontend/src/context/AuthProvider.jsx
import React, { useState, useCallback, useMemo } from 'react';
import { AuthContext } from './AuthContext';

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

    const logout = useCallback(() => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('gs_token');
        localStorage.removeItem('gs_user');
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
'''

write('erp-frontend/src/context/AuthProvider.jsx', NEW_AUTH_PROVIDER)


# ================================================================
# FIX 2: LoginPage.jsx
#
# The ?reason=session_conflict message now correctly describes what
# actually happened (same account logged in elsewhere) vs the old
# confusing "another browser" message that triggered even for
# different users.
# ================================================================

patch(
    'erp-frontend/src/pages/login/LoginPage.jsx',
    "        if (params.get('reason') === 'session_conflict') {\n"
    "            return 'SECURITY: Your session was terminated because this account logged in from another browser.';\n"
    "        }",
    "        if (params.get('reason') === 'session_conflict') {\n"
    "            return 'Your session ended because this account signed in on another device.';\n"
    "        }",
    'LoginPage.jsx session_conflict message'
)


# ================================================================
# FIX 3: axios.js
#
# Remove the idle timer module-load call. The idle timer should only
# start after a confirmed login, not when the module first loads
# (which runs even on the login page before any auth).
# The reset on every API call already handles the timer correctly.
# ================================================================

patch(
    'erp-frontend/src/api/axios.js',
    '// Start the timer immediately when the module loads (user is already logged in)\nresetIdleTimer();',
    '// Timer resets on every API call via the request interceptor below.',
    'axios.js remove premature idle timer start'
)


print()
print("All fixes applied.")
print()
print("WHAT CHANGED:")
print("  AuthProvider.jsx  -- Removed browser-tab single-session enforcement.")
print("                       Server-side JWT sessionVersion handles real security.")
print("                       Different accounts on different computers now work fine.")
print("  LoginPage.jsx     -- Cleaner session_conflict message.")
print("  axios.js          -- Removed idle timer premature start on login page.")
print()
print("HOW SECURITY STILL WORKS:")
print("  - Same account, 2 devices: Computer B login increments sessionVersion in DB.")
print("    Computer A gets 401 on next API call -> axios redirects to /login.")
print("  - Different accounts, different computers: No conflict. Both work fine.")
print("  - Idle timeout: Still active, resets on every API call (30 min).")
print()
print("Run: git add -A && git commit -m 'fix: remove browser session conflict, keep server-side JWT enforcement' && git push")