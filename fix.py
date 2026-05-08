import os

def patch_file(path, old_str, new_str, label):
    if not os.path.exists(path):
        print(f"  MISSING FILE: {path}")
        return
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    content = content.replace("\r\n", "\n")
    old_str = old_str.replace("\r\n", "\n")
    if old_str in content:
        content = content.replace(old_str, new_str, 1)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"  OK: {label}")
    else:
        print(f"  SKIP/NOT FOUND: {label}")

path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java"

with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

content = content.replace("\r\n", "\n")

# Fix line 293: smart quotes in .replace call
content = content.replace(
    'pay.getNotes().replace(",", ";").replace(\u201c, \u2018\')',
    'pay.getNotes().replace(",", ";")'
)
content = content.replace(
    'pay.getNotes().replace(",", ";").replace(\u201c, \'\')',
    'pay.getNotes().replace(",", ";")'
)

# Fix line 309: smart quotes in .append calls
content = content.replace(
    '               .append(\u201c\u201d).append(notes).append(\u201c\u201d).append(NEW_LINE);',
    '               .append("\\"").append(notes).append("\\"").append(NEW_LINE);'
)
content = content.replace(
    '               .append(\u201c).append(notes).append(\u201d).append(NEW_LINE);',
    '               .append("\\"").append(notes).append("\\"").append(NEW_LINE);'
)

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("Done. Check ReportService.java - smart quotes replaced.")