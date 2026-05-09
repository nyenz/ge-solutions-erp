import os

path = "erp-frontend/src/pages/Ledger/LedgerPage.jsx"
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
content = content.replace(
    "        } catch (err) {\n            setLoadError(true);",
    "        } catch {\n            setLoadError(true);"
)
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("OK")