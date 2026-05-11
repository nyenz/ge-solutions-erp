import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        return True
    else:
        print(f"MISSING in {path}: snippet not matched")
        return False

# ================================================================
# FIX 1: IntakePage.jsx
#
# Problem 1: isDirty fires on ANY text input. We want the guard
# only when user has meaningfully started a registration:
#   - plotNumber filled AND at least one owner name/phone filled
#   OR total cost filled
#   OR files queued
#
# Problem 2: Duplicate button should validate+save before duping.
# ================================================================

INTAKE = 'erp-frontend/src/pages/Intake/IntakePage.jsx'

# Fix isDirty -- require plotNumber to be non-empty AND something else meaningful
# so random typing in one box doesn't trigger the guard
patch(
    INTAKE,
    "    const isDirty = React.useMemo(() =>\n        plotNumber.trim() !== '' ||\n        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||\n        totalCost !== '' ||\n        fileQueue.length > 0 ||\n        notesList.length > 0,\n    [plotNumber, owners, totalCost, fileQueue, notesList]);",
    """    // Guard only fires when the user has meaningfully started filling the form:
    // plotNumber set AND (owner name/phone filled OR cost set OR files attached)
    const isDirty = React.useMemo(() => {
        const hasPlot    = plotNumber.trim() !== '';
        const hasOwner   = owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '');
        const hasCost    = totalCost !== '';
        const hasFiles   = fileQueue.length > 0;
        const hasNotes   = notesList.length > 0;
        // Require at least plotNumber PLUS one other meaningful field
        return hasPlot && (hasOwner || hasCost || hasFiles || hasNotes);
    }, [plotNumber, owners, totalCost, fileQueue, notesList]);"""
)

# Fix Duplicate button -- validate+save first, then reset for a new entry
# Replace the current handleDuplicatePlot function
patch(
    INTAKE,
    """    // Duplicate: pre-fill from last submitted or current form data
    const handleDuplicatePlot = () => {
        // Keep all fields except plotNumber (must be unique)
        setTenure(tenure);
        setPhysicalBoxNumber(physicalBoxNumber);
        setDistrict(district);
        setCounty(county);
        setBlockRoad(blockRoad);
        setVolume(volume);
        setFolio(folio);
        setInstrumentNo(instrumentNo);
        setTotalCost(totalCost);
        setInitialPayment('');
        setIsBacklog(isBacklog);
        setMonthlyStorageFee(monthlyStorageFee);
        setInitialStorageFee('');
        // Clear unique fields
        setPlotNumber('');
        setFileQueue([]);
        setNotesList([]);
        // Keep owners as-is
        toast('PLOT DUPLICATED -- enter new Plot ID and adjust details', 'info', 4000);
    };""",
    """    // Duplicate: save current plot first, then pre-fill form for a similar new plot
    const handleDuplicatePlot = async () => {
        if (!validate()) {
            toast('Fix the highlighted fields before duplicating', 'error');
            return;
        }
        setSaving(true);
        try {
            const payload = {
                plotNumber: plotNumber.trim().toUpperCase(),
                tenure,
                physicalBoxNumber: physicalBoxNumber.trim().toUpperCase(),
                district:   district.trim().toUpperCase(),
                county:     county.trim().toUpperCase(),
                blockRoad:  blockRoad.trim().toUpperCase(),
                volume,
                folio,
                instrumentNo: instrumentNo.trim().toUpperCase(),
                totalCost:      Number(totalCost)      || 0,
                initialPayment: Number(initialPayment) || 0,
                isStartAsBacklog: isBacklog,
                isLegacy: false,
                owners: owners.map(o => ({
                    fullName:   o.fullName.trim().toUpperCase(),
                    phone:      o.phone.trim(),
                    email:      o.email.trim().toLowerCase(),
                    nationalId: o.nationalId.trim().toUpperCase(),
                    address:    o.address.trim(),
                })),
                notes: notesList.map(n => ({ content: n })),
            };
            predictionService.learn(payload);
            await landService.createAtomicEntry(payload, fileQueue.length ? fileQueue : null);
            toast('Saved! Now enter a new Plot ID for the duplicate', 'success', 4000);
            // Pre-fill everything except the unique fields
            setPlotNumber('');
            setInitialPayment('');
            setInitialStorageFee('');
            setFileQueue([]);
            setNotesList([]);
            setErrors({});
            // Keep: tenure, physicalBoxNumber, district, county, blockRoad,
            //       volume, folio, instrumentNo, totalCost, isBacklog,
            //       monthlyStorageFee, owners
        } catch (err) {
            const msg = err.response?.data?.message || err.message || 'Save failed';
            toast(msg, 'error', 8000);
        } finally {
            setSaving(false);
        }
    };"""
)

print("OK: IntakePage.jsx - isDirty tightened, duplicate saves first")

# ================================================================
# FIX 2: FolderPage.jsx
#
# Problem: useRouterBlock(!committing && isEditing) means the guard
# fires during the brief window between handleCommit setting
# committing=true -> saving -> setIsEditing(false).
# Also fires if user opened edit mode but changed nothing.
#
# Fix: Track whether any field has actually changed since edit mode
# was opened (hasChanges). Guard only fires when isEditing AND hasChanges.
# ================================================================

FOLDER = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

# Add a hasChanges ref and update it when buffer changes
# We track this by comparing buffer to originalBuffer at edit-start time.
# Simplest approach: track a "touched" boolean that flips true on first buffer change.

# After the existing state declarations, add a touched ref
patch(
    FOLDER,
    "    const firstInputRef = useRef(null);\n    const fileInputRef  = useRef(null);",
    """    const firstInputRef = useRef(null);
    const fileInputRef  = useRef(null);
    // Track whether any field was actually changed since edit mode opened
    const touchedRef    = useRef(false);"""
)

# Reset touchedRef when edit mode opens or closes
patch(
    FOLDER,
    "    const handleUnlock = async () => {\n        setIsEditing(true);\n        try { await landService.logDossierUnlock(id); } catch { /* non-fatal */ }\n    };",
    """    const handleUnlock = async () => {
        touchedRef.current = false; // reset touch tracking
        setIsEditing(true);
        try { await landService.logDossierUnlock(id); } catch { /* non-fatal */ }
    };"""
)

# Reset on abort
patch(
    FOLDER,
    "        if (ok) { setIsEditing(false); setFieldErrors({}); loadFolderData(); }",
    "        if (ok) { touchedRef.current = false; setIsEditing(false); setFieldErrors({}); loadFolderData(); }"
)

# Reset on successful commit
patch(
    FOLDER,
    "            setIsEditing(false);\n            await loadFolderData();\n            toast('ARCHIVE REWRITTEN SUCCESSFULLY', 'success');",
    """            touchedRef.current = false;
            setIsEditing(false);
            await loadFolderData();
            toast('ARCHIVE REWRITTEN SUCCESSFULLY', 'success');"""
)

# Mark touched whenever buffer changes -- wrap existing setBuffer calls.
# Easiest: intercept at the SmartInput/SmartSelect onChange level is complex.
# Better: wrap setBuffer in a helper that also marks touched.
# Add a helper right after touchedRef declaration.

patch(
    FOLDER,
    "    // Track whether any field was actually changed since edit mode opened\n    const touchedRef    = useRef(false);",
    """    // Track whether any field was actually changed since edit mode opened
    const touchedRef    = useRef(false);
    // Wrap setBuffer so any change marks the form as touched
    const touchedSetBuffer = React.useCallback((updater) => {
        touchedRef.current = true;
        setBuffer(updater);
    }, []);"""
)

# Update the guard to use touchedRef
patch(
    FOLDER,
    "    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!committing && isEditing);",
    "    const { blocked: guardModalOpen, proceed: handleLeave, reset: handleStay } =\n        useRouterBlock(!committing && isEditing && touchedRef.current);"
)

# Update beforeunload to also check touchedRef
patch(
    FOLDER,
    "    // beforeunload -- catches tab close, hard refresh, browser back to external site\n    useEffect(() => {\n        if (!isEditing || committing) return;",
    """    // beforeunload -- catches tab close, hard refresh, browser back to external site
    useEffect(() => {
        if (!isEditing || committing || !touchedRef.current) return;"""
)

# Now replace the setBuffer calls in the JSX section with touchedSetBuffer
# These are the direct setBuffer calls inside SmartInput onChange handlers in render
# We target the ones that fire inside isEditing ? (...) blocks

# Plot details inputs
patch(
    FOLDER,
    "                                        <SmartInput ref={firstInputRef} label=\"PLOT ID\" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => setBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />",
    "                                        <SmartInput ref={firstInputRef} label=\"PLOT ID\" value={buffer.plotNumber} showCaps required error={fieldErrors.plotNumber} onChange={e => touchedSetBuffer({...buffer, plotNumber: e.target.value.toUpperCase()})} />"
)
patch(
    FOLDER,
    "                                        <SmartSelect label=\"TENURE\" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => setBuffer({...buffer, tenure: v})} />",
    "                                        <SmartSelect label=\"TENURE\" options={['MAILO','FREEHOLD','LEASEHOLD','CUSTOMARY']} value={buffer.tenure} onChange={v => touchedSetBuffer({...buffer, tenure: v})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"BOX LOCATION\" value={buffer.physicalBoxNumber} showCaps onChange={e => setBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />",
    "                                        <SmartInput label=\"BOX LOCATION\" value={buffer.physicalBoxNumber} showCaps onChange={e => touchedSetBuffer({...buffer, physicalBoxNumber: e.target.value.toUpperCase()})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"DISTRICT\" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => setBuffer({...buffer, district: e.target.value.toUpperCase()})} />",
    "                                        <SmartInput label=\"DISTRICT\" value={buffer.district} showCaps required error={fieldErrors.district} suggestions={sg('district')} onChange={e => touchedSetBuffer({...buffer, district: e.target.value.toUpperCase()})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"COUNTY\" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => setBuffer({...buffer, county: e.target.value.toUpperCase()})} />",
    "                                        <SmartInput label=\"COUNTY\" value={buffer.county} showCaps suggestions={sg('county')} onChange={e => touchedSetBuffer({...buffer, county: e.target.value.toUpperCase()})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"BLOCK / ROAD\" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => setBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />",
    "                                        <SmartInput label=\"BLOCK / ROAD\" value={buffer.blockRoad} showCaps suggestions={sg('blockRoad')} onChange={e => touchedSetBuffer({...buffer, blockRoad: e.target.value.toUpperCase()})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"INSTRUMENT NO.\" value={buffer.instrumentNo} showCaps onChange={e => setBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />",
    "                                        <SmartInput label=\"INSTRUMENT NO.\" value={buffer.instrumentNo} showCaps onChange={e => touchedSetBuffer({...buffer, instrumentNo: e.target.value.toUpperCase()})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"VOLUME\" value={buffer.volume} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => setBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />",
    "                                        <SmartInput label=\"VOLUME\" value={buffer.volume} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => touchedSetBuffer({...buffer, volume: e.target.value.replace(/\\D/g,'')})} />"
)
patch(
    FOLDER,
    "                                        <SmartInput label=\"FOLIO\" value={buffer.folio} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => setBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />",
    "                                        <SmartInput label=\"FOLIO\" value={buffer.folio} inputMode=\"numeric\" hint=\"Numbers only\" onChange={e => touchedSetBuffer({...buffer, folio: e.target.value.replace(/\\D/g,'')})} />"
)

# Owner change handler - uses handleOwnerChange which calls setBuffer internally
# Replace setBuffer in handleOwnerChange
patch(
    FOLDER,
    "        const owners = buffer.owners.map((o,i) => {\n            if (i !== idx) return o;\n            let v = val;\n            if (field==='fullName')   v = val.toUpperCase();\n            if (field==='nationalId') v = val.toUpperCase().replace(/\\s/g,'');\n            if (field==='email')      v = val.toLowerCase().replace(/\\s/g,'');\n            return { ...o, [field]: v };\n        });\n        setBuffer(p => ({ ...p, owners }));",
    """        const owners = buffer.owners.map((o,i) => {
            if (i !== idx) return o;
            let v = val;
            if (field==='fullName')   v = val.toUpperCase();
            if (field==='nationalId') v = val.toUpperCase().replace(/\s/g,'');
            if (field==='email')      v = val.toLowerCase().replace(/\s/g,'');
            return { ...o, [field]: v };
        });
        touchedRef.current = true;
        setBuffer(p => ({ ...p, owners }));"""
)

# Email commit in owner
patch(
    FOLDER,
    "    const handleEmailCommit = (idx, val) => {\n        const owners = buffer.owners.map((o,i) => i===idx ? { ...o, email:val } : o);\n        setBuffer(p => ({ ...p, owners }));\n    };",
    """    const handleEmailCommit = (idx, val) => {
        const owners = buffer.owners.map((o,i) => i===idx ? { ...o, email:val } : o);
        touchedRef.current = true;
        setBuffer(p => ({ ...p, owners }));
    };"""
)

# Currency inputs in financials edit section
patch(
    FOLDER,
    "                                    <CurrencyInput label=\"TOTAL COST\" value={buffer.totalCost} onChange={v => setBuffer({...buffer, totalCost:v})} />",
    "                                    <CurrencyInput label=\"TOTAL COST\" value={buffer.totalCost} onChange={v => touchedSetBuffer({...buffer, totalCost:v})} />"
)
patch(
    FOLDER,
    "                                    <CurrencyInput label=\"AMOUNT PAID\" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => setBuffer({...buffer, initialPayment:v})} />",
    "                                    <CurrencyInput label=\"AMOUNT PAID\" value={buffer.initialPayment} error={fieldErrors.initialPayment} onChange={v => touchedSetBuffer({...buffer, initialPayment:v})} />"
)

print("OK: FolderPage.jsx - guard only fires when actual changes were made")

print("\nAll done!")
print("Changes:")
print("  1. IntakePage: isDirty requires plotNumber + one other meaningful field")
print("  2. IntakePage: Duplicate button saves first, then resets for new entry")
print("  3. FolderPage: Guard only fires when user actually changed something")
print("     (opening edit mode and clicking away without changing = no warning)")
print("")
print("Run: git add -A && git commit -m 'fix: unsaved-changes guard only fires on actual edits, duplicate saves first' && git push")