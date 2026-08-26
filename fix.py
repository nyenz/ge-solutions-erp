#!/usr/bin/env bash
#
# git_push.sh -- stage, commit, and push whatever fix.py (or anything
# else) changed in this repo. Run it from the repo root:
#
#   bash git_push.sh
#   bash git_push.sh "custom commit message"
#
# If no message is given, a default one describing the intake-form
# fix is used.

set -e  # stop on first error, don't push a half-done commit

DEFAULT_MSG="fix: finish removing Volume/Folio/InstrumentNo/PhysicalBoxNumber/SurveyDate from intake, red cancel btn, stage add fallback, shared BackToTopButton, required title fields, 2-button unsaved modal, storage fee default, read-only date started"
MSG="${1:-$DEFAULT_MSG}"

echo "== git status (before) =="
git status --short

# Bail out cleanly if there's nothing to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "Nothing to commit -- working tree is clean."
    exit 0
fi

echo
echo "== staging all changes =="
git add -A

echo
echo "== committing =="
git commit -m "$MSG"

echo
echo "== pushing =="
git push

echo
echo "== done =="
git log -1 --oneline