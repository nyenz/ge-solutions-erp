import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print('$ ' + ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=False)


run(['git', 'add', '-A'])
run(['git', 'commit', '-m',
     'fix66: tooltip system app-wide, Expenses page design+function overhaul, '
     'shared toast/confirm, loading-state contrast pass'])
run(['git', 'push'])