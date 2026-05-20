# Restart-on-login launcher for the AIG Telegram bot.
# Idempotent: if a healthy bun server.ts is already polling, exit. Otherwise
# clean stale state and spawn a fresh one.

$ErrorActionPreference = 'Continue'

$bun = "$env:USERPROFILE\.bun\bin\bun.exe"
$pluginRoot = "$env:USERPROFILE\.claude\plugins\cache\claude-plugins-official\telegram\0.0.6"
$stateDir = "$env:USERPROFILE\.claude\channels\telegram"
$pidFile = Join-Path $stateDir 'bot.pid'
$logFile = Join-Path $stateDir 'server.log'

if (-not (Test-Path $bun)) {
    Write-Output "ERROR: bun.exe not at $bun"; exit 1
}
if (-not (Test-Path "$pluginRoot\server.ts")) {
    Write-Output "ERROR: server.ts not at $pluginRoot"; exit 1
}

# Is there already a healthy poller?
if (Test-Path $pidFile) {
    $existing = (Get-Content $pidFile -ErrorAction SilentlyContinue).Trim()
    if ($existing) {
        $proc = Get-Process -Id $existing -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -eq 'bun') {
            Write-Output ("Bot already running. pid=$existing started=" + $proc.StartTime)
            exit 0
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

# Pre-emptively kill any orphan bun processes that might hold the getUpdates lock
Get-Process -Name 'bun' -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Output ("Killing stale bun pid=" + $_.Id)
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 500

# Spawn detached. Use Start-Process so the process is not tied to this shell.
Push-Location $pluginRoot
$proc = Start-Process -FilePath $bun -ArgumentList 'server.ts' `
    -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError "$logFile.err"
Pop-Location

Start-Sleep -Seconds 2

if ($proc -and -not $proc.HasExited) {
    Write-Output ("Bot spawned. pid=" + $proc.Id)
    exit 0
} else {
    Write-Output 'Spawn failed — check server.log + server.log.err'
    if (Test-Path "$logFile.err") { Get-Content "$logFile.err" -Tail 10 }
    exit 2
}
