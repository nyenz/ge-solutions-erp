#!/usr/bin/env python3
# PATH: fix136.py
# GOLDEN SEED -- fix136: DOCUMENT CATEGORIES -- every upload lands in a category.
#   Before: the Folder page DOCUMENTS tab took any file and stored it with no
#   category at all (file_type only held the browser MIME type). Now:
#
#     1. CATEGORIES. Six built-in categories are seeded on first use:
#        Application Forms, Offer Letters, Forwarding Letters, Deed Plan,
#        Copy of Title, Payment Receipts. New table document_categories
#        (created by ddl-auto=update, nothing to run by hand).
#     2. UPLOAD. Clicking + ADD SCANS now opens an UPLOAD DOCUMENTS window
#        instead of uploading straight away. The uploader picks ONE category
#        for the whole batch, or overrides it per file -- their choice.
#        Nothing uploads until every file has a category.
#     3. NEW CATEGORY. The same window has + NEW CATEGORY. Allowed for
#        Secretary, Manager, Admin and Director. A name that already exists
#        (case/spacing ignored) just returns the existing category.
#     4. BACKEND. POST /land/projects/{id}/documents takes `category` (batch
#        default) and `categories` (one per file, same order as `scans`).
#        Unknown categories are rejected BEFORE any file is stored, so a bad
#        name can never leave half a batch behind. New column
#        project_documents.category. Audit line now lists the categories and
#        adding a category logs DOCUMENT_CATEGORY_ADDED.
#     5. DOCUMENTS TAB. Files are grouped under their category heading.
#        Older files with no category show under UNCATEGORISED (seed rows
#        whose file_type is already a category code, e.g. DEED_PLAN, group
#        correctly).
#
#   Not touched: intake (IntakePage still uploads with no category, so those
#   files show as UNCATEGORISED), re-categorising an existing document, and
#   deleting a category. Each is a separate batch.
#
# Backend (1 entity, 1 repo, 1 service, 1 controller new; LandService,
# LandController, ProjectDocument patched) + frontend (landService.js,
# FolderPage.jsx + css, auditCatalog.js).
#
# Atomic: every patch for every file is matched in memory first; if any
# one is MISSING nothing is written and nothing is committed. Runs
# `npm run build` before committing if node_modules is installed and
# refuses to commit on a red build.
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(ROOT, "erp-frontend")
SRC = os.path.join(FRONTEND, "src")
JAVA = os.path.join(ROOT, "erp-backend", "src", "main", "java", "com", "gesolutions", "erp")
LAND = os.path.join(JAVA, "modules", "land")

DOC_MODEL_JAVA = os.path.join(LAND, "model", "ProjectDocument.java")
CAT_MODEL_JAVA = os.path.join(LAND, "model", "DocumentCategory.java")
CAT_REPO_JAVA = os.path.join(LAND, "repository", "DocumentCategoryRepository.java")
CAT_SERVICE_JAVA = os.path.join(LAND, "service", "DocumentCategoryService.java")
CAT_CTRL_JAVA = os.path.join(LAND, "controller", "DocumentCategoryController.java")
LAND_SERVICE_JAVA = os.path.join(LAND, "service", "LandService.java")
LAND_CTRL_JAVA = os.path.join(LAND, "controller", "LandController.java")
LAND_SVC_JS = os.path.join(SRC, "services", "landService.js")
FOLDER_JSX = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.jsx")
FOLDER_CSS = os.path.join(SRC, "pages", "DigitalFolder", "FolderPage.module.css")
AUDIT_CATALOG_JS = os.path.join(SRC, "pages", "Audit", "auditCatalog.js")

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


def append_once(text, marker, block, desc):
    """Append a block to the end of a file unless the marker is already there."""
    if marker in text:
        print("SKIP: " + desc + " -- already applied")
        return text
    print("OK: " + desc)
    return text.rstrip("\n") + "\n\n" + block.strip("\n") + "\n"


NEW_FILES = []  # (path, text, label)


def create(path, text, label):
    """New file. SKIP if it already exists."""
    if os.path.exists(path):
        print("SKIP: " + label + " -- already exists")
        return
    print("OK: " + label + " (new file)")
    NEW_FILES.append((path, text, label))


# ======================================================================
# NEW: DocumentCategory.java
# ======================================================================
create(CAT_MODEL_JAVA, r'''// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/DocumentCategory.java
package com.gesolutions.erp.modules.land.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

/**
 * GE SOLUTIONS - DOCUMENT CATEGORY (fix136)
 *
 * The catalog a document is filed under: Application Forms, Offer Letters,
 * Forwarding Letters, Deed Plan, Copy of Title, Payment Receipts, plus any
 * category a Secretary / Manager / Admin / Director adds at upload time.
 *
 * code  = stable machine key stored on project_documents.category
 * label = what people read
 */
@Entity
@Table(name = "document_categories", uniqueConstraints = {
    @UniqueConstraint(name = "uq_document_category_code", columnNames = "code")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DocumentCategory {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "code", nullable = false, length = 60)
    private String code;

    @Column(name = "label", nullable = false, length = 120)
    private String label;

    @Builder.Default
    @Column(name = "built_in", nullable = false)
    private boolean builtIn = false;

    /** Built-ins are 1..6 in the order the office files them; custom ones sort after. */
    @Builder.Default
    @Column(name = "sort_order", nullable = false)
    private int sortOrder = 100;

    @Column(name = "created_by", length = 100)
    private String createdBy;

    @Builder.Default
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();
}
''', "Java: DocumentCategory entity")

# ======================================================================
# NEW: DocumentCategoryRepository.java
# ======================================================================
create(CAT_REPO_JAVA, r'''// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/DocumentCategoryRepository.java
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.DocumentCategory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface DocumentCategoryRepository extends JpaRepository<DocumentCategory, UUID> {

    Optional<DocumentCategory> findByCode(String code);

    List<DocumentCategory> findAllByOrderByBuiltInDescSortOrderAscLabelAsc();
}
''', "Java: DocumentCategoryRepository")

# ======================================================================
# NEW: DocumentCategoryService.java
# ======================================================================
create(CAT_SERVICE_JAVA, r'''// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/DocumentCategoryService.java
package com.gesolutions.erp.modules.land.service;

import com.gesolutions.erp.common.audit.AuditService;
import com.gesolutions.erp.common.exception.BusinessException;
import com.gesolutions.erp.modules.land.model.DocumentCategory;
import com.gesolutions.erp.modules.land.repository.DocumentCategoryRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;
import java.util.Optional;

/**
 * GE SOLUTIONS - DOCUMENT CATEGORIES (fix136)
 *
 * Seeds the six built-in categories on first use (no DataInitializer edit
 * needed), lists them, validates the category an upload asks for, and lets
 * Secretary / Manager / Admin / Director add new ones.
 */
@Service
@RequiredArgsConstructor
public class DocumentCategoryService {

    private static final String[][] DEFAULTS = {
        {"APPLICATION_FORM",   "Application Forms"},
        {"OFFER_LETTER",       "Offer Letters"},
        {"FORWARDING_LETTER",  "Forwarding Letters"},
        {"DEED_PLAN",          "Deed Plan"},
        {"COPY_OF_TITLE",      "Copy of Title"},
        {"PAYMENT_RECEIPT",    "Payment Receipts"},
    };

    private final DocumentCategoryRepository repository;
    private final AuditService auditService;

    private volatile boolean seeded = false;

    /** Idempotent: inserts any built-in that is missing, once per app run. */
    private synchronized void ensureDefaults() {
        if (seeded) return;
        for (int i = 0; i < DEFAULTS.length; i++) {
            String code = DEFAULTS[i][0];
            if (repository.findByCode(code).isEmpty()) {
                repository.save(DocumentCategory.builder()
                        .code(code)
                        .label(DEFAULTS[i][1])
                        .builtIn(true)
                        .sortOrder(i + 1)
                        .createdBy("SYSTEM")
                        .build());
            }
        }
        seeded = true;
    }

    public List<DocumentCategory> list() {
        ensureDefaults();
        return repository.findAllByOrderByBuiltInDescSortOrderAscLabelAsc();
    }

    /**
     * Turns what the client sent into a stored category code.
     * null / blank -> null (uncategorised). Unknown -> BusinessException, so the
     * whole upload is refused before a single file is stored.
     */
    public String requireCode(String raw) {
        if (raw == null || raw.isBlank()) return null;
        ensureDefaults();
        String code = toCode(raw);
        if (code.isEmpty() || repository.findByCode(code).isEmpty()) {
            throw new BusinessException("Unknown document category: " + raw.trim());
        }
        return code;
    }

    @Transactional
    public DocumentCategory create(String label) {
        String clean = label == null ? "" : label.trim().replaceAll("\\s+", " ");
        if (clean.length() < 2) throw new BusinessException("Category name is too short.");
        if (clean.length() > 120) throw new BusinessException("Category name is too long (120 characters max).");
        String code = toCode(clean);
        if (code.isEmpty()) throw new BusinessException("Category name needs letters or numbers.");
        ensureDefaults();
        Optional<DocumentCategory> existing = repository.findByCode(code);
        if (existing.isPresent()) return existing.get();
        DocumentCategory saved = repository.save(DocumentCategory.builder()
                .code(code)
                .label(clean)
                .builtIn(false)
                .sortOrder(100)
                .createdBy(currentOperator())
                .build());
        auditService.logAction("DOCUMENT_CATEGORY_ADDED",
                "Operator [" + currentOperator() + "] added document category: " + saved.getLabel());
        return saved;
    }

    private static String toCode(String raw) {
        String code = raw.trim().toUpperCase(Locale.ROOT)
                .replaceAll("[^A-Z0-9]+", "_")
                .replaceAll("^_+|_+$", "");
        return code.length() > 60 ? code.substring(0, 60) : code;
    }

    private String currentOperator() {
        if (SecurityContextHolder.getContext().getAuthentication() != null) {
            return SecurityContextHolder.getContext().getAuthentication().getName();
        }
        return "SYSTEM";
    }
}
''', "Java: DocumentCategoryService")

# ======================================================================
# NEW: DocumentCategoryController.java
# ======================================================================
create(CAT_CTRL_JAVA, r'''// PATH: erp-backend/src/main/java/com/gesolutions/erp/modules/land/controller/DocumentCategoryController.java
package com.gesolutions.erp.modules.land.controller;

import com.gesolutions.erp.modules.land.model.DocumentCategory;
import com.gesolutions.erp.modules.land.service.DocumentCategoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * fix136: document categories. Secretary is allowed to add categories too
 * (same roles that may upload a document).
 */
@RestController
@RequestMapping("/api/v1/land/document-categories")
@RequiredArgsConstructor
@PreAuthorize("hasAnyRole('ROLE_MANAGER', 'ROLE_SECRETARY', 'ROLE_ADMIN', 'ROLE_DIRECTOR')")
public class DocumentCategoryController {

    private final DocumentCategoryService documentCategoryService;

    @GetMapping
    public ResponseEntity<List<DocumentCategory>> list() {
        return ResponseEntity.ok(documentCategoryService.list());
    }

    @PostMapping
    public ResponseEntity<DocumentCategory> create(@RequestBody Map<String, String> body) {
        return ResponseEntity.ok(documentCategoryService.create(body.get("label")));
    }
}
''', "Java: DocumentCategoryController")

# ======================================================================
# ProjectDocument.java
# ======================================================================
doc0 = read(DOC_MODEL_JAVA)
doc = doc0

doc = sub(doc,
          "    private String fileType;\n",
          "    private String fileType;\n"
          "\n"
          "    /**\n"
          "     * fix136: DOCUMENT CATEGORY code (APPLICATION_FORM, OFFER_LETTER,\n"
          "     * FORWARDING_LETTER, DEED_PLAN, COPY_OF_TITLE, PAYMENT_RECEIPT or a\n"
          "     * custom one). null = uploaded before categories existed.\n"
          "     */\n"
          "    @Column(name = \"category\", length = 60)\n"
          "    private String category;\n",
          "Java: ProjectDocument.category column")

# ======================================================================
# LandService.java
# ======================================================================
svc0 = read(LAND_SERVICE_JAVA)
svc = svc0

svc = sub(svc,
          "    private final ProjectDocumentRepository documentRepository;\n",
          "    private final ProjectDocumentRepository documentRepository;\n"
          "    private final DocumentCategoryService documentCategoryService;\n",
          "Java: inject DocumentCategoryService")

svc = sub(svc,
          "public void addScansToProject(UUID projectId, MultipartFile[] scans) throws Exception {\n"
          "        for (MultipartFile file : scans) {\n",
          r'''public void addScansToProject(UUID projectId, MultipartFile[] scans) throws Exception {
        addScansToProject(projectId, scans, null, null);
    }

    /**
     * fix136: every file lands in a document category. batchCategory is the
     * default for the whole upload; fileCategories (same order as scans) lets
     * the uploader override it per file. All categories are validated BEFORE
     * any file is stored so a bad name can never leave half a batch behind.
     */
    @Transactional
    public void addScansToProject(UUID projectId, MultipartFile[] scans, String batchCategory, List<String> fileCategories) throws Exception {
        String batchCode = documentCategoryService.requireCode(batchCategory);
        String[] cats = new String[scans.length];
        for (int i = 0; i < scans.length; i++) {
            String own = (fileCategories != null && i < fileCategories.size())
                    ? documentCategoryService.requireCode(fileCategories.get(i)) : null;
            cats[i] = own != null ? own : batchCode;
        }
        for (int i = 0; i < scans.length; i++) {
            MultipartFile file = scans[i];
''',
          "Java: addScansToProject takes batch + per-file categories")

svc = sub(svc,
          ".fileType(file.getContentType())",
          ".fileType(file.getContentType())\n"
          "                    .category(cats[i])",
          "Java: category saved on each document")

svc = sub(svc,
          "+ \" document(s) to plot: \" + projectId);",
          "+ \" document(s) to plot: \" + projectId\n"
          "            + \" [\" + String.join(\", \", java.util.Arrays.stream(cats)\n"
          "                    .map(c -> c == null ? \"UNCATEGORISED\" : c).distinct().toList()) + \"]\");",
          "Java: audit line lists the categories")

# ======================================================================
# LandController.java
# ======================================================================
ctl0 = read(LAND_CTRL_JAVA)
ctl = ctl0

ctl = sub(ctl,
          '@RequestParam("scans") MultipartFile[] scans) throws Exception {\n'
          "        landService.addScansToProject(id, scans);\n",
          '@RequestParam("scans") MultipartFile[] scans,\n'
          '            @RequestParam(value = "category", required = false) String category,\n'
          '            @RequestParam(value = "categories", required = false) List<String> categories) throws Exception {\n'
          "        landService.addScansToProject(id, scans, category, categories);\n",
          "Java: documents endpoint accepts category + categories")

# ======================================================================
# landService.js
# ======================================================================
js0 = read(LAND_SVC_JS)
js = js0

js = sub(js,
         "    addExtraDocuments: async (projectId, scans) => {\n"
         "        const formData = new FormData();\n"
         "        scans.forEach(file => formData.append('scans', file));\n",
         "    addExtraDocuments: async (projectId, scans, categories = []) => {\n"
         "        const formData = new FormData();\n"
         "        scans.forEach(file => formData.append('scans', file));\n"
         "        // fix136: one category code per file, same order as scans\n"
         "        if (categories.length === scans.length) categories.forEach(c => formData.append('categories', c || ''));\n",
         "landService: addExtraDocuments sends a category per file")

js = sub(js,
         "    deleteDocument: async (docId) => {\n",
         "    getDocumentCategories: async () => {\n"
         "        const response = await api.get('/land/document-categories');\n"
         "        return response.data;\n"
         "    },\n"
         "\n"
         "    addDocumentCategory: async (label) => {\n"
         "        const response = await api.post('/land/document-categories', { label });\n"
         "        return response.data;\n"
         "    },\n"
         "\n"
         "    deleteDocument: async (docId) => {\n",
         "landService: get/add document categories")

# ======================================================================
# FolderPage.jsx
# ======================================================================
fol0 = read(FOLDER_JSX)
fol = fol0

fol = sub(fol,
          "    const fileInputRef = useRef(null);\n",
          "    const fileInputRef = useRef(null);\n"
          "    // fix136: document categories + the UPLOAD DOCUMENTS window\n"
          "    const [docCats, setDocCats] = useState([]);\n"
          "    const [uploadDraft, setUploadDraft] = useState(null); // { batch, files: [{ file, category }] }\n"
          "    const [newCatOpen, setNewCatOpen] = useState(false);\n"
          "    const [newCatName, setNewCatName] = useState('');\n"
          "    const [catBusy, setCatBusy] = useState(false);\n"
          "    const loadDocCats = useCallback(async () => { try { setDocCats(await landService.getDocumentCategories()); } catch { /* headings fall back to the raw code */ } }, []);\n"
          "    useEffect(() => { loadDocCats(); }, [loadDocCats]);\n",
          "folder: category state + loader")

fol = sub(fol,
          r'''const handleVaultAction = async (files) => { if (!files?.length) return; setCommitting(true); try { await landService.addExtraDocuments(id, files); await loadFolderData(); toast(files.length + ' document(s) uploaded', 'success', 3000); } catch { toast('INGESTION FAILED', 'error', 8000); } finally { setCommitting(false); } };''',
          r'''const handleVaultAction = (files) => { if (!files?.length) return; setUploadDraft({ batch: '', files: files.map(file => ({ file, category: '' })) }); };
    const closeUploadDraft = () => { if (committing) return; setUploadDraft(null); setNewCatOpen(false); setNewCatName(''); };
    const setBatchCategory = (code) => setUploadDraft(d => d && ({ batch: code, files: d.files.map(f => ({ ...f, category: code })) }));
    const setFileCategory = (i, code) => setUploadDraft(d => d && ({ ...d, files: d.files.map((f, j) => (j === i ? { ...f, category: code } : f)) }));
    const handleAddCategory = async () => {
        const name = newCatName.trim();
        if (name.length < 2 || catBusy) return;
        setCatBusy(true);
        try {
            const cat = await landService.addDocumentCategory(name);
            await loadDocCats();
            setNewCatName(''); setNewCatOpen(false);
            setUploadDraft(d => d && ({ ...d, batch: d.batch || cat.code, files: d.files.map(f => (f.category ? f : { ...f, category: cat.code })) }));
            toast('Category "' + cat.label + '" ready', 'success', 3000);
        } catch { toast('COULD NOT ADD CATEGORY', 'error', 6000); } finally { setCatBusy(false); }
    };
    const handleUploadConfirm = async () => {
        if (!uploadDraft || committing) return;
        if (uploadDraft.files.some(f => !f.category)) { toast('Pick a category for every file', 'warn', 4000); return; }
        const count = uploadDraft.files.length;
        setCommitting(true);
        try {
            await landService.addExtraDocuments(id, uploadDraft.files.map(f => f.file), uploadDraft.files.map(f => f.category));
            setUploadDraft(null); setNewCatOpen(false); setNewCatName('');
            await loadFolderData();
            toast(count + ' document(s) uploaded', 'success', 3000);
        } catch { toast('INGESTION FAILED', 'error', 8000); } finally { setCommitting(false); }
    };''',
          "folder: upload opens the category window; add-category + confirm handlers")

fol = sub(fol,
          "const docCount = (binder.documents || []).length;",
          r'''const docCount = (binder.documents || []).length;
    const UNCATEGORISED = '__NONE__';
    const catLabel = (code) => (docCats.find(c => c.code === code)?.label) || String(code).replace(/_/g, ' ');
    const docGroups = (() => {
        const groups = new Map();
        (binder.documents || []).forEach(d => {
            const key = d.category || (docCats.some(c => c.code === d.fileType) ? d.fileType : UNCATEGORISED);
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(d);
        });
        const rank = (k) => { if (k === UNCATEGORISED) return 9999; const i = docCats.findIndex(c => c.code === k); return i < 0 ? 9000 : i; };
        return [...groups.entries()].sort((a, b) => rank(a[0]) - rank(b[0]));
    })();''',
          "folder: group documents by category")

fol = sub(fol,
          "{binder.documents.map((doc, idx) => (<div key={idx} className={styles.docTag}>",
          "{docGroups.map(([cat, docs]) => (<React.Fragment key={cat}>"
          "<div className={styles.docGroupLabel}>{cat === UNCATEGORISED ? 'UNCATEGORISED' : catLabel(cat)}<span className={styles.docGroupCount}>{docs.length}</span></div>"
          "{docs.map((doc) => (<div key={doc.id} className={styles.docTag}>",
          "folder: documents tab group headings (open)")

fol = sub(fol,
          '<FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>}\n'
          "                            </div>))}</div>",
          '<FiTrash2 className={styles.redIcon} aria-hidden="true" /></button>}\n'
          "                            </div>))}</React.Fragment>))}</div>",
          "folder: documents tab group headings (close)")

fol = sub(fol,
          "<ConfirmModal state={confirmState} onAnswer={handleAnswer} />",
          r'''<HardwareModal isOpen={!!uploadDraft} onClose={closeUploadDraft} title="UPLOAD DOCUMENTS">
                {uploadDraft && (<>
                    <div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>CATEGORY FOR ALL {uploadDraft.files.length} FILE(S)</label>
                        <select className={modalStyles.modalInput} value={uploadDraft.batch} onChange={e => setBatchCategory(e.target.value)} aria-label="Category for all files">
                            <option value="">-- choose category --</option>
                            {docCats.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
                        </select></div>
                    <div className={styles.upFileList}>{uploadDraft.files.map((f, i) => (<div key={i} className={styles.upFileRow}>
                        <span className={styles.upFileName} title={f.file.name}>{f.file.name}</span>
                        <select className={`${modalStyles.modalInput} ${styles.upFileSelect}`} value={f.category} onChange={e => setFileCategory(i, e.target.value)} aria-label={'Category for ' + f.file.name}>
                            <option value="">-- category --</option>
                            {docCats.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
                        </select></div>))}</div>
                    {newCatOpen ? (<div className={modalStyles.modalField}><label className={modalStyles.modalLabel}>NEW CATEGORY NAME</label>
                        <input type="text" className={modalStyles.modalInput} value={newCatName} maxLength={120} placeholder="e.g. Survey Report" onChange={e => setNewCatName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') handleAddCategory(); }} />
                        <div className={styles.upCatActions}>
                            <button type="button" className={styles.addDocBtn} onClick={handleAddCategory} disabled={catBusy || newCatName.trim().length < 2}>SAVE CATEGORY</button>
                            <button type="button" className={styles.addDocBtn} onClick={() => { setNewCatOpen(false); setNewCatName(''); }}>CANCEL</button>
                        </div></div>)
                        : (<button type="button" className={styles.addDocBtn} onClick={() => setNewCatOpen(true)}>+ NEW CATEGORY</button>)}
                    <div className={modalStyles.modalFooter}>
                        <HardwareButton type="button" onClick={handleUploadConfirm} loading={committing} icon={FiUploadCloud}>UPLOAD</HardwareButton>
                    </div>
                </>)}
            </HardwareModal>
            <ConfirmModal state={confirmState} onAnswer={handleAnswer} />''',
          "folder: UPLOAD DOCUMENTS window")

# ======================================================================
# FolderPage.module.css
# ======================================================================
css0 = read(FOLDER_CSS)
css = css0

css = append_once(css, ".docGroupLabel", r'''
/* fix136: document category headings + the UPLOAD DOCUMENTS window */
.docGroupLabel{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:clamp(4px,0.6vw,8px);padding:0 2px;font-family:'Space Mono',monospace;font-weight:900;font-size:clamp(8px,0.85vw,10px);letter-spacing:1.5px;text-transform:uppercase;color:var(--orange);}
.docGroupLabel:first-child{margin-top:0;}
.docGroupCount{color:rgba(255,255,255,0.35);}
.upFileList{display:flex;flex-direction:column;gap:6px;max-height:clamp(140px,30vh,260px);overflow-y:auto;margin-bottom:8px;}
.upFileRow{display:flex;align-items:center;gap:8px;min-width:0;}
.upFileName{flex:1 1 50%;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:rgba(255,255,255,0.8);font-size:12px;}
.upFileSelect{flex:1 1 50%;min-width:0;}
.upCatActions{display:flex;gap:8px;}
.upCatActions .addDocBtn{flex:1;}
''', "folder css: category headings + upload window")

# ======================================================================
# auditCatalog.js
# ======================================================================
aud0 = read(AUDIT_CATALOG_JS)
aud = aud0

aud = sub(aud,
          "{ code: 'DOCUMENT_DELETED',  label: 'Document deleted',  severity: 'high' },",
          "{ code: 'DOCUMENT_DELETED',  label: 'Document deleted',  severity: 'high' },\n"
          "            { code: 'DOCUMENT_CATEGORY_ADDED', label: 'Document category added', severity: 'low' },",
          "audit catalog: DOCUMENT_CATEGORY_ADDED")

# ======================================================================
# write (atomic) + build gate + commit
# ======================================================================
if MISSING:
    print("")
    print("FAIL: " + str(len(MISSING)) + " patch(es) MISSING -- nothing written, nothing committed:")
    for m in MISSING:
        print("  - " + m)
    print("The source text differs from what this script expects (or was edited since fix135).")
    sys.exit(1)

changed = False
for path, text, label in NEW_FILES:
    write(path, text)
    print("created: " + label)
    changed = True

for path, before, after, label in [
    (DOC_MODEL_JAVA, doc0, doc, "erp-backend/.../model/ProjectDocument.java"),
    (LAND_SERVICE_JAVA, svc0, svc, "erp-backend/.../service/LandService.java"),
    (LAND_CTRL_JAVA, ctl0, ctl, "erp-backend/.../controller/LandController.java"),
    (LAND_SVC_JS, js0, js, "erp-frontend/src/services/landService.js"),
    (FOLDER_JSX, fol0, fol, "erp-frontend/src/pages/DigitalFolder/FolderPage.jsx"),
    (FOLDER_CSS, css0, css, "erp-frontend/src/pages/DigitalFolder/FolderPage.module.css"),
    (AUDIT_CATALOG_JS, aud0, aud, "erp-frontend/src/pages/Audit/auditCatalog.js"),
]:
    if after != before:
        write(path, after)
        print("written: " + label)
        changed = True
if not changed:
    print("note: nothing changed -- fix136 already applied")

# build gate (fix76)
if os.path.isdir(os.path.join(FRONTEND, "node_modules")):
    build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, capture_output=True, text=True, shell=(os.name == "nt"))
    print(build.stdout[-3000:])
    if build.returncode != 0:
        print(build.stderr[-3000:])
        print("FAIL: build is red -- aborting, nothing committed")
        sys.exit(1)
    print("build OK")
else:
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
git("commit", "-m", "fix136: document categories -- upload window picks a category per batch or per file, built-in categories (application forms, offer letters, forwarding letters, deed plan, copy of title, payment receipts), + NEW CATEGORY for secretary/manager/admin/director, Documents tab grouped by category")
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