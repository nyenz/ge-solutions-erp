// PATH: erp-frontend/src/components/common/RetryButton.jsx
// RETRY with visible feedback: the arrows spin and the word changes while it works, then a tick.
import React from 'react';
import { FiRefreshCw, FiCheck } from 'react-icons/fi';
import useActionFeedback from './useActionFeedback';
import styles from './RetryButton.module.css';

const RetryButton = ({ onClick, className = '', label = 'RETRY' }) => {
    const [phase, run] = useActionFeedback(onClick);
    return (
        <button type="button" className={`${className} ${phase !== 'idle' ? styles.on : ''}`} onClick={run} disabled={phase === 'working'} aria-live="polite">
            {phase === 'done' ? <FiCheck aria-hidden="true" /> : <FiRefreshCw aria-hidden="true" className={phase === 'working' ? styles.spin : ''} />}
            {phase === 'working' ? 'TRYING...' : phase === 'done' ? 'DONE' : label}
        </button>
    );
};
export default RetryButton;
