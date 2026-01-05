[CmdletBinding()]
param()

# Removes common junk artifacts safely. Idempotent.

function Remove-ZeroByteZips {
    Get-ChildItem -Recurse -File -Filter *.zip -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -eq 0 } |
        ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -ErrorAction Stop
                Write-Host "Removed zero-byte zip: $($_.FullName)"
            } catch {
                Write-Host "Skipped zero-byte zip (locked?): $($_.FullName) -> $($_.Exception.Message)"
            }
        }
}

function Remove-ZipVerifyFolders {
    Get-ChildItem -Recurse -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like '*_zip_verify' } |
        ForEach-Object {
            try {
                Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop
                Write-Host "Removed verify folder: $($_.FullName)"
            } catch {
                Write-Host "Skipped verify folder (locked?): $($_.FullName) -> $($_.Exception.Message)"
            }
        }
}

function Clean-UiCurrent {
    $path = Join-Path -Path (Get-Location) -ChildPath 'ui_current'
    if (Test-Path $path) {
        try {
            Get-ChildItem $path -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction Stop
            Write-Host "Cleared ui_current/*"
        } catch {
            Write-Host "Skipped clearing ui_current (locked?): $($_.Exception.Message)"
        }
    }
}

Write-Host "Cleanup started..."
Remove-ZeroByteZips
Remove-ZipVerifyFolders
Clean-UiCurrent
Write-Host "Cleanup completed."
