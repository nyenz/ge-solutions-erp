# PATH: fix.py
# BUG-FIX: FolderPage.jsx payment modal title crashes for titleless
# (folder-stage) projects. `project.landTitle.plotNumber` has no null
# check -- the moment staff click PAYMENT on a project with no title
# yet, this throws. Also swaps the em-dash for a plain hyphen per
# Section 3's ASCII-only rule for fix.py-touched strings.
#
# NOTE: the READY_FOR_TITLING filter button fix is already live in the
# repo (added by the last fix.py you ran) -- this script does not touch
# it, to avoid a duplicate/no-op patch.

import subprocess

def read(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def patch(path, old, new, label):
    content = read(path)
    count = content.count(old)
    if count == 1:
        content = content.replace(old, new)
        write(path, content)
        print('OK: ' + label)
    elif count == 0:
        print('MISSING (not found): ' + label)
    else:
        print('MISSING (found ' + str(count) + ' times, expected 1): ' + label)


FP = 'erp-frontend/src/pages/DigitalFolder/FolderPage.jsx'

patch(FP,
'''            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={`RECORD PAYMENT \u2014 ${project.landTitle.plotNumber}`}>''',
'''            <HardwareModal isOpen={payModal.open} onClose={() => { setPayModal({ open: false }); setPayType('TITLE'); setPayAmount(''); setPayNotes(''); }} title={`RECORD PAYMENT - ${project.landTitle?.plotNumber || project.projectIndex || 'FOLDER'}`}>''',
'FolderPage.jsx payment modal title: null-safe plot number (was crashing on titleless projects)')

subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m',
    'Bug-fix: FolderPage payment modal title crashes on titleless projects '
    '(unguarded project.landTitle.plotNumber)'])
subprocess.run(['git', 'push'])