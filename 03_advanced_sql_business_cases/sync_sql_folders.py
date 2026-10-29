
from pathlib import Path
import hashlib
import shutil
import subprocess
from datetime import datetime

# CONFIGURATION
REPO = Path(r"D:\Github - Worklog\data-practice-journal")
TARGET = REPO / "03_advanced_sql_business_cases"
MODE = "sync"

DUPLICATE_PREFIXES = tuple(
    f"day{i}_" for i in range(61, 76)
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not (REPO / ".git").is_dir():
        raise SystemExit(f"Git repository not found: {REPO}")

    if not TARGET.is_dir():
        raise SystemExit(f"Target folder not found: {TARGET}")

    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    if status.stdout.strip():
        raise SystemExit(
            "STOP: Resolve Git changes before cleanup:\n"
            + status.stdout
        )

    removals = []

    print(f"MODE: {MODE.upper()}")
    print("Checking duplicate files...\n")

    for folder in sorted(TARGET.iterdir()):
        if not folder.is_dir():
            continue

        for old_file in folder.rglob("*"):
            if not old_file.is_file():
                continue

            if not old_file.name.startswith(DUPLICATE_PREFIXES):
                continue

            clean_name = old_file.name.split("_", 1)[1]
            clean_file = old_file.with_name(clean_name)

            if not clean_file.is_file():
                print(f"KEEP — no clean equivalent: {old_file}")
                continue

            if sha256(old_file) == sha256(clean_file):
                print(f"DUPLICATE: {old_file.relative_to(REPO)}")
                removals.append(old_file)
            else:
                print(
                    f"REVIEW — contents differ: "
                    f"{old_file.relative_to(REPO)}"
                )

    print(f"\nVerified duplicates: {len(removals)}")

    if MODE == "preview":
        print("PREVIEW COMPLETE. NO FILES WERE MODIFIED.")
        return

    if MODE != "sync":
        raise SystemExit("MODE must be 'preview' or 'sync'.")

    if not removals:
        print("No verified duplicates to remove.")
        return

    answer = input(
        "Type DELETE to remove verified duplicate files: "
    )

    if answer != "DELETE":
        print("Cancelled. No files were removed.")
        return

    backup = REPO.parent / (
        "data-practice-journal_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    shutil.copytree(
        REPO,
        backup,
        ignore=shutil.ignore_patterns(".git"),
    )

    print(f"Backup created: {backup}")

    for path in removals:
        if path.exists():
            path.unlink()
            print(f"REMOVED: {path.relative_to(REPO)}")

    print("\nCleanup complete.")
    print("Next command: git status --short")
    print("Nothing has been pushed to GitHub.")


if __name__ == "__main__":
    main()
