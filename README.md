# Chrome Profile Cleanup Automation
A cross-platform Python script to analyze and clean browsing data (cache, cookies, history) from all Google Chrome profiles on a user's computer. This tool helps improve browser performance, free up disk space, and protect privacy by automating the cleanup process.

# Current Version:  v0.4

# Original Idea: 
Blog post at: [How to Back Up All Chrome Profiles from Your Computer](https://jorgep.com/blog/how-to-back-up-all-chrome-profiles-from-your-computer/)
Followed by a  30 minute Vibe Coding session  first with Perplexity and then Gemini 2.5 Pro
Blog post here:[My Session to create a Chrome Profile cleaner script](https://jorgep.com/blog/my-session-to-create-a-chrome-profile-cleaner-script/)
         


# Features
* Automatic Profile Detection: Scans for and identifies all Chrome profiles (Default, Profile 1, etc.).
* Cross-Platform: Fully compatible with Windows, macOS, and Linux.

* Detailed Reporting: Analyzes profiles to report on the number of items and the disk space that can be reclaimed for each data type.

* Selective Cleaning: Allows users to choose which specific data types to clean (e.g., cache, history, cookies).

* Safety First:
* Checks if Chrome is running and prompts the user to close it before making any changes.

* Requires explicit user confirmation before deleting any data.
* Default Behavior: Informative Only
* By default, the script runs in a "dry run" mode. It will perform a full analysis of all profiles and generate a detailed report of what would be cleaned, but it will not delete or alter any files.

* Data is only deleted when the script is run with the --clean flag and after the user provides explicit confirmation.

# Dependencies
The script requires Python 3 and two external packages:

    psutil: To safely check if the Chrome process is running.
    rich: To display the analysis report in a clean, formatted table.

# Installation
* Clone the repository or download the script to your local machine.

* Install the required Python package using pip. It's recommended to use the Python launcher py on Windows or python3 on macOS/Linux to ensure the package is installed for the correct Python version.

|  Operating system  | Command:  | 
|-------------|--------------|
| On Windows          | py -m pip install psutil rich         |
| On macOS / Linux    | python3 -m pip install psutil rich |





# Usage
All commands should be run from your terminal or command prompt in the directory where the chrome_cleaner.py script is located.

## Command-Line Switches
      
| Switch          | Argument     | Description |
|-----------------|--------------|----------|
| --help       | (No argument)    | LIst available parameters.       |
| --clean       | (No argument)    | Required to delete data. Executes the cleanup process after displaying a warning and receiving user confirmation.       |
| --types     | cache,history | (Optional) A comma-separated list of data types to clean. If not provided, it defaults to all available types.        |


    * Available Data Types: history, cookies, downloads, cache, code_cache 




## Examples
## 1. Perform a Dry Run (Default, Safe Mode)

This command will analyze all profiles and show a report of what can be cleaned without deleting anything.
|  Operating system  | Command:  | 
|-------------|--------------|
| On Windows          | py chrome_cleaner.py         |
| On macOS / Linux    | python3 chrome_cleaner.py |


### 2. Clean ALL Default Data Types

This command will permanently delete all default data types (history, cookies, downloads, cache, and code_cache) from every profile after you confirm.

|  Operating system  | Command:  | 
|-------------|--------------|
| On Windows          | py chrome_cleaner.py --clean         |
| On macOS / Linux    | python3 chrome_cleaner.py --clean |


### 3. Clean ONLY Cache and Code Cache

This command will permanently delete only the cache and code_cache folders from every profile.


|  Operating system  | Command:  | 
|-------------|--------------|
| On Windows          | py chrome_cleaner.py --clean --types cache,code_cache         |
| On macOS / Linux    | python3 chrome_cleaner.py --clean --types cache,code_cache |



### 4. Clean ONLY History

This command will permanently delete only the browsing history from every profile.


|  Operating system  | Command:  | 
|-------------|--------------|
| On Windows          | py chrome_cleaner.py --clean --types history       |
| On macOS / Linux    | python3 chrome_cleaner.py --clean --types history |



# Change Log
## v0.4
* Added better display of results (in table format) to the terminal requiring rich library
* Added Profile Name to the Column List
* fix error not showing the correct cookies in profile counter
* Updated Readme.MD file

## v0.3
* Removed Downloads column, as it is just a counter. Will clean the counter as part of the cache cleanup
* Added --force-close  as an option to close Chrome Browser

## v0.2  
* Fix Some bugs 

## v0.1  
*Initial Version  

# License
MIT License

Copyright (c) 2025 Jorge Pereira

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

# Contributions
Contributions are welcome! If you'd like to contribute to the project, please fork the repository, create a feature branch, and submit a pull request.

Steps to Contribute:
* Fork the repository
* Create a new branch (git checkout -b feature-branch)
* Commit your changes (git commit -m 'Add new feature')
* Push to the branch (git push origin feature-branch)
* Create a pull request

# Author
If you have any questions or suggestions, feel free to reach out:

Jorge Pereira

GitHub: @jorper98

Website: https://jorgep.com