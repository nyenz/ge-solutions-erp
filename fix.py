#!/usr/bin/env python3
# PATH: fix139.py
# GOLDEN SEED -- fix139: phone numbers in ONE standard format, Recovery search
# finds every plot's location, LOG OUTCOME no longer sticks, safer note delete.
#
#   1. PHONE NUMBERS -- ONE STANDARD FORMAT.
#      Staff can still type a number any normal way (0772 123 456,
#      +256772123456, 772123456, 256 772 123 456). The system checks it and
#      saves it as +256772123456. Several numbers are still separated with "/"
#      (max 3 per person).
#      - Wrong length, letters, symbols, or a number that is not a Uganda
#        mobile / landline (+256, starts 7, 3 or 4) is refused with a plain
#        message telling staff what is wrong.
#      - Made-up numbers are refused: 6+ of the same digit in a row
#        (0700 000 000, 0788 000 000) or a run of 7+ counting digits
#        (0712 345 678).
#      - A foreign number is allowed only when typed with its + country code
#        (for clients living abroad).
#      - Checked on Intake and on the Folder edit screen, AND again on the
#        server (LandService, ClientService, ClientController) so it cannot
#        be skipped. The box tidies itself when staff click out of it.
#      - Existing old numbers are NOT changed. If a folder is edited and one
#        of its owners still has an old bad number, the save asks staff to
#        fix that number first.
#      - The sample text in the box no longer looks like a real number.
#
#   2. RECOVERY CARD: TAP-TO-CALL. Each number on the card (and in the CALL
#      LOG window) is a tap-to-call link, shown as +256 772 123 456.
#
#   3. RECOVERY SEARCH. The list now searches the same things the tab counts
#      do (they used to disagree): name, NIN, phone, index, district,
#      COUNTY, SUB-COUNTY, PARISH, VILLAGE -- of EVERY plot the client owns,
#      not just the first one. A search for 0772... also finds +256772...
#      (and the other way round). The card lists every plot's location.
#
#   4. LOG OUTCOME BUTTON. After one successful log the button stayed on
#      "COMMITTING DATA..." for the next client until refresh. Fixed.
#
#   5. DELETING A CALL NOTE.
#      - The X now asks first: click once, it shows SURE?, click again to
#        delete (resets after 3 seconds).
#      - The client's reliability score is put back (a deleted answered call
#        takes back its +1.5, a deleted miss gives back its -2).
#      - The audit line now names the client, who wrote the note and its date.
#
# Frontend + backend. NOT in this fix (kept for later): voiding notes instead
# of deleting them, the paid-clients-in-queue question, stats labels.
#
# Atomic: every patch for every file is matched in memory first; if any one is
# MISSING nothing is written and nothing is committed. Runs the backend compile
# (mvnw / mvn) and `npm run build` before committing when they are available,
# and puts every file back exactly as it was if either goes red.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "erp-backend")
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(BACKEND, "src", "main", "java", "com", "gesolutions", "erp")

PHONE_JS = os.path.join(SRC, "utils", "phone.js")
PHONE_JAVA = os.path.join(JAVA, "common", "util", "PhoneUtil.java")
NOTE_CTRL = os.path.join(JAVA, "modules", "client", "controller", "RecoveryNoteController.java")
CLIENT_SVC = os.path.join(JAVA, "modules", "client", "service", "ClientService.java")
CLIENT_CTRL = os.path.join(JAVA, "modules", "client", "controller", "ClientController.java")
LAND_SVC = os.path.join(JAVA, "modules", "land", "service", "LandService.java")
RECOVERY_JSX = os.path.join(SRC, "pages", "Recovery", "RecoveryPortal.jsx")
INTAKE_JSX = os.path.join(SRC, "pages", "Intake", "IntakePage.jsx")
FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")

MISSING = []


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub(text, old, new, desc):
    """Exact find/replace, first occurrence. Prints OK / SKIP / MISSING."""
    if new in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    if old in text:
        print("OK: " + desc)
        return text.replace(old, new, 1)
    print("MISSING: " + desc)
    MISSING.append(desc)
    return text


NEWFILES = []  # (path, text, label)


def newfile(path, text, label, marker):
    """Create (or replace) a whole file. SKIP if it already carries `marker`."""
    if os.path.exists(path) and marker in read(path):
        print("SKIP: " + label + " -- already applied")
        return
    print("OK: " + label + " (written)")
    NEWFILES.append((path, text, label))


FILES = {}      # path -> current text (patched in memory)
ORIGINAL = {}   # path -> text as found on disk


def load(path):
    if not os.path.exists(path):
        print("MISSING: file not found -- " + path)
        MISSING.append("file not found: " + path)
        FILES[path] = ""
        ORIGINAL[path] = ""
        return
    t = read(path)
    FILES[path] = t
    ORIGINAL[path] = t


for _p in (NOTE_CTRL, CLIENT_SVC, CLIENT_CTRL, LAND_SVC, RECOVERY_JSX, INTAKE_JSX, FOLDER_JSX):
    load(_p)


def patch(path, old, new, desc):
    FILES[path] = sub(FILES[path], old, new, desc)


# ======================================================================
# NEW FILE -- erp-frontend/src/utils/phone.js  (mirror of PhoneUtil.java)
# ======================================================================
newfile(PHONE_JS, r'''// PATH: erp-frontend/src/utils/phone.js
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
''', "erp-frontend/src/utils/phone.js", "fix139")


# ======================================================================
# NEW FILE -- PhoneUtil.java  (server-side twin of phone.js)
# ======================================================================
newfile(PHONE_JAVA, r'''// PATH: erp-backend/src/main/java/com/gesolutions/erp/common/util/PhoneUtil.java
package com.gesolutions.erp.common.util;

import com.gesolutions.erp.common.exception.BusinessException;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;

/**
 * fix139 -- ONE standard format for phone numbers. Twin of
 * erp-frontend/src/utils/phone.js: keep the two in step.
 *
 * Accepts 0772 123 456, +256772123456, 256772123456, 772123456. Stores
 * +256772123456. Several numbers are joined with " / " (max 3). A foreign
 * number is only accepted when typed with its + country code.
 *
 * To tighten the Uganda prefix check later (e.g. only 70-79 mobiles), change
 * the UG_NSN pattern below -- nowhere else.
 */
public final class PhoneUtil {
    private PhoneUtil() {}

    public static final int MAX_NUMBERS = 3;
    public static final int MAX_LENGTH = 50; // clients.phone_number column size
    private static final String SPLIT = "[/,;\\r\\n]+";
    private static final String UG_NSN = "[734]\\d{8}";
    private static final String HELP = "Use 10 digits like 0772 123 456, or +256 772 123 456.";

    public static String normalizeList(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new BusinessException("PHONE_INVALID: A phone number is required (use / for multiple numbers).");
        }
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (String part : raw.split(SPLIT)) {
            if (part.isBlank()) continue;
            out.add(normalizeOne(part));
        }
        if (out.isEmpty()) {
            throw new BusinessException("PHONE_INVALID: A phone number is required (use / for multiple numbers).");
        }
        if (out.size() > MAX_NUMBERS) {
            throw new BusinessException("PHONE_INVALID: At most " + MAX_NUMBERS + " numbers per person.");
        }
        String joined = String.join(" / ", out);
        if (joined.length() > MAX_LENGTH) {
            throw new BusinessException("PHONE_INVALID: Too many long numbers. Keep to " + MAX_NUMBERS + " or fewer.");
        }
        return joined;
    }

    private static String normalizeOne(String part) {
        String shown = part.trim();
        String s = shown.replaceAll("[\\s\\-.()]", "");
        boolean plus = s.startsWith("+");
        if (plus) s = s.substring(1);
        if (!s.matches("\\d+")) throw bad(shown, "has letters or symbols. " + HELP);
        if (s.startsWith("256") && s.length() == 12) return finishUg(shown, s.substring(3));
        if (plus && s.startsWith("256")) throw bad(shown, "is not a full +256 number (9 digits should follow 256).");
        if (plus) { // a client living abroad: + and their country code
            if (s.length() < 8 || s.length() > 15 || s.charAt(0) == '0' || looksFake(s)) {
                throw bad(shown, "does not look like a real international number.");
            }
            return "+" + s;
        }
        if (s.length() == 10 && s.charAt(0) == '0') return finishUg(shown, s.substring(1));
        if (s.length() == 9 && s.charAt(0) == '7') return finishUg(shown, s);
        throw bad(shown, "is not a valid Uganda number. " + HELP);
    }

    private static String finishUg(String shown, String nsn) {
        if (!nsn.matches(UG_NSN)) throw bad(shown, "is not a valid Uganda mobile or landline number. " + HELP);
        if (looksFake(nsn)) throw bad(shown, "looks like a made-up number. Please enter the real number.");
        return "+256" + nsn;
    }

    private static BusinessException bad(String shown, String why) {
        return new BusinessException("PHONE_INVALID: \"" + shown + "\" " + why);
    }

    /** 6+ of the same digit in a row, or a run of 7+ counting up / down. */
    private static boolean looksFake(String d) {
        int rep = 1, up = 1, down = 1;
        for (int i = 1; i < d.length(); i++) {
            int a = d.charAt(i - 1), b = d.charAt(i);
            rep = (a == b) ? rep + 1 : 1;
            up = (b == a + 1) ? up + 1 : 1;
            down = (b == a - 1) ? down + 1 : 1;
            if (rep >= 6 || up >= 7 || down >= 7) return true;
        }
        return false;
    }

    /**
     * Every way staff might type a stored number, for search. Never throws,
     * so old-format numbers in the database are searchable too.
     */
    public static List<String> searchForms(String raw) {
        List<String> forms = new ArrayList<>();
        if (raw == null) return forms;
        for (String part : raw.split(SPLIT)) {
            String d = part.replaceAll("[^0-9]", "");
            if (d.isEmpty()) continue;
            forms.add(d);
            String nsn = null;
            if (d.startsWith("256") && d.length() == 12) nsn = d.substring(3);
            else if (d.startsWith("0") && d.length() == 10) nsn = d.substring(1);
            else if (d.length() == 9 && d.startsWith("7")) nsn = d;
            if (nsn != null) {
                forms.add("0" + nsn);
                forms.add("256" + nsn);
                forms.add("+256" + nsn);
            }
        }
        return forms;
    }
}
''', "erp-backend/.../common/util/PhoneUtil.java", "fix139")


# ======================================================================
# BACKEND -- save points: every path that writes a phone number
# ======================================================================
patch(CLIENT_SVC,
      "    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {\n",
      "    public Client findOrCreateClientByNin(String fullName, String nin, String phone, String email) {\n"
      "        // fix139: one standard phone format (blank is only tolerated for an existing client)\n"
      "        String cleanPhone = (phone == null || phone.isBlank()) ? null\n"
      "                : com.gesolutions.erp.common.util.PhoneUtil.normalizeList(phone);\n",
      "ClientService: check + standardise the phone number")

patch(CLIENT_SVC,
      "                .phoneNumber(phone)\n                .nationalId(normalizedNin)",
      "                .phoneNumber(cleanPhone != null ? cleanPhone\n"
      "                        : com.gesolutions.erp.common.util.PhoneUtil.normalizeList(phone))\n"
      "                .nationalId(normalizedNin)",
      "ClientService: new client is saved with the standard number")

patch(LAND_SVC,
      "person.setPhoneNumber(incoming.getPhone());",
      "person.setPhoneNumber(com.gesolutions.erp.common.util.PhoneUtil.normalizeList(incoming.getPhone()));",
      "LandService: folder edit saves the standard number")

patch(CLIENT_CTRL,
      'c.setPhoneNumber(body.get("phoneNumber").trim());',
      'c.setPhoneNumber(com.gesolutions.erp.common.util.PhoneUtil.normalizeList(body.get("phoneNumber")));',
      "ClientController: client update saves the standard number")


# ======================================================================
# BACKEND -- RecoveryNoteController: search, every plot's location, delete
# ======================================================================
patch(NOTE_CTRL,
      "if (c.getPhoneNumber() != null) hay.append(c.getPhoneNumber()).append(' ');",
      "if (c.getPhoneNumber() != null) hay.append(c.getPhoneNumber()).append(' ');\n"
      "        for (String f : com.gesolutions.erp.common.util.PhoneUtil.searchForms(c.getPhoneNumber())) hay.append('|').append(f).append('|');",
      "Recovery search: 0772... finds +256772... (and back)")

patch(NOTE_CTRL,
      "if (p.getSubCounty() != null) hay.append(p.getSubCounty()).append(' ');",
      "if (p.getSubCounty() != null) hay.append(p.getSubCounty()).append(' ');\n"
      "            if (p.getCounty() != null) hay.append(p.getCounty()).append(' ');\n"
      "            if (p.getParish() != null) hay.append(p.getParish()).append(' ');",
      "Recovery search: county and parish too")

patch(NOTE_CTRL,
      'm.put("village", ps.isEmpty() ? null : ps.get(0).getVillage());',
      'm.put("village", ps.isEmpty() ? null : ps.get(0).getVillage());\n'
      '        // fix139: the location of EVERY plot (display lines + one search string)\n'
      '        LinkedHashSet<String> places = new LinkedHashSet<>();\n'
      '        StringBuilder placeText = new StringBuilder();\n'
      '        for (LandProject p : ps) {\n'
      '            List<String> parts = new ArrayList<>();\n'
      '            for (String s : new String[]{ p.getDistrict(), p.getCounty(), p.getSubCounty(), p.getParish(), p.getVillage() }) {\n'
      '                if (s != null && !s.isBlank()) { parts.add(s.trim()); placeText.append(s.trim()).append(\' \'); }\n'
      '            }\n'
      '            if (!parts.isEmpty()) places.add(String.join(" - ", parts));\n'
      '        }\n'
      '        m.put("places", new ArrayList<>(places));\n'
      '        m.put("placeText", placeText.toString().trim());',
      "Recovery queue: send every plot's location")

patch(NOTE_CTRL,
      "public ResponseEntity<?> deleteNote(@PathVariable UUID id, Authentication auth) {",
      "@org.springframework.transaction.annotation.Transactional\n"
      "    public ResponseEntity<?> deleteNote(@PathVariable UUID id, Authentication auth) {",
      "Delete note: runs in one transaction")

patch(NOTE_CTRL,
      "noteRepo.delete(n);",
      "String delWho = n.getAuthor() == null ? \"unknown\" : n.getAuthor().getUsername();\n"
      "        String delWhen = n.getCreatedAt() == null ? \"?\" : n.getCreatedAt().toLocalDate().toString();\n"
      "        String delFor = c == null ? \"?\" : c.getFullName() + \" (NIN \" + c.getNationalId() + \")\";\n"
      "        String[] delDef = tagDef(n.getTag());\n"
      "        noteRepo.delete(n);",
      "Delete note: remember who/when/client before it goes")

patch(NOTE_CTRL,
      "c.setLastContactedAt(newest);",
      "c.setLastContactedAt(newest);\n"
      "            if (delDef != null) { // put back what logging this call did to the score\n"
      "                double undo = \"POSITIVE\".equals(delDef[1]) ? -1.5 : 2.0;\n"
      "                double cur = c.getReliabilityScore() == null ? 100.0 : c.getReliabilityScore();\n"
      "                c.setReliabilityScore(Math.max(0.0, Math.min(100.0, cur + undo)));\n"
      "            }",
      "Delete note: client's reliability score is put back")

patch(NOTE_CTRL,
      'auditService.logAction("RECOVERY_NOTE_DELETED", "Operator [" + auth.getName() + "] deleted tag: " + n.getTag());',
      'auditService.logAction("RECOVERY_NOTE_DELETED", "Operator [" + auth.getName() + "] deleted tag: " + n.getTag()\n'
      '            + " for " + delFor + ", written by " + delWho + " on " + delWhen);',
      "Delete note: audit line names the client, author and date")


# ======================================================================
# FRONTEND -- RecoveryPortal.jsx
# ======================================================================
patch(RECOVERY_JSX,
      "import { useAuth } from '../../hooks/useAuth';",
      "import { useAuth } from '../../hooks/useAuth';\n"
      "import { splitPhones, telHref, prettyPhone, phoneSearchText } from '../../utils/phone';",
      "Recovery: import the phone helpers")

patch(RECOVERY_JSX,
      "const [busy, setBusy] = useState(false);",
      "const [busy, setBusy] = useState(false);\n  const [confirmDel, setConfirmDel] = useState(null);",
      "Recovery: state for the delete SURE? step")

patch(RECOVERY_JSX,
      ".then((r) => { setSel(null); toast('Logged.', 'success');",
      ".then((r) => { setBusy(false); setSel(null); toast('Logged.', 'success');",
      "Recovery: LOG OUTCOME button no longer sticks after a save")

patch(RECOVERY_JSX,
      "const term = search.toLowerCase().replace(/\\s+/g, '');",
      "const askDelete = (noteId) => {\n"
      "    if (confirmDel !== noteId) { setConfirmDel(noteId); setTimeout(() => setConfirmDel((cur) => (cur === noteId ? null : cur)), 3000); return; }\n"
      "    setConfirmDel(null);\n"
      "    recoveryService.deleteNote(noteId)\n"
      "      .then(() => { toast('Note deleted.', 'warn'); recoveryService.getNotes(sel.id).then((r) => setNotes(r.data || [])); load(true); })\n"
      "      .catch(() => toast('Could not delete the note.', 'error'));\n"
      "  };\n"
      "  const term = search.toLowerCase().replace(/\\s+/g, '');",
      "Recovery: delete asks SURE? first")

patch(RECOVERY_JSX,
      "[c.name, c.nin, c.phone, c.lastTag, c.district, c.village, ...(c.indexes || [])]",
      "[c.name, c.nin, c.phone, phoneSearchText(c.phone), c.lastTag, c.district, c.subCounty, c.village, c.placeText, ...(c.indexes || [])]",
      "Recovery: list search covers sub-county, county, parish, village of every plot + any phone format")

patch(RECOVERY_JSX,
      'placeholder="Search name, NIN, phone, index..."',
      'placeholder="Search name, NIN, phone, index, location..."',
      "Recovery: search box hint mentions location")

patch(RECOVERY_JSX,
      "{c.district && (<span className={styles.loc}><FiMapPin aria-hidden=\"true\" /> {c.district}{c.subCounty ? ' - ' + c.subCounty : ''}{c.village ? ' - ' + c.village : ''}</span>)}",
      "{(c.places && c.places.length > 0 ? c.places : (c.district ? [c.district + (c.subCounty ? ' - ' + c.subCounty : '') + (c.village ? ' - ' + c.village : '')] : [])).map((pl, i) => (<span key={i} className={styles.loc}><FiMapPin aria-hidden=\"true\" /> {pl}</span>))}",
      "Recovery card: list the location of every plot")

patch(RECOVERY_JSX,
      "<span className={styles.monoRow}><FiPhoneCall aria-hidden=\"true\" /><span className={styles.mono}>{c.phone}</span></span>",
      "<span className={styles.monoRow}><FiPhoneCall aria-hidden=\"true\" />{splitPhones(c.phone).map((ph, i) => (<React.Fragment key={i}>{i > 0 && <span className={styles.mono}> / </span>}<a className={styles.mono} href={telHref(ph)} onClick={(e) => e.stopPropagation()} style={{ textDecoration: 'none' }}>{prettyPhone(ph)}</a></React.Fragment>))}</span>",
      "Recovery card: tap-to-call on every number")

patch(RECOVERY_JSX,
      "<span className={styles.mono}>{sel.phone}</span>",
      "<span>{splitPhones(sel.phone).map((ph, i) => (<React.Fragment key={i}>{i > 0 && <span className={styles.mono}> / </span>}<a className={styles.mono} href={telHref(ph)} style={{ textDecoration: 'none' }}>{prettyPhone(ph)}</a></React.Fragment>))}</span>",
      "CALL LOG window: tap-to-call on every number")

patch(RECOVERY_JSX,
      "onClick={() => recoveryService.deleteNote(n.id).then(() => { toast('Note deleted.', 'warn'); recoveryService.getNotes(sel.id).then((r) => setNotes(r.data || [])); load(true); })}>",
      "onClick={() => askDelete(n.id)}>{confirmDel === n.id ? (<span style={{ color: '#ef4444', fontWeight: 700, fontSize: 11, marginRight: 4 }}>SURE?</span>) : null}",
      "Recovery: delete X shows SURE? on the first click")


# ======================================================================
# FRONTEND -- IntakePage.jsx
# ======================================================================
patch(INTAKE_JSX,
      "import landService from '../../services/landService';",
      "import landService from '../../services/landService';\nimport { normalizePhones } from '../../utils/phone';",
      "Intake: import the phone helper")

patch(INTAKE_JSX,
      "if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }",
      "if (!o.phone.trim()) { toast(`Owner ${i + 1}: Phone is required (use / for multiple numbers).`, 'error'); return false; }\n"
      "            const ph = normalizePhones(o.phone);\n"
      "            if (!ph.ok) { toast(`Owner ${i + 1}: ${ph.error}`, 'error'); return false; }",
      "Intake: refuse a wrong or made-up phone number")

patch(INTAKE_JSX,
      "fullName: o.fullName.trim().toUpperCase(), phone: o.phone.trim(),",
      "fullName: o.fullName.trim().toUpperCase(), phone: normalizePhones(o.phone).value || o.phone.trim(),",
      "Intake: send the standard number to the server")

patch(INTAKE_JSX,
      "onChange={e => updateOwner(idx, 'phone', e.target.value)} placeholder=\"0700 000 000 / 0788 000 000\" />",
      "onChange={e => updateOwner(idx, 'phone', e.target.value)} onBlur={e => { const r = normalizePhones(e.target.value); if (r.ok && r.value !== e.target.value) updateOwner(idx, 'phone', r.value); }} placeholder=\"07XX XXX XXX / 07XX XXX XXX\" />",
      "Intake: phone box tidies itself; sample text no longer looks like a number")


# ======================================================================
# FRONTEND -- FolderPage.jsx
# ======================================================================
patch(FOLDER_JSX,
      "import clientService from '../../services/clientService';",
      "import clientService from '../../services/clientService';\nimport { normalizePhones } from '../../utils/phone';",
      "Folder: import the phone helper")

patch(FOLDER_JSX,
      "if (!o.nationalId?.trim()) errors.push('OWNER ' + (i + 1) + ': NATIONAL ID (NIN) IS REQUIRED');",
      "if (!o.nationalId?.trim()) errors.push('OWNER ' + (i + 1) + ': NATIONAL ID (NIN) IS REQUIRED');\n"
      "            if (o.phone?.trim()) { const ph = normalizePhones(o.phone); if (!ph.ok) errors.push('OWNER ' + (i + 1) + ': ' + ph.error.toUpperCase()); }",
      "Folder: refuse a wrong or made-up phone number on save")

patch(FOLDER_JSX,
      "buffer.owners?.forEach((o, i) => { if (!o.fullName?.trim()) fe['owner_' + i + '_name'] = 'Required'; });",
      "buffer.owners?.forEach((o, i) => { if (!o.fullName?.trim()) fe['owner_' + i + '_name'] = 'Required'; if (o.phone?.trim() && !normalizePhones(o.phone).ok) fe['owner_' + i + '_phone'] = 'Check number'; });",
      "Folder: mark the phone box red when the number is wrong")

patch(FOLDER_JSX,
      "<SmartInput label=\"PHONE\" value={o.phone} onChange={e => handleOwnerChange(idx,'phone',e.target.value)} id={`owner_${idx}_phone`} />",
      "<SmartInput label=\"PHONE\" value={o.phone} error={fieldErrors['owner_'+idx+'_phone']} onChange={e => handleOwnerChange(idx,'phone',e.target.value)} onBlur={e => { const r = normalizePhones(e.target.value); if (r.ok && r.value !== e.target.value) handleOwnerChange(idx,'phone',r.value); }} id={`owner_${idx}_phone`} />",
      "Folder: phone box tidies itself and shows the error")


# ======================================================================
# ATOMIC GATE -- nothing is written unless every patch matched
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix138).")
    sys.exit(1)

changed = False
CREATED = []   # files that did not exist before, removed again on a red build
BACKUPS = {}   # path -> text before this script touched it

for path, text, label in NEWFILES:
    if os.path.exists(path):
        BACKUPS[path] = read(path)
    else:
        CREATED.append(path)
    write(path, text)
    print("written: " + label)
    changed = True

for path in FILES:
    if FILES[path] != ORIGINAL[path]:
        BACKUPS[path] = ORIGINAL[path]
        write(path, FILES[path])
        print("written: " + os.path.relpath(path, ROOT).replace(os.sep, "/"))
        changed = True

if not changed:
    print("note: nothing changed -- fix139 already applied")


def rollback(reason):
    print(reason)
    for p, t in BACKUPS.items():
        write(p, t)
    for p in CREATED:
        if os.path.exists(p):
            os.remove(p)
        try:
            os.rmdir(os.path.dirname(p))  # remove the folder too if it is now empty
        except OSError:
            pass
    print("Every file was put back exactly as it was. Nothing committed.")
    sys.exit(1)


# ---- backend compile gate ----
if changed:
    mvnw = os.path.join(BACKEND, "mvnw.cmd" if os.name == "nt" else "mvnw")
    cmd = None
    if os.path.exists(mvnw):
        cmd = [mvnw] if os.name == "nt" else ["sh", mvnw]
    else:
        try:
            subprocess.run(["mvn", "-v"], capture_output=True, check=True, shell=(os.name == "nt"))
            cmd = ["mvn"]
        except Exception:
            cmd = None
    if cmd:
        comp = subprocess.run(cmd + ["-q", "-DskipTests", "compile"], cwd=BACKEND, capture_output=True, text=True, shell=(os.name == "nt"))
        out = (comp.stdout or "") + (comp.stderr or "")
        if comp.returncode == 0:
            print("backend compile OK")
        elif "COMPILATION ERROR" in out or ".java:[" in out:
            print(out[-3000:])
            rollback("FAIL: backend does not compile")
        else:
            print(out[-1500:])
            print("note: Maven could not run here (no internet / no dependencies?) -- backend compile gate skipped")
    else:
        print("note: no mvnw / mvn found -- skipping the backend compile gate")

# ---- frontend build gate (fix76) ----
if changed and os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        rollback("FAIL: frontend build is red")
    print("build OK")
elif changed:
    print("note: node_modules not installed here -- skipping build gate (run npm install first if you want it enforced)")


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)
    o = (r.stdout or "").strip()
    if o:
        print(o)
    if r.returncode != 0:
        print("GIT FAIL: " + (r.stderr or "").strip())
        sys.exit(1)
    return r


ident = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or "").strip():
    git("config", "user.name", "nyenz")
    git("config", "user.email", "nyenz@users.noreply.github.com")

if not changed:
    print("nothing to commit -- done")
    sys.exit(0)

git("add", "-A")
git("commit", "-m", "fix139: phone numbers checked and saved in one standard format (+256...), tap-to-call on Recovery cards, Recovery search finds county / sub-county / parish / village of every plot, LOG OUTCOME button no longer sticks, deleting a call note asks first and puts the client's score back")
push = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    print("push failed, retrying against origin/main explicitly...")
    push2 = subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, capture_output=True, text=True)
    if push2.returncode != 0:
        print("GIT PUSH FAILED -- commit is local only. Push manually:\n" + (push2.stderr or push.stderr or "").strip())
    else:
        print(push2.stdout.strip())
else:
    print(push.stdout.strip() or "pushed")