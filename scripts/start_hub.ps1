# AAS Hub Startup Script
# Starts the Hub as a detached background process

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$logFile = Join-Path $projectRoot "artifacts\hub.log"
$pidFile = Join-Path $projectRoot "artifacts\hub.pid"
$envFile = Join-Path $projectRoot ".env"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$dbFile = Join-Path $projectRoot "artifacts\aas_hub.db"

function Test-Prerequisites {
    param([switch]$Verbose)
    
    $issues = @()
    
    # Check if virtual environment exists
    if (-not (Test-Path $pythonExe)) {
        $issues += "Virtual environment not found at .venv\"
        Write-Host "[!] Virtual environment missing" -ForegroundColor Red
        Write-Host "    Run: python -m venv .venv" -ForegroundColor Yellow
    } elseif ($Verbose) {
        Write-Host "[OK] Virtual environment found" -ForegroundColor Green
    }
    
    # Check if .env file exists
    if (-not (Test-Path $envFile)) {
        $issues += ".env file not found"
        Write-Host "[!] Configuration file missing" -ForegroundColor Red
        Write-Host "    Copy .env.example to .env and configure" -ForegroundColor Yellow
    } elseif ($Verbose) {
        Write-Host "[OK] Configuration file found" -ForegroundColor Green
    }
    
    # Check artifacts directory and permissions
    $artifactsDir = Join-Path $projectRoot "artifacts"
    if (-not (Test-Path $artifactsDir)) {
        Write-Host "[*] Creating artifacts directory..." -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null
    } elseif ($Verbose) {
        Write-Host "[OK] Artifacts directory exists" -ForegroundColor Green
    }
    
    # Test write permissions
    $testFile = Join-Path $artifactsDir ".write_test"
    try {
        "test" | Out-File $testFile -ErrorAction Stop
        Remove-Item $testFile -ErrorAction SilentlyContinue
        if ($Verbose) { Write-Host "[OK] Artifacts directory writable" -ForegroundColor Green }
    } catch {
        $issues += "Cannot write to artifacts directory"
        Write-Host "[!] Artifacts directory not writable" -ForegroundColor Red
    }
    
    # Check log file size and rotate if needed (> 100MB)
    if (Test-Path $logFile) {
        $logSize = (Get-Item $logFile).Length / 1MB
        if ($logSize -gt 100) {
            Write-Host "[*] Log file is $([math]::Round($logSize, 2))MB, rotating..." -ForegroundColor Yellow
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $archiveLog = Join-Path $projectRoot "artifacts\hub_$timestamp.log"
            Move-Item $logFile $archiveLog -Force
            Write-Host "[OK] Log rotated to hub_$timestamp.log" -ForegroundColor Green
        } elseif ($Verbose) {
            Write-Host "[OK] Log file size OK ($([math]::Round($logSize, 2))MB)" -ForegroundColor Green
        }
    }
    
    # Check database file integrity (basic check)
    if (Test-Path $dbFile) {
        try {
            $dbBytes = [System.IO.File]::ReadAllBytes($dbFile)
            if ($dbBytes.Length -lt 100) {
                $issues += "Database file appears corrupted (too small)"
                Write-Host "[!] Database may be corrupted" -ForegroundColor Red
            } elseif ($Verbose) {
                $dbSize = (Get-Item $dbFile).Length / 1KB
                $roundedSize = [math]::Round($dbSize, 2)
                Write-Host "[OK] Database exists ($roundedSize KB)" -ForegroundColor Green
            }
        } catch {
            $issues += "Cannot read database file"
            Write-Host "[!] Database file unreadable" -ForegroundColor Red
        }
    } elseif ($Verbose) {
        Write-Host "[*] Database will be created on first run" -ForegroundColor Gray
    }
    
    # Check available disk space (warn if < 1GB)
    $drive = (Get-Item $projectRoot).PSDrive
    $freeSpace = (Get-PSDrive $drive.Name).Free / 1GB
    if ($freeSpace -lt 1) {
        Write-Host "[!] Low disk space: $([math]::Round($freeSpace, 2))GB free" -ForegroundColor Yellow
    } elseif ($Verbose) {
        $roundedFree = [math]::Round($freeSpace, 2)
        Write-Host "[OK] Disk space OK ($roundedFree GB free)" -ForegroundColor Green
    }
    
    return ($issues.Count -eq 0)
}

function Get-HubStatus {
    if (Test-Path $pidFile) {
        $processId = Get-Content $pidFile
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "[OK] AAS Hub is running (PID: $processId)" -ForegroundColor Green
            Write-Host "  Started: $($process.StartTime)" -ForegroundColor Gray
            Write-Host "  CPU: $([math]::Round($process.CPU, 2))s" -ForegroundColor Gray
            Write-Host "  Memory: $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Gray
            return $true
        }
    }
    Write-Host "[-] AAS Hub is not running" -ForegroundColor Red
    return $false
}

function Stop-Hub {
    if (Test-Path $pidFile) {
        $processId = Get-Content $pidFile
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Stopping AAS Hub (PID: $processId)..." -ForegroundColor Yellow
            Stop-Process -Id $processId -Force
            Start-Sleep -Seconds 2
            Remove-Item $pidFile -ErrorAction SilentlyContinue
            Write-Host "[OK] Hub stopped" -ForegroundColor Green
        } else {
            Write-Host "Hub process not found, cleaning up PID file" -ForegroundColor Yellow
            Remove-Item $pidFile -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "Hub not running (no PID file)" -ForegroundColor Gray
    }
    
    # Stop tray application if running
    $trayProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*aas_tray.py*"
    }
    if ($trayProcesses) {
        Write-Host "Stopping system tray application..." -ForegroundColor Yellow
        $trayProcesses | Stop-Process -Force
        Write-Host "[OK] System tray stopped" -ForegroundColor Green
    }
}

function Clear-ZombieProcesses {
    Write-Host "Checking for zombie processes..." -ForegroundColor Gray
    
    # Check if port 50051 is in use
    $portInUse = netstat -ano | Select-String ":50051.*LISTENING"
    if ($portInUse) {
        $portInUse | ForEach-Object {
            if ($_ -match "\s+(\d+)$") {
                $zombiePid = $Matches[1]
                $zombieProcess = Get-Process -Id $zombiePid -ErrorAction SilentlyContinue
                if ($zombieProcess -and $zombieProcess.ProcessName -eq "python") {
                    Write-Host "  Killing zombie process holding port 50051 (PID: $zombiePid)" -ForegroundColor Yellow
                    Stop-Process -Id $zombiePid -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 500
                }
            }
        }
    }
    
    # Check if port 8000 is in use
    $portInUse = netstat -ano | Select-String ":8000.*LISTENING"
    if ($portInUse) {
        $portInUse | ForEach-Object {
            if ($_ -match "\s+(\d+)$") {
                $zombiePid = $Matches[1]
                $zombieProcess = Get-Process -Id $zombiePid -ErrorAction SilentlyContinue
                if ($zombieProcess -and $zombieProcess.ProcessName -eq "python") {
                    Write-Host "  Killing zombie process holding port 8000 (PID: $zombiePid)" -ForegroundColor Yellow
                    Stop-Process -Id $zombiePid -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 500
                }
            }
        }
    }
    
    # Clean up stale PID file if process isn't running
    if (Test-Path $pidFile) {
        $processId = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($processId) {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if (-not $process) {
                Write-Host "  Removing stale PID file" -ForegroundColor Yellow
                Remove-Item $pidFile -ErrorAction SilentlyContinue
            }
        }
    }
}

function Start-Hub {
    # Check if already running
    if (Test-Path $pidFile) {
        $processId = Get-Content $pidFile
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "[-] Hub already running (PID: $processId)" -ForegroundColor Red
            Write-Host "  Use -Stop or -Restart flag" -ForegroundColor Gray
            return
        }
    }
    
    # Verify prerequisites
    Write-Host "`nValidating environment..." -ForegroundColor Cyan
    if (-not (Test-Prerequisites)) {
        Write-Host "`n[!] Prerequisites check failed. Fix issues above before starting." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Environment ready`n" -ForegroundColor Green
    
    # Clear any zombie processes before starting
    Clear-ZombieProcesses

    Write-Host "Starting AAS Hub..." -ForegroundColor Cyan
    $startCmd = @"
`$env:PYTHONPATH = '$projectRoot'
Set-Location '$projectRoot'
& '$pythonExe' hub.py
"@

    # Start detached process
    $process = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $startCmd `
        -WindowStyle Hidden -PassThru

    # Save PID
    $process.Id | Out-File $pidFile
    
    # Wait a bit to check if it started
    Start-Sleep -Seconds 3
    
    if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
        Write-Host "[OK] AAS Hub started (PID: $($process.Id))" -ForegroundColor Green
        Write-Host "  Web: http://localhost:8000" -ForegroundColor Gray
        Write-Host "  IPC: localhost:50051" -ForegroundColor Gray
        Write-Host "  Logs: $logFile" -ForegroundColor Gray
        
        # Launch system tray application
        Write-Host "Launching system tray..." -ForegroundColor Cyan
        $trayScript = Join-Path $scriptDir "aas_tray.py"
        $trayCmd = @"
`$env:PYTHONPATH = '$projectRoot'
Set-Location '$projectRoot'
& '$pythonExe' '$trayScript'
"@
        Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $trayCmd `
            -WindowStyle Hidden
        Write-Host "[OK] System tray icon launched" -ForegroundColor Green
    } else {
        Write-Host "[-] Hub failed to start" -ForegroundColor Red
        Write-Host "  Check logs: $logFile" -ForegroundColor Yellow
    }
}

# Handle command flags
if ($Status) {
    Test-Prerequisites -Verbose
    Write-Host ""
    Get-HubStatus
} elseif ($Stop) {
    Stop-Hub
} elseif ($Restart) {
    Stop-Hub
    Start-Sleep -Seconds 1
    Start-Hub
} else {
    Start-Hub
}
