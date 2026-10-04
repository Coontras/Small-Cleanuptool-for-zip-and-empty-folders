#!/usr/bin/env python3
import os
import sys
import msvcrt
import time
from pathlib import Path

ARCHIVE_EXTENSIONS = (".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz")
INSTALLER_KEYWORDS = ("setup", "install")

RED = "\033[91m"
RESET = "\033[0m"
os.system("")

try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


def choose_folder() -> str:
    if HAS_GUI:
        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Choose folder (or drive) to clean up")
        root.destroy()
        return folder
    else:
        return input("Enter path to folder/drive: ").strip()


def find_archives(base: str):
    hits = []
    for dirpath, _, filenames in os.walk(base):
        for name in filenames:
            if name.lower().endswith(ARCHIVE_EXTENSIONS):
                path = Path(dirpath) / name
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                hits.append((path, size))
    return hits


def find_installers(base: str):
    hits = []
    for dirpath, _, filenames in os.walk(base):
        for name in filenames:
            lower = name.lower()
            if lower.endswith(".exe") and any(k in lower for k in INSTALLER_KEYWORDS):
                path = Path(dirpath) / name
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                hits.append((path, size))
    return hits


def is_protected_name(name: str) -> bool:
    lower = name.lower()
    return "mod" in lower or "addon" in lower


def find_empty_folders(base: str):
    empty = []

    def scan(path: str) -> bool:
        has_content = False
        try:
            entries = list(os.scandir(path))
        except OSError:
            return True
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                if is_protected_name(entry.name):
                    has_content = True
                    continue
                if scan(entry.path):
                    has_content = True
            else:
                has_content = True
        if not has_content:
            empty.append(Path(path))
        return has_content

    scan(base)
    return [p for p in empty if str(p) != str(Path(base))]


def format_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def ask_confirmation() -> str:
    return input("Type 'YES' to actually delete, 'TEST' for a dry run (just show), anything else to cancel: ").strip()


def wait_after_done():
    print("\nDone! Closing in 5 seconds, press any key to continue.")
    start = time.time()
    while time.time() - start < 5:
        if msvcrt.kbhit():
            msvcrt.getch()
            return True
        time.sleep(0.05)
    return False


def mode_delete_archives():
    print(f"\nExtensions that will be deleted: {', '.join(ARCHIVE_EXTENSIONS)}\n")
    folder = choose_folder()
    if not folder or not os.path.isdir(folder):
        print("No valid folder selected. Aborting.")
        return

    print(f"\nScanning: {folder}\n")
    archives = find_archives(folder)

    if not archives:
        print("No archive files found.")
        return

    total_bytes = sum(size for _, size in archives)
    print(f"Found: {len(archives)} file(s), {format_size(total_bytes)} total\n")
    for path, size in archives:
        print(f"  {path}  ({format_size(size)})")

    print()
    choice = ask_confirmation()
    if choice == "TEST":
        print("\nDry run: nothing was deleted.")
        return
    if choice != "YES":
        print(f"{RED}Cancelled due to input '{choice}'. Nothing was deleted.{RESET}")
        return

    deleted, errors = 0, 0
    for path, _ in archives:
        try:
            os.remove(path)
            deleted += 1
        except OSError as e:
            print(f"Error deleting {path}: {e}")
            errors += 1

    print(f"\n{deleted} file(s) deleted, {errors} error(s).")


def mode_delete_installers():
    print(f"\nFiles ending in .exe containing: {', '.join(INSTALLER_KEYWORDS)}\n")
    folder = choose_folder()
    if not folder or not os.path.isdir(folder):
        print("No valid folder selected. Aborting.")
        return

    print(f"\nScanning: {folder}\n")
    installers = find_installers(folder)

    if not installers:
        print("No installer files found.")
        return

    total_bytes = sum(size for _, size in installers)
    print(f"Found: {len(installers)} file(s), {format_size(total_bytes)} total\n")
    for path, size in installers:
        print(f"  {path}  ({format_size(size)})")

    print()
    choice = ask_confirmation()
    if choice == "TEST":
        print("\nDry run: nothing was deleted.")
        return
    if choice != "YES":
        print(f"{RED}Cancelled due to input '{choice}'. Nothing was deleted.{RESET}")
        return

    deleted, errors = 0, 0
    for path, _ in installers:
        try:
            os.remove(path)
            deleted += 1
        except OSError as e:
            print(f"Error deleting {path}: {e}")
            errors += 1

    print(f"\n{deleted} file(s) deleted, {errors} error(s).")


def mode_delete_empty_folders():
    folder = choose_folder()
    if not folder or not os.path.isdir(folder):
        print("No valid folder selected. Aborting.")
        return

    print(f"\nScanning: {folder}\n")
    empty = find_empty_folders(folder)

    if not empty:
        print("No empty folders found.")
        return

    print(f"Found: {len(empty)} empty folder(s)\n")
    for path in empty:
        print(f"  {path}")

    print()
    choice = ask_confirmation()
    if choice == "TEST":
        print("\nDry run: nothing was deleted.")
        return
    if choice != "YES":
        print(f"{RED}Cancelled due to input '{choice}'. Nothing was deleted.{RESET}")
        return

    deleted, errors = 0, 0
    for path in empty:
        try:
            os.rmdir(path)
            deleted += 1
        except OSError as e:
            print(f"Error deleting {path}: {e}")
            errors += 1

    print(f"\n{deleted} folder(s) deleted, {errors} error(s).")


def main():
    while True:
        print("=== Cleanup Tool ===\n")
        print("1) Delete archives (zip, rar, 7z, tar, gz, ...)")
        print("2) Delete empty folders")
        print("3) Delete installer files (setup.exe, installer.exe, ...)")
        choice = input("\nChoice (1/2/3): ").strip()

        if choice == "1":
            mode_delete_archives()
        elif choice == "2":
            mode_delete_empty_folders()
        elif choice == "3":
            mode_delete_installers()
        else:
            print("Invalid choice.")

        continue_running = wait_after_done()
        if not continue_running:
            sys.exit(0)
        print()


if __name__ == "__main__":
    main()
