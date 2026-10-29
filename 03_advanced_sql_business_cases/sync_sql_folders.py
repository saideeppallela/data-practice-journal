
from pathlib import Path
import hashlib
import shutil
import subprocess
from datetime import datetime

# CONFIGURATION
REPO = Path(r"D:\Github - Worklog\data-practice-journal")
TARGET = REPO / "03_advanced_sql_business_cases"
MODE = "preview"  # Change to "sync" only after checking the preview

DUPLICATE_PREFIXES = ("day61_", "day62_", "day63_", "day64_", "day65_",
                      "day66_", "day67_", "day68_", "day69_", "day70_",
                      "day71_", "day72_", "day73_", "day74_", "day75_")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not TARGET.is_dir():
        raise SystemExit(f"Folder not found: {TARGET}")

    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain"],
        capture_output=True, text=True, check=True
    )
    if status.stdout.strip():
        raise SystemExit(
            "STOP: Commit or safely resolve Git changes first:\n"
            + status.stdout
        )

    print("MODE:", MODE.upper())
    print("Checking duplicate day-prefixed files...\n")

    removals = []

    for folder in sorted(TARGET.iterdir()):
        if not folder.is_dir() or not folder.name[:2].isdigit():
            continue

        print(f"\n{folder.name}/")
        files = [p for p in folder.rglob("*") if p.is_file()]

        for old_file in files:
            if not old_file.name.startswith(DUPLICATE_PREFIXES):
                continue

            clean_name = old_file.name.split("_", 1)[1]
            clean_file = old_file.with_name(clean_name)

            if not clean_file.is_file():
                print(f"  KEEP — no clean equivalent: {old_file.name}")
                continue

            if sha256(old_file) == sha256(clean_file):
                print(f"  DUPLICATE: {old_file.name}")
                removals.append(old_file)
            else:
                print(f"  REVIEW — contents differ: {old_file.name}")

    print(f"\nVerified duplicate files: {len(removals)}")

    if MODE == "preview":
        print("PREVIEW COMPLETE. NO FILES WERE MODIFIED.")
        return

    if MODE != "sync":
        raise SystemExit("MODE must be 'preview' or 'sync'.")

    answer = input("Type DELETE to remove verified duplicates: ")
    if answer != "DELETE":
        print("Cancelled.")
        return

    backup = REPO.parent / (
        "data-practice-journal_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    shutil.copytree(
        REPO, backup, ignore=shutil.ignore_patterns(".git")
    )
    print("Backup created:", backup)

    for path in removals:
        if path.exists():
            path.unlink()
            print("REMOVED:", path.relative_to(REPO))

    print("\nCleanup complete.")
    print("Review changes using: git status --short")
    print("Nothing has been pushed to GitHub.")


if __name__ == "__main__":
    main()
