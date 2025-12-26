#!/usr/bin/env python3
# version 0.9

import argparse
import os
import pathlib
import psutil
import shutil
import sqlite3
import sys
import json
import subprocess
import re

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("[ERROR] The 'rich' library is required. Install: python -m pip install rich")
    sys.exit(1)

# --- Configuration ---
DATA_TYPE_MAPPING = {
    "history": {"type": "sqlite", "file": "History", "table": "urls"},
    "cookies": {"type": "sqlite_nocount", "file": "Network/Cookies", "table": "cookies"},
    "cache": {"type": "folder", "path": "Cache"},
    "code_cache": {"type": "folder", "path": "Code Cache"},
}
DEFAULT_CLEANUP_TYPES = ["cache", "code_cache", "cookies"]
BACKUP_SCRIPT_NAME = "BackupChromeProfiles.ps1"

# --- Helper Functions ---

def natural_sort_key(s):
    """Sorts strings containing numbers naturally (Profile 2 before Profile 10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', str(s))]

def get_profile_display_names(user_data_path):
    """Reads Local State to map folder names to actual names (e.g. jorper98)."""
    names = {}
    local_state_path = user_data_path / "Local State"
    if local_state_path.exists():
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                info_cache = data.get('profile', {}).get('info_cache', {})
                for folder, info in info_cache.items():
                    names[folder] = info.get('name', folder)
        except Exception: pass
    return names

# --- Core Functions ---

def get_chrome_user_data_path():
    if sys.platform == "win32":
        return pathlib.Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"
    return None

def get_profiles(user_data_path):
    """Finds and naturally sorts profiles."""
    profiles = []
    if user_data_path.exists():
        default_p = user_data_path / "Default"
        if default_p.is_dir(): profiles.append(default_p)
        numbered = [p for p in user_data_path.iterdir() if p.is_dir() and p.name.startswith("Profile ")]
        numbered.sort(key=lambda x: natural_sort_key(x.name))
        profiles.extend(numbered)
    return profiles

def format_bytes(byte_count):
    if byte_count <= 0: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if byte_count < 1024: return f"{byte_count:.2f} {unit}"
        byte_count /= 1024
    return f"{byte_count:.2f} TB"

def run_backup_script():
    script_path = pathlib.Path(__file__).parent / BACKUP_SCRIPT_NAME
    if not script_path.exists(): return False
    try:
        result = subprocess.run(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)], shell=True)
        return result.returncode == 0
    except Exception: return False

def analyze_profile(profile_path, types_to_scan):
    report = {}
    for dt in types_to_scan:
        cfg = DATA_TYPE_MAPPING.get(dt)
        if cfg["type"] == "folder":
            folder_p = profile_path / cfg["path"]
            report[dt] = {"size": sum(f.stat().st_size for f in folder_p.glob('**/*') if f.is_file()) if folder_p.exists() else 0}
        else:
            db_p = profile_path / cfg["file"]
            report[dt] = {"size": db_p.stat().st_size if db_p.exists() else 0}
    return report

def clean_profile(profile_path, types_to_clean):
    print(f"\n--- Cleaning Profile: {profile_path.name} ---")
    bytes_freed = 0
    for dt in types_to_clean:
        cfg = DATA_TYPE_MAPPING.get(dt)
        print(f"  [-] Cleaning {dt}...", end="", flush=True)
        try:
            if cfg["type"] == "folder":
                p = profile_path / cfg["path"]
                if p.exists():
                    sz = sum(f.stat().st_size for f in p.glob('**/*') if f.is_file())
                    shutil.rmtree(p)
                    bytes_freed += sz
                print(" Done.")
            else:
                db_p = profile_path / cfg["file"]
                if db_p.exists():
                    init_sz = db_p.stat().st_size
                    conn = sqlite3.connect(db_p); conn.execute(f"DELETE FROM {cfg['table']}"); conn.commit(); conn.execute("VACUUM"); conn.close()
                    bytes_freed += (init_sz - db_p.stat().st_size)
                    print(" Done.")
        except Exception as e: print(f" FAILED: {e}")
    return bytes_freed

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--clean", action="store_true"); parser.add_argument("--types", type=str, default=",".join(DEFAULT_CLEANUP_TYPES)); args = parser.parse_args()
    user_data = get_chrome_user_data_path()
    profiles = get_profiles(user_data)
    display_names = get_profile_display_names(user_data)
    types_to_process = [t.strip() for t in args.types.split(',')]

    if not args.clean:
        console = Console(); table = Table(title="Profile Analysis", header_style="bold magenta")
        table.add_column("Folder"); table.add_column("Profile Name")
        for t in types_to_process: table.add_column(t.capitalize(), justify="right")
        for p in profiles:
            rep = analyze_profile(p, types_to_process)
            table.add_row(p.name, display_names.get(p.name, "Unknown"), *[format_bytes(rep[t]["size"]) for t in types_to_process])
        console.print(table)
    else:
        if (input("\nCreate backup first? (y/n): ").lower() or 'y') == 'y' and not run_backup_script(): sys.exit(1)
        if input(f"\nConfirm DELETION for {len(profiles)} profiles? (YES/NO): ") == "YES":
            total = sum(clean_profile(p, types_to_process) for p in profiles)
            print(f"\nTOTAL RECLAIMED: {format_bytes(total)}")

if __name__ == "__main__":
    main()