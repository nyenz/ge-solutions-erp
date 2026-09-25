import os
import subprocess

def apply_fixes():
    """
    TEMPLATE: Auto-apply codebase fixes and commit/push to the remote repository.
    This script is designed to be populated by an LLM or developer with specific fixes.
    """
    print("🔧 Starting fix application...")

    # 1. DEFINE THE FIXES
    # Format: { 'path/to/file.ext': { 'search': 'old_string', 'replace': 'new_string' } }
    fixes = {
        # Example of how to populate this (currently commented out so it does nothing):
        # 'erp-frontend/src/pages/Reports/ReportStudio.jsx': {
        #     'search': 'preview it, take it home',
        #     'replace': 'chart it, take it home',
        # },
        # 'erp-frontend/src/pages/Reports/ReportStudio.module.css': {
        #     'search': 'old-class-name',
        #     'replace': 'new-class-name',
        # }
    }

    # 2. APPLY THE FIXES
    for file_path, fix in fixes.items():
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace(fix['search'], fix['replace'])
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Modified: {file_path}")
            else:
                print(f"ℹ️  No changes needed for: {file_path}")
        else:
            print(f"❌ File not found: {file_path}")

    # 3. AUTO GIT ADD, COMMIT, AND PUSH
    print("\n--- Git Operations ---")
    try:
        # Stage all changes
        subprocess.run(['git', 'add', '.'], check=True)
        print("✅ Files staged successfully.")
        
        # Commit the changes with a descriptive message
        commit_message = "fix: update report page ui to match prototype"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print(f"✅ Committed with message: '{commit_message}'")
        
        # Push to remote (requires proper git credentials in the environment)
        subprocess.run(['git', 'push'], check=True)
        print("✅ Pushed to remote repository.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")

if __name__ == "__main__":
    apply_fixes()