#!/usr/bin/env python3
# version 0.4

import argparse
import os
import pathlib
import psutil
import shutil
import sqlite3
import sys
import json
import time

# --- New Dependency: rich ---
# This library is used for creating the formatted table output.
# Install it with: pip install rich
try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("[ERROR] The 'rich' library is required for table formatting.")
    print("Please install it by running: python -m pip install rich")
    sys.exit(1)

# --- Configuration ---
DATA_TYPE_MAPPING = {
    "history": {"type": "sqlite", "file": "History", "table": "urls"},
    "cookies": {"type": "sqlite_nocount", "file": "Network/Cookies", "table": "cookies"},
    "cache": {"type": "folder", "path": "Cache"},
    "code_cache": {"type": "folder", "path": "Code Cache"},
}

DEFAULT_CLEANUP_TYPES = ["history", "cookies", "cache", "code_cache"]

# --- Core Functions ---

def get_chrome_user_data_path():
    """Determines the default path to the Chrome User Data directory based on the OS."""
    if sys.platform == "win32":
        return pathlib.Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"
    elif sys.platform == "darwin":
        return pathlib.Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    elif sys.platform == "linux":
        return pathlib.Path.home() / ".config" / "google-chrome"
    else:
        return None

def find_chrome_processes():
    """Finds all running Google Chrome processes."""
    chrome_procs = []
    for proc in psutil.process_iter(['name', 'pid']):
        if "chrome" in proc.info['name'].lower():
            chrome_procs.append(proc)
    return chrome_procs

def kill_chrome_processes(procs):
    """Terminates a list of given processes."""
    print(f"[!] Terminating {len(procs)} Chrome processes...")
    for proc in procs:
        try:
            proc.terminate()
        except psutil.NoSuchProcess:
            pass # Process already terminated
    
    gone, alive = psutil.wait_procs(procs, timeout=3)
    for p in alive:
        p.kill() # Force kill any stubborn processes
    print("[+] Chrome processes terminated.")

def get_profiles(user_data_path):
    """Finds all Chrome profile directories within the User Data directory."""
    profiles = []
    if user_data_path.exists():
        default_profile = user_data_path / "Default"
        if default_profile.is_dir(): profiles.append(default_profile)
        for item in user_data_path.iterdir():
            if item.is_dir() and item.name.startswith("Profile "):
                profiles.append(item)
    return profiles

def get_profile_names(user_data_path):
    """Reads the Local State file to get human-readable profile names."""
    names = {}
    local_state_path = user_data_path / "Local State"
    if local_state_path.exists():
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            profile_info = local_state.get('profile', {}).get('info_cache', {})
            for folder_name, info in profile_info.items():
                name = info.get('name')
                if name: names[folder_name] = name
        except (json.JSONDecodeError, IOError) as e:
            print(f"[!] Warning: Could not read profile names from Local State file: {e}")
    return names

def get_folder_size(folder_path):
    """Calculates the total size of a folder and all its subfolders."""
    if not folder_path.exists(): return 0
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_bytes(byte_count):
    """Formats bytes into a human-readable string (KB, MB, GB)."""
    if byte_count is None or not isinstance(byte_count, (int, float)): return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels):
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}B"

def analyze_profile(profile_path, types_to_scan):
    """Analyzes a single profile to see what data can be cleaned."""
    report = {}
    for data_type in types_to_scan:
        config = DATA_TYPE_MAPPING.get(data_type)
        if not config: continue

        if config["type"] == "folder":
            report[data_type] = {"size": get_folder_size(profile_path / config["path"])}
        
        elif config["type"] in ["sqlite", "sqlite_nocount"]:
            db_path = profile_path / config["file"]
            if not db_path.exists():
                if config["type"] == "sqlite_nocount":
                    report[data_type] = {"count": None, "size": 0}
                else:
                    report[data_type] = {"count": 0, "size": 0}
                continue

            db_size = db_path.stat().st_size
            
            if config["type"] == "sqlite_nocount":
                report[data_type] = {"count": None, "size": db_size}
                continue

            try:
                source_conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                mem_conn = sqlite3.connect(':memory:')
                source_conn.backup(mem_conn)
                source_conn.close()

                cursor = mem_conn.cursor()
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{config['table']}';")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {config['table']}")
                    count = cursor.fetchone()[0]
                    report[data_type] = {"count": count, "size": db_size}
                else:
                    report[data_type] = {"count": 0, "size": db_size}
                mem_conn.close()

            except sqlite3.Error as e:
                report[data_type] = {"count": f"DB Error: {e}", "size": db_size}
    return report

def clean_profile(profile_path, types_to_clean):
    """Performs the actual deletion of data for a single profile."""
    print(f"\n--- Cleaning Profile: {profile_path.name} ---")
    for data_type in types_to_clean:
        config = DATA_TYPE_MAPPING.get(data_type)
        if not config: continue

        print(f"  [-] Cleaning {data_type}...", end="", flush=True)
        try:
            if config["type"] == "folder":
                folder_path = profile_path / config["path"]
                if folder_path.exists(): shutil.rmtree(folder_path)
                print(" Done.")
                
                if data_type == 'cache':
                    print(f"  [-] Cleaning downloads history (bundled)...", end="", flush=True)
                    try:
                        db_path_hist = profile_path / "History"
                        if db_path_hist.exists():
                            with sqlite3.connect(db_path_hist) as conn_dl:
                                conn_dl.execute("DELETE FROM downloads")
                                conn_dl.execute("VACUUM")
                            print(" Done.")
                        else: print(" History DB not found.")
                    except sqlite3.Error as e: print(f" FAILED. Error: {e}")
            
            elif config["type"] in ["sqlite", "sqlite_nocount"]:
                db_path = profile_path / config["file"]
                if db_path.exists():
                    with sqlite3.connect(db_path) as conn:
                        conn.execute(f"DELETE FROM {config['table']}")
                        conn.execute("VACUUM")
                    print(" Done.")
                else: print(" Not found.")
        except Exception as e: print(f" FAILED. Error: {e}")

# --- Main Execution Logic ---
def main():
    parser = argparse.ArgumentParser(description="A script to clean browsing data from all Google Chrome profiles.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--clean", action="store_true", help="Execute the cleanup. Without this flag, the script runs in 'dry run' mode.")
    parser.add_argument("--force-close", action="store_true", help="Forcefully terminate all running Chrome processes before analysis.")
    parser.add_argument("--types", type=str, default=",".join(DEFAULT_CLEANUP_TYPES), help=f"Comma-separated list of data types to clean.\nAvailable types: {', '.join(DATA_TYPE_MAPPING.keys())}")
    args = parser.parse_args()
    
    chrome_procs = find_chrome_processes()
    if chrome_procs:
        if args.force_close:
            print("[WARNING] The --force-close flag is active.")
            print("This will terminate all Chrome processes and may cause loss of unsaved work (e.g., tabs).")
            try:
                confirm = input("Type 'FORCE CLOSE' to continue: ")
                if confirm == "FORCE CLOSE":
                    kill_chrome_processes(chrome_procs)
                    time.sleep(1)
                else:
                    print("Confirmation not received. Aborting.")
                    sys.exit(0)
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                sys.exit(1)
        else:
            print("[ERROR] Google Chrome is currently running. Please close it completely and try again, or use the --force-close flag.")
            sys.exit(1)

    user_data_path = get_chrome_user_data_path()
    if not user_data_path or not user_data_path.exists():
        print("[ERROR] Could not find the Google Chrome User Data directory.")
        sys.exit(1)
        
    profiles = get_profiles(user_data_path)
    if not profiles:
        print("[INFO] No Chrome profiles found.")
        sys.exit(0)

    profile_names = get_profile_names(user_data_path)
    types_to_process = [t.strip() for t in args.types.split(',')]

    if not args.clean:
        console = Console()
        console.print("\n--- Chrome Cleanup Report (Dry Run) ---", style="bold blue")
        console.print("No data will be deleted. Run with the --clean flag to execute cleanup.")

        table = Table(show_header=True, header_style="bold magenta", show_footer=True, title="Profile Analysis")
        table.add_column("Folder", style="dim", width=12)
        table.add_column("Profile Name", footer="TOTALS", width=15)
        
        for data_type in types_to_process:
            table.add_column(data_type.replace("_", " ").capitalize(), justify="right")
        
        totals = {data_type: {"count": 0, "size": 0} for data_type in types_to_process}

        for profile in profiles:
            report = analyze_profile(profile, types_to_process)
            profile_display_name = profile_names.get(profile.name, profile.name)
            row_data = [profile.name, profile_display_name]
            
            for data_type in types_to_process:
                cell_str = ""
                value = report.get(data_type)
                if value:
                    size = value.get('size', 0)
                    count = value.get('count')
                    
                    if count is not None:
                        if isinstance(count, int):
                            totals[data_type]["count"] += count
                            count_str = f"{count:,} items"
                        else:
                            count_str = f"[red]{count}[/red]"
                        cell_str = f"{count_str}\n[dim]{format_bytes(size)}[/dim]"
                    else:
                        cell_str = f"[green]{format_bytes(size)}[/green]"
                    
                    if isinstance(size, int):
                        totals[data_type]["size"] += size
                row_data.append(cell_str)
            table.add_row(*row_data)
        
        footer_data = ["", "TOTALS"]
        for data_type in types_to_process:
            config = DATA_TYPE_MAPPING.get(data_type)
            total_value = totals[data_type]
            size = total_value.get('size')
            
            if config['type'] == 'sqlite':
                 count = total_value.get('count')
                 footer_data.append(f"[bold]{count:,} items\n{format_bytes(size)}[/bold]")
            else: # sqlite_nocount and folder
                 footer_data.append(f"[bold green]{format_bytes(size)}[/bold green]")
        
        table.columns[1].footer = "TOTALS"
        for i, col in enumerate(table.columns[2:], 2):
             col.footer = footer_data[i]
        console.print(table)
    else:
        # --- Clean Mode ---
        print("!!! WARNING: You are about to permanently delete browser data. !!!")
        print(f"This will affect {len(profiles)} profile(s).")
        print(f"Data types to be cleaned: {', '.join(types_to_process)}")
        
        try:
            confirm = input("Type 'YES' to continue: ")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)

        if confirm == "YES":
            print("\nStarting cleanup...")
            for profile in profiles:
                clean_profile(profile, types_to_process)
            print("\nCleanup complete.")
        else:
            print("Confirmation not received. Aborting.")

if __name__ == "__main__":
    main()
