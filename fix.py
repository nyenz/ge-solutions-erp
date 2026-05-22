import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

def patch(path, old, new):
    data = read(path)
    if old in data:
        write(path, data.replace(old, new, 1))
    else:
        print(f"MISSING patch target in: {path}")

print("=== FIX 1a: Add monthlyStorageFee and initialStorageFee to LandEntryRequest.java ===")
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/dto/LandEntryRequest.java',
    '''    @JsonProperty("isStartAsBacklog")
    private boolean isStartAsBacklog;''',
    '''    @JsonProperty("isStartAsBacklog")
    private boolean isStartAsBacklog;

    private java.math.BigDecimal monthlyStorageFee;
    private java.math.BigDecimal initialStorageFee;'''
)

print("=== FIX 1b: Map monthlyStorageFee and initialStorageFee in LandService.java atomicIntake ===")
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/LandService.java',
    '''        if (startAsBacklog && outstanding.compareTo(BigDecimal.ZERO) > 0) {
            builder.isBacklog(true)
                   .backlogStartDate(LocalDateTime.now())
                   .originalDebt(outstanding)
                   .storageFeesAccumulated(BigDecimal.ZERO);
        }''',
    '''        if (startAsBacklog && outstanding.compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal initialFees = request.getInitialStorageFee() != null
                    ? request.getInitialStorageFee() : BigDecimal.ZERO;
            builder.isBacklog(true)
                   .backlogStartDate(LocalDateTime.now())
                   .originalDebt(outstanding)
                   .storageFeesAccumulated(initialFees);
            if (request.getMonthlyStorageFee() != null
                    && request.getMonthlyStorageFee().compareTo(BigDecimal.ZERO) > 0) {
                builder.storageFeeOverride(request.getMonthlyStorageFee());
            }
        }'''
)

print("=== FIX 2: Friendly duplicate plot error in GlobalExceptionHandler.java ===")
patch(
    'erp-backend/src/main/java/com/gesolutions/erp/common/exception/GlobalExceptionHandler.java',
    '''    // --- 5. DATABASE INTEGRITY FAULTS ---
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> handleDataIntegrity(DataIntegrityViolationException ex) {
        String msg = ex.getMessage().toLowerCase();
        System.err.println(">>> [DB_CONFLICT]: " + msg);
        if (msg.contains("unique") || msg.contains("duplicate")) {
            return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A record with this ID already exists.");
        }
        return buildResponse(HttpStatus.CONFLICT, "INTEGRITY_VIOLATION", "Cannot modify record: Active data links found.");
    }''',
    '''    // --- 5. DATABASE INTEGRITY FAULTS ---
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<Map<String, Object>> handleDataIntegrity(DataIntegrityViolationException ex) {
        String msg = ex.getMessage() != null ? ex.getMessage().toLowerCase() : "";
        System.err.println(">>> [DB_CONFLICT]: " + msg);
        if (msg.contains("unique") || msg.contains("duplicate")) {
            if (msg.contains("plot_number") || msg.contains("plot number") || msg.contains("plotnumber")) {
                return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A plot with this ID already exists in the system.");
            }
            return buildResponse(HttpStatus.CONFLICT, "REGISTRY_CONFLICT", "A record with this ID already exists.");
        }
        return buildResponse(HttpStatus.CONFLICT, "INTEGRITY_VIOLATION", "Cannot modify record: Active data links found.");
    }'''
)

print("=== FIX 3: Mandatory document scan in IntakePage.jsx ===")
patch(
    'erp-frontend/src/pages/Intake/IntakePage.jsx',
    '''    const validate = () => {
        const e = {};
        if (!plotNumber.trim())        e.plotNumber = 'Required';
        if (!district.trim())          e.district   = 'Required';
        if (!totalCost)                e.totalCost  = 'Required';
        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
        });
        setErrors(e);
        return Object.keys(e).length === 0;
    };''',
    '''    const validate = () => {
        const e = {};
        if (!plotNumber.trim())        e.plotNumber = 'Required';
        if (!district.trim())          e.district   = 'Required';
        if (!totalCost)                e.totalCost  = 'Required';
        owners.forEach((o, i) => {
            if (!o.fullName.trim())    e['owner_' + i + '_name']  = 'Required';
            if (!o.phone.trim())       e['owner_' + i + '_phone'] = 'Required';
        });
        if (fileQueue.length === 0) {
            toast('At least one document scan is required.', 'error', 6000);
            setDrawers(prev => ({ ...prev, docs: true }));
        }
        setErrors(e);
        return Object.keys(e).length === 0 && fileQueue.length > 0;
    };'''
)

print("=== ALL FIXES APPLIED ===")