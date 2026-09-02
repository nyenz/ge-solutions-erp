# fix.py — REPAIR: fix broken import paths + rebuild folderPortalService header
import os, re, sys, shutil, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FE = os.path.join(ROOT, "erp-frontend", "src")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()
def write(p, c):
    with open(p, "w", encoding="utf-8") as f: f.write(c)
def find(name, base):
    for r, d, fs in os.walk(base):
        if name in fs: return os.path.join(r, name)
    return None

folder_jsx = find("FolderPage.jsx", FE)
land_svc   = find("landService.js", FE) or find("landService.jsx", FE)
useauth    = find("useAuth.js", FE) or find("useAuth.jsx", FE)
if not folder_jsx or not land_svc:
    print("ABORT: FolderPage.jsx or landService not found."); sys.exit(1)

PAGE_DIR = os.path.dirname(folder_jsx)
SVC_DIR  = os.path.dirname(land_svc)
svc_path = os.path.join(SVC_DIR, "folderPortalService.js")

def rel_import(from_dir, to_file):
    d = os.path.dirname(to_file)
    name = os.path.splitext(os.path.basename(to_file))[0]
    rel = os.path.relpath(d, from_dir).replace(os.sep, "/")
    if not rel.startswith("."): rel = "./" + rel
    return (rel.rstrip("/") + "/" + name) if rel != "." else "./" + name

# ---- 1) Rebuild folderPortalService.js with a CORRECT header (imports + api instance) ----
ls = read(land_svc)
m = re.search(r"([\s\S]*?)\bexport\b", ls)      # everything BEFORE first export
header = m.group(1) if m else ""
inst_m = re.search(r"\b([A-Za-z_$][\w$]*)\.(?:get|post|put|delete)\(", ls)
inst = inst_m.group(1) if inst_m else "api"
if not re.search(r"\b" + inst + r"\b", header):
    header += ("\nimport axios from 'axios';\n"
               "const " + inst + " = axios.create({ baseURL: '/api/v1' });\n"
               + inst + ".interceptors.request.use(c => { const t = localStorage.getItem('token'); if (t) c.headers.Authorization = 'Bearer ' + t; return c; });\n")

body = """
export const folderPortalService = {
  getReceivable: (id) => %s.get(`/land/portal/${id}/receivable`).then(r => r.data),
  getPortfolio:  (id) => %s.get(`/land/portal/${id}/portfolio`).then(r => r.data),
  enter:    (id) => %s.post(`/land/portal/${id}/receivable/enter`).then(r => r.data),
  exit: (id, action) => %s.post(`/land/portal/${id}/receivable/exit`, { action }).then(r => r.data),
  settings: (id, payload) => %s.post(`/land/portal/${id}/receivable/settings`, payload).then(r => r.data),
};
export default folderPortalService;
""" % (inst, inst, inst, inst, inst)
write(svc_path, header + body)
print("REPAIRED: folderPortalService.js (instance='" + inst + "')")

# ---- 2) Fix the broken import lines in FolderPage.jsx ----
src = read(folder_jsx)
spec_svc = rel_import(PAGE_DIR, svc_path)
src, n1 = re.subn(r"import\s+folderPortalService\s+from\s+['\"][^'\"]*['\"];",
                  "import folderPortalService from '%s';" % spec_svc, src)
n2 = 0
spec_auth = "n/a"
if useauth:
    spec_auth = rel_import(PAGE_DIR, useauth)
    src, n2 = re.subn(r"import\s+\{\s*useAuth\s*\}\s+from\s+['\"][^'\"]*['\"];",
                      "import { useAuth } from '%s';" % spec_auth, src)
write(folder_jsx, src)
print("REPAIRED imports: svc=%s (n=%d), useAuth=%s (n=%d)" % (spec_svc, n1, spec_auth, n2))

# ---- 3) commit + push ----
try:
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-m", "repair: fix folderPortalService import path + api instance"], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print("GIT: committed and pushed.")
except Exception as e:
    print("GIT WARN:", e)
print("DONE.")