import os

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("OK")

path = 'erp-frontend/src/pages/Intake/IntakePage.jsx'
content = read(path)

# Fix isDirty useMemo that still references notesList
content = content.replace(
    """    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        notesList.length > 0 ||
        noteText.trim() !== '',
    [plotNumber, owners, totalCost, fileQueue, notesList, noteText]);""",
    """    const isDirty = React.useMemo(() =>
        plotNumber.trim() !== '' ||
        owners.some(o => o.fullName.trim() !== '' || o.phone.trim() !== '') ||
        totalCost !== '' ||
        fileQueue.length > 0 ||
        noteText.trim() !== '',
    [plotNumber, owners, totalCost, fileQueue, noteText]);"""
)

write(path, content)