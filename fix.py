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

def patch(path, old, new, label):
    content = read(path)
    if old in content:
        write(path, content.replace(old, new, 1))
        print(f"OK       {label}")
    else:
        print(f"MISSING  {label} -- snippet not found")

INTAKE = 'erp-frontend/src/pages/Intake/IntakePage.jsx'
INTAKE_CSS = 'erp-frontend/src/pages/Intake/IntakePage.module.css'

# FIX 1 -- Replace the fileDisplay block (use a shorter unique anchor)
patch(INTAKE,
    '''                                    <div className={styles.fileDisplay}>
                                        {fileQueue.length === 0 ? (
                                            <div className={styles.emptyState}>
                                                <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                                <span>No files selected</span>
                                            </div>
                                        ) : fileQueue.map((f, i) => {
                                            const isPDF = f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf');
                                            const previewUrl = !isPDF ? URL.createObjectURL(f) : null;
                                            return (
                                            <div key={i} className={styles.fileTag}>
                                                <a
                                                    href={isPDF ? '#' : previewUrl}
                                                    target={isPDF ? undefined : '_blank'}
                                                    rel="noreferrer"
                                                    className={styles.fileClickable}
                                                    onClick={isPDF ? (e) => {
                                                        e.preventDefault();
                                                        const url = URL.createObjectURL(f);
                                                        window.open(url, '_blank');
                                                        setTimeout(() => URL.revokeObjectURL(url), 5000);
                                                    } : undefined}
                                                    title={`Open ${f.name}`}
                                                >
                                                    <span className={styles.fileName}>{isPDF ? '\\u{1F4C4} ' : '\\u{1F5BC} '}{f.name}</span>
                                                </a>
                                                <button type="button" className={styles.removeFile}
                                                    onClick={() => setFileQueue(prev => prev.filter((_,j) => j !== i))}>
                                                    <FiX />
                                                </button>
                                            </div>
                                            );
                                        })}
                                        </div>''',
    '''                                    <div className={styles.fileDisplay}>
                                        {fileQueue.length === 0 && (
                                            <div className={styles.emptyState}>
                                                <FiUploadCloud className={styles.emptyIcon} aria-hidden="true" />
                                                <span>No files selected</span>
                                            </div>
                                        )}
                                        {fileQueue.map((f, i) => {
                                            const isPDF = f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf');
                                            return (
                                                <div key={f.name + i} className={styles.fileTag}>
                                                    <button
                                                        type="button"
                                                        className={styles.fileClickable}
                                                        onClick={() => {
                                                            const url = URL.createObjectURL(f);
                                                            window.open(url, '_blank');
                                                            setTimeout(() => URL.revokeObjectURL(url), 5000);
                                                        }}
                                                        title={`Open ${f.name}`}
                                                    >
                                                        <span className={styles.fileName}>{isPDF ? '\\u{1F4C4} ' : '\\u{1F5BC} '}{f.name}</span>
                                                    </button>
                                                    <button type="button" className={styles.removeFile}
                                                        onClick={() => setFileQueue(prev => prev.filter((_, j) => j !== i))}
                                                        aria-label={`Remove ${f.name}`}>
                                                        <FiX />
                                                    </button>
                                                </div>
                                            );
                                        })}
                                        </div>''',
    "IntakePage fileDisplay -- fix rendering, button instead of anchor"
)

# FIX 2 -- CSS: fix fileClickable to work as a button
patch(INTAKE_CSS,
    '''.fileClickable {
    display: flex; align-items: center; gap: clamp(6px, 0.8vw, 8px);
    flex: 1; background: none; border: none; cursor: pointer;
    /* White text -- sits on dark file display */
    color: rgba(255, 255, 255, 0.75);
    font-size: clamp(10px, 1vw, 11px); font-weight: 800;
    font-family: 'Space Mono', monospace; min-width: 0; padding: 0;
    transition: color 0.15s;
}''',
    '''.fileClickable {
    display: flex; align-items: center; gap: clamp(6px, 0.8vw, 8px);
    flex: 1; background: none; border: none; cursor: pointer;
    color: rgba(255, 255, 255, 0.75);
    font-size: clamp(10px, 1vw, 11px); font-weight: 800;
    font-family: 'Space Mono', monospace; min-width: 0;
    padding: clamp(3px, 0.4vw, 5px) 0;
    text-align: left;
    transition: color 0.15s;
}''',
    "IntakePage.module.css -- fileClickable padding and text-align"
)

print()
print("--- Done ---")
print("Run: git add -A && git commit -m 'fix: file upload display in IntakePage' && git push")