// PATH: erp-frontend/src/constants/projectTypes.js
// fix180: the eight project types (same list as ProjectType.java on the server -- keep the two in step).
// titleMode: ALWAYS = Title Details always shown, OPTIONAL = staff switch them on, NEVER = never shown.
// The status list of each type comes from the server (GET /status-templates?projectType=...).
export const PROJECT_TYPES = [
    { value: 'FRESH_SURVEY',       label: 'Fresh Survey',       titleMode: 'NEVER' },
    { value: 'SUBDIVISION',        label: 'Subdivision',        titleMode: 'ALWAYS' },
    { value: 'LEGACY_TITLES',      label: 'Legacy Titles',      titleMode: 'ALWAYS' },
    { value: 'TRANSFER_OF_TITLE',  label: 'Transfer of Title',  titleMode: 'ALWAYS' },
    { value: 'BOUNDARY_OPENING',   label: 'Boundary Opening',   titleMode: 'ALWAYS' },
    { value: 'TOPOGRAPHIC_SURVEY', label: 'Topographic Survey', titleMode: 'OPTIONAL' },
    { value: 'RESURVEY',           label: 'Resurvey',           titleMode: 'ALWAYS' },
    { value: 'SPECIAL_PROJECTS',   label: 'Special Projects',   titleMode: 'NEVER' },
];

const BY_VALUE = Object.fromEntries(PROJECT_TYPES.map(t => [t.value, t]));

// A project saved before fix180 has no type: Legacy Title entries read as Legacy Titles, the rest as Fresh Survey.
export const projectTypeOf = (project) => {
    const t = project && BY_VALUE[project.projectType];
    if (t) return t;
    return BY_VALUE[project && project.isLegacy ? 'LEGACY_TITLES' : 'FRESH_SURVEY'];
};

export const projectTypeLabel = (value) => (BY_VALUE[value] ? BY_VALUE[value].label : (value || '---'));

// Is the Title Details panel shown for this type? (OPTIONAL: only when switched on)
export const showsTitle = (type, switchedOn) => {
    const t = typeof type === 'string' ? BY_VALUE[type] : type;
    if (!t) return false;
    return t.titleMode === 'ALWAYS' || (t.titleMode === 'OPTIONAL' && !!switchedOn);
};
