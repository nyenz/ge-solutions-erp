import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"OK: {path}")

path = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'
content = read(path)
content = content.replace(
    'const handleOpenDoc = (filePath, fileName) => {',
    'const handleOpenDoc = (filePath) => {'
)
write(path, content)