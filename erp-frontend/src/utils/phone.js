// PATH: erp-frontend/src/utils/phone.js
// fix139 -- ONE standard format for phone numbers. Mirror of PhoneUtil.java
// on the server: keep the two in step.
//
// Staff type a number any normal way; we check it and store it as
// +256772123456. Several numbers are separated with "/" (max 3).

const MAX_NUMBERS = 3;
const MAX_LENGTH = 50; // clients.phone_number column size
const SPLIT = /[\/,;\n\r]+/;
const HELP = 'Use 10 digits like 0772 123 456, or +256 772 123 456.';

// 6+ of the same digit in a row, or a run of 7+ counting up / down.
function looksFake(d) {
  let rep = 1, up = 1, down = 1;
  for (let i = 1; i < d.length; i++) {
    const a = d.charCodeAt(i - 1), b = d.charCodeAt(i);
    rep = a === b ? rep + 1 : 1;
    up = b === a + 1 ? up + 1 : 1;
    down = b === a - 1 ? down + 1 : 1;
    if (rep >= 6 || up >= 7 || down >= 7) return true;
  }
  return false;
}

function finishUg(shown, nsn) {
  if (!/^[734]\d{8}$/.test(nsn)) return { error: '"' + shown + '" is not a valid Uganda mobile or landline number. ' + HELP };
  if (looksFake(nsn)) return { error: '"' + shown + '" looks like a made-up number. Please enter the real number.' };
  return { value: '+256' + nsn };
}

function normalizeOne(part) {
  const shown = part.trim();
  let s = shown.replace(/[\s\-.()]/g, '');
  const plus = s.startsWith('+');
  if (plus) s = s.slice(1);
  if (!/^\d+$/.test(s)) return { error: '"' + shown + '" has letters or symbols. ' + HELP };
  if (s.startsWith('256') && s.length === 12) return finishUg(shown, s.slice(3));
  if (plus && s.startsWith('256')) return { error: '"' + shown + '" is not a full +256 number (9 digits should follow 256).' };
  if (plus) { // a client living abroad: + and their country code
    if (s.length < 8 || s.length > 15 || s[0] === '0' || looksFake(s)) return { error: '"' + shown + '" does not look like a real international number.' };
    return { value: '+' + s };
  }
  if (s.length === 10 && s[0] === '0') return finishUg(shown, s.slice(1));
  if (s.length === 9 && s[0] === '7') return finishUg(shown, s);
  return { error: '"' + shown + '" is not a valid Uganda number. ' + HELP };
}

// -> { ok, value, error }   value = "+256772123456 / +256752123456"
export function normalizePhones(raw) {
  const parts = String(raw || '').split(SPLIT).map((x) => x.trim()).filter(Boolean);
  if (parts.length === 0) return { ok: false, value: '', error: 'Phone is required (use / for multiple numbers).' };
  const out = [];
  for (const p of parts) {
    const r = normalizeOne(p);
    if (r.error) return { ok: false, value: '', error: r.error };
    if (!out.includes(r.value)) out.push(r.value);
  }
  if (out.length > MAX_NUMBERS) return { ok: false, value: '', error: 'At most ' + MAX_NUMBERS + ' numbers per person.' };
  const value = out.join(' / ');
  if (value.length > MAX_LENGTH) return { ok: false, value: '', error: 'Too many long numbers. Keep to ' + MAX_NUMBERS + ' or fewer.' };
  return { ok: true, value, error: '' };
}

// stored text -> ["+256772123456", "+256752123456"]  (works on old formats too)
export function splitPhones(raw) {
  return String(raw || '').split(SPLIT).map((x) => x.trim()).filter(Boolean);
}

export function telHref(num) {
  return 'tel:' + String(num).replace(/[^\d+]/g, '');
}

export function prettyPhone(num) {
  const m = /^\+256(\d{3})(\d{3})(\d{3})$/.exec(String(num).trim());
  return m ? '+256 ' + m[1] + ' ' + m[2] + ' ' + m[3] : String(num).trim();
}

// Every way staff might type a stored number, so 0772..., 256772... and
// +256772... all find the same client (also works on old-format numbers).
export function phoneSearchText(raw) {
  const forms = [];
  for (const part of splitPhones(raw)) {
    const d = part.replace(/\D/g, '');
    if (!d) continue;
    forms.push(d);
    let nsn = null;
    if (d.startsWith('256') && d.length === 12) nsn = d.slice(3);
    else if (d.startsWith('0') && d.length === 10) nsn = d.slice(1);
    else if (d.length === 9 && d[0] === '7') nsn = d;
    if (nsn) forms.push('0' + nsn, '256' + nsn, '+256' + nsn);
  }
  return forms.join('|');
}
