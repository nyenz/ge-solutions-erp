// PATH: erp-frontend/src/utils/paymentHealth.js
// fix181 (2.2, 5.2, 6.10, 11.9): THE payment-recency colour, used by the Project Ledger, the Client Ledger, the Portfolio
// and Recovery. The number of days comes from the SERVER (daysSincePayment), never from this device's clock.
// 0 days = green, 14 = yellow, 30 = orange, 60 or more = red, blended smoothly; no payment date = red.
// A client whose only unpaid projects are in their first month after starting shows a neutral NEW look.

const STOPS = [
    [0, [34, 197, 94]],     // green  #22c55e
    [14, [234, 179, 8]],    // yellow #eab308
    [30, [249, 115, 22]],   // orange #f97316
    [60, [239, 68, 68]],    // red    #ef4444
];
export const NEW_COLOR = '#94a3b8';

export function paymentColor(days) {
    if (days === null || days === undefined || Number.isNaN(Number(days))) return 'rgb(239, 68, 68)';
    const d = Math.max(0, Number(days));
    for (let i = 1; i < STOPS.length; i++) {
        const [d1, c1] = STOPS[i - 1];
        const [d2, c2] = STOPS[i];
        if (d <= d2) {
            const t = (d - d1) / (d2 - d1);
            const c = c1.map((v, k) => Math.round(v + (c2[k] - v) * t));
            return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
        }
    }
    return 'rgb(239, 68, 68)';
}

export function paymentLabel(days, isNew, startsOn) {
    if (isNew) return 'New project' + (startsOn ? ' - recovery starts ' + String(startsOn).slice(0, 10) : '');
    if (days === null || days === undefined) return 'No payment recorded';
    if (Number(days) === 0) return 'Last payment today';
    return 'Last payment ' + days + ' day' + (Number(days) === 1 ? '' : 's') + ' ago';
}

