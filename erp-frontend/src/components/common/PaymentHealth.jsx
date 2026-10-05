// PATH: erp-frontend/src/components/common/PaymentHealth.jsx
// fix181 (2.2): the payment dot and its gradient legend (rules in utils/paymentHealth.js)
import React from 'react';
import { paymentColor, paymentLabel, NEW_COLOR, SETTLED_COLOR } from '../../utils/paymentHealth';
import styles from './PaymentHealth.module.css';

/** The 10px dot with its tooltip and screen-reader text. */
export function PaymentHealthDot({ days, isNew = false, startsOn = null, settled = false, style }) {
    // fix182: nothing owed = green whatever the last payment date (a paid-up client is never "60+ days without paying")
    const color = settled ? SETTLED_COLOR : isNew ? NEW_COLOR : paymentColor(days);
    const label = settled ? 'Paid up - nothing owed' : paymentLabel(days, isNew, startsOn);
    return (
        <span role="img" title={label} aria-label={label}
            style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: color,
                boxShadow: `0 0 4px ${color}`, flexShrink: 0, marginTop: 3, ...(style || {}) }} />
    );
}

/** The legend: one gradient bar instead of three coloured words. */
export function PaymentHealthLegend() {
    return (
        <span className={styles.legend} aria-label="Payment recency: from paid recently to no payment for 60 days or more">
            <span>paid recently</span>
            <span aria-hidden="true" className={styles.bar} />
            <span>no payment for 60+ days</span>
        </span>
    );
}
