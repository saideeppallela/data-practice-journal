
from pathlib import Path
import hashlib
import shutil
import subprocess
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

SOURCE = Path(r"D:\Github - Worklog\sql-advanced-practice")
REPO = Path(r"D:\Github - Worklog\data-practice-journal")
TARGET = REPO / "03_advanced_sql_business_cases"

# First run in preview mode. Change to "sync" only after review.
MODE = "preview"

EXCLUDED_FOLDERS = {"temp-check"}

# These old prefixes are removed only when a clean equivalent
# exists in the same folder.
OLD_FILE_PREFIX = {
    "database_table_setup.sql": "day",
    "output_result.png": "day",
    "query_execution.png": "day",
}


def file_hash(path: Path) -> str:
    """Return SHA-256 hash of a file."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def files_in(folder: Path) -> dict:
    """Return relative file paths mapped to their absolute paths."""
    return {
        p.relative_to(folder).as_posix(): p
        for p in folder.rglob("*")
        if p.is_file()
    }


def numbered_folders(folder: Path) -> dict:
    """Find folders named 01_something through 15_something."""
    return {
        p.name: p
        for p in folder.iterdir()
        if p.is_dir()
        and p.name not in EXCLUDED_FOLDERS
        and len(p.name) >= 4
        and p.name[:2].isdigit()
        and p.name[2] == "_"
    }


def validate():
    """Validate paths and repository state."""
    for path, label in [
        (SOURCE, "Source"),
        (REPO, "Repository"),
        (TARGET, "Target"),
    ]:
        if not path.is_dir():
            raise SystemExit(f"ERROR: {label} folder not found: {path}")

    if not (REPO / ".git").exists():
        raise SystemExit("ERROR: Git repository not found.")

    local = numbered_folders(SOURCE)

    if len(local) != 15:
        raise SystemExit(
            f"ERROR: Expected 15 source folders; found {len(local)}."
        )

    names = sorted(local)

    expected = [f"{i:02d}_" for i in range(1, 16)]

    for i, name in enumerate(names):
        if not name.startswith(expected[i]):
            raise SystemExit(
                f"ERROR: Unexpected folder sequence: {name}"
            )

    # Do not overwrite uncommitted work.
    status = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    if status.stdout.strip():
        raise SystemExit(
            "STOP: Commit or safely resolve existing Git changes first:\n"
            + status.stdout
        )

    return local


def make_plan(local: dict):
    """Map old GitHub folders to source folder names."""
    existing = {
        p.name: p
        for p in TARGET.iterdir()
        if p.is_dir()
    }

    mapping = {}

    for index, local_name in enumerate(sorted(local), start=61):
        candidates = [
            name
            for name in existing
            if name.startswith(f"day{index}_")
        ]

        if len(candidates) != 1:
            raise SystemExit(
                f"ERROR: Expected one old folder for day{index}; "
                f"found {candidates}."
            )

        mapping[local_name] = existing[candidates[0]]

    destinations = [TARGET / name for name in mapping]

    for destination in destinations:
        if destination.exists() and destination not in mapping.values():
            raise SystemExit(
                f"ERROR: Destination already exists: {destination}\n"
                "Resolve this collision before syncing."
            )

    return mapping


def build_operations(local: dict, mapping: dict):
    """
    Build a conservative sync plan.

    Existing files with matching names are compared by hash.
    GitHub-only files are preserved.
    Legacy day-prefixed duplicate files are removed only when
    the equivalent clean file exists and has identical content.
    """
    operations = []

    for local_name, source_folder in sorted(local.items()):
        old_folder = mapping[local_name]
        print(f"\n{old_folder.name} -> {local_name}")

        source_files = files_in(source_folder)
        target_files = files_in(old_folder)

        # Report additions and content differences.
        for relative_name, source_file in sorted(source_files.items()):
            target_file = target_files.get(relative_name)

            if target_file is None:
                print(f"  ADD: {relative_name}")
                operations.append(
                    ("copy", local_name, relative_name, source_file)
                )
            elif file_hash(source_file) != file_hash(target_file):
                print(f"  UPDATE: {relative_name}")
                operations.append(
                    ("copy", local_name, relative_name, source_file)
                )
            else:
                print(f"  MATCH: {relative_name}")

        # Preserve files that exist only on GitHub.
        for relative_name in sorted(
            target_files.keys() - source_files.keys()
        ):
            print(f"  KEEP GitHub-only: {relative_name}")

        # Identify legacy duplicates safely.
        for old_relative, old_file in sorted(target_files.items()):
            old_name = Path(old_relative).name

            if old_name.startswith("day"):
                clean_name = old_name.split("_", 1)

                if len(clean_name) != 2:
                    continue

                clean_name = clean_name[1]

                if clean_name not in {
                    "database_table_setup.sql",
                    "output_result.png",
                    "query_execution.png",
                }:
                    continue

                clean_relative = str(
                    Path(old_relative).with_name(clean_name)
                ).replace("\\", "/")

                clean_file = target_files.get(clean_relative)

                if clean_file is None:
                    clean_file = source_files.get(clean_relative)

                if clean_file is not None:
                    if file_hash(old_file) == file_hash(clean_file):
                        print(f"  REMOVE verified duplicate: {old_relative}")
                        operations.append(
                            ("remove_duplicate", local_name, old_relative, None)
                        )
                    else:
                        print(
                            f"  REVIEW: Different content in "
                            f"{old_relative} and {clean_relative}"
                        )

    return operations


def main():
    if MODE not in {"preview", "sync"}:
        raise SystemExit("MODE must be 'preview' or 'sync'.")

    local = validate()
    mapping = make_plan(local)

    print(f"Source: {SOURCE}")
    print(f"Target: {TARGET}")
    print(f"Mode: {MODE.upper()}")

    operations = build_operations(local, mapping)

    print("\n" + "=" * 60)
    print(f"Planned file operations: {len(operations)}")

    if MODE == "preview":
        print("PREVIEW COMPLETE. NO FILES WERE MODIFIED.")
        print("Review the output before changing MODE to 'sync'.")
        return

    confirmation = input(
        "\nType SYNC to back up and apply the planned changes: "
    ).strip()

    if confirmation != "SYNC":
        print("Cancelled. No changes made.")
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

    # Rename all old folders to temporary names first.
    temporary = {}

    for index, (local_name, old_folder) in enumerate(mapping.items()):
        temp = TARGET / f"__sync_temp_{index:02d}"

        if temp.exists():
            raise SystemExit(
                f"ERROR: Temporary folder already exists: {temp}"
            )

        old_folder.rename(temp)
        temporary[local_name] = temp

    # Rename temporary folders to their clean names.
    for local_name, temp in temporary.items():
        destination = TARGET / local_name

        if destination.exists():
            raise SystemExit(
                f"ERROR: Destination exists: {destination}. "
                "Restore from backup if necessary."
            )

        temp.rename(destination)

    # Apply additions and updates.
    for operation, local_name, relative_name, source_file in operations:
        destination_folder = TARGET / local_name

        if operation == "copy":
            destination = destination_folder / relative_name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination)
            print(f"SYNCED: {local_name}/{relative_name}")

    # Remove only duplicates verified by identical content.
    for operation, local_name, relative_name, _ in operations:
        if operation == "remove_duplicate":
            duplicate = TARGET / local_name / relative_name

            if duplicate.exists():
                duplicate.unlink()
                print(f"REMOVED DUPLICATE: {duplicate}")

    print("\nSYNC COMPLETE.")
    print(f"Backup: {backup}")
    print("GitHub has not been updated yet.")
    print("Review with: git status --short")
    print("Commit and push only after checking the changes.")


if __name__ == "__main__":
    main()
