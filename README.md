# Chrome Profile Cleanup Automation

A cross-platform Python script to analyze and clean browsing data (cache, cookies, history) from all Google Chrome profiles on a user's computer. This tool helps improve browser performance, free up disk space, and protect privacy by automating the cleanup process.

# Current Version: v0.9

# Original Idea:

Blog post at: [How to Back Up All Chrome Profiles from Your Computer](https://jorgep.com/blog/how-to-back-up-all-chrome-profiles-from-your-computer/)
Followed by a 30 minute Vibe Coding session first with Perplexity and then Gemini 2.0 Flash.
Blog post here: [My Session to create a Chrome Profile cleaner script](https://jorgep.com/blog/my-session-to-create-a-chrome-profile-cleaner-script/)

# Features

* **Automatic Profile Detection**: Scans for and identifies all Chrome profiles (Default, Profile 1, etc.) and retrieves their human-readable display names.
* **Natural Sorting**: Profiles are ordered numerically (1, 2, 3... 10) instead of alphabetically (1, 10, 11) for better organization.
* **Cross-Platform**: Fully compatible with Windows, macOS, and Linux.
* **Detailed Reporting**: Analyzes profiles to report on the disk space that can be reclaimed for each data type using a clean, formatted table.
* **Integrated Backup**: Built-in prompt to trigger a PowerShell backup of all profiles to `D:\Temp` before cleaning.
* **Selective Cleaning**: Allows users to choose which specific data types to clean (e.g., cache, history, cookies).
* **Safety First**:
* Checks if Chrome is running and prompts the user to close it before making any changes.
* Includes **Safe-Stop** logic: If the backup is cancelled or fails, the cleanup process is aborted to protect data.
* Requires explicit `YES` confirmation before deleting any data.


* **Default Behavior (Dry Run)**: By default, the script runs in "safe mode." It performs a full analysis and generates a report but does not delete any files until the `--clean` flag is used.

# Dependencies

The script requires Python 3 and two external packages:

* **psutil**: To safely check if the Chrome process is running.
* **rich**: To display the analysis report in a clean, formatted table.

# Installation

Install the required Python packages using pip. On Windows, it is recommended to use the `py` launcher.

| Operating System | Command |
| --- | --- |
| **On Windows** | `py -m pip install psutil rich` |
| **On macOS / Linux** | `python3 -m pip install psutil rich` |

# Usage

All commands should be run from your terminal in the directory where `chrome_cleaner.py` is located.

## Command-Line Switches

| Switch | Argument | Description |
| --- | --- | --- |
| `--help` | (No argument) | List available parameters. |
| `--clean` | (No argument) | Required to delete data. Executes the backup and cleanup process after user confirmation. |
| `--force-close` | (No argument) | (Optional) Automatically closes Chrome if it is running. |
| `--types` | `cache,history` | (Optional) A comma-separated list of data types to clean. |

* **Available Data Types**: `history`, `cookies`, `cache`, `code_cache`.

## Examples

### 1. Perform a Dry Run (Default, Safe Mode)

Analyze profiles and show a report of what can be cleaned without deleting anything.
`py chrome_cleaner.py`

### 2. Clean ALL Default Data Types

Permanently delete default data types from every profile after a backup and confirmation.
`py chrome_cleaner.py --clean`

# Troubleshooting

If you encounter a "scripts are disabled on this system" error in PowerShell:

* Run PowerShell as Administrator and enter: `Set-ExecutionPolicy RemoteSigned`.
* Alternatively, the script is designed to attempt a `Bypass` policy automatically for the session.

# Change Log

## v0.9

* **Natural Sorting**: Fixed 1, 10, 11 alphabetical sorting for numerical profiles.
* **Profile Name Mapping**: Restored folder-to-name mapping (e.g., "jorper98(Gmail)").
* **Advanced Backup**: Integrated `BackupChromeProfiles.ps1` with "Accurate Progress" (only real profiles) and "Silent IO."
* **Safe-Stop Mechanism**: Cleanup now aborts if the PowerShell backup is cancelled or fails.

## v0.4

* Added better display of results in table format requiring `rich` library.
* Added Profile Name to the Column List.
* Fixed error not showing correct cookies in profile counter.

## v0.3

* Removed Downloads column (cleaned as part of cache).
* Added `--force-close` as an option to close Chrome Browser.

## v0.2 & v0.1

* General bug fixes and initial release.

# License

MIT License. Copyright (c) 2025 Jorge Pereira.

# Author

Jorge Pereira | GitHub: @jorper98 | Website: [https://jorgep.com](https://jorgep.com)



