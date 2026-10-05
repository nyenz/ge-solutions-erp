// PATH: erp-frontend/src/components/common/PaymentHealth.jsx
// fix181 (2.2): the payment dot and its gradient legend (rules in utils/paymentHealth.js)
import React from 'react';
import { paymentColor, paymentLabel, NEW_COLOR } from '../../utils/paymentHealth';

/** The 10px dot with its tooltip and screen-reader text. */
export function PaymentHealthDot({ days, isNew = false, startsOn = null, style }) {
    const color = isNew ? NEW_COLOR : paymentColor(days);
    const label = paymentLabel(days, isNew, startsOn);
    return (
        <span role="img" title={label} aria-label={label}
            style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: color,
                boxShadow: `0 0 4px ${color}`, flexShrink: 0, marginTop: 3, ...(style || {}) }} />
    );
}

/** The legend: one gradient bar instead of three coloured words. */
export function PaymentHealthLegend() {
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', opacity: 0.85 }} aria-label="Payment recency: from paid recently to no payment for 60 days or more">
            <span>paid recently</span>
            <span aria-hidden="true" style={{ display: 'inline-block', width: 110, height: 8, borderRadius: 4,
                background: 'linear-gradient(90deg, #22c55e 0%, #eab308 23%, #f97316 50%, #ef4444 100%)' }} />
            <span>no payment for 60+ days</span>
        </span>
    );
}
