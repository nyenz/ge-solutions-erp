// PATH: erp-frontend/src/utils/roles.js
// fix181: THE rank list of the page (same order as Role.java on the server -- keep the two in step).
//  5 ADMIN     the system designer, exactly one account
//  4 DIRECTOR  the business owner
//  3 MANAGER
//  2 SECRETARY
//  1 EMPLOYEE  field data entry only (Pending projects), never sees money
// Every page reads who may do what from roleFlags(user); no page compares role strings itself.

export const RANKS = {
    ROLE_ADMIN:     { rank: 5, label: 'Admin',     chip: 'ADMIN',     hint: 'The system designer. Only one Admin exists.' },
    ROLE_DIRECTOR:  { rank: 4, label: 'Director',  chip: 'DIRECTOR',  hint: 'The owner: all money, staff below Director, archive.' },
    ROLE_MANAGER:   { rank: 3, label: 'Manager',   chip: 'MANAGER',   hint: 'Runs the work: statuses, payments, edits. No company money totals.' },
    ROLE_SECRETARY: { rank: 2, label: 'Secretary', chip: 'SECRETARY', hint: 'Office entry and recovery calls; sets prices on Pending projects.' },
    ROLE_EMPLOYEE:  { rank: 1, label: 'Employee',  chip: 'EMPLOYEE',  hint: 'Field entry only: new projects go in as Pending. Sees no money.' },
};

/** Ranks shown highest first. */
export const RANK_ORDER = Object.keys(RANKS).sort((a, b) => RANKS[b].rank - RANKS[a].rank);

export const rankOf = (role) => (RANKS[role] ? RANKS[role].rank : 0);
export const rankLabel = (role) => (RANKS[role] ? RANKS[role].label : 'Staff');

/** Ranks the given person may create or move people to (strictly below their own; never Admin). */
export const manageableRanks = (user) => {
    const f = roleFlags(user);
    if (!f.isOwnerLevel) return [];
    return RANK_ORDER.filter(r => r !== 'ROLE_ADMIN' && rankOf(r) < f.rank);
};

export function roleFlags(user) {
    const role = String(user?.role || '').toUpperCase();
    // the Admin account is the one with isRoot; an old non-root ROLE_ADMIN row still counts as Admin rank
    const rank = user?.isRoot ? 5 : rankOf(role);
    const isAdmin = rank >= 5;
    const isOwnerLevel = rank >= 4;           // Director and Admin
    const isManager = rank >= 3;              // Manager and above
    const isSecretary = role === 'ROLE_SECRETARY';
    const isEmployee = role === 'ROLE_EMPLOYEE';
    return {
        role, rank,
        isAdmin,
        isDirector: isOwnerLevel,             // "Director or above" (kept name used by the pages)
        isOwnerLevel,
        isManager,
        isSecretary,
        isEmployee,
        isStaff: rank >= 2,                   // everyone except Employee
        canSeeCompanyMoney: isOwnerLevel,     // Payments, Reports, money columns on client pages
        canEditRecords: isManager,            // edit mode, statuses, payments on the Folder page
        canUploadDocs: rank >= 2,             // add scans without edit mode
        canAddStatus: isManager,              // only Admin, Director, Manager create statuses
        canManageStaff: isOwnerLevel,         // Staff tab
        canUseArchive: isOwnerLevel,          // delete / restore projects, Archive tab
        canWipe: isAdmin,                     // Danger Zone
        chip: isAdmin ? 'ADMIN' : (RANKS[role] ? RANKS[role].chip : 'STAFF'),
    };
}

// fix181 (14.0a): the start pages a person may pick (every rank from Secretary up may open all four). The Employee has
// no choice and always starts at New Project. The saved value is checked again at sign-in, because devices are shared.
export const LANDING_PATHS = {
    dashboard: '/dashboard',
    ledger:    '/land/projects',
    recovery:  '/recovery',
    clients:   '/clients',
};
export const LANDING_OPTIONS = [
    { value: 'dashboard', label: 'HOME' },
    { value: 'ledger', label: 'LEDGER' },
    { value: 'recovery', label: 'RECOVERY' },
    { value: 'clients', label: 'CLIENTS' },
];
export const landingPathFor = (user, saved) => {
    const f = roleFlags(user);
    if (f.isEmployee) return '/land/new';
    if (!f.isStaff) return '/login';
    return LANDING_PATHS[saved] || '/dashboard';
};
