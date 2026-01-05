# Resolution: Long Directory Name Failure

## Issue
Local migration or Git operations failed due to directory paths exceeding the Windows 260-character limit (MAX_PATH).

## Root Cause
1.  **Windows Registry:** `LongPathsEnabled` was previously disabled (or not recognized by all tools).
2.  **Git Configuration:** Git was not configured to handle long paths, causing it to fail even if the OS supported them.
3.  **Deep Nesting:** Build artifacts (`bin`/`obj`), publish folders, and nested library clones (e.g., `ProjectMaelstrom/ProjectMaelstrom/Scripts/Library/...`) created paths exceeding 240 characters.

## Corrective Actions Taken
1.  **Git Config:** Enabled long path support in Git.
    ```bash
    git config core.longpaths true
    ```
2.  **Workspace Cleanup:** Removed deep build artifacts (`bin`, `obj`) and `publish` folders to reduce immediate path depth.
    ```bash
    python -c "import shutil, os; [shutil.rmtree(os.path.join(r, d)) for r, ds, fs in os.walk('.') for d in ds if d in ('bin', 'obj', 'publish')]"
    ```
3.  **Directory Flattening:** Removed redundant nesting in `ProjectMaelstrom` and `artifacts/handoff` to shorten paths by ~20 characters.
    - Moved `game_manager/maelstrom/ProjectMaelstrom/ProjectMaelstrom/*` to `game_manager/maelstrom/ProjectMaelstrom/`.
    - Updated `AaroneousAutomationSuite.sln` to reflect the new project path.

## Recommendations for Prevention
1.  **Flatten Structures:** Avoid redundant nesting like `ProjectMaelstrom/ProjectMaelstrom/`.
2.  **Registry Check:** Ensure `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled` is set to `1`.
3.  **Shorten Library Paths:** When cloning external libraries, use shorter directory names or move them closer to the root.
4.  **Clean Publish Folders:** Regularly clear `publish` and `bin` directories if they are not needed for active development.
