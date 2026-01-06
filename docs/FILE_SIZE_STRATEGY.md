# AAS File Size Management Strategy

## GitHub File Size Limits

- **< 5 MB**: ✅ Recommended (fast clones, good performance)
- **5-50 MB**: ⚠️ Warning from GitHub (acceptable but monitored)
- **50-100 MB**: 🚨 GitHub will warn but accept
- **> 100 MB**: ❌ GitHub will reject the push

## Our Strategy: 50 MB Hard Limit

**Target**: Keep all committed files **under 50 MB** to avoid GitHub warnings.

## File Categories & Handling

### 1. **Source Code** (Already Good ✅)
- Python/C# files: Typically <1 MB
- **Action**: Track normally in git

### 2. **Documentation & Config** (Already Good ✅)
- Markdown, JSON, YAML: <100 KB
- **Action**: Track normally in git

### 3. **Build Artifacts** (Excluded ✅)
- Executables, DLLs: Often >50 MB
- **Action**: Already in `.gitignore`, not tracked
- **Distribution**: Use GitHub Releases for distributing builds

### 4. **Data Files & Logs**
- **Small (<5 MB)**: Track in git
- **Medium (5-50 MB)**: Compress with gzip before committing
- **Large (>50 MB)**: Split into chunks or use external storage

### 5. **Machine Learning Models** (If applicable)
- **<50 MB**: Compress and commit
- **>50 MB**: Use Git LFS or external storage (S3, Hugging Face)

### 6. **Database Files**
- **SQLite <10 MB**: Track in git (with periodic cleanup)
- **SQLite >10 MB**: Add to `.gitignore`, document seed/migration process
- **Large DBs**: Use dumps or migration scripts instead

## Compression Strategy

For files between 5-50 MB that MUST be in git:

```powershell
# Compress a file
Compress-Archive -Path file.json -DestinationPath file.json.zip

# Decompress on checkout (add to setup script)
Expand-Archive -Path file.json.zip -DestinationPath .
```

## Large File Alternatives

### Option 1: GitHub Releases
- Attach binary builds to releases
- Not counted toward repo size
- **Best for**: Distributing executables

### Option 2: Git LFS (Large File Storage)
- First 1 GB free, then paid
- **Best for**: Versioned large files that change

### Option 3: External Storage
- AWS S3, Azure Blob, Google Cloud Storage
- Download script in repo
- **Best for**: Static large assets

### Option 4: Submodules
- Already using for `game_manager/maelstrom`
- Each submodule has its own size limit
- **Best for**: Independent projects

## Current Status

### Tracked Files Analysis:
```powershell
# Check current repo size
git count-objects -vH

# Find large tracked files
git ls-files | xargs -I{} stat -c '%s %n' {} 2>/dev/null | sort -rn | head -20
```

### Artifacts Directory:
- `artifacts/builds/` - Excluded (build outputs)
- `artifacts/batch/` - Tracked (small JSON/text files)
- `artifacts/handoff/` - Tracked (coordination files)
- `artifacts/aas.db` - Tracked if <10 MB

## Automated Size Monitoring

Add to `.github/workflows/size-check.yml`:
```yaml
name: Check File Sizes
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check for large files
        run: |
          find . -type f -size +50M | while read file; do
            echo "::error::File too large: $file"
            exit 1
          done
```

## Best Practices

1. **Before Committing Large Files**:
   - Ask: "Does this NEED to be in git?"
   - Consider: GitHub Releases, LFS, or external storage
   - If necessary: Compress or split

2. **Regular Audits**:
   ```powershell
   git ls-files | xargs du -h | sort -rh | head -20
   ```

3. **Clean History**:
   - If large file accidentally committed, use `git filter-branch` immediately
   - Keep `.gitignore` comprehensive

4. **Submodule Strategy**:
   - Large C# projects in submodules (already done)
   - Each submodule manages its own size

## Reference Commands

```powershell
# Find large files in working directory
Get-ChildItem -Recurse | Where-Object { $_.Length -gt 5MB } | Sort-Object Length -Descending

# Check what's tracked by git
git ls-files | ForEach-Object { if (Test-Path $_) { Get-Item $_ | Select-Object FullName, Length } }

# Repository total size
git count-objects -vH

# Remove file from all history
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch path/to/file" --prune-empty --tag-name-filter cat -- --all
```

---
*Last Updated: January 3, 2026*
