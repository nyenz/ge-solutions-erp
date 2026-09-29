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
 * GOLDEN SEED -- SCENARIO DATASET v3 (pure data, no Spring, no database).
 *
 * Every date is written as "days ago" so the dataset is always fresh no matter
 * when it is seeded. ScenarioSeeder turns this into rows. selfCheck() proves the
 * money adds up (no overpayment, receivable maths matches the nightly scheduler)
 * BEFORE anything touches the database.
 *
 * Situations covered (one or more projects each):
 *   entry modes ........ New Folder, New Title, Legacy Title
 *   folders ............ no stages, deposit only, every stage step, custom stages,
 *                        refused by land board, ready for titling, prepaid, stale
 *   titles ............. released, paid-not-released, partial, critical (<25%),
 *                        bulk-marked titled (details pending), stage override
 *   tenure ............. FREEHOLD, MAILO, LEASEHOLD, CUSTOMARY
 *   receivables ........ at intake, partial payments, paused, deadline soon,
 *                        deadline expired, custom rate, late-entry override,
 *                        joint silent, auto-flagged (365d), problem, commercial
 *   receivable exits ... paid off, fees waived, fees capitalized, set aside
 *   about to auto-flag . titled, no payment for 351 days
 *   flags .............. PROBLEM on folder / titled / receivable
 *   soft delete ........ deleted (recent), deleted (old), deleted then restored
 *   owners ............. solo, joint (2), joint (3), one person on 3 projects,
 *                        shared phone, very long name, missing email/address
 *   recovery states .... NEW, CONTACTED, MISSED, SITE, LOCKED (calls), LOCKED
 *                        (payment), unlock tomorrow, unlock soon, co-owner warning
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

    private static final String[][] PEOPLE = {
        {"kaggwa", "KAGGWA STEVEN", "", "Nansana, Wakiso", ""},
        {"nambooze", "NAMBOOZE SARAH", "sarah.nambooze@mail.ug", "Bweyogerere, Wakiso", ""},
        {"okello", "OKELLO RICHARD", "", "Pece, Gulu", ""},
        {"nakato", "NAKATO GRACE", "", "Kayabwe, Mpigi", ""},
        {"muwanga", "MUWANGA DAVID", "", "Kayabwe, Mpigi", "nakato"},
        {"birungi", "BIRUNGI LILIAN", "", "Rukungiri Municipality", ""},
        {"kyomuhendo", "KYOMUHENDO PATIENCE", "patience.k@mail.ug", "Hoima City", ""},
        {"atim", "ATIM CHRISTINE", "christine.atim@mail.ug", "Lira City West", ""},
        {"waiswa", "WAISWA GEOFFREY", "", "Walukuba, Jinja", ""},
        {"tusiime", "TUSIIME AGNES", "", "Kisoro Town", ""},
        {"matovu", "MATOVU HENRY", "", "Masaka City", ""},
        {"okwir", "OKWIR PATRICK", "", "Ayivu, Arua", ""},
        {"wandera", "WANDERA MOSES", "", "Mbale City", ""},
        {"okurut", "OKURUT SAMUEL", "", "Kumi Town", ""},
        {"twinomujuni", "TWINOMUJUNI DAVID", "david.twino@mail.ug", "Kasese Municipality", ""},
        {"mukasa", "MUKASA JOHN BOSCO", "", "Kawempe, Kampala", ""},
        {"kirabo", "KIRABO ALLAN", "", "Luweero Town", ""},
        {"naiga", "NAIGA RUTH", "", "Kira, Wakiso", ""},
        {"mbabazi", "MBABAZI CLARE", "", "Fort Portal", ""},
        {"nalweyiso", "NALWEYISO JOAN", "", "Kayunga Town", ""},
        {"lukwago", "LUKWAGO ERIAS", "", "Mityana Town", ""},
        {"ochen", "OCHEN SIMON", "", "Soroti City East", ""},
        {"adong", "ADONG BETTY", "", "Soroti City East", "ochen"},
        {"mugabi", "MUGABI FRED", "fred.mugabi@mail.ug", "Iganga Town", ""},
        {"namwanje", "NAMWANJE FLAVIA", "", "Mukono Town", ""},
        {"nakiryowa", "NAKIRYOWA SHARON", "sharon.n@mail.ug", "Entebbe Municipality", ""},
        {"nabirye", "NABIRYE SOPHIA", "", "Lugazi, Buikwe", ""},
        {"kizza", "KIZZA ANDREW", "", "Lugazi, Buikwe", ""},
        {"nansubuga", "NANSUBUGA IRENE", "", "Lugazi, Buikwe", ""},
        {"opio", "OPIO DENIS", "opio.denis@mail.ug", "Nebbi Town", ""},
        {"acen", "ACEN LOY", "", "Kitgum Town", ""},
        {"asiimwe", "ASIIMWE JOVIA", "", "Ntungamo Town", ""},
        {"byaruhanga", "BYARUHANGA JOSEPH", "", "Kyenjojo Town", ""},
        {"kobusinge", "KOBUSINGE ANNET", "", "Boma Road, Fort Portal", ""},
        {"lubega", "LUBEGA MOSES", "", "Masaka City", ""},
        {"namaganda", "NAMAGANDA EDITH", "", "Wakiso Town", ""},
        {"ssebunya", "SSEBUNYA ISMAIL", "", "Kibuli, Kampala", ""},
        {"nakawesi", "NAKAWESI FATUMA", "", "Kibuli, Kampala", "ssebunya"},
        {"nakabuye", "NAKABUYE HELLEN", "", "Kyengera, Wakiso", ""},
        {"baguma", "BAGUMA GODFREY", "", "Bushenyi-Ishaka", ""},
        {"tumwebaze", "TUMWEBAZE ROBERT", "", "Kakoba, Mbarara", ""},
        {"otieno", "OTIENO JAMES", "", "Tororo Municipality", ""},
        {"auma", "AUMA STELLA", "", "Busia Town", ""},
        {"muhumuza", "MUHUMUZA BRIAN", "brian.muhumuza@mail.ug", "Kabale Town", ""},
        {"ssegawa", "SSEGAWA CHARLES", "", "Bulenga, Wakiso", ""},
        {"mwebe", "MWEBE HASSAN", "", "Nakawa, Kampala", ""},
        {"nabatanzi", "NABATANZI ROSE", "", "Nakawa, Kampala", ""},
        {"nsubuga", "NSUBUGA ALEX", "", "Kajjansi, Wakiso", ""},
        {"kagimu", "KAGIMU PAUL", "", "Bukedea Town", ""},
        {"kayondo", "KAYONDO EMMANUEL", "kayondo.e@mail.ug", "Kololo, Kampala", ""},
        {"wamala", "WAMALA JOSEPH", "", "Kiboga Town", ""},
        {"kyosiimire", "KYOSIIMIRE DOREEN", "", "Rakai Town", ""},
        {"nabwire", "NABWIRE PROSSY", "", "Busia Town", ""},
        {"tumusiime", "TUMUSIIME JOSEPH", "", "Ishaka, Bushenyi", ""},
        {"namiiro", "NAMIIRO GLORIA", "", "Mukono Town", ""},
        {"sserwadda", "SSERWADDA HERBERT", "", "Kasangati, Wakiso", ""},
        {"katende", "KATENDE MICHAEL", "", "Mpigi Town", ""},
        {"nandutu", "NANDUTU SARAH", "", "Kayunga Town", ""},
        {"kasule", "KASULE ISAAC", "", "Mityana Town", ""},
        {"ssekandi", "SSEKANDI PETER", "peter.ssekandi@mail.ug", "Ntinda, Kampala", ""},
        {"namukasa", "NAMUKASA-NAKAWUKI BERNADETTE MARY-ANN", "", "Kajjansi, Wakiso", ""},
    };

    static List<Person> people() {
        List<Person> l = new ArrayList<>();
        for (String[] p : PEOPLE) l.add(new Person(p[0], p[1], p[2], p[3], p[4]));
        return l;
    }

    /** Seed NIN: 14 characters, CMS3 + 6 digits + 4 letters. Real NINs never have a letter in position 3. */
    static String nin(int idx) {
        String letters = "ABCDEFGHJKLMNPRSTUWXYZ";
        int n = 210000 + (idx * 7331) % 700000;
        return "CMS3" + String.format("%06d", n)
                + letters.charAt(idx % letters.length())
                + letters.charAt((idx * 5 + 3) % letters.length())
                + letters.charAt((idx * 7 + 1) % letters.length())
                + letters.charAt((idx * 11 + 2) % letters.length());
    }

    /** Uganda mobile in the app's standard stored form: +256 then 9 digits starting with 7 (PhoneUtil). */
    static String phone(int idx) {
        String[] prefix = {"01", "52", "72", "82", "57", "06", "75", "78"};
        return "+2567" + prefix[idx % prefix.length] + String.format("%06d", 234000 + idx * 173);
    }

    /**
     * What is stored in clients.phone_number for this person. Two special cases exercise the
     * phone rules: a person with two numbers (joined with " / ") and one living abroad (+44).
     */
    static String phoneFor(String key, int phoneIdx) {
        if ("atim".equals(key)) return phone(phoneIdx) + " / " + phone(phoneIdx + 40);
        if ("kyomuhendo".equals(key)) return "+447700900123";
        return phone(phoneIdx);
    }

    // -------------------------------------------------------------- project
    static final String FW = "Field Work";
    static final String DP = "Deed Plan";
    static final String LCI = "LC Inspection";
    static final String DLB = "District Land Board Approval";
    static final String TASD = "Tax Assessment and Stamp Duty";
    static final String REG = "Registration and Title Issuance";
    static final String[] STAGES = {FW, DP, LCI, DLB, TASD, REG};

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
        boolean receipt;
        Pay(int ago, long amount, String by, String note) {
            this.ago = ago;
            this.amount = amount;
            this.by = by;
            this.note = note;
        }
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
        final String category;  // null = uncategorised (uploaded before categories existed)
        final String fileName;  // null = generated from owner + category
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
        int done = 0;
        boolean noStages = false;
        // title
        String plot, titleId, block, tenure = "FREEHOLD";
        int issuedAgo = -1;
        boolean pendingTitle = false;
        int releasedAgo = -1;
        int overrideAgo = -1;   // manual stage override (STAGE_OVERRIDE audit + bell)
        int overrideTo = 0;     // target stage 1..5; 5 sets status COMPLETED
        // receivable
        int recvAgo = -1;
        long initFee = 0;
        long rate = 50000;
        int billed = -1;
        boolean paused = false;
        Integer deadlineIn = null;
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
        int deletedAgo = -1;
        int restoredAgo = -1;

        Spec(String key, String mode, String[] owners) {
            this.key = key;
            this.mode = mode;
            this.owners = owners;
        }

        // ---- fluent builders
        Spec loc(String d, String c, String s, String p, String v, String a) {
            district = d; county = c; subCounty = s; parish = p; village = v; area = a;
            return this;
        }
        Spec cost(long c) { cost = c; return this; }
        Spec times(int start, int entry) { startAgo = start; entryAgo = entry; return this; }
        Spec by(String staff) { intakeBy = staff; return this; }
        Spec deposit(long amt) { if (amt > 0) pays.add(new Pay(-1, amt, null, "Initial deposit at intake")); return this; }
        Spec pay(int ago, long amt, String by) { pays.add(new Pay(ago, amt, by, null)); return this; }
        Spec pay(int ago, long amt, String by, String note) { pays.add(new Pay(ago, amt, by, note)); return this; }
        Spec rcpt() { if (!pays.isEmpty()) pays.get(pays.size() - 1).receipt = true; return this; }
        Spec stages(int n) { done = n; return this; }
        Spec noStages() { noStages = true; return this; }
        Spec custom(String name, long c, boolean d) { custom.add(new Custom(name, c, d)); return this; }
        Spec title(String plot, String block, String titleId, int issuedAgo) {
            this.plot = plot; this.block = block; this.titleId = titleId; this.issuedAgo = issuedAgo;
            return this;
        }
        Spec tenure(String t) { tenure = t; return this; }
        Spec pendingTitle(int ago) { pendingTitle = true; issuedAgo = ago; return this; }
        Spec released(int ago) { releasedAgo = ago; return this; }
        Spec override(int to, int ago) { overrideTo = to; overrideAgo = ago; return this; }
        Spec recv(int startAgo, long initFee, int billed) { recvAgo = startAgo; this.initFee = initFee; this.billed = billed; return this; }
        Spec recvAtIntake(long initFee, int billed) { recvAtIntake = true; recvAgo = entry(); this.initFee = initFee; this.billed = billed; return this; }
        Spec rate(long r) { rate = r; customRate = true; return this; }
        Spec paused() { paused = true; return this; }
        Spec deadline(int inDays) { deadlineIn = inDays; paused = inDays >= 0; return this; }
        Spec auto365() { auto365 = true; return this; }
        Spec startOverride() { startOverride = true; return this; }
        Spec origDebt(long d) { origDebt = d; return this; }
        Spec exit(String kind, int ago) { exit = kind; exitAgo = ago; return this; }
        Spec problem(int ago, String note) { problemAgo = ago; problemNote = note; return this; }
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
        boolean stagesAttached() { return isFolder() && !noStages; }
        boolean hasTitle() { return !isFolder() || done >= 6 || pendingTitle; }
        boolean legacy() { return "LEGACY".equals(mode); }
        long paid() { long s = 0; for (Pay p : pays) s += p.amount; return s; }
        int payAgo(Pay p) { return p.ago < 0 ? entry() : p.ago; }
        long feesAccrued() { return recvAgo >= 0 ? initFee + Math.max(0, billed) * rate : 0; }
        boolean receivableNow() { return recvAgo >= 0 && exit == null; }
        long feesStored() {
            if (recvAgo < 0) return 0;
            if (exit == null) return feesAccrued();
            if ("WAIVE".equals(exit) || "CAPITALIZE".equals(exit)) return 0;
            return feesAccrued();
        }
        long owedNow() {
            if (receivableNow()) return Math.max(0, cost + feesStored() - paid());
            return Math.max(0, cost - paid());
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
            for (Pay p : pays) if (payAgo(p) >= recvAgo) s += p.amount;
            return s;
        }
        String status() {
            if (releasedAgo >= 0) return "RELEASED";
            if (receivableNow()) return "RECEIVABLE";
            if (overrideTo >= 5) return "COMPLETED";
            return "ACTIVE";
        }
        /** Mirrors the app: 1 at intake, 5 if entered as receivable, otherwise only a manual override moves it. */
        int stageIndex() {
            if (recvAtIntake) return 5;
            return overrideTo > 0 ? overrideTo : 1;
        }
    }

    private static Spec folder(String key, String... o) { return new Spec(key, "FOLDER", o); }
    private static Spec newTitle(String key, String... o) { return new Spec(key, "TITLE", o); }
    private static Spec legacy(String key, String... o) { return new Spec(key, "LEGACY", o); }

    static List<Spec> projects() {
        List<Spec> l = new ArrayList<>();
        final String M1 = MGR1, M2 = MGR2, AD = ADMIN, DR = DIRECTOR, S1 = SEC1, S2 = SEC2;

        // ============ A: NEW FOLDER MODE (no title yet) ============
        l.add(folder("f_walkin_today", "kaggwa").loc("WAKISO", "KYADONDO", "NANSANA MUNICIPALITY", "NANSANA EAST", "KYEBANDO", "0.25 acre")
            .cost(3600000).times(0, 0).noStages().intakeNote("Walk-in today. Will bring the copy of the deed plan next week."));
        l.add(folder("f_deposit_only", "nambooze").loc("WAKISO", "KYADONDO", "KIRA MUNICIPALITY", "BWEYOGERERE", "BUWATE", "50x100 ft")
            .cost(4200000).times(14, 12).deposit(1050000).stages(0).by(S2).intakeNote("Deposit received; field work to be scheduled."));
        l.add(folder("f_fw_done", "okello").loc("GULU", "ASWA", "LAYIBI DIVISION", "PECE", "LACOR", "1.5 acres")
            .cost(3800000).times(46, 44).deposit(1520000).pay(20, 760000, M1).rcpt().stages(1).override(2, 30));
        l.add(folder("f_joint_siblings", "nakato", "muwanga").loc("MPIGI", "MAWOKOTA", "MPIGI TOWN COUNCIL", "KAFUMU", "KAYABWE", "2 acres")
            .cost(4600000).times(80, 79).deposit(1150000).pay(50, 1150000, AD).stages(2)
            .intakeNote("Siblings; both must sign the deed plan.")
            .ownerNote(1, S1, "muwanga", "Called Muwanga. Nakato will sign the deed plan on Friday.")
            .docs(78, AF).doc(40, SP, "boundary-site-photo-kayabwe.jpg", "image/jpeg", M1));
        l.add(folder("f_lc_inspection", "birungi").loc("RUKUNGIRI", "RUBABO", "RUKUNGIRI MUNICIPALITY", "NYARUSHANJE", "KEBISONI", "3 acres")
            .cost(5200000).times(115, 113).deposit(2080000).pay(75, 1040000, M1).pay(31, 520000, M2).stages(3).override(3, 60)
            .note(18, M1, "LC1 chairman letter stamped. Waiting for the parish chief."));
        l.add(folder("f_board_refused", "kyomuhendo").loc("HOIMA", "BUGAHYA", "HOIMA CITY EAST DIVISION", "KIGOROBYA", "BUJUMBURA", "1 acre")
            .cost(4900000).times(190, 188).deposit(1960000).pay(140, 980000, AD).pay(95, 490000, M1).stages(3)
            .note(25, M1, "District Land Board refused: boundary mismatch on the deed plan. Surveyor to correct and resubmit."));
        l.add(folder("f_custom_stages", "atim").loc("LIRA", "ERUTE", "LIRA CITY WEST DIVISION", "ADYEL", "OGUR", "0.5 acre")
            .cost(5600000).times(95, 94).deposit(1680000).pay(60, 1120000, M2).stages(1)
            .custom("Neighbour Consent Letters", 150000, true).custom("Boundary Re-opening", 450000, false)
            .note(30, M2, "Neighbour disputes the eastern boundary. Two extra stages added.")
            .docs(30, CL, SP));
        l.add(folder("f_ready_paid", "waiswa").loc("JINJA", "BUDIOPE", "JINJA CITY SOUTH DIVISION", "WALUKUBA", "MPUMUDDE", "0.4 acre")
            .cost(4300000).times(230, 229).deposit(1290000).pay(190, 1290000, AD).pay(120, 860000, M1).pay(45, 860000, M1).stages(5).override(4, 50)
            .note(9, M1, "Returned from the Land Board with approval. Waiting for registration.").docs(220, AF, DPL).docs(15, FL));
        l.add(folder("f_ready_partial", "tusiime").loc("KISORO", "BUFUMBIRA", "KISORO MUNICIPALITY", "NYAKABANDE", "RUGABANO", "1 acre")
            .cost(3900000).times(210, 208).deposit(1170000).pay(160, 780000, M2).pay(100, 780000, M2).stages(5)
            .note(9, M1, "Same Land Board batch as the Jinja file.").docs(200, AF, DPL));
        l.add(folder("f_ready_80", "matovu").loc("MASAKA", "BUDDU", "MASAKA CITY", "KIMAANYA", "KYESIGA", "2 acres")
            .cost(6100000).times(260, 258).deposit(1830000).pay(200, 1220000, AD).pay(140, 1220000, AD).pay(64, 610000, M1).stages(5)
            .note(9, M1, "Same Land Board batch. Client to clear the balance before titling.").docs(250, AF, DPL));
        l.add(folder("f_prepaid", "okwir").loc("ARUA", "AYIVU", "ARUA CITY", "RIVER OLI", "ANYAFIO", "0.25 acre")
            .cost(2800000).times(30, 29).deposit(2800000).stages(1).rcpt().intakeNote("Paid in full at intake."));
        l.add(folder("f_stale", "wandera").loc("MBALE", "BUNGOKHO", "MBALE CITY", "NAMAKWEKWE", "WANALE", "1.2 acres")
            .cost(4400000).times(310, 309).deposit(880000).pay(295, 440000, M1).stages(1)
            .note(200, M1, "Client travelling; promised to return in the dry season."));
        l.add(folder("f_never_paid", "okurut").loc("KUMI", "KUMI", "KUMI TOWN COUNCIL", "NGORA", "OGINO", null)
            .cost(3300000).times(60, 58).stages(2).intakeNote("No deposit taken. Client says the family is pooling money."));

        // ============ B: FOLDER PATH -> TITLED ============
        l.add(folder("t_released", "twinomujuni").loc("KASESE", "BUKONZO", "KASESE MUNICIPALITY", "RWENZORI", "KILEMBE", "0.5 acre")
            .cost(5000000).times(300, 299).deposit(1500000).pay(250, 1000000, AD).pay(200, 1000000, M1).pay(150, 1500000, M1).rcpt().stages(6)
            .title("3021", "KASESE BLOCK 17", "LRV 4102 FOLIO 3", 30).released(20)
            .docs(298, AF).docs(290, OL).docs(280, FL).docs(270, DPL).docs(30, CT)
            .doc(260, SP, "site-photo-north-boundary.jpg", "image/jpeg", M1)
            .doc(250, null, "nin-scan-twinomujuni.jpg", "image/jpeg", S1));
        l.add(folder("t_paid_unreleased", "mukasa").loc("KAMPALA", "KYADONDO", "KAWEMPE DIVISION", "MAKERERE III", "KIKONI", "0.1 acre")
            .cost(4800000).times(220, 219).deposit(1440000).pay(170, 1440000, AD).pay(90, 960000, M2).pay(14, 960000, M2).rcpt().stages(6)
            .title("1187", "KYADONDO BLOCK 190", "LRV 4188 FOLIO 21", 12).docs(12, CT));
        l.add(folder("t_partial_60", "kirabo").loc("LUWEERO", "KATIKAMU", "LUWEERO TOWN COUNCIL", "BAMUNANIKA", "WOBULENZI", "1 acre")
            .cost(5400000).times(250, 249).deposit(1620000).pay(170, 810000, M1).pay(60, 810000, AD).stages(6)
            .title("4406", "KATIKAMU BLOCK 62", "LRV 4090 FOLIO 24", 40));
        l.add(folder("t_critical_15", "naiga").loc("WAKISO", "KYADONDO", "KIRA MUNICIPALITY", "KIRA", "KIMWANYI", "0.75 acre")
            .cost(6000000).times(200, 198).deposit(900000).stages(6)
            .title("2290", "KYADONDO BLOCK 205", "LRV 4210 FOLIO 30", 60));
        l.add(folder("t_pending_details_a", "mbabazi").loc("KABAROLE", "BURAHYA", "FORT PORTAL CITY EAST DIVISION", "KARAMBI", "KISIMBA", "1 acre")
            .cost(4500000).times(240, 238).deposit(1350000).pay(150, 1800000, M1).stages(6).pendingTitle(3)
            .note(3, M1, "Marked as title produced in the Ready for Titling batch. Title details still to be entered."));
        l.add(folder("t_pending_details_b", "nalweyiso").loc("KAYUNGA", "BBAALE", "KAYUNGA TOWN COUNCIL", "KAYUNGA", "NAZIGO", "1 acre")
            .cost(3700000).times(205, 203).deposit(1110000).pay(101, 740000, M2).stages(6).pendingTitle(3));
        l.add(folder("t_stage_override", "lukwago").loc("MITYANA", "BUSUJJU", "MITYANA TOWN COUNCIL", "KAKINDU", "BUSIMBI", "1.5 acres")
            .cost(3300000).times(140, 139).deposit(990000).pay(80, 990000, M2).stages(4).override(5, 25)
            .note(25, M2, "Stage moved manually to 5: the Land Board decision was verbal."));

        // ============ C: NEW TITLE MODE ============
        l.add(newTitle("n_paid_released", "ochen", "adong").loc("SOROTI", "SOROTI", "SOROTI CITY EAST DIVISION", "GWERI", "ARAPAI", "1 acre")
            .cost(3200000).times(60, 58).deposit(3200000).title("7715", "SOROTI BLOCK 21", "LRV 3915 FOLIO 2", 70).released(8)
            .intakeNote("Spouses; title in joint names.").docs(58, CT, AF));
        l.add(newTitle("n_partial_45", "mugabi").loc("IGANGA", "BUKOOLI", "IGANGA MUNICIPALITY", "NAKAVULE", "BUGONO", "0.5 acre")
            .cost(4100000).times(100, 98).deposit(1230000).pay(35, 615000, M2)
            .title("5532", "BUGWERI BLOCK 40", "LRV 3960 FOLIO 27", 120));
        l.add(newTitle("n_no_payment", "namwanje").loc("MUKONO", "NAKIFUMA", "MUKONO MUNICIPALITY", "CENTRAL", "NAMUMIRA", "0.2 acre")
            .cost(2900000).times(25, 24).title("6108", "MUKONO BLOCK 33", "LRV 4233 FOLIO 12", 40).intakeNote("Title in hand; no deposit yet."));
        l.add(newTitle("n_paid_unreleased", "nakiryowa").loc("WAKISO", "BUSIRO", "ENTEBBE MUNICIPALITY", "KIGUNGU", "KATABI", "0.3 acre")
            .cost(6800000).times(75, 73).deposit(2040000).pay(50, 2380000, AD).pay(6, 2380000, DR).rcpt()
            .title("2841", "BUSIRO BLOCK 402", "LRV 4050 FOLIO 6", 90));
        l.add(newTitle("n_mailo_three_owners", "nabirye", "kizza", "nansubuga").tenure("MAILO")
            .loc("BUIKWE", "NAKISUNGA", "LUGAZI TOWN COUNCIL", "NAJJEMBE", "KASENYI", "4 acres")
            .cost(9000000).times(150, 148).deposit(2700000).pay(90, 2250000, M1).pay(28, 1350000, M2)
            .title("555", "KYADONDO BLOCK 190", "LRV 1584 FOLIO 22", 200)
            .ownerNote(5, S2, "nabirye", "Spoke to Nabirye. She will consult the other two owners."));
        l.add(newTitle("n_leasehold_commercial", "opio").tenure("LEASEHOLD")
            .loc("NEBBI", "PADYERE", "NEBBI TOWN COUNCIL", "PAIDHA", "PANYIMUR", "12 acres")
            .cost(24000000).times(210, 208).deposit(7200000).pay(150, 4800000, AD).pay(100, 4800000, AD).pay(40, 2400000, DR)
            .title("102", "NEBBI BLOCK 8", "LRV 3902 FOLIO 9", 300).docs(207, AF, OL));
        l.add(newTitle("n_customary_small", "acen").tenure("CUSTOMARY")
            .loc("KITGUM", "CHUA", "KITGUM MUNICIPALITY", "PANDWONG", "LAMOLA", "0.5 acre")
            .cost(1200000).times(45, 44).deposit(1200000).title("88", "CHUA BLOCK 3", "LRV 3122 FOLIO 13", 50));
        l.add(newTitle("n_stale_351_days", "asiimwe").loc("NTUNGAMO", "RUSHENYI", "NTUNGAMO MUNICIPALITY", "RUHAAMA", "KAKYERERE", "1 acre")
            .cost(5200000).times(353, 351).deposit(1300000).title("3390", "RUSHENYI BLOCK 14", "LRV 4021 FOLIO 11", 400)
            .note(120, M1, "Called several times. Client has gone quiet. Will auto-flag as receivable at 365 days."));

        // ============ D: LEGACY TITLE MODE ============
        l.add(legacy("l_paid_released", "byaruhanga").loc("KYENJOJO", "MUGUSU", "KYENJOJO TOWN COUNCIL", "NYANKWANZI", "KIHURA", "2 acres")
            .cost(3500000).times(13000, 210).deposit(3500000).title("355", "MUGUSU BLOCK 61", "LRV 1120 FOLIO 7", 13000).released(190)
            .doc(205, CT, "copy-of-title-byaruhanga.pdf", "application/pdf", S1));
        l.add(legacy("l_owing_active", "kobusinge").loc("KABAROLE", "BURAHYA", "FORT PORTAL CITY EAST DIVISION", "KARAMBI", "KISIMBA", "1 acre")
            .cost(4000000).times(11000, 130).deposit(800000).pay(70, 800000, M1)
            .title("412", "BURAHYA BLOCK 8", "LRV 1584 FOLIO 22", 11000));
        l.add(legacy("l_legacy_receivable", "lubega").loc("MASAKA", "BUDDU", "MASAKA CITY", "KIMAANYA", "KYESIGA", "0.5 acre")
            .cost(3500000).times(14000, 520).deposit(1750000).recv(430, 50000, 14).origDebt(1750000)
            .title("356", "BUDDU BLOCK 61", "LRV 1121 FOLIO 8", 14000)
            .note(400, M1, "Legacy file. Client silent for over a year. Moved to receivables manually."));
        l.add(legacy("l_recent_payment", "namaganda").loc("WAKISO", "BUSIRO", "WAKISO TOWN COUNCIL", "KASANGATI", "GAYAZA", "0.3 acre")
            .cost(3000000).times(9000, 60).deposit(1000000).pay(9, 500000, M2).rcpt()
            .title("620", "BUSIRO BLOCK 77", "LRV 2210 FOLIO 5", 9000));
        l.add(legacy("l_mailo_joint", "ssebunya", "nakawesi").tenure("MAILO")
            .loc("KAMPALA", "KYADONDO", "MAKINDYE DIVISION", "KIBULI", "KIBULI", "0.4 acre")
            .cost(7500000).times(15000, 300).deposit(2250000).pay(200, 1500000, AD).pay(120, 1500000, AD)
            .title("1204", "KYADONDO BLOCK 118", "LRV 1900 FOLIO 14", 15000).intakeNote("Husband and wife; shared phone."));

        // ============ E: RECEIVABLES (money still owed, storage fees running) ============
        l.add(folder("r_at_intake_folder", "nakabuye").loc("WAKISO", "KYADONDO", "KYENGERA TOWN COUNCIL", "BUNAMWAYA", "KYENGERA", "50x100 ft")
            .cost(4500000).times(100, 95).deposit(900000).stages(2).recvAtIntake(50000, 3).origDebt(3600000)
            .intakeNote("Entered as receivable from day one; client relocating."));
        l.add(newTitle("r_partial_payments", "baguma").loc("BUSHENYI", "IGARA", "BUSHENYI-ISHAKA MUNICIPALITY", "NYAKABIRIZI", "KATUNGURU", "1 acre")
            .cost(6000000).times(330, 328).deposit(1800000).pay(310, 600000, M1)
            .recv(300, 0, 10).pay(210, 300000, M1).pay(120, 300000, M2).pay(45, 300000, AD).rcpt()
            .title("2417", "IGARA BLOCK 96", "LRV 3310 FOLIO 14", 340));
        l.add(newTitle("r_storage_paused", "tumwebaze").loc("MBARARA", "KASHARI", "MBARARA CITY NORTH DIVISION", "KAKOBA", "NYAMITANGA", "1 acre")
            .cost(4200000).times(280, 278).deposit(840000).recv(260, 0, 6).paused()
            .title("781", "KASHARI BLOCK 96", "LRV 4102 FOLIO 3", 285)
            .note(80, DR, "Storage billing paused: bereavement in the family."));
        l.add(newTitle("r_deadline_in_3_days", "otieno").loc("TORORO", "TORORO", "TORORO MUNICIPALITY", "MOLO", "KADAMA", "0.8 acre")
            .cost(3800000).times(250, 248).deposit(760000).recv(240, 0, 8).deadline(3)
            .title("2210", "TORORO BLOCK 45", "LRV 3941 FOLIO 18", 255)
            .note(4, DR, "Negotiation window closes in 3 days. Client promised a lump sum."));
        l.add(newTitle("r_deadline_expired", "auma").loc("BUSIA", "SAMIA-BUGWE", "BUSIA MUNICIPALITY", "MASABA", "MAYENZE", "1 acre")
            .cost(3500000).times(220, 218).deposit(700000).recv(200, 0, 4).deadline(-2)
            .title("1533", "BUSIA BLOCK 33", "LRV 3890 FOLIO 5", 225)
            .note(2, DR, "Negotiation deadline passed with no payment. Fees resume at the next nightly run."));
        l.add(newTitle("r_custom_rate", "muhumuza").loc("KABALE", "NDORWA", "KABALE MUNICIPALITY", "KITUMBA", "KAMUGANGUZI", "0.6 acre")
            .cost(5000000).times(302, 300).deposit(1000000).recv(280, 75000, 9).rate(75000)
            .title("903", "NDORWA BLOCK 22", "LRV 3902 FOLIO 9", 305).note(279, DR, "Storage fee agreed at UGX 75,000 a month."));
        l.add(newTitle("r_late_entry_override", "ssegawa").loc("WAKISO", "BUSIRO", "KASANGATI TOWN COUNCIL", "BULENGA", "KIKAJJO", "0.5 acre")
            .cost(4000000).times(200, 20).deposit(800000).recv(150, 0, 5).startOverride().origDebt(3200000)
            .title("3777", "BUSIRO BLOCK 12", "LRV 4333 FOLIO 9", 210).note(19, ADMIN, "Keyed in late. Receivable start date set to the real date."));
        l.add(newTitle("r_joint_silent", "mwebe", "nabatanzi").loc("KAMPALA", "KYADONDO", "NAKAWA DIVISION", "BUGOLOBI", "BUGOLOBI", "0.2 acre")
            .cost(4400000).times(352, 350).deposit(880000).recv(330, 0, 11)
            .title("2500", "KYADONDO BLOCK 205", "LRV 4001 FOLIO 2", 360).intakeNote("Two owners; neither answers calls."));
        l.add(newTitle("r_auto_flagged_365", "nsubuga").loc("WAKISO", "KYADONDO", "KAJJANSI TOWN COUNCIL", "KAJJANSI", "LUBBE", "0.5 acre")
            .cost(5600000).times(422, 420).deposit(1120000).recv(55, 0, 1).auto365().origDebt(4480000)
            .title("1930", "KYADONDO BLOCK 244", "LRV 3800 FOLIO 1", 430));
        l.add(newTitle("r_problem", "kagimu").loc("BUKEDEA", "KABERAMAIDO", "BUKEDEA TOWN COUNCIL", "KACHUMBALA", "MALERA", "1 acre")
            .cost(4800000).times(260, 258).deposit(960000).recv(220, 0, 7)
            .title("2066", "BUKEDEA BLOCK 9", "LRV 3811 FOLIO 4", 265)
            .problem(60, "Boundary dispute with the neighbour. Case pending at the LC court."));
        l.add(newTitle("r_commercial_big", "kayondo").loc("KAMPALA", "KYADONDO", "KAWEMPE DIVISION", "MAKERERE I", "KAGUGUBE", "2 acres")
            .cost(18000000).times(262, 260).deposit(5400000).recv(240, 150000, 8).rate(150000).origDebt(12600000)
            .pay(100, 2000000, DR).pay(45, 500000, DR, "[STORAGE FEE PAYMENT] Part payment of accrued fees.").rcpt()
            .title("4001", "KYADONDO BLOCK 12", "LRV 4600 FOLIO 33", 270).docs(258, AF, OL).docs(90, CL));

        // ============ F: RECEIVABLE EXITS ============
        l.add(newTitle("x_paid_off", "wamala").loc("KIBOGA", "KIBOGA", "KIBOGA TOWN COUNCIL", "KIBOGA", "NKANDWA", "1 acre")
            .cost(3600000).times(700, 698).deposit(720000).recv(330, 0, 10)
            .pay(200, 1000000, M1).pay(120, 1000000, M1).pay(60, 1000000, M1).pay(12, 380000, DR).rcpt()
            .exit("PAID_OFF", 12).title("2755", "KIBOGA BLOCK 4", "LRV 3400 FOLIO 6", 705).released(5).docs(5, CT));
        l.add(newTitle("x_fees_waived", "kyosiimire").loc("RAKAI", "KOOKI", "RAKAI TOWN COUNCIL", "KALISIZO", "KYOTERA", "1 acre")
            .cost(3900000).times(400, 398).deposit(780000).pay(380, 390000, M1)
            .recv(250, 0, 7).exit("WAIVE", 40).pay(30, 500000, M2)
            .title("3001", "KOOKI BLOCK 27", "LRV 4066 FOLIO 13", 405));
        l.add(newTitle("x_fees_capitalized", "nabwire").loc("BUSIA", "SAMIA-BUGWE", "BUSIA MUNICIPALITY", "MASABA", "MAYENZE", "0.7 acre")
            .cost(4300000).times(380, 378).deposit(1200000)
            .recv(210, 0, 6).exit("CAPITALIZE", 30).pay(15, 600000, M1)
            .title("3002", "BUSIA BLOCK 34", "LRV 4067 FOLIO 14", 385));
        l.add(newTitle("x_set_aside", "tumusiime").loc("BUSHENYI", "IGARA", "BUSHENYI-ISHAKA MUNICIPALITY", "NYAKABIRIZI", "KATUNGURU", "1 acre")
            .cost(4600000).times(200, 198).deposit(920000)
            .recv(190, 0, 5).exit("SET_ASIDE", 35)
            .title("3003", "IGARA BLOCK 97", "LRV 4068 FOLIO 15", 205));

        // ============ G: SPECIAL SITUATIONS ============
        l.add(folder("p_problem_folder", "namiiro").loc("MUKONO", "NAKIFUMA", "NAKIFUMA TOWN COUNCIL", "NAKIFUMA", "NAMANVE", "1 acre")
            .cost(3900000).times(90, 88).deposit(1170000).pay(40, 780000, M1).stages(2)
            .problem(14, "Owner name on the deed plan does not match the National ID.")
            .doc(14, null, "problem-proof-id-mismatch.jpg", "image/jpeg", M1));
        l.add(newTitle("p_problem_titled", "sserwadda").loc("WAKISO", "BUSIRO", "KASANGATI TOWN COUNCIL", "KASANGATI", "MATUGGA", "0.5 acre")
            .cost(5700000).times(130, 128).deposit(1710000).pay(70, 1140000, AD)
            .title("3004", "BUSIRO BLOCK 90", "LRV 4069 FOLIO 16", 135)
            .problem(8, "Title deed shows a different plot size from the survey."));
        l.add(newTitle("d_deleted_recent", "katende").loc("MPIGI", "MAWOKOTA", "MPIGI TOWN COUNCIL", "KAFUMU", "KAYABWE", "1 acre")
            .cost(4000000).times(150, 148).deposit(1200000).pay(90, 800000, M1)
            .title("3005", "MAWOKOTA BLOCK 5", "LRV 4070 FOLIO 17", 155).deleted(12).docs(140, DPL));
        l.add(folder("d_deleted_old", "nandutu").loc("KAYUNGA", "BBAALE", "KAYUNGA TOWN COUNCIL", "KAYUNGA", "NAZIGO", "0.3 acre")
            .cost(3000000).times(100, 99).stages(0).deleted(50));
        l.add(folder("d_deleted_restored", "kasule").loc("MITYANA", "BUSUJJU", "MITYANA TOWN COUNCIL", "KAKINDU", "BUSIMBI", "1 acre")
            .cost(3500000).times(120, 118).deposit(700000).pay(70, 700000, M2).stages(1).restored(40, 33));
        l.add(folder("o_same_owner_folder", "ssekandi").loc("KAMPALA", "KYADONDO", "NAKAWA DIVISION", "NTINDA", "NAKAWA", "0.1 acre")
            .cost(3400000).times(35, 34).deposit(1020000).pay(10, 680000, M1).rcpt().stages(1));
        l.add(newTitle("o_same_owner_title", "ssekandi").loc("WAKISO", "KYADONDO", "KIRA MUNICIPALITY", "KIRA", "KIRA", "0.4 acre")
            .cost(4900000).times(180, 178).deposit(1470000).pay(100, 980000, M2)
            .title("3006", "KYADONDO BLOCK 260", "LRV 4071 FOLIO 18", 185));
        l.add(newTitle("o_same_owner_receivable", "ssekandi").loc("MUKONO", "NAKIFUMA", "MUKONO MUNICIPALITY", "CENTRAL", "NAMUMIRA", "0.3 acre")
            .cost(3000000).times(222, 220).deposit(600000).recv(120, 0, 4)
            .title("3007", "MUKONO BLOCK 31", "LRV 4072 FOLIO 19", 225));
        l.add(folder("o_very_long_name", "namukasa").loc("WAKISO", "KYADONDO", "KAJJANSI TOWN COUNCIL", "KAJJANSI", "BUYALA", "0.25 acre")
            .cost(3200000).times(20, 19).deposit(800000).stages(1));

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

    static List<Call> calls() {
        List<Call> c = new ArrayList<>();
        final String M1 = MGR1, M2 = MGR2, S1 = SEC1, S2 = SEC2, DR = DIRECTOR, SU = SUSPENDED;
        // CONTACTED (last call good)
        c.add(new Call("okello", NOP, 24, S1, null));
        c.add(new Call("okello", ANS, 3, S1, "Will bring the balance next week."));
        c.add(new Call("birungi", ANS, 40, SU, "Asked to reschedule the site meeting."));
        c.add(new Call("tusiime", ANS, 16, S1, "Batch is back; will collect the balance."));
        c.add(new Call("muwanga", ANS, 1, S1, "Nakato will sign the deed plan on Friday."));
        c.add(new Call("nabirye", ANS, 2, S2, "Will consult the other two owners."));
        c.add(new Call("tumwebaze", ANS, 82, DR, "Family bereavement. Asked to pause storage fees."));
        // MISSED (last call bad, fewer than two in 30 days)
        c.add(new Call("nambooze", ANS, 52, SU, "Asked for the stage timeline."));
        c.add(new Call("nambooze", NOP, 6, S2, null));
        c.add(new Call("kyomuhendo", ANS, 62, M1, null));
        c.add(new Call("kyomuhendo", ANS, 47, M1, "Will visit the office."));
        c.add(new Call("kyomuhendo", NTH, 12, S2, null));
        c.add(new Call("okurut", WRN, 15, S1, "Number belongs to someone else."));
        c.add(new Call("auma", NOP, 2, S2, null));
        c.add(new Call("naiga", NOP, 35, S1, null));
        c.add(new Call("naiga", NOP, 33, S1, null));
        c.add(new Call("lubega", NOP, 95, S1, null));
        c.add(new Call("lubega", NTH, 70, S1, "Phone off since the last call."));
        // SITE VISIT (two misses, no good call in 30 days)
        c.add(new Call("mwebe", NOP, 18, S1, null));
        c.add(new Call("mwebe", NTH, 9, S2, null));
        c.add(new Call("nabatanzi", WRN, 25, S1, "Phone off since March."));
        c.add(new Call("nabatanzi", NOP, 4, M1, null));
        c.add(new Call("wandera", NTH, 8, M1, null));
        c.add(new Call("wandera", NOP, 3, M1, null));
        // LOCKED by two good calls
        c.add(new Call("kobusinge", ANS, 20, M1, "Will pay after the coffee harvest."));
        c.add(new Call("kobusinge", ANS, 5, M2, "Confirmed the payment date."));
        c.add(new Call("baguma", ANS, 28, S1, "Asked for a statement of fees."));
        c.add(new Call("baguma", ANS, 10, S1, "Will pay 300,000 on the 5th."));
        c.add(new Call("kayondo", ANS, 21, M2, "Needs board approval to pay."));
        c.add(new Call("kayondo", ANS, 7, M2, "Board approved a part payment."));
        // callable again (lock ended two days ago)
        c.add(new Call("nakabuye", ANS, 45, S1, "Relocating; will call back."));
        c.add(new Call("nakabuye", ANS, 32, S1, "Settling in; asked for a payment plan."));
        return c;
    }

    /** People whose reliability meter is set by hand (everyone else is computed from their calls). */
    static Map<String, Double> reliabilityOverrides() {
        Map<String, Double> m = new HashMap<>();
        m.put("lubega", 35.0);
        m.put("mwebe", 45.0);
        m.put("nabatanzi", 40.0);
        m.put("naiga", 60.0);
        m.put("wandera", 55.0);
        m.put("kobusinge", 92.0);
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
        Random r = new Random(20260929L);
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
        // rare and large
        l.add(new Exp(75 * DAY, "Vehicle Repairs", 1400000, "Replaced clutch on the field van", MGR1, "Driver - Okello Moses", 0, null));
        l.add(new Exp(190 * DAY, "Vehicle Repairs", 2900000, "Gearbox overhaul", DIRECTOR, "Driver - Okello Moses", 0, null));
        l.add(new Exp(310 * DAY, "Vehicle Repairs", 850000, "Four new tyres", MGR1, null, 0, null));
        l.add(new Exp(120 * DAY, "Stationery", 240000, "Printer toner and survey paper", SEC1, null, 0, null));
        l.add(new Exp(45 * DAY, "Internet & Utilities", 320000, "Fibre internet, electricity and water", ADMIN, null, 0, null));
        // last 24 hours: still editable
        l.add(new Exp(95, "Fuel", 120000, "Fuel for the Nansana site visit", SEC1, "Driver - Okello Moses", 0, null));
        l.add(new Exp(310, "Airtime & Data", 50000, null, SEC2, null, 0, null));
        l.add(new Exp(700, "Land Office", 450000, "Deed plan checking fee, Wakiso", MGR1, null, 0, null));
        // corrected within the edit window
        l.add(new Exp(900, "Fieldwork", 380000, "Boundary re-opening allowance (corrected from 830,000)", MGR2, "Field Team - Kasozi", 600, MGR1));
        // just outside the 24-hour edit window
        l.add(new Exp(1800, "Office", 90000, "Stationery and printing", SEC1, null, 0, null));
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
            for (String o : s.owners) if (!byKey.containsKey(o)) throw new IllegalStateException(at + "unknown owner " + o);
            if (s.cost <= 0) throw new IllegalStateException(at + "cost missing");
            if (s.entry() > s.startAgo && !s.legacy() && s.startAgo != 0) throw new IllegalStateException(at + "entry date earlier than start date");
            if (!staff.contains(s.intakeBy)) throw new IllegalStateException(at + "unknown intake staff");
            for (Pay p : s.pays) {
                if (p.amount <= 0) throw new IllegalStateException(at + "bad payment amount");
                if (p.by != null && !staff.contains(p.by)) throw new IllegalStateException(at + "unknown payer staff " + p.by);
                if (s.payAgo(p) > s.entry()) throw new IllegalStateException(at + "payment older than intake");
            }
            for (Note n : s.notes) {
                if (n.by != null && !staff.contains(n.by)) throw new IllegalStateException(at + "unknown note author " + n.by);
                if (n.ownerKey != null) {
                    boolean found = false;
                    for (String o : s.owners) if (o.equals(n.ownerKey)) found = true;
                    if (!found) throw new IllegalStateException(at + "owner note for a non-owner " + n.ownerKey);
                }
            }
            if (s.hasTitle() && !s.pendingTitle) {
                if (s.plot == null || s.block == null || s.titleId == null) throw new IllegalStateException(at + "title details missing");
                if (!plots.add(s.plot)) throw new IllegalStateException(at + "duplicate plot " + s.plot);
            }
            if (s.isFolder() && s.done >= 6 && !s.hasTitle()) throw new IllegalStateException(at + "all stages done but no title");
            if (s.pendingTitle && s.done < 6) throw new IllegalStateException(at + "pending title needs all stages done");
            if (s.releasedAgo >= 0) {
                if (!s.hasTitle() || s.pendingTitle) throw new IllegalStateException(at + "released without title details");
                if (s.paid() < s.cost && !"PAID_OFF".equals(s.exit)) throw new IllegalStateException(at + "released while not fully paid");
            }
            // money
            long paid = s.paid();
            if (s.recvAgo >= 0) {
                if (s.billed < 0) throw new IllegalStateException(at + "receivable needs billed months");
                if (!s.startOverride && s.recvAgo > s.entry()) throw new IllegalStateException(at + "receivable starts before intake");
                if (s.exit == null || "SET_ASIDE".equals(s.exit)) {
                    int maxBilled = s.recvAgo / 30;
                    if (s.billed > maxBilled) throw new IllegalStateException(at + "billed more months than have passed");
                    if (s.exit == null && !s.paused && s.deadlineIn == null && s.billed != maxBilled)
                        throw new IllegalStateException(at + "running receivable must be billed to " + maxBilled + " months, has " + s.billed);
                    if (s.exit == null && s.paused && s.billed > maxBilled)
                        throw new IllegalStateException(at + "paused receivable billed too far");
                }
                if (s.exit != null) {
                    int atExit = (s.recvAgo - s.exitAgo) / 30;
                    if (s.billed != atExit) throw new IllegalStateException(at + "exit billed months should be " + atExit + " not " + s.billed);
                }
                if (s.exit == null) {
                    if (paid > s.cost + s.feesStored()) throw new IllegalStateException(at + "overpaid");
                    if (s.owedNow() <= 0) throw new IllegalStateException(at + "receivable with nothing owed");
                } else if ("PAID_OFF".equals(s.exit)) {
                    if (paid != s.cost + s.feesAccrued()) throw new IllegalStateException(at + "paid-off must equal cost + fees (" + (s.cost + s.feesAccrued()) + ") but paid " + paid);
                } else if (paid > s.cost) throw new IllegalStateException(at + "overpaid after exit");
            } else if (paid > s.cost) {
                throw new IllegalStateException(at + "overpaid");
            }
            if (s.deadlineIn != null && s.deadlineIn >= 0 && !s.paused) throw new IllegalStateException(at + "future deadline needs paused");
            if (s.deadlineIn != null && s.deadlineIn < 0 && s.paused) throw new IllegalStateException(at + "expired deadline must not be paused (scheduler skips paused plots)");
            if (s.problemAgo >= 0 && s.problemNote == null) throw new IllegalStateException(at + "problem note missing");
        }
        Set<String> personKeys = byKey.keySet();
        for (Call c : calls()) {
            if (!personKeys.contains(c.person)) throw new IllegalStateException("call for unknown person " + c.person);
            if (!staff.contains(c.by)) throw new IllegalStateException("call by unknown staff " + c.by);
        }
        for (Exp e : expenses()) {
            if (e.amount <= 0) throw new IllegalStateException("bad expense amount");
            if (!staff.contains(e.by)) throw new IllegalStateException("expense by unknown staff " + e.by);
        }
    }
}
