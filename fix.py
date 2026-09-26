#!/usr/bin/env python3
# PATH: fix.py
# GOLDEN SEED -- fix105: close the three unclosed CSS blocks that fix104
# left open in Header.module.css (.header, .bellIcon, .badge). Each had an
# opening brace but no closing brace, breaking the PostCSS build.
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HEADER_CSS = os.path.join(ROOT, 'erp-frontend', 'src', 'components', 'layout', 'Header.module.css')


def read(p):
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


css = read(HEADER_CSS)

# The three rules fix104 inserted without closing braces:
# .header { ... (no })
# .bellIcon { ... (no })
# .badge { ... (no })

# Pattern: rule opens with { but the next non-whitespace is /* or . or @
# instead of a closing }. We insert } before the next comment or rule.
broken_patterns = [
    (r'(\.header\s*\{[^\}]+?)(\s*(?:/\*|\.header|\.headerLeft|\.headerRight|\.sidebarToggle))',
     r'\1}\2',
     '.header block'),
    (r'(\.bellIcon\s*\{[^\}]+?)(\s*(?:/\*|\.activeSensor))',
     r'\1}\2',
     '.bellIcon block'),
    (r'(\.badge\s*\{[^\}]+?)(\s*(?:/\*|\.userCard))',
     r'\1}\2',
     '.badge block'),
]

for pattern, replacement, label in broken_patterns:
    m = re.search(pattern, css, re.S)
    if m:
        css = re.sub(pattern, replacement, css, count=1, flags=re.S)
        print('patched: closed ' + label)
    else:
        # Try a simpler fix: if the rule exists and ends without }, add }
        rule_pat = re.compile(r'(' + pattern.split(r'\s*\{')[0] + r'\s*\{[^}]+)')
        m2 = rule_pat.search(css)
        if m2:
            old = m2.group(1)
            new = old + '\n}'
            css = css.replace(old, new, 1)
            print('patched: appended } to ' + label)
        else:
            print('note: ' + label + ' not found or already closed')

write(HEADER_CSS, css)
print('written: ' + os.path.relpath(HEADER_CSS, ROOT))


def git(*args):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout or '').strip()
    if out:
        print(out)
    if r.returncode != 0:
        print('GIT FAIL: ' + (r.stderr or '').strip())
        sys.exit(1)
    return r


ident = subprocess.run(['git', 'config', 'user.email'], cwd=ROOT, capture_output=True, text=True)
if not (ident.stdout or '').strip():
    git('config', 'user.name', 'nyenz')
    git('config', 'user.email', 'nyenz@users.noreply.github.com')

git('add', '-A')
git('commit', '-m', 'fix105: close unclosed CSS blocks in Header.module.css (.header, .bellIcon, .badge)')
push = subprocess.run(['git', 'push'], cwd=ROOT, capture_output=True, text=True)
if push.returncode != 0:
    git('push', 'origin', 'HEAD:main')
print('fix105 done: patched, committed and pushed to main.')