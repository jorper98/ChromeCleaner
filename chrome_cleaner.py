#version 0.2
#!/usr/bin/env python3


import argparse
import os
import pathlib
import psutil
import shutil
import sqlite3
import sys

# --- Configuration ---
# A dictionary mapping the data type names to their respective files or folders.
# This makes the script easily extensible.
DATA_TYPE_MAPPING = {
    "history": {"type": "sqlite", "file": "History", "table": "urls"},
    "cookies": {"type": "sqlite", "file": "Cookies", "table": "cookies"},
    "downloads": {"type": "sqlite", "file": "History", "table": "downloads"},
    "cache": {"type": "folder", "path": "Cache"},
    "code_cache": {"type": "folder", "path": "Code Cache"},
}

DEFAULT_CLEANUP_TYPES = ["history", "cookies", "downloads", "cache", "code_cache"]

# --- Core Functions ---

def get_chrome_user_data_path():
    """
    Determines the default path to the Chrome User Data directory based on the OS.

    Returns:
        pathlib.Path: A Path object to the User Data directory.
        None: If the operating system is not supported.
    """
    if sys.platform == "win32":
        # Windows
        return pathlib.Path(os.environ["LOCALAPPDATA"]) / "Google" / "Chrome" / "User Data"
    elif sys.platform == "darwin":
        # macOS
        return pathlib.Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    elif sys.platform == "linux":
        # Linux
        return pathlib.Path.home() / ".config" / "google-chrome"
    else:
        return None

def is_chrome_running():
    """
    Checks if a Google Chrome process is currently running.
    This is crucial to prevent database corruption.

    Returns:
        bool: True if Chrome is running, False otherwise.
    """
    for proc in psutil.process_iter(['name']):
        if "chrome" in proc.info['name'].lower():
            return True
    return False

def get_profiles(user_data_path):
    """
    Finds all Chrome profile directories within the User Data directory.

    Args:
        user_data_path (pathlib.Path): The path to the Chrome User Data directory.

    Returns:
        list[pathlib.Path]: A list of Path objects for each found profile.
    """
    profiles = []
    if user_data_path.exists():
        # The default profile is in a folder named 'Default'
        default_profile = user_data_path / "Default"
        if default_profile.is_dir():
            profiles.append(default_profile)

        # Other profiles are in folders named 'Profile 1', 'Profile 2', etc.
        for item in user_data_path.iterdir():
            if item.is_dir() and item.name.startswith("Profile "):
                profiles.append(item)
    return profiles

def get_folder_size(folder_path):
    """
    Calculates the total size of a folder and all its subfolders.

    Args:
        folder_path (pathlib.Path): The path to the folder.

    Returns:
        int: The total size of the folder in bytes. Returns 0 if path doesn't exist.
    """
    if not folder_path.exists():
        return 0
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Skip if it is a symlink
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_bytes(byte_count):
    """Formats bytes into a human-readable string (KB, MB, GB)."""
    if byte_count is None:
        return "N/A"
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while byte_count >= power and n < len(power_labels):
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}B"


def analyze_profile(profile_path, types_to_scan):
    """
    Analyzes a single profile to see what data can be cleaned.

    Args:
        profile_path (pathlib.Path): Path to the specific profile directory.
        types_to_scan (list[str]): A list of data types to analyze (e.g., ['cache', 'history']).

    Returns:
        dict: A dictionary containing the analysis results (e.g., {'cache': 12345, 'history': {'count': 500, 'size': 1024}}).
    """
    report = {}
    for data_type in types_to_scan:
        config = DATA_TYPE_MAPPING.get(data_type)
        if not config:
            continue

        if config["type"] == "folder":
            folder_path = profile_path / config["path"]
            size = get_folder_size(folder_path)
            report[data_type] = size
        
        elif config["type"] == "sqlite":
            db_path = profile_path / config["file"]
            if db_path.exists():
                db_size = db_path.stat().st_size
                try:
                    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) # Read-only connection
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{config['table']}';")
                    if cursor.fetchone():
                        cursor.execute(f"SELECT COUNT(*) FROM {config['table']}")
                        count = cursor.fetchone()[0]
                        report[data_type] = {"count": count, "size": db_size}
                    else:
                        report[data_type] = {"count": 0, "size": db_size} # Table doesn't exist
                    conn.close()
                except sqlite3.Error as e:
                    print(f"  [!] Warning: Could not read {data_type} DB for {profile_path.name}: {e}")
                    report[data_type] = {"count": "Error", "size": db_size}
            else:
                report[data_type] = {"count": 0, "size": 0}
    return report


def clean_profile(profile_path, types_to_clean):
    """
    Performs the actual deletion of data for a single profile.

    Args:
        profile_path (pathlib.Path): Path to the specific profile directory.
        types_to_clean (list[str]): A list of data types to delete.
    """
    print(f"\n--- Cleaning Profile: {profile_path.name} ---")
    for data_type in types_to_clean:
        config = DATA_TYPE_MAPPING.get(data_type)
        if not config:
            print(f"  [!] Skipping unknown type: {data_type}")
            continue

        print(f"  [-] Cleaning {data_type}...", end="", flush=True)
        
        try:
            if config["type"] == "folder":
                folder_path = profile_path / config["path"]
                if folder_path.exists():
                    shutil.rmtree(folder_path)
                    print(" Done.")
                else:
                    print(" Not found.")
            
            elif config["type"] == "sqlite":
                db_path = profile_path / config["file"]
                if db_path.exists():
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {config['table']}")
                    conn.commit()
                    # VACUUM reclaims disk space
                    conn.execute("VACUUM")
                    conn.close()
                    print(" Done.")
                else:
                    print(" Not found.")
        except Exception as e:
            print(f" FAILED. Error: {e}")

# --- Main Execution Logic ---

def main():
    """Main function to parse arguments and orchestrate the cleanup."""
    parser = argparse.ArgumentParser(
        description="A script to clean browsing data from all Google Chrome profiles.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Execute the cleanup. Without this flag, the script runs in 'dry run' mode."
    )
    parser.add_argument(
        "--types",
        type=str,
        default=",".join(DEFAULT_CLEANUP_TYPES),
        help="Comma-separated list of data types to clean.\n"
             f"Available types: {', '.join(DATA_TYPE_MAPPING.keys())}\n"
             f"Default: {','.join(DEFAULT_CLEANUP_TYPES)}"
    )
    args = parser.parse_args()
    
    # --- Pre-flight Checks ---
    if is_chrome_running():
        print("[ERROR] Google Chrome is currently running. Please close it completely and try again.")
        sys.exit(1)

    user_data_path = get_chrome_user_data_path()
    if not user_data_path or not user_data_path.exists():
        print("[ERROR] Could not find the Google Chrome User Data directory.")
        sys.exit(1)
        
    profiles = get_profiles(user_data_path)
    if not profiles:
        print("[INFO] No Chrome profiles found.")
        sys.exit(0)

    types_to_process = [t.strip() for t in args.types.split(',')]

    # --- Mode Selection: Dry Run or Clean ---
    if not args.clean:
        # --- Dry Run Mode (Default) ---
        print("--- Chrome Cleanup Report (Dry Run) ---")
        print("No data will be deleted. Run with the --clean flag to execute cleanup.")
        total_report = {}

        for profile in profiles:
            print(f"\n--- Analyzing Profile: {profile.name} ---")
            report = analyze_profile(profile, types_to_process)
            for data_type, value in report.items():
                # Handle folders (value is an int)
                if isinstance(value, int):
                    print(f"  [+] {data_type.capitalize()}: {format_bytes(value)}")
                    total_report[data_type] = total_report.get(data_type, 0) + value
                # Handle SQLite DBs (value is a dict)
                elif isinstance(value, dict):
                    count = value['count']
                    size = value['size']
                    print(f"  [+] {data_type.capitalize()}: {count} items ({format_bytes(size)})")
                    if data_type not in total_report:
                        total_report[data_type] = {"count": 0, "size": 0}
                    if isinstance(total_report[data_type].get("count"), int) and isinstance(count, int):
                        total_report[data_type]["count"] += count
                    total_report[data_type]["size"] += size
                else: # Error case
                     print(f"  [!] {data_type.capitalize()}: {value}")


        print("\n" + "="*40)
        print("--- Total Estimated Savings ---")
        for data_type, value in total_report.items():
             if isinstance(value, int):
                 print(f"  [+] Total {data_type.capitalize()}: {format_bytes(value)}")
             elif isinstance(value, dict):
                 print(f"  [+] Total {data_type.capitalize()}: {value['count']} items ({format_bytes(value['size'])})")
        print("="*40)

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

