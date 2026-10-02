// PATH: erp-backend/src/main/java/com/gesolutions/erp/config/ScenarioData.java
package com.gesolutions.erp.config;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

/**
 * GOLDEN SEED -- SCENARIO DATASET v4 (fix167; pure data, no Spring, no database).
 *
 * EVERY situation the app knows is seeded AT LEAST TWICE (two different people, places and amounts), so each
 * screen, filter and report has more than one row to show. Every date is "days ago", so the data is always fresh.
 * ScenarioSeeder turns this into rows; selfCheck() proves the money adds up BEFORE anything touches the database.
 *
 * Situations (each x2 or more):
 *   New Folder ....... walk-in (no statuses), deposit only, statuses ticked AT INTAKE + later, custom statuses, refused by
 *                      the land board, ready for titling (paid / part paid), never paid, prepaid, stale, reverted title
 *   Folder -> titled . released (with hand-over note), paid not released, part paid, critical (<25%), title produced
 *                      in bulk (details pending), manual status override, hand-over UNDONE
 *   New Title ........ paid + released, part paid, no payment, FREEHOLD / MAILO / LEASEHOLD / CUSTOMARY, 351 days silent
 *   Legacy Title ..... paid + released, owing, legacy receivable, joint owners
 *   Receivables ...... at intake, part payments incl. STORAGE-FEE payments, joint owners paying separately, paused now,
 *                      pause ended (paused days not charged), deadline in 3 days, custom rate, rate 0 (no fee),
 *                      late-entry start date, joint + silent, auto-flagged at 365 days, PROBLEM, commercial,
 *                      fees REDUCED after negotiation, payment REVERSED
 *   Exits ............ paid off, fees waived (some fees already paid), fees added to cost, set aside (fees kept)
 *   Flags ............ PROBLEM on folder / titled / receivable, PROBLEM flagged then CLEARED
 *   Soft delete ...... deleted recently, deleted long ago, deleted then restored
 *   Owners ........... solo, joint (2), joint (3), one person on 3 projects (x2 people), shared phone, two phone
 *                      numbers, foreign number, very long name, no email / no address
 *   Recovery ......... NEW, CONTACTED, MISSED, SITE VISIT, LOCKED (2 good calls), LOCKED (recent payment),
 *                      callable again
 */
final class ScenarioData {

    private ScenarioData() { }

    // ---------------------------------------------------------------- staff
    static final String ADMIN = "demo.admin";
    static final String DIRECTOR = "demo.director";
    static final String MGR1 = "demo.manager1";
    static final String MGR2 = "demo.manager2";
    static final String SEC1 = "demo.secretary1";
    static final String SEC2 = "demo.secretary2";
    static final String SUSPENDED = "demo.suspended";
    static final String NEWHIRE = "demo.newhire";
    static final String ROOT = "admin_root";

    static final class Staff {
        final String username;
        final String role;
        final boolean active;
        final boolean mustChange;
        final int createdAgo;
        final int promotedAgo;   // 0 = never
        final int suspendedAgo;  // 0 = never
        final int keyResetAgo;   // 0 = never

        Staff(String username, String role, boolean active, boolean mustChange, int createdAgo, int promotedAgo, int suspendedAgo, int keyResetAgo) {
            this.username = username;
            this.role = role;
            this.active = active;
            this.mustChange = mustChange;
            this.createdAgo = createdAgo;
            this.promotedAgo = promotedAgo;
            this.suspendedAgo = suspendedAgo;
            this.keyResetAgo = keyResetAgo;
        }
    }

    static List<Staff> staff() {
        List<Staff> s = new ArrayList<>();
        s.add(new Staff(ADMIN, "ROLE_ADMIN", true, false, 400, 0, 0, 0));
        s.add(new Staff(DIRECTOR, "ROLE_DIRECTOR", true, false, 400, 0, 0, 0));
        s.add(new Staff(MGR1, "ROLE_MANAGER", true, false, 380, 0, 0, 0));
        s.add(new Staff(MGR2, "ROLE_MANAGER", true, false, 210, 60, 0, 0));
        s.add(new Staff(SEC1, "ROLE_SECRETARY", true, false, 300, 0, 0, 0));
        s.add(new Staff(SEC2, "ROLE_SECRETARY", true, false, 120, 0, 0, 20));
        s.add(new Staff(SUSPENDED, "ROLE_SECRETARY", false, false, 250, 0, 40, 0));
        s.add(new Staff(NEWHIRE, "ROLE_SECRETARY", true, true, 3, 0, 0, 0));
        return s;
    }

    static String[] staffNames() {
        List<Staff> s = staff();
        String[] out = new String[s.size()];
        for (int i = 0; i < out.length; i++) out[i] = s.get(i).username;
        return out;
    }

    // --------------------------------------------------------------- people
    static final class Person {
        final String key;
        final String name;
        final String email;
        final String address;
        final String shareWith;
        Person(String key, String name, String email, String address, String shareWith) {
            this.key = key;
            this.name = name;
            this.email = email;
            this.address = address;
            this.shareWith = shareWith;
        }
    }

    private static final String[] SURNAMES = {
        "KATO", "NAMULI", "OKELLO", "NAKATO", "MUWANGA", "BIRUNGI", "KYOMUHENDO", "ATIM", "WAISWA", "TUSIIME",
        "MATOVU", "OKWIR", "WANDERA", "OKURUT", "TWINOMUJUNI", "MUKASA", "KIRABO", "NAIGA", "MBABAZI", "NALWEYISO",
        "LUKWAGO", "OCHEN", "ADONG", "MUGABI", "NAMWANJE", "NAKIRYOWA", "NABIRYE", "KIZZA", "NANSUBUGA", "OPIO",
        "ACEN", "ASIIMWE", "BYARUHANGA", "KOBUSINGE", "LUBEGA", "NAMAGANDA", "SSEBUNYA", "NAKAWESI", "NAKABUYE", "BAGUMA",
        "TUMWEBAZE", "OTIENO", "AUMA", "MUHUMUZA", "SSEGAWA", "MWEBE", "NABATANZI", "NSUBUGA", "KAGIMU", "KAYONDO",
        "WAMALA", "KYOSIIMIRE", "NABWIRE", "TUMUSIIME", "NAMIIRO", "SSERWADDA", "KATENDE", "NANDUTU", "KASULE", "SSEKANDI",
        "AKELLO", "OBURA", "NAMBI", "KIGGUNDU", "AYEBARE", "NINSIIMA", "KAWEESA", "ODONGO", "ALUM", "MUGISHA",
        "NAKIGOZI", "SEMPALA", "AINEMBABAZI", "OKOTH", "NANKYA", "BWAMBALE", "KABUGO", "NASSALI", "ORYEMA", "ATWINE",
        "MUTEBI", "NAKALEMBE", "EBONG", "ARINAITWE", "SSALI", "NAMATOVU", "OWOR", "KANSIIME", "LWANGA", "NAKANWAGI",
        "OGWANG", "AMONG", "BAZIRAKE", "NAMAYANJA", "ODUR", "KYALIGONZA", "MAGEZI", "NAKITTO", "ONYANGO", "KEMIGISHA",
        "SEBUNYA", "NAGGAYI", "OCHIENG", "TUMUHIMBISE", "KIWANUKA", "NABUKENYA", "OLUKA", "MUHWEZI", "NAKAYIZA", "ENYAKU",
        "BUSINGE", "NAKIMULI", "OKIDI", "TUHAISE", "KAJUMBA", "NAMUGGA", "OPOLOT", "ABAASA", "WALUSIMBI", "NAKAWUNDE",
        "OKIROR", "KYARIMPA", "SEGAWA", "NAMPIIMA", "OCHOLA", "BESIGYE", "KISAKYE", "NABASIRYE", "OTIM", "KIRUNDA",
        "NAKANJAKO", "OBONYO", "ATUHAIRE", "SSENTONGO", "NANTEZA", "OKUMU", "KYOMUGISHA", "MAYANJA", "NAKIBUUKA", "EGESA"
    };
    static final int JOINT_LONG = 138;   // OKELLO-OBURA CHRISTOPHER EMMANUEL (joint owner)
    static final int VERY_LONG = 139;    // NAMUKASA-NAKAWUKI BERNADETTE MARY-ANN
    private static final String[] GIVEN = {
        "STEVEN", "SARAH", "RICHARD", "GRACE", "DAVID", "LILIAN", "PATIENCE", "CHRISTINE", "GEOFFREY", "AGNES",
        "HENRY", "PATRICK", "MOSES", "SAMUEL", "JOSEPH", "JOHN BOSCO", "ALLAN", "RUTH", "CLARE", "JOAN",
        "ERIAS", "SIMON", "BETTY", "FRED", "FLAVIA", "SHARON", "SOPHIA", "ANDREW", "IRENE", "DENIS",
        "LOY", "JOVIA", "GODFREY", "ANNET", "MARTIN", "EDITH", "ISMAIL", "FATUMA", "HELLEN", "ROBERT",
        "JAMES", "STELLA", "BRIAN", "CHARLES", "HASSAN", "ROSE", "ALEX", "PAUL", "EMMANUEL", "PETER",
        "DOREEN", "PROSSY", "GLORIA", "HERBERT", "MICHAEL", "ISAAC", "MARY", "BENON", "JUDITH", "VINCENT",
        "ESTHER", "IVAN", "FIONA", "COLLINS", "MERCY", "RONALD", "SUSAN", "ARTHUR", "DIANA", "EDWARD",
        "JANET", "KENNETH", "LYDIA", "NOAH", "OLIVIA", "PHILLIP", "QUEEN", "RAYMOND", "SYLVIA", "TIMOTHY",
        "URSULA", "VICTOR", "WINNIE", "YASIN", "ZAINAB", "ABEL", "BRENDA", "CALVIN", "DORCAS", "ELIJAH",
        "FAITH", "GERALD", "HOPE", "IRIS", "JONAH", "KEVIN", "LEAH", "MARK", "NORAH", "OSCAR",
        "PRISCILLA", "RACHEL", "SOLOMON", "TRACY", "UMAR", "VIOLA", "WILSON", "YVONNE", "ZACK", "ANNA"
    };
    private static final String[] TOWNS = {
        "Nansana, Wakiso", "Bweyogerere, Wakiso", "Pece, Gulu", "Kayabwe, Mpigi", "Rukungiri Municipality", "Hoima City",
        "Lira City West", "Walukuba, Jinja", "Kisoro Town", "Masaka City", "Ayivu, Arua", "Mbale City", "Kumi Town",
        "Kasese Municipality", "Kawempe, Kampala", "Luweero Town", "Kira, Wakiso", "Fort Portal", "Kayunga Town",
        "Mityana Town", "Soroti City East", "Iganga Town", "Mukono Town", "Entebbe Municipality", "Lugazi, Buikwe",
        "Nebbi Town", "Kitgum Town", "Ntungamo Town", "Kyenjojo Town", "Kibuli, Kampala", "Kyengera, Wakiso"
    };

    static String keyOf(int i) { return SURNAMES[i].toLowerCase().replace(' ', '_'); }

    static List<Person> people() {
        List<Person> l = new ArrayList<>();
        for (int i = 0; i < SURNAMES.length; i++) {
            String name = SURNAMES[i] + " " + GIVEN[i % GIVEN.length];
            if (i == VERY_LONG) name = "NAMUKASA-NAKAWUKI BERNADETTE MARY-ANN";   // very long name
            if (i == JOINT_LONG) name = "OKELLO-OBURA CHRISTOPHER EMMANUEL";      // long name, joint owner
            String email = (i % 4 == 1) ? GIVEN[i % GIVEN.length].toLowerCase().replace(' ', '.') + "." + SURNAMES[i].toLowerCase() + "@mail.ug" : "";
            String address = (i % 9 == 4) ? "" : TOWNS[i % TOWNS.length];               // some have no address
            String share = "";
            if (i == 4) share = keyOf(3);      // shared phone (married couple)
            if (i == 37) share = keyOf(36);    // shared phone
            l.add(new Person(keyOf(i), name, email, address, share));
        }
        return l;
    }

    /** Seed NIN: 14 characters, CMS4 + 6 digits + 4 letters. Real NINs never have a letter in position 3. */
    static String nin(int idx) {
        String letters = "ABCDEFGHJKLMNPRSTUWXYZ";
        int n = 310000 + (idx * 7331) % 680000;
        return "CMS4" + String.format("%06d", n)
                + letters.charAt(idx % letters.length())
                + letters.charAt((idx * 5 + 3) % letters.length())
                + letters.charAt((idx * 7 + 1) % letters.length())
                + letters.charAt((idx * 11 + 2) % letters.length());
    }

    /** Uganda mobile in the app's stored form: +256 then 9 digits starting with 7 (PhoneUtil). */
    static String phone(int idx) {
        String[] prefix = {"01", "52", "72", "82", "57", "06", "75", "78"};
        return "+2567" + prefix[idx % prefix.length] + String.format("%06d", 234000 + idx * 173);
    }

    /** Two people with two numbers (joined " / ") and two living abroad (+44 / +1). */
    static String phoneFor(String key, int phoneIdx) {
        if (keyOf(7).equals(key) || keyOf(70).equals(key)) return phone(phoneIdx) + " / " + phone(phoneIdx + 400);
        if (keyOf(6).equals(key)) return "+447700900123";
        if (keyOf(66).equals(key)) return "+14155550123";
        return phone(phoneIdx);
    }

    // -------------------------------------------------------------- project
    // fix180: a folder's progress is written in 6 steps (done = 0..6, 6 = finished). The seeder spreads those steps
    // over the project type's own status list (ProjectType), so the data follows whatever list a type has.
    static final int STEPS = 6;

    static final String AF = "APPLICATION_FORM";
    static final String OL = "OFFER_LETTER";
    static final String FL = "FORWARDING_LETTER";
    static final String DPL = "DEED_PLAN";
    static final String CT = "COPY_OF_TITLE";
    static final String PR = "PAYMENT_RECEIPT";
    static final String SP = "SITE_PHOTOS";     // custom category
    static final String CL = "COUNCIL_LETTERS"; // custom category

    static final class Pay {
        final int ago;        // -1 = the intake day (deposit)
        final long amount;
        final String by;      // null = intake staff
        final String note;
        final String payer;   // owner key; null = the only owner (or the first owner for an intake deposit)
        final boolean storage;
        boolean receipt;
        int reversedAgo = -1;
        String reverseBy;
        String reverseWhy;
        Pay(int ago, long amount, String by, String note, String payer, boolean storage) {
            this.ago = ago;
            this.amount = amount;
            this.by = by;
            this.note = note;
            this.payer = payer;
            this.storage = storage;
        }
        boolean reversed() { return reversedAgo >= 0; }
    }

    static final class Note {
        final int ago;
        final String by;
        final String text;
        final String ownerKey;
        Note(int ago, String by, String text, String ownerKey) {
            this.ago = ago;
            this.by = by;
            this.text = text;
            this.ownerKey = ownerKey;
        }
    }

    static final class Doc {
        final int ago;
        final String category;
        final String fileName;
        final String mime;
        final String by;
        Doc(int ago, String category, String fileName, String mime, String by) {
            this.ago = ago;
            this.category = category;
            this.fileName = fileName;
            this.mime = mime;
            this.by = by;
        }
    }

    static final class Custom {
        final String name;
        final long cost;
        final boolean done;
        Custom(String name, long cost, boolean done) {
            this.name = name;
            this.cost = cost;
            this.done = done;
        }
    }

    static final class Reduce {
        final int ago;
        final long amount;
        final String why;
        Reduce(int ago, long amount, String why) { this.ago = ago; this.amount = amount; this.why = why; }
    }

    static final class Spec {
        final String key;
        final String mode;      // FOLDER, TITLE, LEGACY
        final String[] owners;
        String district = "", county = "", subCounty = "", parish = "", village = "", area;
        long cost;
        int startAgo;
        int entryAgo = -1;
        String intakeBy = SEC1;
        final List<Pay> pays = new ArrayList<>();
        final List<Note> notes = new ArrayList<>();
        final List<Doc> docs = new ArrayList<>();
        final List<Custom> custom = new ArrayList<>();
        final List<Reduce> reductions = new ArrayList<>();
        int done = 0;
        int intakeTicks = -1;   // statuses ticked on the New Project page (-1 = first status only when any are done)
        boolean noStatuses = false;
        // title
        String plot, volumeFolio, block, tenure = "FREEHOLD";   // fix180: volumeFolio = "LRV 4001 FOLIO 2" (Title ID is gone)
        int issuedAgo = -1;
        boolean pendingTitle = false;
        int releasedAgo = -1;
        int undoReleaseAgo = -1;
        int overrideAgo = -1;
        int overrideTo = 0;
        int revertAgo = -1;     // folder whose title was taken off again
        String revertedPlot;
        // receivable
        int recvAgo = -1;
        long initFee = 0;
        long rate = 50000;
        int billed = -1;
        int pauseAgo = -1;          // active pause started this many days ago
        Integer deadlineIn = null;  // active pause ends in N days
        int pastPauseFrom = -1, pastPauseTo = -1;   // a pause that already ended
        boolean recvAtIntake = false;
        boolean auto365 = false;
        boolean startOverride = false;
        boolean customRate = false;
        long origDebt = -1;
        String exit;            // WAIVE, CAPITALIZE, SET_ASIDE, PAID_OFF
        int exitAgo = -1;
        // flags
        String problemNote;
        int problemAgo = -1;
        int problemClearedAgo = -1;
        String clearNote;
        int deletedAgo = -1;
        int restoredAgo = -1;

        Spec(String key, String mode, String[] owners) {
            this.key = key;
            this.mode = mode;
            this.owners = owners;
        }

        // ---- fluent builders
        Spec loc(String[] l, String a) {
            district = l[0]; county = l[1]; subCounty = l[2]; parish = l[3]; village = l[4]; area = a;
            return this;
        }
        Spec cost(long c) { cost = c; return this; }
        Spec times(int start, int entry) { startAgo = start; entryAgo = entry; return this; }
        Spec by(String staff) { intakeBy = staff; return this; }
        Spec deposit(long amt) { if (amt > 0) pays.add(new Pay(-1, amt, null, "Initial deposit at intake", null, false)); return this; }
        Spec pay(int ago, long amt, String by) { pays.add(new Pay(ago, amt, by, null, null, false)); return this; }
        Spec pay(int ago, long amt, String by, String note) { pays.add(new Pay(ago, amt, by, note, null, false)); return this; }
        Spec payBy(int ago, long amt, String by, String payer) { pays.add(new Pay(ago, amt, by, null, payer, false)); return this; }
        Spec storePay(int ago, long amt, String by, String payer) { pays.add(new Pay(ago, amt, by, "Storage fees", payer, true)); return this; }
        Spec rcpt() { if (!pays.isEmpty()) pays.get(pays.size() - 1).receipt = true; return this; }
        Spec reverseLast(int ago, String by, String why) {
            Pay p = pays.get(pays.size() - 1);
            p.reversedAgo = ago; p.reverseBy = by; p.reverseWhy = why;
            return this;
        }
        Spec statuses(int n) { done = n; return this; }
        Spec ticks(int atIntake, int total) { intakeTicks = atIntake; done = total; return this; }
        Spec noStatuses() { noStatuses = true; return this; }
        Spec custom(String name, long c, boolean d) { custom.add(new Custom(name, c, d)); return this; }
        Spec title(String plot, String block, String volumeFolio, int issuedAgo) {
            this.plot = plot; this.block = block; this.volumeFolio = volumeFolio; this.issuedAgo = issuedAgo;
            return this;
        }
        Spec tenure(String t) { tenure = t; return this; }
        Spec pendingTitle(int ago) { pendingTitle = true; issuedAgo = ago; return this; }
        Spec released(int ago) { releasedAgo = ago; return this; }
        Spec releasedThenUndone(int relAgo, int undoAgo) { releasedAgo = relAgo; undoReleaseAgo = undoAgo; return this; }
        Spec override(int to, int ago) { overrideTo = to; overrideAgo = ago; return this; }
        Spec reverted(int ago, String oldPlot) { revertAgo = ago; revertedPlot = oldPlot; return this; }
        Spec recv(int startAgo, long initFee, int billed) { recvAgo = startAgo; this.initFee = initFee; this.billed = billed; return this; }
        Spec recvAtIntake(long initFee, int billed) { recvAtIntake = true; recvAgo = entry(); this.initFee = initFee; this.billed = billed; return this; }
        Spec rate(long r) { rate = r; customRate = true; return this; }
        Spec pauseActive(int startedAgo, int endsInDays) { pauseAgo = startedAgo; deadlineIn = endsInDays; return this; }
        Spec pausePast(int fromAgo, int toAgo) { pastPauseFrom = fromAgo; pastPauseTo = toAgo; return this; }
        Spec auto365() { auto365 = true; return this; }
        Spec startOverride() { startOverride = true; return this; }
        Spec origDebt(long d) { origDebt = d; return this; }
        Spec reduce(int ago, long amount, String why) { reductions.add(new Reduce(ago, amount, why)); return this; }
        Spec exit(String kind, int ago) { exit = kind; exitAgo = ago; return this; }
        Spec problem(int ago, String note) { problemAgo = ago; problemNote = note; return this; }
        Spec problemCleared(int flagAgo, int clearAgo, String note, String clear) { problemAgo = flagAgo; problemNote = note; problemClearedAgo = clearAgo; clearNote = clear; return this; }
        Spec deleted(int ago) { deletedAgo = ago; return this; }
        Spec restored(int deletedAgo, int restoredAgo) { this.deletedAgo = deletedAgo; this.restoredAgo = restoredAgo; return this; }
        Spec note(int ago, String by, String text) { notes.add(new Note(ago, by, text, null)); return this; }
        Spec ownerNote(int ago, String by, String ownerKey, String text) { notes.add(new Note(ago, by, text, ownerKey)); return this; }
        Spec intakeNote(String text) { notes.add(new Note(-1, null, text, null)); return this; }
        Spec docs(int ago, String... cats) { for (String c : cats) docs.add(new Doc(ago, c, null, null, null)); return this; }
        Spec doc(int ago, String cat, String file, String mime, String by) { docs.add(new Doc(ago, cat, file, mime, by)); return this; }

        // ---- derived values
        int entry() { return entryAgo >= 0 ? entryAgo : Math.max(0, startAgo - 2); }
        boolean isFolder() { return "FOLDER".equals(mode); }
        boolean statusesAttached() { return !noStatuses; }   // fix180: every project type has statuses
        /** fix180: the project type this spec is entered as. */
        com.gesolutions.erp.modules.land.model.ProjectType type() {
            if (legacy()) return com.gesolutions.erp.modules.land.model.ProjectType.LEGACY_TITLES;
            if (!isFolder()) return com.gesolutions.erp.modules.land.model.ProjectType.TRANSFER_OF_TITLE;
            return hasTitle() ? com.gesolutions.erp.modules.land.model.ProjectType.RESURVEY : com.gesolutions.erp.modules.land.model.ProjectType.FRESH_SURVEY;
        }
        boolean hasTitle() { return !isFolder() || done >= STEPS || pendingTitle; }
        boolean legacy() { return "LEGACY".equals(mode); }
        int ticksAtIntake() { return intakeTicks >= 0 ? Math.min(intakeTicks, done) : Math.min(1, done); }
        boolean problemNow() { return problemAgo >= 0 && problemClearedAgo < 0; }
        boolean releasedNow() { return releasedAgo >= 0 && undoReleaseAgo < 0; }
        int payAgo(Pay p) { return p.ago < 0 ? entry() : p.ago; }
        long paid() { long s = 0; for (Pay p : pays) if (!p.reversed()) s += p.amount; return s; }
        long storagePaid() { long s = 0; for (Pay p : pays) if (p.storage && !p.reversed()) s += p.amount; return s; }
        long titlePaid() { return paid() - storagePaid(); }
        long reduced() { long s = 0; for (Reduce r : reductions) s += r.amount; return s; }
        long feesAccrued() { return recvAgo >= 0 ? initFee + Math.max(0, billed) * rate : 0; }
        long feesNet() { return Math.max(0, feesAccrued() - reduced()); }
        boolean receivableNow() { return recvAgo >= 0 && exit == null; }
        boolean activePause() { return receivableNow() && pauseAgo >= 0; }
        int pastPauseDays() { return pastPauseFrom >= 0 ? pastPauseFrom - pastPauseTo : 0; }
        /** Days ago the billing clock started (moved forward by any pause that already ended). */
        int clockAgo() { return recvAgo - pastPauseDays(); }

        /** total_cost as stored (fix167 exit rules: paid fees always end up in the cost once out of receivables). */
        long storedCost() {
            if (recvAgo < 0 || exit == null) return cost;
            if ("PAID_OFF".equals(exit) || "CAPITALIZE".equals(exit)) return cost + feesNet();
            return cost + storagePaid();   // WAIVE and SET_ASIDE keep the paid fees counted
        }
        /** storage_fees_accumulated as stored. */
        long storedFees() {
            if (recvAgo < 0) return 0;
            if (exit == null) return feesNet();
            if ("SET_ASIDE".equals(exit)) return Math.max(0, feesNet() - storagePaid());
            return 0;
        }
        long storedFeesPaid() { return receivableNow() ? storagePaid() : 0; }
        long keptFees() { return "SET_ASIDE".equals(exit) ? storedFees() : 0; }
        long owedNow() {
            if (receivableNow()) return Math.max(0, cost + feesNet() - paid());
            return Math.max(0, storedCost() - paid());
        }
        /** Was this payment taken while the plot was in receivables? */
        boolean paidWhileReceivable(Pay p) {
            if (p.ago < 0 || recvAgo < 0) return false;
            if (p.ago > recvAgo) return false;
            return exit == null || p.ago >= exitAgo;
        }
        String payType(Pay p) {
            if (p.ago < 0) return "INITIAL_DEPOSIT";
            return paidWhileReceivable(p) ? "RECEIVABLE_PARTIAL" : "STANDARD";
        }
        long feesAt(int ago) {
            if (recvAgo < 0) return 0;
            int months = Math.max(0, Math.min(billed, (recvAgo - ago) / 30));
            return initFee + months * rate;
        }
        long paidBeforeReceivable() {
            long s = 0;
            for (Pay p : pays) if (!p.reversed() && payAgo(p) >= recvAgo) s += p.amount;
            return s;
        }
        String status() {
            if (releasedNow()) return "RELEASED";
            if (receivableNow()) return "RECEIVABLE";
            if (overrideTo >= 5) return "COMPLETED";
            return "ACTIVE";
        }
        int statusIndex() {
            if (recvAtIntake) return 5;
            return overrideTo > 0 ? overrideTo : 1;
        }
    }

    private static Spec folder(String key, String... o) { return new Spec(key, "FOLDER", o); }
    private static Spec newTitle(String key, String... o) { return new Spec(key, "TITLE", o); }
    private static Spec legacy(String key, String... o) { return new Spec(key, "LEGACY", o); }

    private static final String[][] LOCS = {
        {"WAKISO", "KYADONDO", "NANSANA MUNICIPALITY", "NANSANA EAST", "KYEBANDO"},
        {"WAKISO", "KYADONDO", "KIRA MUNICIPALITY", "BWEYOGERERE", "BUWATE"},
        {"GULU", "ASWA", "LAYIBI DIVISION", "PECE", "LACOR"},
        {"MPIGI", "MAWOKOTA", "MPIGI TOWN COUNCIL", "KAFUMU", "KAYABWE"},
        {"RUKUNGIRI", "RUBABO", "RUKUNGIRI MUNICIPALITY", "NYARUSHANJE", "KEBISONI"},
        {"HOIMA", "BUGAHYA", "HOIMA CITY EAST DIVISION", "KIGOROBYA", "BUJUMBURA"},
        {"LIRA", "ERUTE", "LIRA CITY WEST DIVISION", "ADYEL", "OGUR"},
        {"JINJA", "BUDIOPE", "JINJA CITY SOUTH DIVISION", "WALUKUBA", "MPUMUDDE"},
        {"KISORO", "BUFUMBIRA", "KISORO MUNICIPALITY", "NYAKABANDE", "RUGABANO"},
        {"MASAKA", "BUDDU", "MASAKA CITY", "KIMAANYA", "KYESIGA"},
        {"ARUA", "AYIVU", "ARUA CITY", "RIVER OLI", "ANYAFIO"},
        {"MBALE", "BUNGOKHO", "MBALE CITY", "NAMAKWEKWE", "WANALE"},
        {"KUMI", "KUMI", "KUMI TOWN COUNCIL", "NGORA", "OGINO"},
        {"KASESE", "BUKONZO", "KASESE MUNICIPALITY", "RWENZORI", "KILEMBE"},
        {"KAMPALA", "KYADONDO", "KAWEMPE DIVISION", "MAKERERE III", "KIKONI"},
        {"LUWEERO", "KATIKAMU", "LUWEERO TOWN COUNCIL", "BAMUNANIKA", "WOBULENZI"},
        {"KABAROLE", "BURAHYA", "FORT PORTAL CITY EAST DIVISION", "KARAMBI", "KISIMBA"},
        {"KAYUNGA", "BBAALE", "KAYUNGA TOWN COUNCIL", "KAYUNGA", "NAZIGO"},
        {"MITYANA", "BUSUJJU", "MITYANA TOWN COUNCIL", "KAKINDU", "BUSIMBI"},
        {"SOROTI", "SOROTI", "SOROTI CITY EAST DIVISION", "GWERI", "ARAPAI"},
        {"IGANGA", "BUKOOLI", "IGANGA MUNICIPALITY", "NAKAVULE", "BUGONO"},
        {"MUKONO", "NAKIFUMA", "MUKONO MUNICIPALITY", "CENTRAL", "NAMUMIRA"},
        {"BUIKWE", "NAKISUNGA", "LUGAZI TOWN COUNCIL", "NAJJEMBE", "KASENYI"},
        {"NEBBI", "PADYERE", "NEBBI TOWN COUNCIL", "PAIDHA", "PANYIMUR"},
        {"BUSHENYI", "IGARA", "BUSHENYI-ISHAKA MUNICIPALITY", "NYAKABIRIZI", "KATUNGURU"},
        {"MBARARA", "KASHARI", "MBARARA CITY NORTH DIVISION", "KAKOBA", "NYAMITANGA"},
        {"TORORO", "TORORO", "TORORO MUNICIPALITY", "MOLO", "KADAMA"},
        {"BUSIA", "SAMIA-BUGWE", "BUSIA MUNICIPALITY", "MASABA", "MAYENZE"},
        {"KABALE", "NDORWA", "KABALE MUNICIPALITY", "KITUMBA", "KAMUGANGUZI"},
        {"KIBOGA", "KIBOGA", "KIBOGA TOWN COUNCIL", "KIBOGA", "NKANDWA"},
    };

    /** Hands out people in order, so every project gets its own owner unless one is named on purpose. */
    private static final class Pool {
        int next = 0;
        final Set<Integer> reserved = new HashSet<>();
        String take() {
            while (reserved.contains(next)) next++;
            if (next >= SURNAMES.length) throw new IllegalStateException("seed people ran out: add names to SURNAMES");
            return keyOf(next++);
        }
    }

    private static int plotNo = 3100;
    private static String plot() { return String.valueOf(plotNo++); }

    static List<Spec> projects() {
        plotNo = 3100;
        List<Spec> l = new ArrayList<>();
        Pool pool = new Pool();
        final String M1 = MGR1, M2 = MGR2, AD = ADMIN, DR = DIRECTOR, S1 = SEC1, S2 = SEC2;
        // people reused on purpose (one person, three projects; joint owners; the two shared-phone couples)
        final String multiA = keyOf(59), multiB = keyOf(58);   // each owns 3 projects
        final String coupleA1 = keyOf(3), coupleA2 = keyOf(4); // shared phone
        final String coupleB1 = keyOf(36), coupleB2 = keyOf(37);
        final String jointLong = keyOf(JOINT_LONG);            // long hyphenated name, joint owner
        final String veryLong = keyOf(VERY_LONG);              // very long name
        for (int r : new int[] {0, 1, 3, 4, 21, 22, 36, 37, 58, 59, JOINT_LONG, VERY_LONG}) pool.reserved.add(r);
        int li = 0;

        for (int v = 0; v < 2; v++) {
            String s = v == 0 ? "_a" : "_b";
            long k = v == 0 ? 0 : 400000;   // the second copy uses different amounts
            int d = v == 0 ? 0 : 7;         // ... and different days

            // ============ A: NEW FOLDER MODE ============
            l.add(folder("f_walkin" + s, v == 0 ? keyOf(0) : keyOf(1)).loc(LOCS[li++ % LOCS.length], "0.25 acre")
                .cost(3600000 + k).times(0, 0).noStatuses().intakeNote("Walk-in today. Will bring the deed plan copy next week."));
            l.add(folder("f_deposit_only" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "50x100 ft")
                .cost(4200000 + k).times(14 + d, 12 + d).deposit(1050000).ticks(1, 1).by(S2).intakeNote("Deposit received; field work to be scheduled."));
            l.add(folder("f_ticked_at_intake" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1.5 acres")
                .cost(3800000 + k).times(46 + d, 44 + d).deposit(1520000).pay(20 + d, 760000, M1).rcpt().ticks(3, 3)
                .intakeNote("Field work, deed plan and LC inspection were already done before the client came to us."));
            l.add(folder("f_mid_statuses" + s, coupleA1, coupleA2).loc(LOCS[li++ % LOCS.length], "2 acres")
                .cost(4600000 + k).times(80 + d, 79 + d).deposit(1150000).payBy(50 + d, 1150000, AD, coupleA2).rcpt().ticks(1, 3)
                .intakeNote("Spouses; both must sign the deed plan.")
                .ownerNote(1 + v, S1, coupleA2, "Called. Will sign the deed plan on Friday.")
                .docs(78 + d, AF).doc(40 + d, SP, "boundary-site-photo-" + (v + 1) + ".jpg", "image/jpeg", M1));
            l.add(folder("f_custom_statuses" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(5600000 + k).times(95 + d, 94 + d).deposit(1680000).pay(60 + d, 1120000, M2).rcpt().ticks(1, 2)
                .custom("Neighbour Consent Letters", 150000, true).custom("Boundary Re-opening", 450000, false)
                .note(30 + d, M2, "Neighbour disputes the eastern boundary. Two extra statuses added.").docs(30 + d, CL, SP));
            l.add(folder("f_board_refused" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4900000 + k).times(190 + d, 188 + d).deposit(1960000).pay(140 + d, 980000, AD).rcpt().ticks(1, 3)
                .note(25 + d, M1, "District Land Board refused: boundary mismatch on the deed plan. Surveyor to correct and resubmit."));
            l.add(folder("f_ready_paid" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.4 acre")
                .cost(4300000 + k).times(230 + d, 229 + d).deposit(1290000 + k).pay(190 + d, 1290000, AD).rcpt().pay(45 + d, 1720000, M1).rcpt().ticks(2, 5).override(4, 50 + d)
                .note(9, M1, "Back from the Land Board with approval. Waiting for registration.").docs(220, AF, DPL).docs(15, FL));
            l.add(folder("f_ready_partial" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3900000 + k).times(210 + d, 208 + d).deposit(1170000).pay(160 + d, 780000, M2).rcpt().ticks(1, 5)
                .note(9, M1, "Same Land Board batch. Client to clear the balance before titling.").docs(200, AF, DPL));
            l.add(folder("f_never_paid" + s, pool.take()).loc(LOCS[li++ % LOCS.length], null)
                .cost(3300000 + k).times(60 + d, 58 + d).ticks(1, 2).intakeNote("No deposit taken. The family is pooling money."));
            l.add(folder("f_prepaid" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.25 acre")
                .cost(2800000 + k).times(30 + d, 29 + d).deposit(2800000 + k).ticks(1, 1).intakeNote("Paid in full at intake."));
            l.add(folder("f_stale" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1.2 acres")
                .cost(4400000 + k).times(310 + d, 309 + d).deposit(880000).pay(295 + d, 440000, M1).rcpt().ticks(1, 1)
                .note(200, M1, "Client travelling; promised to return in the dry season."));
            l.add(folder("f_title_reverted" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.6 acre")
                .cost(4100000 + k).times(170 + d, 168 + d).deposit(1230000).pay(80 + d, 1230000, M1).rcpt().ticks(2, 5)
                .reverted(6 + d, "99" + (10 + v))
                .note(6 + d, DR, "Title details were typed on the wrong project; taken off again. The real title is still at the Land Board."));
            l.add(folder("f_recv_at_intake" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "50x100 ft")
                .cost(4500000 + k).times(100 + d, 95 + d).deposit(900000).ticks(2, 2).recvAtIntake(50000, (95 + d) / 30).origDebt(3600000 + k)
                .intakeNote("Entered as receivable from day one; client relocating."));

            // ============ B: FOLDER PATH -> TITLED ============
            l.add(folder("t_released" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(5000000 + k).times(300 + d, 299 + d).deposit(1500000).pay(250 + d, 1000000, AD).rcpt().pay(200 + d, 1000000, M1).rcpt().pay(150 + d, 1500000 + k, M1).rcpt().ticks(1, 6)
                .title(plot(), "BLOCK 17", "LRV 4102 FOLIO " + (3 + v), 30 + d).released(20 - v * 5)
                .docs(298, AF).docs(290, OL).docs(280, FL).docs(270, DPL).docs(30, CT)
                .doc(250, null, "nin-scan-" + (v + 1) + ".jpg", "image/jpeg", S1));
            l.add(folder("t_paid_unreleased" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.1 acre")
                .cost(4800000 + k).times(220 + d, 219 + d).deposit(1440000).pay(170 + d, 1440000, AD).rcpt().pay(14 + d, 1920000 + k, M2).rcpt().ticks(1, 6)
                .title(plot(), "KYADONDO BLOCK 190", "LRV 4188 FOLIO " + (21 + v), 12 + d).docs(12, CT));
            l.add(folder("t_partial" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(5400000 + k).times(250 + d, 249 + d).deposit(1620000).pay(170 + d, 810000, M1).rcpt().pay(60 + d, 810000, AD).rcpt().ticks(1, 6)
                .title(plot(), "KATIKAMU BLOCK 62", "LRV 4090 FOLIO " + (24 + v), 40 + d));
            l.add(folder("t_critical" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.75 acre")
                .cost(6000000 + k).times(200 + d, 198 + d).deposit(900000).ticks(1, 6)
                .title(plot(), "KYADONDO BLOCK 205", "LRV 4210 FOLIO " + (30 + v), 60 + d));
            l.add(folder("t_pending_details" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4500000 + k).times(240 + d, 238 + d).deposit(1350000).pay(150 + d, 1800000, M1).rcpt().ticks(1, 6).pendingTitle(3)
                .note(3, M1, "Marked as title produced in the Ready for Titling batch. Title details still to be entered."));
            l.add(folder("t_status_override" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1.5 acres")
                .cost(3300000 + k).times(140 + d, 139 + d).deposit(990000).pay(80 + d, 990000, M2).rcpt().ticks(1, 4).override(5, 25 + d)
                .note(25 + d, M2, "Status moved manually to 5: the Land Board decision was verbal."));
            l.add(folder("t_handover_undone" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.3 acre")
                .cost(4000000 + k).times(260 + d, 258 + d).deposit(2000000).pay(120 + d, 2000000 + k, AD).rcpt().ticks(1, 6)
                .title(plot(), "BUSIRO BLOCK 77", "LRV 2210 FOLIO " + (5 + v), 90 + d).releasedThenUndone(15 + d, 14 + d)
                .note(14 + d, DR, "Hand-over was recorded on the wrong plot. Undone; the client has NOT collected yet."));

            // ============ C: NEW TITLE MODE ============
            l.add(newTitle("n_paid_released" + s, v == 0 ? keyOf(21) : coupleB1, v == 0 ? keyOf(22) : coupleB2).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3200000 + k).times(60 + d, 58 + d).deposit(3200000 + k).title(plot(), "SOROTI BLOCK 21", "LRV 3915 FOLIO " + (2 + v), 70 + d).released(8 + d)
                .intakeNote("Spouses; title in joint names.").docs(58, CT, AF));
            l.add(newTitle("n_partial" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(4100000 + k).times(100 + d, 98 + d).deposit(1230000).pay(35 + d, 615000, M2).rcpt()
                .title(plot(), "BUGWERI BLOCK 40", "LRV 3960 FOLIO " + (27 + v), 120 + d));
            l.add(newTitle("n_no_payment" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.2 acre")
                .cost(2900000 + k).times(25 + d, 24 + d).title(plot(), "MUKONO BLOCK 33", "LRV 4233 FOLIO " + (12 + v), 40).intakeNote("Title in hand; no deposit yet."));
            String m1 = pool.take(), m2 = pool.take(), m3 = v == 0 ? jointLong : pool.take();
            l.add(newTitle("n_mailo_three_owners" + s, m1, m2, m3).tenure("MAILO").loc(LOCS[li++ % LOCS.length], "4 acres")
                .cost(9000000 + k).times(150 + d, 148 + d).deposit(2700000).payBy(90 + d, 2250000, M1, m2).rcpt().payBy(28 + d, 1350000, M2, m3).rcpt()
                .ownerNote(5 + d, S2, m1, "Spoke to the first owner. She will consult the other two.")
                .title(plot(), "KYADONDO BLOCK 190", "LRV 1584 FOLIO " + (22 + v), 200));
            l.add(newTitle("n_leasehold" + s, pool.take()).tenure("LEASEHOLD").loc(LOCS[li++ % LOCS.length], "12 acres")
                .cost(24000000 + k).times(210 + d, 208 + d).deposit(7200000).pay(150 + d, 4800000, AD).rcpt().pay(40 + d, 2400000, DR).rcpt()
                .title(plot(), "NEBBI BLOCK 8", "LRV 3902 FOLIO " + (9 + v), 300).docs(207, AF, OL));
            l.add(newTitle("n_customary" + s, pool.take()).tenure("CUSTOMARY").loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(1200000 + k).times(45 + d, 44 + d).deposit(1200000 + k).title(plot(), "CHUA BLOCK 3", "LRV 3122 FOLIO " + (13 + v), 50));
            l.add(newTitle("n_freehold_owing" + s, pool.take()).tenure("FREEHOLD").loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(5200000 + k).times(120 + d, 118 + d).deposit(2600000).pay(30 + d, 600000, M1).rcpt()
                .title(plot(), "BUSIRO BLOCK 12", "LRV 4333 FOLIO " + (19 + v), 130));
            l.add(newTitle("n_silent_351" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(5200000 + k).times(353 + v, 351 + v).deposit(1300000).title(plot(), "RUSHENYI BLOCK 14", "LRV 4021 FOLIO " + (11 + v), 400)
                .note(120, M1, "Called several times. Client has gone quiet. Will move to receivables by itself at 365 days."));

            // ============ D: LEGACY TITLE MODE ============
            l.add(legacy("l_paid_released" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "2 acres")
                .cost(3500000 + k).times(13000, 210 + d).deposit(3500000 + k).title(plot(), "MUGUSU BLOCK 61", "LRV 1120 FOLIO " + (7 + v), 13000).released(190 + d)
                .doc(205, CT, "copy-of-title-legacy-" + (v + 1) + ".pdf", "application/pdf", S1));
            l.add(legacy("l_owing" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4000000 + k).times(11000, 130 + d).deposit(800000).pay(70 + d, 800000, M1).rcpt()
                .title(plot(), "BURAHYA BLOCK 8", "LRV 1584 FOLIO " + (40 + v), 11000));
            l.add(legacy("l_receivable" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(3500000 + k).times(14000, 520 + d).deposit(1750000).recv(430 + d, 50000, (430 + d) / 30).origDebt(1750000 + k)
                .title(plot(), "BUDDU BLOCK 61", "LRV 1121 FOLIO " + (8 + v), 14000)
                .note(400, M1, "Legacy file. Client silent for over a year. Moved to receivables manually."));
            String lj1 = pool.take(), lj2 = pool.take();
            l.add(legacy("l_joint" + s, lj1, lj2).tenure("MAILO").loc(LOCS[li++ % LOCS.length], "0.4 acre")
                .cost(7500000 + k).times(15000, 300 + d).deposit(2250000).payBy(200 + d, 1500000, AD, lj1).rcpt().payBy(120 + d, 1500000, AD, lj2).rcpt()
                .title(plot(), "KYADONDO BLOCK 118", "LRV 1900 FOLIO " + (14 + v), 15000).intakeNote("Brother and sister; they pay separately."));

            // ============ E: RECEIVABLES ============
            String jp1 = pool.take(), jp2 = pool.take();
            l.add(newTitle("r_storage_payments" + s, jp1, jp2).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(6000000 + k).times(330 + d, 328 + d).deposit(1800000).payBy(310 + d, 600000, M1, jp1).rcpt()
                .recv(300 + d, 0, (300 + d) / 30)
                .payBy(210 + d, 300000, M1, jp2).rcpt().storePay(120 + d, 150000, M2, jp1).rcpt().storePay(45 + d, 100000, AD, jp2).rcpt()
                .title(plot(), "IGARA BLOCK 96", "LRV 3310 FOLIO " + (14 + v), 340)
                .note(45 + d, AD, "Each owner pays separately; storage fees and title payments are recorded per owner."));
            l.add(newTitle("r_paused_now" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4200000 + k).times(280 + d, 278 + d).deposit(840000).recv(260 + d, 0, (260 + d - 80) / 30).pauseActive(80, 120 - v * 30)
                .title(plot(), "KASHARI BLOCK 96", "LRV 4102 FOLIO " + (30 + v), 285)
                .note(80, DR, "Storage billing paused: bereavement in the family. The paused days are not charged."));
            l.add(newTitle("r_deadline_3_days" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.8 acre")
                .cost(3800000 + k).times(250 + d, 248 + d).deposit(760000).recv(240 + d, 0, (240 + d - 27) / 30).pauseActive(27, 3 + v)
                .title(plot(), "TORORO BLOCK 45", "LRV 3941 FOLIO " + (18 + v), 255)
                .note(4, DR, "Negotiation window closes in a few days. Client promised a lump sum."));
            l.add(newTitle("r_pause_ended" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3500000 + k).times(220 + d, 218 + d).deposit(700000).recv(200 + d, 0, (200 + d - 60) / 30).pausePast(120 + d, 60 + d)
                .title(plot(), "BUSIA BLOCK 33", "LRV 3890 FOLIO " + (5 + v), 225)
                .note(60 + d, DR, "Pause ended with no payment. Fees restarted; the 60 paused days were not charged."));
            l.add(newTitle("r_custom_rate" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.6 acre")
                .cost(5000000 + k).times(302 + d, 300 + d).deposit(1000000).recv(280 + d, 75000, (280 + d) / 30).rate(75000 + v * 25000)
                .title(plot(), "NDORWA BLOCK 22", "LRV 3902 FOLIO " + (29 + v), 305).note(279, DR, "Storage fee agreed below / above the default."));
            l.add(newTitle("r_rate_zero" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.3 acre")
                .cost(3600000 + k).times(200 + d, 198 + d).deposit(720000).recv(180 + d, 100000, (180 + d) / 30).rate(0)
                .title(plot(), "BUSIRO BLOCK 21", "LRV 4300 FOLIO " + (7 + v), 205).note(150, DR, "Director stopped the monthly fee (rate set to 0): the client is paying the balance monthly."));
            l.add(newTitle("r_late_entry" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(4000000 + k).times(200 + d, 20 + d).deposit(800000).recv(150 + d, 0, (150 + d) / 30).startOverride().origDebt(3200000 + k)
                .title(plot(), "BUSIRO BLOCK 12", "LRV 4333 FOLIO " + (9 + v), 210).note(19, ADMIN, "Keyed in late. Receivable start date set to the real date."));
            l.add(newTitle("r_joint_silent" + s, pool.take(), pool.take()).loc(LOCS[li++ % LOCS.length], "0.2 acre")
                .cost(4400000 + k).times(352 + d, 350 + d).deposit(880000).recv(330 + d, 0, (330 + d) / 30)
                .title(plot(), "KYADONDO BLOCK 205", "LRV 4001 FOLIO " + (2 + v), 360).intakeNote("Two owners; neither answers calls."));
            l.add(newTitle("r_auto_365" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(5600000 + k).times(422 + d, 420 + d).deposit(1120000).recv(55 + d, 0, (55 + d) / 30).auto365().origDebt(4480000 + k)
                .title(plot(), "KYADONDO BLOCK 244", "LRV 3800 FOLIO " + (1 + v), 430));
            l.add(newTitle("r_problem" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4800000 + k).times(260 + d, 258 + d).deposit(960000).recv(220 + d, 0, (220 + d) / 30)
                .title(plot(), "BUKEDEA BLOCK 9", "LRV 3811 FOLIO " + (4 + v), 265)
                .problem(60 + d, "Boundary dispute with the neighbour. Case pending at the LC court."));
            l.add(newTitle("r_commercial" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "2 acres")
                .cost(18000000 + k).times(262 + d, 260 + d).deposit(5400000).recv(240 + d, 150000, (240 + d) / 30).rate(150000).origDebt(12600000 + k)
                .pay(100 + d, 2000000, DR).rcpt().storePay(45 + d, 500000, DR, null).rcpt()
                .title(plot(), "KYADONDO BLOCK 12", "LRV 4600 FOLIO " + (33 + v), 270).docs(258, AF, OL).docs(90, CL));
            l.add(newTitle("r_fees_reduced" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4600000 + k).times(320 + d, 318 + d).deposit(920000).recv(300 + d, 0, (300 + d) / 30)
                .reduce(30 + d, 200000, "[Agreed with the client] Director agreed a lower figure after a hardship letter.")
                .title(plot(), "IGARA BLOCK 98", "LRV 4069 FOLIO " + (40 + v), 330));
            l.add(newTitle("r_payment_reversed" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(4300000 + k).times(240 + d, 238 + d).deposit(860000).recv(200 + d, 0, (200 + d) / 30)
                .pay(60 + d, 500000, M1).rcpt().reverseLast(55 + d, DR, "Cheque bounced at the bank.")
                .pay(20 + d, 300000, M2).rcpt()
                .title(plot(), "BUDDU BLOCK 70", "LRV 4070 FOLIO " + (50 + v), 245));

            // ============ F: RECEIVABLE EXITS ============
            l.add(newTitle("x_paid_off" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3600000).times(700, 698).deposit(720000).recv(330, 0, 10)
                .pay(200, 1000000, M1).rcpt().pay(120, 1000000, M1).rcpt().storePay(60, 300000 + v * 100000, M1, null).rcpt().pay(12, 880000, DR).rcpt().storePay(12, 200000 - v * 100000, DR, null).rcpt()
                .exit("PAID_OFF", 12).title(plot(), "KIBOGA BLOCK 4", "LRV 3400 FOLIO " + (6 + v), 705).released(5).docs(5, CT));
            l.add(newTitle("x_fees_waived" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3900000 + k).times(400, 398).deposit(780000).pay(380, 390000, M1).rcpt()
                .recv(250, 0, 7).storePay(100, 100000, M2, null).rcpt().exit("WAIVE", 40).pay(30, 500000, M2).rcpt()
                .title(plot(), "KOOKI BLOCK 27", "LRV 4066 FOLIO " + (13 + v), 405));
            l.add(newTitle("x_fees_capitalized" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.7 acre")
                .cost(4300000 + k).times(380, 378).deposit(1200000)
                .recv(210, 0, 6).exit("CAPITALIZE", 30).pay(15, 600000, M1).rcpt()
                .title(plot(), "BUSIA BLOCK 34", "LRV 4067 FOLIO " + (14 + v), 385));
            l.add(newTitle("x_set_aside" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4600000 + k).times(200, 198).deposit(920000)
                .recv(190, 0, 5).storePay(100, 50000, M1, null).rcpt().exit("SET_ASIDE", 35)
                .title(plot(), "IGARA BLOCK 97", "LRV 4068 FOLIO " + (15 + v), 205)
                .note(35, DR, "Set aside while the court case runs. Unpaid fees are kept on the project."));

            // ============ G: FLAGS, DELETES, OWNERS ============
            l.add(folder("p_problem_folder" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3900000 + k).times(90 + d, 88 + d).deposit(1170000).pay(40 + d, 780000, M1).rcpt().ticks(1, 2)
                .problem(14 + d, "Owner name on the deed plan does not match the National ID.")
                .doc(14, null, "problem-proof-id-mismatch-" + (v + 1) + ".jpg", "image/jpeg", M1));
            l.add(newTitle("p_problem_titled" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(5700000 + k).times(130 + d, 128 + d).deposit(1710000).pay(70 + d, 1140000, AD).rcpt()
                .title(plot(), "BUSIRO BLOCK 90", "LRV 4069 FOLIO " + (16 + v), 135)
                .problem(8 + d, "Title deed shows a different plot size from the survey."));
            l.add(newTitle("p_problem_cleared" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.5 acre")
                .cost(4400000 + k).times(160 + d, 158 + d).deposit(1320000).pay(50 + d, 880000, M2).rcpt()
                .title(plot(), "BUSIRO BLOCK 91", "LRV 4069 FOLIO " + (60 + v), 165)
                .problemCleared(40 + d, 10 + d, "Two different spellings of the owner's name on the documents.", "Corrected deed plan received; names now match the National ID."));
            l.add(newTitle("d_deleted_recent" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(4000000 + k).times(150 + d, 148 + d).deposit(1200000).pay(90 + d, 800000, M1).rcpt()
                .title(plot(), "MAWOKOTA BLOCK 5", "LRV 4070 FOLIO " + (17 + v), 155).deleted(12 + d).docs(140, DPL));
            l.add(folder("d_deleted_old" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "0.3 acre")
                .cost(3000000 + k).times(100 + d, 99 + d).statuses(0).deleted(50 + d));
            l.add(folder("d_deleted_restored" + s, pool.take()).loc(LOCS[li++ % LOCS.length], "1 acre")
                .cost(3500000 + k).times(120 + d, 118 + d).deposit(700000).pay(70 + d, 700000, M2).rcpt().ticks(1, 1).restored(40 + d, 33 + d));
            String multi = v == 0 ? multiA : multiB;
            l.add(folder("o_same_owner_folder" + s, multi).loc(LOCS[li++ % LOCS.length], "0.1 acre")
                .cost(3400000 + k).times(35 + d, 34 + d).deposit(1020000).pay(10 + d, 680000, M1).rcpt().ticks(1, 1));
            l.add(newTitle("o_same_owner_title" + s, multi).loc(LOCS[li++ % LOCS.length], "0.4 acre")
                .cost(4900000 + k).times(180 + d, 178 + d).deposit(1470000).pay(100 + d, 980000, M2).rcpt()
                .title(plot(), "KYADONDO BLOCK 260", "LRV 4071 FOLIO " + (18 + v), 185));
            l.add(newTitle("o_same_owner_receivable" + s, multi).loc(LOCS[li++ % LOCS.length], "0.3 acre")
                .cost(3000000 + k).times(222 + d, 220 + d).deposit(600000).recv(120 + d, 0, (120 + d) / 30)
                .title(plot(), "MUKONO BLOCK 31", "LRV 4072 FOLIO " + (19 + v), 225));
            l.add(folder("o_long_name" + s, v == 0 ? veryLong : pool.take()).loc(LOCS[li++ % LOCS.length], "0.25 acre")
                .cost(3200000 + k).times(20 + d, 19 + d).deposit(800000).ticks(1, 1));
        }

        // oldest first so project indexes (001A, 002A ...) follow real chronology
        l.sort((a, b) -> Integer.compare(b.entry(), a.entry()));
        return l;
    }

    // ------------------------------------------------------ recovery calls
    static final class Call {
        final String person;
        final String tag;
        final int ago;
        final String by;
        final String text;
        Call(String person, String tag, int ago, String by, String text) {
            this.person = person;
            this.tag = tag;
            this.ago = ago;
            this.by = by;
            this.text = text;
        }
    }

    static final String ANS = "answered call";
    static final String NOP = "not picking up";
    static final String NTH = "not going through";
    static final String WRN = "wrong number";

    /** Calls go to the owners of the projects at the given keys, so each recovery state shows on 2+ real cards. */
    static List<Call> calls() {
        Map<String, String> owner = new HashMap<>();
        for (Spec s : projects()) owner.put(s.key, s.owners[0]);
        List<Call> c = new ArrayList<>();
        final String M1 = MGR1, M2 = MGR2, S1 = SEC1, S2 = SEC2, DR = DIRECTOR, SU = SUSPENDED;
        for (String s : new String[] {"_a", "_b"}) {
            // CONTACTED (last call good)
            c.add(new Call(owner.get("t_partial" + s), NOP, 24, S1, null));
            c.add(new Call(owner.get("t_partial" + s), ANS, 3, S1, "Will bring the balance next week."));
            c.add(new Call(owner.get("f_mid_statuses" + s), ANS, 1, S1, "Will sign the deed plan on Friday."));
            c.add(new Call(owner.get("r_paused_now" + s), ANS, 82, DR, "Family bereavement. Asked to pause storage fees."));
            // MISSED (last call bad, fewer than two misses in 30 days)
            c.add(new Call(owner.get("n_partial" + s), ANS, 52, SU, "Asked for the status timeline."));
            c.add(new Call(owner.get("n_partial" + s), NOP, 6, S2, null));
            c.add(new Call(owner.get("f_never_paid" + s), WRN, 15, S1, "Number belongs to someone else."));
            c.add(new Call(owner.get("r_pause_ended" + s), NOP, 2, S2, null));
            // SITE VISIT (two misses, no good call in 30 days)
            c.add(new Call(owner.get("r_joint_silent" + s), NOP, 18, S1, null));
            c.add(new Call(owner.get("r_joint_silent" + s), NTH, 9, S2, null));
            c.add(new Call(owner.get("f_stale" + s), NTH, 8, M1, null));
            c.add(new Call(owner.get("f_stale" + s), NOP, 3, M1, null));
            // LOCKED by two good calls
            c.add(new Call(owner.get("l_owing" + s), ANS, 20, M1, "Will pay after the coffee harvest."));
            c.add(new Call(owner.get("l_owing" + s), ANS, 5, M2, "Confirmed the payment date."));
            c.add(new Call(owner.get("r_commercial" + s), ANS, 21, M2, "Needs board approval to pay."));
            c.add(new Call(owner.get("r_commercial" + s), ANS, 7, M2, "Board approved a part payment."));
            // callable again (lock ended)
            c.add(new Call(owner.get("f_recv_at_intake" + s), ANS, 45, S1, "Relocating; will call back."));
            c.add(new Call(owner.get("f_recv_at_intake" + s), ANS, 32, S1, "Settling in; asked for a payment plan."));
        }
        return c;
    }

    /** People whose reliability meter is set by hand (everyone else is computed from their calls). */
    static Map<String, Double> reliabilityOverrides() {
        Map<String, String> owner = new HashMap<>();
        for (Spec s : projects()) owner.put(s.key, s.owners[0]);
        Map<String, Double> m = new HashMap<>();
        m.put(owner.get("r_joint_silent_a"), 45.0);
        m.put(owner.get("r_joint_silent_b"), 40.0);
        m.put(owner.get("f_stale_a"), 55.0);
        m.put(owner.get("f_stale_b"), 50.0);
        m.put(owner.get("l_owing_a"), 92.0);
        m.put(owner.get("l_owing_b"), 88.0);
        return m;
    }

    // ------------------------------------------------------------- expenses
    static final class Exp {
        final int minutesAgo;
        final String category;
        final long amount;
        final String note;
        final String by;
        final String spentBy;
        final int editedMinutesAgo;   // 0 = never edited
        final String editedBy;
        Exp(int minutesAgo, String category, long amount, String note, String by, String spentBy, int editedMinutesAgo, String editedBy) {
            this.minutesAgo = minutesAgo;
            this.category = category;
            this.amount = amount;
            this.note = note;
            this.by = by;
            this.spentBy = spentBy;
            this.editedMinutesAgo = editedMinutesAgo;
            this.editedBy = editedBy;
        }
    }

    static List<Exp> expenses() {
        List<Exp> l = new ArrayList<>();
        Random r = new Random(20261001L);
        String[] fieldAgents = {"Field Team - Kasozi", "Driver - Okello Moses", "Surveyor - Ssenyonga", null, null};
        String[] recorders = {SEC1, SEC2, MGR1, MGR2};
        final int DAY = 1440;
        for (int m = 0; m < 14; m++) {
            int base = m * 30;
            l.add(new Exp((base + 27) * DAY + 300, "Rent", 1800000, "Office rent for the month", ADMIN, null, 0, null));
            l.add(new Exp((base + 2) * DAY + 200, "Salaries", 6500000, "Monthly staff salaries", DIRECTOR, null, 0, null));
            l.add(new Exp((base + 20) * DAY + 90, "Airtime & Data", 100000 + r.nextInt(9) * 10000, "Office and recovery-call airtime", SEC1, null, 0, null));
            int fuelCount = 2 + r.nextInt(2);
            for (int i = 0; i < fuelCount; i++) {
                l.add(new Exp((base + 3 + i * 9) * DAY + r.nextInt(500), "Fuel", 80000 + r.nextInt(14) * 10000, "Fuel for site visits", recorders[r.nextInt(4)], fieldAgents[r.nextInt(5)], 0, null));
            }
            int landOffice = 1 + r.nextInt(2);
            for (int i = 0; i < landOffice; i++) {
                l.add(new Exp((base + 5 + i * 12) * DAY + r.nextInt(500), "Land Office", 150000 + r.nextInt(20) * 50000, "Search fees and stamps at the land office", recorders[r.nextInt(4)], null, 0, null));
            }
            int field = 1 + r.nextInt(2);
            for (int i = 0; i < field; i++) {
                l.add(new Exp((base + 7 + i * 10) * DAY + r.nextInt(500), "Fieldwork", 200000 + r.nextInt(14) * 50000, "Survey crew allowance and boundary marks", recorders[r.nextInt(4)], fieldAgents[r.nextInt(3)], 0, null));
            }
            l.add(new Exp((base + 14) * DAY + r.nextInt(500), "Office", 50000 + r.nextInt(8) * 50000, "Tea, water and cleaning supplies", SEC2, null, 0, null));
        }
        // rare and large (each kind twice)
        l.add(new Exp(75 * DAY, "Vehicle Repairs", 1400000, "Replaced clutch on the field van", MGR1, "Driver - Okello Moses", 0, null));
        l.add(new Exp(190 * DAY, "Vehicle Repairs", 2900000, "Gearbox overhaul", DIRECTOR, "Driver - Okello Moses", 0, null));
        l.add(new Exp(310 * DAY, "Vehicle Repairs", 850000, "Four new tyres", MGR1, null, 0, null));
        l.add(new Exp(120 * DAY, "Stationery", 240000, "Printer toner and survey paper", SEC1, null, 0, null));
        l.add(new Exp(260 * DAY, "Stationery", 180000, "Box files and folders", SEC2, null, 0, null));
        l.add(new Exp(45 * DAY, "Internet & Utilities", 320000, "Fibre internet, electricity and water", ADMIN, null, 0, null));
        l.add(new Exp(75 * DAY + 60, "Internet & Utilities", 300000, "Fibre internet, electricity and water", ADMIN, null, 0, null));
        // last 24 hours: still editable (x2)
        l.add(new Exp(95, "Fuel", 120000, "Fuel for the Nansana site visit", SEC1, "Driver - Okello Moses", 0, null));
        l.add(new Exp(310, "Airtime & Data", 50000, null, SEC2, null, 0, null));
        l.add(new Exp(700, "Land Office", 450000, "Deed plan checking fee, Wakiso", MGR1, null, 0, null));
        // corrected within the edit window (x2)
        l.add(new Exp(900, "Fieldwork", 380000, "Boundary re-opening allowance (corrected from 830,000)", MGR2, "Field Team - Kasozi", 600, MGR1));
        l.add(new Exp(1000, "Fieldwork", 380000, "Survey pegs (corrected from 830,000)", SEC1, null, 700, MGR2));
        // just outside the 24-hour edit window (x2)
        l.add(new Exp(1800, "Office", 90000, "Stationery and printing", SEC1, null, 0, null));
        l.add(new Exp(2000, "Office", 60000, "Cleaning supplies", SEC2, null, 0, null));
        return l;
    }

    // ----------------------------------------------------------- self check
    static void selfCheck() {
        Map<String, Person> byKey = new LinkedHashMap<>();
        for (Person p : people()) {
            if (byKey.put(p.key, p) != null) throw new IllegalStateException("duplicate person key " + p.key);
        }
        Set<String> plots = new HashSet<>();
        Set<String> keys = new HashSet<>();
        Set<String> staff = new HashSet<>();
        for (String s : staffNames()) staff.add(s);
        staff.add(ROOT);
        for (Spec s : projects()) {
            String at = "[" + s.key + "] ";
            if (!keys.add(s.key)) throw new IllegalStateException(at + "duplicate project key");
            if (s.owners.length == 0) throw new IllegalStateException(at + "no owners");
            Set<String> ownerSet = new HashSet<>();
            for (String o : s.owners) {
                if (o == null || !byKey.containsKey(o)) throw new IllegalStateException(at + "unknown owner " + o);
                if (!ownerSet.add(o)) throw new IllegalStateException(at + "same owner twice " + o);
            }
            if (s.cost <= 0) throw new IllegalStateException(at + "cost missing");
            if (s.entry() > s.startAgo && !s.legacy() && s.startAgo != 0) throw new IllegalStateException(at + "entry date earlier than start date");
            if (!staff.contains(s.intakeBy)) throw new IllegalStateException(at + "unknown intake staff");
            for (Pay p : s.pays) {
                if (p.amount <= 0) throw new IllegalStateException(at + "bad payment amount");
                if (p.by != null && !staff.contains(p.by)) throw new IllegalStateException(at + "unknown payer staff " + p.by);
                if (s.payAgo(p) > s.entry()) throw new IllegalStateException(at + "payment older than intake");
                if (p.payer != null && !ownerSet.contains(p.payer)) throw new IllegalStateException(at + "payer is not an owner " + p.payer);
                if (p.payer == null && p.ago >= 0 && s.owners.length > 1) throw new IllegalStateException(at + "joint owners: say which owner paid");
                if (p.storage && !s.paidWhileReceivable(p)) throw new IllegalStateException(at + "storage payment outside receivables");
                if (p.reversed() && (p.reversedAgo > p.ago || p.ago < 0)) throw new IllegalStateException(at + "reversal before its payment");
                if (p.reversed() && (p.reverseBy == null || !staff.contains(p.reverseBy))) throw new IllegalStateException(at + "reversal staff unknown");
            }
            for (Note n : s.notes) {
                if (n.by != null && !staff.contains(n.by)) throw new IllegalStateException(at + "unknown note author " + n.by);
                if (n.ownerKey != null && !ownerSet.contains(n.ownerKey)) throw new IllegalStateException(at + "owner note for a non-owner " + n.ownerKey);
            }
            if (s.hasTitle() && !s.pendingTitle) {
                if (s.plot == null || s.block == null || s.volumeFolio == null) throw new IllegalStateException(at + "title details missing");
                if (!plots.add(s.plot)) throw new IllegalStateException(at + "duplicate plot " + s.plot);
            }
            if (s.revertAgo >= 0 && (s.hasTitle() || !s.isFolder())) throw new IllegalStateException(at + "a reverted project is a folder without title");
            if (s.isFolder() && s.done >= STEPS && !s.hasTitle()) throw new IllegalStateException(at + "all statuses done but no title");
            if (s.pendingTitle && s.done < 6) throw new IllegalStateException(at + "pending title needs all statuses done");
            if (s.intakeTicks > s.done) throw new IllegalStateException(at + "more statuses ticked at intake than in total");
            if (s.releasedAgo >= 0) {
                if (!s.hasTitle() || s.pendingTitle) throw new IllegalStateException(at + "released without title details");
                if (s.owedNow() > 0) throw new IllegalStateException(at + "released while UGX " + s.owedNow() + " is owed");
                if (s.keptFees() > 0) throw new IllegalStateException(at + "released with set-aside fees");
                if (s.problemNow()) throw new IllegalStateException(at + "released while flagged PROBLEM");
                if (s.undoReleaseAgo >= 0 && s.undoReleaseAgo > s.releasedAgo) throw new IllegalStateException(at + "undo before hand-over");
            }
            if (s.problemClearedAgo >= 0 && s.problemClearedAgo > s.problemAgo) throw new IllegalStateException(at + "cleared before flagged");
            // money
            long paid = s.paid();
            if (s.titlePaid() > s.cost + ("CAPITALIZE".equals(s.exit) || "PAID_OFF".equals(s.exit) ? s.feesNet() : 0))
                throw new IllegalStateException(at + "title overpaid (" + s.titlePaid() + " of " + s.cost + ")");
            if (s.recvAgo >= 0) {
                if (s.billed < 0) throw new IllegalStateException(at + "receivable needs billed months");
                if (!s.startOverride && s.recvAgo > s.entry()) throw new IllegalStateException(at + "receivable starts before intake");
                if (s.storagePaid() > s.feesNet()) throw new IllegalStateException(at + "storage fees overpaid");
                if (s.reduced() > s.feesAccrued()) throw new IllegalStateException(at + "reduced below zero");
                if (s.exit == null) {
                    int expected;
                    if (s.activePause()) expected = (s.recvAgo - s.pauseAgo) / 30;
                    else expected = s.clockAgo() / 30;
                    if (s.billed != expected) throw new IllegalStateException(at + "running receivable must be billed " + expected + " months, has " + s.billed);
                    if (s.owedNow() <= 0) throw new IllegalStateException(at + "receivable with nothing owed");
                    if (s.deadlineIn != null && s.deadlineIn <= 0) throw new IllegalStateException(at + "an active pause must end in the future");
                    if (s.pauseAgo >= 0 && s.pauseAgo > s.recvAgo) throw new IllegalStateException(at + "pause before receivables");
                } else {
                    int atExit = (s.recvAgo - s.exitAgo) / 30;
                    if (s.billed != atExit) throw new IllegalStateException(at + "exit billed months should be " + atExit + " not " + s.billed);
                    if ("PAID_OFF".equals(s.exit) && paid != s.cost + s.feesNet())
                        throw new IllegalStateException(at + "paid-off must equal cost + fees (" + (s.cost + s.feesNet()) + ") but paid " + paid);
                    if (paid > s.storedCost()) throw new IllegalStateException(at + "overpaid after exit");
                }
            } else if (paid > s.cost) {
                throw new IllegalStateException(at + "overpaid");
            }
            if (s.problemAgo >= 0 && s.problemNote == null) throw new IllegalStateException(at + "problem note missing");
        }
        Set<String> personKeys = byKey.keySet();
        for (Call c : calls()) {
            if (c.person == null || !personKeys.contains(c.person)) throw new IllegalStateException("call for unknown person " + c.person);
            if (!staff.contains(c.by)) throw new IllegalStateException("call by unknown staff " + c.by);
        }
        for (Exp e : expenses()) {
            if (e.amount <= 0) throw new IllegalStateException("bad expense amount");
            if (!staff.contains(e.by)) throw new IllegalStateException("expense by unknown staff " + e.by);
        }
    }
}
