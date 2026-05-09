import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    content = read(path)
    if old not in content:
        print(f"MISSING: {path}")
        return
    write(path, content.replace(old, new, 1))

# 1. Remove unused 'api' import from FolderPage.jsx
patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    "import recoveryService from '../../services/recoveryService';\nimport api from '../../api/axios';",
    "import recoveryService from '../../services/recoveryService';"
)

# 2. Remove unused handleRelease function (it's defined but never called)
patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    """    const handleRelease = async () => {
        // Check if documents exist
        if (!binder.documents || binder.documents.length === 0) {
            const ok = await confirm(
                'NO DOCUMENTS ATTACHED',
                'This plot has no scanned documents attached. It is strongly recommended to upload the title deed and ID scans before release. Continue anyway?',
                'warn'
            );
            if (!ok) return;
        }
        // Check payment
        if (project.amountPaid < project.totalCost) {
            toast('RELEASE DENIED: Outstanding balance detected.', 'error');
            return;
        }
        try {
            await landService.authorizeRelease(id, null);
            await loadFolderData();
            toast('PLOT RELEASED SUCCESSFULLY', 'success');
        } catch (err) {
            toast('RELEASE FAILED: ' + (err.response?.data?.message || err.message), 'error');
        }
    };

    const handleStageClick""",
    "    const handleStageClick"
)

# 3. Fix useless escape in getVaultUrl (line 687)
patch(
    "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx",
    "const parts = filePath.split(/ge_uploads[\\/]/);",
    "const parts = filePath.split(/ge_uploads[/]/);"
)

# 4. Remove unused MONTHLY_STORAGE_FEE constant from BacklogSchedulerService.java
patch(
    "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/BacklogSchedulerService.java",
    "    private static final BigDecimal DEFAULT_MONTHLY_FEE = new BigDecimal(\"50000\");\n    private static final BigDecimal MONTHLY_STORAGE_FEE = new BigDecimal(\"50000\"); // kept for reference",
    "    private static final BigDecimal DEFAULT_MONTHLY_FEE = new BigDecimal(\"50000\");"
)

print("Done.")