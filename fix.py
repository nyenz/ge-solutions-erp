import subprocess
import os
import re
import base64
import urllib.request
import urllib.error
import json

TARGET = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java"
GITHUB_PATH = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/repository/PaymentRecordRepository.java"

FALLBACK_JAVA = """\
package com.gesolutions.erp.modules.land.repository;

import com.gesolutions.erp.modules.land.model.PaymentRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PaymentRecordRepository extends JpaRepository<PaymentRecord, Long> {

    List<PaymentRecord> findByPlotId(Long plotId);

    List<PaymentRecord> findByPlotIdOrderByPaymentDateDesc(Long plotId);

    @Query("SELECT SUM(p.amount) FROM PaymentRecord p WHERE p.plotId = :plotId")
    Double sumAmountByPlotId(@Param("plotId") Long plotId);
}
"""


def get_repo_info():
    """Extract owner/repo from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True
        )
        url = result.stdout.strip()
        m = re.search(r'github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$', url)
        if m:
            return m.group(1), m.group(2)
    except Exception as e:
        print(f"[git remote] {e}")
    return None, None


def get_github_token():
    """Try to find a GitHub token from common locations."""
    for var in ("GH_TOKEN", "GITHUB_TOKEN"):
        val = os.environ.get(var)
        if val:
            return val
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, check=True
        )
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=5
        )
        m = re.search(r'password=(.+)', result.stdout)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


def fetch_from_github(owner, repo, token):
    """Fetch file content from GitHub API, searching commit history for clean version."""
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "fix-script"}
    if token:
        headers["Authorization"] = f"token {token}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{GITHUB_PATH}"
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            content = base64.b64decode(data["content"]).decode("utf-8")
            if "package com.gesolutions" in content and "interface PaymentRecordRepository" in content:
                print(f"[github api] Fetched clean file from HEAD ({data.get('sha', '')[:7]})")
                return content
            else:
                print("[github api] HEAD version appears corrupted, searching commit history...")
    except urllib.error.HTTPError as e:
        print(f"[github api] HEAD fetch failed: {e.code} {e.reason}")
    except Exception as e:
        print(f"[github api] HEAD fetch error: {e}")

    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?path={GITHUB_PATH}&per_page=30"
    try:
        req = urllib.request.Request(commits_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            commits = json.loads(resp.read())
            for commit in commits:
                sha = commit["sha"]
                file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{GITHUB_PATH}?ref={sha}"
                try:
                    req2 = urllib.request.Request(file_url, headers=headers)
                    with urllib.request.urlopen(req2, timeout=10) as resp2:
                        fdata = json.loads(resp2.read())
                        content = base64.b64decode(fdata["content"]).decode("utf-8")
                        if ("package com.gesolutions" in content and
                                "interface PaymentRecordRepository" in content and
                                "def " not in content and
                                "import os" not in content):
                            print(f"[github api] Found clean version at commit {sha[:7]}")
                            return content
                except Exception:
                    continue
    except Exception as e:
        print(f"[github api] Commit history search failed: {e}")

    return None


def try_git_show():
    """Try to restore from local git history."""
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "--", TARGET],
            capture_output=True, text=True, check=True
        )
        for line in log.stdout.strip().splitlines():
            if not line.strip():
                continue
            commit_hash = line.split()[0]
            show = subprocess.run(
                ["git", "show", f"{commit_hash}:{TARGET}"],
                capture_output=True, text=True
            )
            content = show.stdout
            if ("package com.gesolutions" in content and
                    "interface PaymentRecordRepository" in content and
                    "def " not in content and
                    "import os" not in content):
                print(f"[git show] Found clean version at {commit_hash}")
                return content
    except Exception as e:
        print(f"[git show] {e}")
    return None


def adapt_fallback():
    """Adapt fallback content by reading the actual entity file."""
    global FALLBACK_JAVA
    entity_path = "erp-backend/src/main/java/com/gesolutions/erp/modules/land/model/PaymentRecord.java"
    try:
        with open(entity_path, "r", encoding="utf-8") as f:
            src = f.read()
        fields = re.findall(r'private\s+\S+\s+(\w+)\s*;', src)
        print(f"[entity] Fields detected: {fields}")

        has_plot_id_field = bool(re.search(r'private\s+Long\s+plotId\s*;', src))
        has_plot_obj = bool(re.search(r'private\s+\w*[Pp]lot\w*\s+plot\s*;', src))

        if has_plot_obj and not has_plot_id_field:
            FALLBACK_JAVA = FALLBACK_JAVA.replace(
                "WHERE p.plotId = :plotId",
                "WHERE p.plot.id = :plotId"
            )
            print("[entity] Adjusted JPQL for object relationship (p.plot.id)")
        else:
            print("[entity] Using direct plotId field")
    except FileNotFoundError:
        print("[entity] Entity not found, using unmodified fallback")
    except Exception as e:
        print(f"[entity] Error reading entity: {e}")


def write_file(content):
    os.makedirs(os.path.dirname(TARGET), exist_ok=True)
    with open(TARGET, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"[ok] Restored: {TARGET}")


def main():
    print("=== PaymentRecordRepository.java restore ===")

    # 1. Try GitHub API (most authoritative)
    owner, repo = get_repo_info()
    if owner and repo:
        print(f"[info] Repo: {owner}/{repo}")
        token = get_github_token()
        print(f"[info] Token: {'found' if token else 'not found (unauthenticated)'}")
        content = fetch_from_github(owner, repo, token)
        if content:
            write_file(content)
            return

    # 2. Try local git history
    content = try_git_show()
    if content:
        write_file(content)
        return

    # 3. Write fallback content, adapted to actual entity if possible
    print("[fallback] Writing reconstructed Java content...")
    adapt_fallback()
    write_file(FALLBACK_JAVA)


if __name__ == "__main__":
    main()