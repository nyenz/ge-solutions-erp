# PATH: fix.py
import os

path = "erp-frontend/src/pages/login/LoginPage.jsx"

if not os.path.isfile(path):
    print(f"MISSING: {path}")
else:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Normalize line endings
    content = content.replace("\r\n", "\n")

    # Step 1: Remove useAuth() from below the conditional early return
    old_use_auth = (
        "    const { login } = useAuth();\n"
        "\n"
        "    const handleLogin = async (e) => {"
    )
    new_use_auth = "    const handleLogin = async (e) => {"

    # Step 2: Insert useAuth() at the very top of the component, before the useEffect
    old_top_position = (
        "    const [recoverySuccess, setRecoverySuccess] = useState('');\n"
        "\n"
        "    useEffect(() => {"
    )
    new_top_position = (
        "    const [recoverySuccess, setRecoverySuccess] = useState('');\n"
        "    const { login } = useAuth();\n"
        "\n"
        "    useEffect(() => {"
    )

    if old_use_auth in content and old_top_position in content:
        content = content.replace(old_use_auth, new_use_auth)
        content = content.replace(old_top_position, new_top_position)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"OK: Moved useAuth hook to top level in {path} successfully.")
    else:
        print(f"SKIP or FAIL: Indentation or structures did not match in {path}")