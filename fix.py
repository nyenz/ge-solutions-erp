import os
import sys
import subprocess

# ============================================================================
# BUILD CHECK + GIT
# (the actual Intake/Folder edits are already in place -- this just verifies
# the build is green before committing and pushing)
# ============================================================================
ROOT = os.getcwd()

frontend = os.path.join(ROOT, 'erp-frontend')
if os.path.isdir(os.path.join(frontend, 'node_modules')):
    print('running npm run build sanity check...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=frontend, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print('')
        print('BUILD RED -- nothing was committed or pushed.')
        sys.exit(1)
    print('build OK')
else:
    print('(erp-frontend/node_modules not installed -- skipping build check)')

print('')
print('git: staging, committing, pushing...')
MSG = ('fix: intake/folder stage flow -- first stage locked required, last '
       'stage blocked at intake, unchecked stages now saved as pending, '
       'folder page stage edits gated on edit mode, TITLE READY/UNDO button '
       'drives the last stage tick together with the title panel')
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', MSG])
subprocess.run(['git', 'push'])
print('')
print('Done. Wait for the green tick, then walk both pages and tell me what still fights you.')