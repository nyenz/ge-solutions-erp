// PATH: erp-frontend/src/components/common/useFeedback.js
import { useState, useCallback } from 'react';

/**
 * GOLDEN SEED -- TALKING BACK TO THE USER (the state half)
 *
 * These used to be copy-pasted per page: FolderPage and SettingsPage each had
 * their own toast stack, and Expenses had a third take on it plus a raw
 * window.confirm(). One copy now, shared.
 *
 * Pair each hook with its component from Feedback.jsx:
 *   const { toasts, toast, dismissToast } = useToasts();
 *   <ToastStack toasts={toasts} onDismiss={dismissToast} />
 *
 *   const { confirmState, confirm, handleAnswer } = useConfirm();
 *   <ConfirmDialog state={confirmState} onAnswer={handleAnswer} />
 *
 * confirm() returns a Promise<boolean>, so it drops straight in wherever a
 * window.confirm() used to sit:
 *   if (!await confirm('DELETE ENTRY', 'This cannot be undone.', 'danger')) return;
 */

export const useToasts = () => {
    const [toasts, setToasts] = useState([]);
    const dismissToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);
    const toast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }, []);
    return { toasts, toast, dismissToast };
};

export const useConfirm = () => {
    const [confirmState, setState] = useState({
        open: false, title: '', message: '', variant: 'warn', resolve: null,
    });
    const confirm = useCallback(
        (title, message, variant = 'warn') =>
            new Promise(resolve => setState({ open: true, title, message, variant, resolve })),
        [],
    );
    const handleAnswer = useCallback((answer) => {
        setState(s => { s.resolve?.(answer); return { ...s, open: false, resolve: null }; });
    }, []);
    return { confirmState, confirm, handleAnswer };
};
