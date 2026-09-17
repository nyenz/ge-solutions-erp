#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 GOLDEN SEED ERP  --  fix.py  (git commit + push helper)
================================================================================

WHAT THIS IS

  A small, separate script that does ONLY git operations: stage, commit, push.
  It does not touch any source file. Run the patcher (the earlier fix.py, or
  whatever produced your current working tree) first, confirm the app still
  builds, THEN run this one to get it onto GitHub.

  This is deliberately its own file rather than folded into the patcher: a
  script that edits source AND pushes to git in one run is a script you cannot
  safely dry-run, and a bad patch you already pushed is much more annoying to
  undo than a bad patch sitting locally.

HOW TO RUN

      python3 fix.py --dry-run          # show exactly what would be committed
                                         # and the exact push command, do nothing
      python3 fix.py                    # stage everything, commit, push
      python3 fix.py -m "custom message"
      python3 fix.py --no-verify-build  # skip the npm build sanity check

WHAT IT CHECKS BEFORE TOUCHING GIT

  1. You are inside a git repository.
  2. There is a configured remote (`origin` by default, or --remote).
  3. There is something to commit at all (refuses to make an empty commit).
  4. If erp-frontend/package.json exists and node_modules is present, it runs
     `npm run build` and refuses to commit on a red build -- unless you pass
     --no-verify-build. This is the same check the earlier fix.py told you to
     run by hand; doing it here means a broken build never reaches GitHub by
     accident.
  5. It does NOT force-push, ever. If the remote has moved ahead of your local
     branch, the push will fail on purpose and this script tells you to pull
     first rather than guessing at a resolution.

WHAT IT DOES

  1. git add -A
  2. git commit -m "<message>"   (default message summarises file counts by
     top-level area -- frontend / backend / other -- not a placeholder)
  3. git push <remote> <current-branch>

SAFETY

  * --dry-run shows the exact commit message and the exact push command
    without running either.
  * Refuses to run with a merge/rebase/cherry-pick sitting mid-flight --
    checks .git/MERGE_HEAD, .git/rebase-apply, .git/rebase-merge,
    .git/CHERRY_PICK_HEAD first, since committing on top of one of those is
    how you get a confusing history.
  * Prints the full `git status --short` it is about to commit before it
    commits, every time, dry-run or not.
  * Never force-pushes and never rewrites history.
--------------------------------------------------------------------------------
"""

import argparse
import os
import subprocess
import sys


# ----------------------------------------------------------------------------
# small git helpers
# ----------------------------------------------------------------------------

def run(cmd, check=True, capture=True):
    """Run a command, return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        out = (result.stdout or "") + (result.stderr or "")
        sys.exit("ERROR running " + " ".join(cmd) + ":\n" + out.strip())
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def in_git_repo():
    code, _out, _err = run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
    return code == 0


def repo_root():
    _code, out, _err = run(["git", "rev-parse", "--show-toplevel"])
    return out


def current_branch():
    _code, out, _err = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if out == "HEAD":
        sys.exit(
            "ERROR: you are in a detached HEAD state (not on a branch).\n"
            "       Check out a branch before running this: git checkout main"
        )
    return out


def remote_exists(remote):
    _code, out, _err = run(["git", "remote"], check=False)
    return remote in out.splitlines()


def ahead_of_upstream(remote, branch):
    """How many local commits exist that <remote>/<branch> does not have yet
    -- distinct from an unclean working tree. This matters after resolving a
    rebase or merge conflict by hand: the working tree is clean (nothing left
    to stage) but a real commit is sitting there unpushed, and a script whose
    whole job is "get my work onto GitHub" should not call that "nothing to
    do".

    Deliberately does NOT rely on `@{u}` / the branch's configured upstream:
    a branch pushed with plain `git push origin main` (no -u) has no tracking
    branch set even though the remote ref exists and the comparison is
    perfectly well-defined. Comparing directly against
    refs/remotes/<remote>/<branch> works whether or not tracking was ever
    configured.

    If that remote-tracking ref does not exist locally yet (a fresh clone
    that has not fetched, or a branch that has genuinely never been pushed),
    a quiet fetch is attempted to get an accurate answer. If even that fails
    (no network, unreachable remote), this returns 1 rather than 0 -- the
    conservative direction for a script whose job is to push: "I don't know,
    so try" beats "I don't know, so silently skip your work"."""
    ref = "refs/remotes/" + remote + "/" + branch

    code, _out, _err = run(["git", "rev-parse", "--verify", "--quiet", ref], check=False)
    if code != 0:
        run(["git", "fetch", "--quiet", remote, branch], check=False)
        code, _out, _err = run(["git", "rev-parse", "--verify", "--quiet", ref], check=False)
        if code != 0:
            return 1

    code, out, _err = run(["git", "rev-list", "--count", ref + "..HEAD"], check=False)
    if code != 0:
        return 1
    try:
        return int(out)
    except ValueError:
        return 1


def mid_operation(git_dir):
    """True if a merge/rebase/cherry-pick is in progress -- committing on top
    of one of those silently is how a confusing history happens."""
    markers = [
        os.path.join(git_dir, "MERGE_HEAD"),
        os.path.join(git_dir, "rebase-apply"),
        os.path.join(git_dir, "rebase-merge"),
        os.path.join(git_dir, "CHERRY_PICK_HEAD"),
    ]
    return [m for m in markers if os.path.exists(m)]


def porcelain_lines():
    """Raw `git status --porcelain` output, one entry per line, with each
    line's LEADING characters intact.

    NOTE: this deliberately does not go through run(), whose generic .strip()
    on the whole captured blob eats the leading space off only the FIRST
    line (porcelain's status column is column-aligned with a literal space
    for "no change on this side", e.g. " M path" for a worktree-only edit).
    Stripping the whole blob silently turned " M fix.py" into "M fix.py" and
    then a fixed-width slice read the wrong three characters -- "fix.py"
    became "ix.py" in the commit-message summary. Individual lines are still
    rstripped for the trailing newline, which is safe.
    """
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit("ERROR running git status --porcelain:\n" + (result.stderr or "").strip())
    return [l for l in result.stdout.split("\n") if l]


def has_changes():
    return bool(porcelain_lines())


def status_short():
    _code, out, _err = run(["git", "status", "--short"])
    return out


def summarise_changes():
    """Build a default commit message from what actually changed, grouped by
    top-level area, rather than a fixed placeholder string."""
    areas = {}
    for line in porcelain_lines():
        # porcelain format is a fixed 2-character status column, then a
        # space, then the path (or "orig -> new" for a rename) -- e.g.
        # " M erp-frontend/src/App.jsx" or "?? fix.py".
        path = line[3:].split(" -> ")[-1].strip()
        top = path.split("/", 1)[0] if "/" in path else path
        areas[top] = areas.get(top, 0) + 1

    if not areas:
        return "Update"

    parts = [str(n) + " file" + ("s" if n != 1 else "") + " in " + area
             for area, n in sorted(areas.items())]
    total = sum(areas.values())
    header = "Update " + str(total) + " file" + ("s" if total != 1 else "")
    return header + "\n\n" + "\n".join("- " + p for p in parts)


# ----------------------------------------------------------------------------
# build sanity check
# ----------------------------------------------------------------------------

def verify_frontend_build(root):
    frontend = os.path.join(root, "erp-frontend")
    pkg = os.path.join(frontend, "package.json")
    modules = os.path.join(frontend, "node_modules")

    if not os.path.isfile(pkg):
        print("  (no erp-frontend/package.json found -- skipping build check)")
        return True
    if not os.path.isdir(modules):
        print("  (erp-frontend/node_modules not installed -- skipping build check)")
        print("   run `npm install` in erp-frontend/ if you want this check active)")
        return True

    print("  running `npm run build` in erp-frontend/ ...")
    result = subprocess.run(
        ["npm", "run", "build"], cwd=frontend,
        capture_output=True, text=True, shell=(os.name == "nt"),
    )
    if result.returncode != 0:
        print("")
        print((result.stdout or "")[-2000:])
        print((result.stderr or "")[-2000:])
        return False
    print("  build OK")
    return True


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Stage, commit and push the current working tree.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true",
                     help="show what would be committed and pushed, do nothing")
    ap.add_argument("-m", "--message", default=None,
                     help="commit message (default: auto-summarised from changed files)")
    ap.add_argument("--remote", default="origin",
                     help="git remote to push to (default: origin)")
    ap.add_argument("--no-verify-build", action="store_true",
                     help="skip the npm build sanity check before committing")
    args = ap.parse_args()

    if not in_git_repo():
        sys.exit("ERROR: not inside a git repository.")

    root = repo_root()
    os.chdir(root)

    blockers = mid_operation(os.path.join(root, ".git"))
    if blockers:
        sys.exit(
            "ERROR: a merge, rebase or cherry-pick looks unfinished:\n"
            + "\n".join("    " + b for b in blockers)
            + "\nResolve or abort that first (git status will tell you how),"
              " then re-run this."
        )

    branch = current_branch()

    print("=" * 72)
    print("  GOLDEN SEED  git commit + push  " + ("(DRY RUN)" if args.dry_run else ""))
    print("=" * 72)
    print("  repo:   " + root)
    print("  branch: " + branch)
    print("  remote: " + args.remote + ("  (configured)" if remote_exists(args.remote) else "  ** NOT CONFIGURED **"))
    print("")

    def do_push():
        push_cmd = ["git", "push", args.remote, branch]
        if args.dry_run:
            print("Would run:")
            print("    " + " ".join(push_cmd))
            print("")
            print("Dry run -- nothing pushed.")
            return 0
        print("Running:")
        print("    " + " ".join(push_cmd))
        print("")
        code, out, err = run(push_cmd, check=False)
        if code != 0:
            print("")
            print("Push failed:")
            print("    " + (out + "\n" + err).strip())
            if "rejected" in err.lower() or "non-fast-forward" in err.lower():
                print("")
                print("  The remote has commits you don't have locally. Pull first:")
                print("      git pull --rebase " + args.remote + " " + branch)
                print("  then re-run this script.")
            return 1
        print("Pushed to " + args.remote + "/" + branch + ".")
        return 0

    if not has_changes():
        ahead = ahead_of_upstream(args.remote, branch)
        if ahead <= 0:
            print("Nothing to commit and nothing unpushed -- working tree matches")
            print(args.remote + "/" + branch + ". Nothing to do.")
            return 0

        # A clean working tree with unpushed commits happens after resolving a
        # rebase or merge conflict by hand: the commit already exists, it is
        # just sitting local. The job here is "get my work onto GitHub", so
        # that counts as something to do, not nothing.
        print("Working tree is clean, but " + str(ahead) + " local commit"
              + ("s" if ahead != 1 else "") + " on " + branch
              + " have not been pushed yet.")
        print("")
        if not remote_exists(args.remote):
            sys.exit(
                "ERROR: remote '" + args.remote + "' is not configured.\n"
                "       git remote add " + args.remote + " <your-repo-url>"
            )
        return do_push()

    print("Changes to be committed:")
    print(status_short())
    print("")

    message = args.message or summarise_changes()
    print("Commit message:")
    for line in message.splitlines():
        print("    " + line)
    print("")

    if not args.no_verify_build:
        print("Build check:")
        ok = verify_frontend_build(root)
        print("")
        if not ok:
            sys.exit(
                "ERROR: erp-frontend build failed. Nothing was committed or pushed.\n"
                "       Fix the build, or re-run with --no-verify-build to skip this\n"
                "       check (not recommended)."
            )

    if not remote_exists(args.remote):
        sys.exit(
            "ERROR: remote '" + args.remote + "' is not configured.\n"
            "       git remote add " + args.remote + " <your-repo-url>"
        )

    print("Would run:" if args.dry_run else "Running:")
    print("    git add -A")
    print("    git commit -m \"" + message.splitlines()[0] + "\" ...")
    print("    git push " + args.remote + " " + branch)

    if args.dry_run:
        print("")
        print("Dry run -- nothing staged, committed, or pushed.")
        return 0

    print("")
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", message])
    print("")
    result = do_push()
    if result != 0:
        print("  (the commit above succeeded locally either way -- re-running")
        print("   this script after resolving the push problem will just push,")
        print("   since there will be nothing left to commit)")
    return result


if __name__ == "__main__":
    sys.exit(main())