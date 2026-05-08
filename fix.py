import os

path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/service/ReportService.java"

with open(path, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

content = content.replace("\r\n", "\n")

# Remove the bad ClientRepository import
content = content.replace(
    "import com.gesolutions.erp.modules.client.repository.ClientRepository;\n",
    ""
)

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("OK: Removed bad ClientRepository import")