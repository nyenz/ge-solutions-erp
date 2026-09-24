// PATH: erp-frontend/src/pages/Reports/reportsCatalog.js
// GOLDEN SEED -- REPORT CATALOGUE (single source of truth for ReportStudio).
// Exports exactly: GROUPS, ENTITIES, CATALOGUE.
// Def shape: { id, title, desc, ds, group, money, scopes, period, groupBy,
//              measure, cols, chart, sort }
//   scopes  : entity types this report can narrow to (see ENTITIES)
//   period  : true = honours the period chips; false = right-now snapshot
//   groupBy : field LABEL to group by ('' = row level)
//   measure : {agg:'sum'|'count', field:LABEL} or {agg:'count'} or null
//   cols    : field LABELS for the results table
//   chart   : BAR | COLUMN | LINE | DONUT | NONE
//   sort    : {col:LABEL, dir:'asc'|'desc'}
export const GROUPS = ['WORK IN','IN PROCESS','MONEY IN','MONEY OUT','CLIENTS / RECOVERY','COMPLIANCE / ARCHIVE'];

export const ENTITIES = {
  PROJECTS: [
    { type:'PROJECT',  label:'Project',  field:'Project Index' },
    { type:'CLIENT',   label:'Client',   field:'Primary Owner' },
    { type:'LOCATION', label:'Location', field:'District' },
  ],
  CLIENTS: [
    { type:'CLIENT',   label:'Client',   field:'Client Name' },
    { type:'LOCATION', label:'Location', field:'District' },
  ],
  PAYMENTS: [
    { type:'PROJECT',  label:'Project',  field:'Plot' },
    { type:'CLIENT',   label:'Client',   field:'Owner Name' },
    { type:'OPERATOR', label:'Operator', field:'Recorded By' },
  ],
  EXPENSES: [
    { type:'CATEGORY', label:'Category', field:'Category' },
    { type:'OPERATOR', label:'Operator', field:'Spent By' },
  ],
  COMPANY: [
    { type:'OPERATOR', label:'Operator', field:'Operator' },
  ],
};

export const CATALOGUE = [
  // ── PROJECTS / MONEY IN ──
  { id:'p_owed_dist', title:'OWED BY DISTRICT', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','District','Sub-County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'What is still owed, added up per district.' },
  { id:'p_owed_county', title:'OWED BY COUNTY', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'County', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'What is still owed, added up per county.' },
  { id:'p_owed_sub', title:'OWED BY SUB-COUNTY', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Sub-County', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Sub-County','Status','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'What is still owed, added up per sub-county.' },
  { id:'p_owed_owner', title:'OWED BY OWNER', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT'], period:false, groupBy:'Primary Owner', measure:{agg:'sum',field:'Balance Owed'}, cols:['Project Index','Primary Owner','Owner Phone','District','Balance Owed'], chart:'BAR', sort:{col:'Balance Owed',dir:'desc'}, desc:'Every primary owner ranked by what they still owe.' },
  { id:'p_paid_cost', title:'PAID VS COST', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Status', measure:{agg:'sum',field:'Amount Paid'}, cols:['Project Index','Primary Owner','Status','Total Cost','Amount Paid','Balance Owed'], chart:'COLUMN', sort:{col:'Amount Paid',dir:'desc'}, desc:'What has been collected per status against live cost.' },
  { id:'p_never_paid', title:'NEVER-PAID PROJECTS', ds:'PROJECTS', group:'MONEY IN', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Amount Paid',op:'eq',value:0}, cols:['Project Index','Primary Owner','District','Status','Balance Owed'], chart:'BAR', sort:{col:'Project Index',dir:'asc'}, desc:'Projects with no payment recorded at all.' },
  // ── PROJECTS / IN PROCESS ──
  { id:'p_by_stage', title:'PROJECTS BY STAGE', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Stage', measure:{agg:'count'}, cols:['Project Index','Primary Owner','District','Stage','Status'], chart:'DONUT', sort:{col:'Project Index',dir:'asc'}, desc:'How many projects sit at each survey stage right now.' },
  { id:'p_by_status', title:'PROJECTS BY STATUS', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Status', measure:{agg:'count'}, cols:['Project Index','Primary Owner','District','Status'], chart:'DONUT', sort:{col:'Project Index',dir:'asc'}, desc:'Active against released against receivable, right now.' },
  { id:'p_stalled', title:'STALLED PROJECTS', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Days Since Payment',op:'gt',value:60}, cols:['Project Index','Primary Owner','District','Days Since Payment','Status'], chart:'BAR', sort:{col:'Days Since Payment',dir:'desc'}, desc:'Projects with no payment in 60+ days, per district.' },
  { id:'p_titles_issued', title:'TITLES ISSUED', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, cols:['Project Index','Title ID','Primary Owner','District','Title Date'], chart:'COLUMN', sort:{col:'Title Date',dir:'desc'}, desc:'Titles issued in the chosen period, per district.' },
  { id:'p_released', title:'RELEASED PROJECTS', ds:'PROJECTS', group:'IN PROCESS', money:false, scopes:['CLIENT','LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Status',op:'is',value:'RELEASED'}, cols:['Project Index','Primary Owner','District','Status'], chart:'BAR', sort:{col:'Project Index',dir:'asc'}, desc:'Projects handed back to clients, per district.' },
  // ── PROJECTS / WORK IN ──
  { id:'p_new_folders', title:'NEW FOLDERS OPENED', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'New Folder'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'}, desc:'New Folder intakes in the chosen period, per district.' },
  { id:'p_new_titles', title:'NEW TITLES ENTERED', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'New Title'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'}, desc:'New Title intakes in the chosen period, per district.' },
  { id:'p_legacy', title:'LEGACY INTAKES', ds:'PROJECTS', group:'WORK IN', money:false, scopes:['CLIENT','LOCATION'], period:true, groupBy:'District', measure:{agg:'count'}, filter:{field:'Entry Mode',op:'is',value:'Legacy Title'}, cols:['Project Index','Primary Owner','District','Entry Mode','Project Start'], chart:'COLUMN', sort:{col:'Project Start',dir:'desc'}, desc:'Legacy Title intakes in the chosen period, per district.' },
  // ── CLIENTS ──
  { id:'c_by_district', title:'CLIENTS BY DISTRICT', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, cols:['Client Name','Phone','District','Sub-County','Projects'], chart:'DONUT', sort:{col:'Client Name',dir:'asc'}, desc:'How many registered clients each district has.' },
  { id:'c_top_debtors', title:'TOP DEBTORS', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:true, scopes:['CLIENT','LOCATION'], period:false, groupBy:'Client Name', measure:{agg:'sum',field:'Total Owed'}, cols:['Client Name','Phone','District','Total Owed','Total Paid'], chart:'BAR', sort:{col:'Total Owed',dir:'desc'}, desc:'Clients ranked by what they still owe.' },
  { id:'c_never_called', title:'NEVER-CALLED CLIENTS', ds:'CLIENTS', group:'CLIENTS / RECOVERY', money:false, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'count'}, filter:{field:'Last Contact',op:'empty'}, cols:['Client Name','Phone','District','Last Contact'], chart:'BAR', sort:{col:'Client Name',dir:'asc'}, desc:'Clients nobody has called yet, per district.' },
  { id:'c_owed_dist', title:'CLIENT DEBT BY DISTRICT', ds:'CLIENTS', group:'MONEY IN', money:true, scopes:['LOCATION'], period:false, groupBy:'District', measure:{agg:'sum',field:'Total Owed'}, cols:['Client Name','District','Total Owed','Total Paid'], chart:'BAR', sort:{col:'Total Owed',dir:'desc'}, desc:'Client debt added up per district.' },
  // ── PAYMENTS ──
  { id:'pay_received', title:'PAYMENTS RECEIVED', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT','CLIENT','OPERATOR'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Payment Type','Amount Paid','Recorded By'], chart:'LINE', sort:{col:'Date',dir:'desc'}, desc:'Money in per month for the chosen period.' },
  { id:'pay_by_type', title:'PAYMENTS BY TYPE', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT','CLIENT','OPERATOR'], period:true, groupBy:'Payment Type', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Payment Type','Amount Paid'], chart:'DONUT', sort:{col:'Amount Paid',dir:'desc'}, desc:'Standard against deposit against receivable-part.' },
  { id:'pay_operator', title:'COLLECTIONS PER OPERATOR', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['OPERATOR'], period:true, groupBy:'Recorded By', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Amount Paid','Recorded By'], chart:'COLUMN', sort:{col:'Amount Paid',dir:'desc'}, desc:'Who collected how much in the chosen period.' },
  { id:'pay_by_plot', title:'PAYMENTS BY PROJECT', ds:'PAYMENTS', group:'MONEY IN', money:true, scopes:['PROJECT'], period:true, groupBy:'Plot', measure:{agg:'sum',field:'Amount Paid'}, cols:['Date','Plot','Owner Name','Payment Type','Amount Paid'], chart:'BAR', sort:{col:'Amount Paid',dir:'desc'}, desc:'Every project ranked by what it has paid.' },
  // ── EXPENSES ──
  { id:'e_by_category', title:'EXPENSES BY CATEGORY', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['CATEGORY','OPERATOR'], period:true, groupBy:'Category', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Item','Amount','Spent By'], chart:'DONUT', sort:{col:'Amount',dir:'desc'}, desc:'Which category ate the money in the chosen period.' },
  { id:'e_by_operator', title:'EXPENSES PER OPERATOR', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['OPERATOR'], period:true, groupBy:'Spent By', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Item','Amount','Spent By'], chart:'COLUMN', sort:{col:'Amount',dir:'desc'}, desc:'Who spent how much in the chosen period.' },
  { id:'e_over_time', title:'EXPENSES OVER TIME', ds:'EXPENSES', group:'MONEY OUT', money:true, scopes:['CATEGORY','OPERATOR'], period:true, groupBy:'Month', measure:{agg:'sum',field:'Amount'}, cols:['Date','Category','Item','Amount','Spent By'], chart:'LINE', sort:{col:'Date',dir:'desc'}, desc:'Money out per month for the chosen period.' },
  // ── COMPANY ─
  { id:'co_workload', title:'OPERATOR WORKLOAD', ds:'COMPANY', group:'WORK IN', money:false, scopes:['OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Entity'], chart:'COLUMN', sort:{col:'Operator',dir:'asc'}, desc:'Every staff action counted per operator in the period.' },
  { id:'co_by_action', title:'AUDIT BY ACTION', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['OPERATOR'], period:true, groupBy:'Action', measure:{agg:'count'}, cols:['Timestamp','Operator','Action','Entity'], chart:'BAR', sort:{col:'Operator',dir:'asc'}, desc:'Which system actions happened most in the period.' },
  { id:'co_logins', title:'LOGINS PER OPERATOR', ds:'COMPANY', group:'COMPLIANCE / ARCHIVE', money:false, scopes:['OPERATOR'], period:true, groupBy:'Operator', measure:{agg:'count'}, filter:{field:'Action',op:'is',value:'LOGIN_SUCCESS'}, cols:['Timestamp','Operator','Action','Device'], chart:'COLUMN', sort:{col:'Operator',dir:'asc'}, desc:'Who signed in how often in the chosen period.' },
];
export default CATALOGUE;
