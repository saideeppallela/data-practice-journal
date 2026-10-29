
from pathlib import Path
import hashlib
import shutil
import subprocess
from datetime import datetime

# ---------------- CONFIGURATION ----------------

SOURCE = Path(r"D:\Github - Worklog\sql-advanced-practice")
REPO = Path(r"D:\Github - Worklog\data-practice-journal")
TARGET = REPO / "03_advanced_sql_business_cases"

EXCLUDED_FOLDERS = {"temp-check"}
MODE = "sync" 

def get_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_files(folder):
    return {
        p.relative_to(folder).as_posix(): p
        for p in folder.rglob("*")
        if p.is_file()
    }


def numbered_folders(folder):
    return {
        p.name: p
        for p in folder.iterdir()
        if p.is_dir()
        and p.name not in EXCLUDED_FOLDERS
        and len(p.name) >= 4
        and p.name[:2].isdigit()
        and p.name[2] == "_"
    }


def main():
    if not SOURCE.is_dir():
        raise SystemExit(f"Source folder not found: {SOURCE}")

    if not (REPO / ".git").is_dir():
        raise SystemExit(f"Git repository not found: {REPO}")

    if not TARGET.is_dir():
        raise SystemExit(f"Target folder not found: {TARGET}")

    local = numbered_folders(SOURCE)

    if len(local) != 15:
        raise SystemExit(f"Expected 15 local folders; found {len(local)}.")

    # Map local 01-15 folders to existing GitHub day61-day75 folders.
    existing = {
        p.name: p for p in TARGET.iterdir() if p.is_dir()
    }

    github = {}
    for i in range(15):
        local_name = sorted(local)[i]
        old_name = next(
            (
                name for name in existing
                if name.startswith(f"day{61 + i}_")
            ),
            None,
        )

        if old_name is None:
            raise SystemExit(
                f"Cannot find existing GitHub folder for {local_name}."
            )

        github[local_name] = existing[old_name]

    print(f"Source: {SOURCE}")
    print(f"Target: {TARGET}")
    print(f"Mode: {MODE.upper()}")
    print("=" * 60)

    for local_name, source_folder in sorted(local.items()):
        target_folder = github[local_name]
        source_files = get_files(source_folder)
        target_files = get_files(target_folder)

        print(f"\n{target_folder.name} -> {local_name}")

        for filename in sorted(source_files):
            if filename not in target_files:
                print(f"  ADD: {filename}")
            elif get_hash(source_files[filename]) != get_hash(
                target_files[filename]
            ):
                print(f"  UPDATE: {filename}")

        for filename in sorted(target_files.keys() - source_files.keys()):
            print(f"  KEEP GitHub-only file: {filename}")

    print("\nPREVIEW COMPLETE. No files were modified.")

    if MODE == "preview":
        return

    if MODE != "sync":
        raise SystemExit("MODE must be 'preview' or 'sync'.")

    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    if status.stdout.strip():
        raise SystemExit(
            "STOP: Repository has uncommitted changes.\n"
            + status.stdout
        )

    backup = REPO.parent / (
        "data-practice-journal_backup_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    shutil.copytree(
        REPO, backup, ignore=shutil.ignore_patterns(".git")
    )
    print(f"\nBackup created: {backup}")

    # Use temporary names to avoid collisions during folder renames.
    temporary = {}
    for i, (local_name, old_folder) in enumerate(github.items()):
        temp = TARGET / f"__sync_temp_{i:02d}"
        old_folder.rename(temp)
        temporary[local_name] = temp

    for local_name, temp in temporary.items():
        destination_folder = TARGET / local_name
        temp.rename(destination_folder)
        source_folder = local[local_name]

        for relative_name, source_file in get_files(source_folder).items():
            destination = destination_folder / Path(relative_name)
            destination.parent.mkdir(parents=True, exist_ok=True)

            if (
                not destination.exists()
                or get_hash(source_file) != get_hash(destination)
            ):
                shutil.copy2(source_file, destination)
                print(f"SYNCED: {local_name}/{relative_name}")

    print("\nSYNC COMPLETE.")
    print(f"Backup: {backup}")
    print("GitHub-only files were retained.")
    print("Review with: git status --short")
    print("Nothing has been pushed to GitHub yet.")


if __name__ == "__main__":
    main()
