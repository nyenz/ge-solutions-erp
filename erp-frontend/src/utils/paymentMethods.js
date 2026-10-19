// fix214 (David): THE list of payment methods on the pages. Keep it in step with the server's PaymentMethods.java.
// OFFICE = cash paid at the office. OTHER needs a few words saying how (for example a cheque number).
export const PAY_METHODS = [
    { value: 'OFFICE', label: 'Office', hint: 'Cash paid at the office.' },
    { value: 'MOBILE_MONEY', label: 'Mobile Money', hint: 'MTN or Airtel money. Type the transaction ID as the reference.' },
    { value: 'BANK', label: 'Bank', hint: 'Deposit or transfer into the company bank account. Type the bank reference.' },
    { value: 'OTHER', label: 'Other', hint: 'Any other way. Say how it was paid (for example: cheque no. 1042).' },
];

/** The words for a stored code. Payments saved before fix214 have none: "Not recorded". */
export const methodLabel = (code) => {
    if (!code) return 'Not recorded';
    const m = PAY_METHODS.find(x => x.value === code);
    return m ? m.label : String(code);
};

/** The code for the words picked in a list ("Mobile Money" -> "MOBILE_MONEY"); '' when nothing is picked. */
export const methodCode = (label) => {
    const m = PAY_METHODS.find(x => x.label === label || x.value === label);
    return m ? m.value : '';
};

/** The label for the reference box, which changes with the method. */
export const referenceLabel = (code) => code === 'OTHER' ? 'How was it paid? (required)'
    : code === 'MOBILE_MONEY' ? 'Transaction ID (optional)'
    : code === 'BANK' ? 'Bank reference (optional)'
    : 'Receipt book number (optional)';

/** Same checks as the server. Returns '' when fine, else the message. */
export const checkMethod = (code, reference) => {
    if (!code) return 'Pick how the money was paid: Office, Mobile Money, Bank or Other.';
    const ref = String(reference || '').trim();
    if (ref.length > 80) return 'The payment reference can be at most 80 characters.';
    if (code === 'OTHER' && ref.length < 3) return 'For Other, write how the money was paid (for example: cheque no. 1042).';
    return '';
};

/** One short line: "Mobile Money - MP2410" */
export const methodLine = (code, reference) => methodLabel(code) + (reference ? ' - ' + reference : '');
