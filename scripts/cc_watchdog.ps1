# cc_watchdog.ps1 — AIG Claude Code crash watchdog.
#
# One check per invocation; meant to be triggered by Windows Task Scheduler
# every 60 seconds. Detects:
#   PRIMARY:   last_sprint_fire.txt stale > 30 min (catches REPL hangs)
#   SECONDARY: claude.exe absent AND sentinel >15 min (covers true crash)
#
# After CONSECUTIVE_CHECKS_REQUIRED stale checks in a row (3 min by default),
# launches `claude -p` headless with session_resume_prompt.txt. Logs to
# crash_log.md / crash_log.json; Telegrams on detect / recover / fail.
#
# State: scripts/cc_watchdog_state.json (counters, mode, history)
# Recovery lock: scripts/cc_watchdog_recovery.lock (prevents re-entry)
#
# Runs in user session (Task Scheduler configured INTERACTIVE) so the
# spawned claude.cmd has access to ~/.claude config + auto-memory.

[CmdletBinding()]
param(
    [switch]$VerboseLog,
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'

# --- Paths -------------------------------------------------------------------
$ProjectRoot   = 'C:\Users\ahmed\OneDrive\Documents\Projects\stocks\Ahmed group\Working Area\aig_engine'
$ScriptsDir    = Join-Path $ProjectRoot 'scripts'
$StateFile     = Join-Path $ScriptsDir 'cc_watchdog_state.json'
$LockFile      = Join-Path $ScriptsDir 'cc_watchdog_recovery.lock'
$WatchdogLog   = Join-Path $ScriptsDir 'cc_watchdog.log'
$SentinelFile  = Join-Path $ProjectRoot 'last_sprint_fire.txt'
$ResumePrompt  = Join-Path $ScriptsDir 'session_resume_prompt.txt'
$CrashLogMd    = Join-Path $ProjectRoot 'crash_log.md'
$CrashLogJson  = Join-Path $ProjectRoot 'crash_log.json'
$TelegramHelper = Join-Path $ScriptsDir 'cc_watchdog_telegram.py'
$ClaudeExe     = "$env:USERPROFILE\AppData\Roaming\npm\claude.cmd"

# --- Thresholds (mirror these in CRASH_RECOVERY.md if you change them) -------
$SentinelStaleSecondsHard = 1800   # 30 min: primary crash signal
$SentinelStaleSecondsSoft = 900    # 15 min: secondary (paired with no-process)
$ConsecutiveChecksRequired = 3     # 3 ticks of 60s each => 3 min confirmation
$RecoveryMaxRetries = 3
$RecoveryRetryDelaySeconds = 30
$RecoveryTimeoutSeconds = 600      # 10 min cap per attempt

# --- Helpers -----------------------------------------------------------------
function Write-WD([string]$msg) {
    $ts = (Get-Date).ToUniversalTime().ToString('o')
    $line = "$ts $msg"
    try { Add-Content -Path $WatchdogLog -Value $line -Encoding utf8 } catch {}
    if ($VerboseLog) { Write-Output $line }
}

function Send-Telegram([string]$kind, [hashtable]$extra) {
    if ($DryRun) { Write-WD "DRYRUN telegram $kind $($extra | ConvertTo-Json -Compress)"; return }
    $args = @($TelegramHelper, $kind)
    foreach ($k in $extra.Keys) {
        $args += "--$k"
        $args += "$($extra[$k])"
    }
    try {
        & python @args 2>&1 | ForEach-Object { Write-WD "telegram: $_" }
    } catch {
        Write-WD "telegram exception: $_"
    }
}

function Append-CrashLogMd([string]$ts, [string]$cause, [string]$recoveredTs, [int]$durationSec, [string]$status) {
    if (-not (Test-Path $CrashLogMd)) {
        $header = "# AIG CC Crash Log`n`nOne line per detected crash. Auto-appended by cc_watchdog.ps1.`n`n"
        Set-Content -Path $CrashLogMd -Value $header -Encoding utf8
    }
    $line = "- $ts cause=$cause | $status | recovered_at=$recoveredTs | duration=${durationSec}s"
    Add-Content -Path $CrashLogMd -Value $line -Encoding utf8
}

function Append-CrashLogJson([hashtable]$entry) {
    $arr = @()
    if (Test-Path $CrashLogJson) {
        try { $arr = @(Get-Content $CrashLogJson -Raw | ConvertFrom-Json) } catch { $arr = @() }
    }
    $arr = @($arr) + @([pscustomobject]$entry)
    # Keep last 200 entries
    if ($arr.Count -gt 200) { $arr = $arr[($arr.Count - 200)..($arr.Count - 1)] }
    $arr | ConvertTo-Json -Depth 4 | Set-Content -Path $CrashLogJson -Encoding utf8
}

function Load-State {
    $default = [ordered]@{
        consecutive_stale_checks       = 0
        mode                           = 'normal'
        last_check_ts                  = $null
        last_crash_ts                  = $null
        last_crash_cause               = $null
        last_recovery_ts               = $null
        last_recovery_duration_seconds = $null
        recoveries_today               = 0
        recoveries_today_date          = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
        total_recoveries               = 0
        total_recovery_failures        = 0
        longest_gap_seconds            = 0
        recent_recovery_durations      = @()
        watchdog_version               = '1.0'
    }
    if (Test-Path $StateFile) {
        try {
            $loaded = Get-Content $StateFile -Raw | ConvertFrom-Json
            foreach ($k in $default.Keys) {
                if ($loaded.PSObject.Properties.Name -contains $k) {
                    $default[$k] = $loaded.$k
                }
            }
        } catch { Write-WD "state load failed: $_" }
    }
    return $default
}

function Save-State([hashtable]$state) {
    try {
        $state | ConvertTo-Json -Depth 4 | Set-Content -Path $StateFile -Encoding utf8
    } catch { Write-WD "state save failed: $_" }
}

# --- Recovery in progress? ---------------------------------------------------
if (Test-Path $LockFile) {
    $lockAge = (Get-Date) - (Get-Item $LockFile).LastWriteTime
    if ($lockAge.TotalSeconds -lt $RecoveryTimeoutSeconds) {
        Write-WD "skip: recovery in progress (lock age $([int]$lockAge.TotalSeconds)s)"
        exit 0
    } else {
        Write-WD "stale lock cleared (age $([int]$lockAge.TotalSeconds)s)"
        Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    }
}

# --- Load state + reset daily counters --------------------------------------
$state = Load-State
$todayUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
if ($state.recoveries_today_date -ne $todayUtc) {
    $state.recoveries_today = 0
    $state.recoveries_today_date = $todayUtc
}
$state.last_check_ts = (Get-Date).ToUniversalTime().ToString('o')

# --- Read sentinel age ------------------------------------------------------
$sentinelAge = $null
if (Test-Path $SentinelFile) {
    try {
        $sentinelStr = (Get-Content $SentinelFile -Raw).Trim()
        $sentinelTs = [DateTime]::Parse($sentinelStr).ToUniversalTime()
        $sentinelAge = ((Get-Date).ToUniversalTime() - $sentinelTs).TotalSeconds
    } catch { Write-WD "sentinel parse failed: $_" }
}

# --- Process check ----------------------------------------------------------
$claudeProcs = @(Get-Process -Name claude -ErrorAction SilentlyContinue)
$claudeAlive = $claudeProcs.Count -gt 0

# --- Classify ---------------------------------------------------------------
$crashed = $false
$cause = ''
if ($null -ne $sentinelAge -and $sentinelAge -gt $SentinelStaleSecondsHard) {
    $crashed = $true
    $cause = "sentinel-stale-$([int]($sentinelAge/60))min"
} elseif (-not $claudeAlive -and $null -ne $sentinelAge -and $sentinelAge -gt $SentinelStaleSecondsSoft) {
    $crashed = $true
    $cause = "process-absent+sentinel-$([int]($sentinelAge/60))min"
}

# Track longest observed gap
if ($null -ne $sentinelAge -and [int]$sentinelAge -gt $state.longest_gap_seconds) {
    $state.longest_gap_seconds = [int]$sentinelAge
}

if (-not $crashed) {
    if ($state.consecutive_stale_checks -gt 0) {
        Write-WD "all-clear (was $($state.consecutive_stale_checks)). sentinel_age=$([int]$sentinelAge)s claude_alive=$claudeAlive"
    }
    $state.consecutive_stale_checks = 0
    $state.mode = 'normal'
    Save-State $state
    exit 0
}

# Crash candidate
$state.consecutive_stale_checks += 1
$state.mode = 'detecting'
Write-WD "stale-check $($state.consecutive_stale_checks)/$ConsecutiveChecksRequired cause=$cause sentinel_age=$([int]$sentinelAge)s claude_alive=$claudeAlive"

if ($state.consecutive_stale_checks -lt $ConsecutiveChecksRequired) {
    Save-State $state
    exit 0
}

# --- CRASH CONFIRMED — RECOVERY ---------------------------------------------
$state.mode = 'recovering'
$state.last_crash_cause = $cause
$crashTs = (Get-Date).ToUniversalTime().ToString('o')
$state.last_crash_ts = $crashTs
Save-State $state

Write-WD "CRASH CONFIRMED cause=$cause sentinel_age=$([int]$sentinelAge)s"
Send-Telegram detected @{ cause = $cause }

# Lock recovery (Remove-Item on completion)
$crashTs | Set-Content -Path $LockFile -Encoding utf8

if (-not (Test-Path $ResumePrompt)) {
    Write-WD "ABORT: resume prompt not found at $ResumePrompt"
    Send-Telegram failed @{ attempts = 0 }
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    $state.mode = 'failed'
    $state.total_recovery_failures += 1
    Save-State $state
    exit 1
}

$resumeText = (Get-Content $ResumePrompt -Raw).Trim()
$recovered = $false
$recoveryStart = Get-Date
$attemptsUsed = 0

for ($attempt = 1; $attempt -le $RecoveryMaxRetries; $attempt++) {
    $attemptsUsed = $attempt
    Write-WD "recovery attempt $attempt/$RecoveryMaxRetries"

    if ($DryRun) {
        Write-WD "DRYRUN would run: $ClaudeExe -p `"$resumeText`""
        $recovered = $true
        break
    }

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $proc = Start-Process -FilePath $ClaudeExe `
                              -ArgumentList "-p", $resumeText `
                              -WorkingDirectory $ProjectRoot `
                              -NoNewWindow `
                              -PassThru `
                              -RedirectStandardOutput $stdoutFile `
                              -RedirectStandardError $stderrFile
        $exited = $proc.WaitForExit($RecoveryTimeoutSeconds * 1000)
        if (-not $exited) {
            try { $proc.Kill() } catch {}
            Write-WD "recovery attempt $attempt TIMEOUT after $RecoveryTimeoutSeconds s"
        } elseif ($proc.ExitCode -eq 0) {
            $recovered = $true
            $stdoutLen = (Get-Item $stdoutFile).Length
            Write-WD "recovery attempt $attempt SUCCESS exit=0 stdout_bytes=$stdoutLen"
        } else {
            $stderrTail = Get-Content $stderrFile -Raw -ErrorAction SilentlyContinue
            $stderrTail = if ($stderrTail) { $stderrTail.Substring(0, [Math]::Min(500, $stderrTail.Length)) } else { '' }
            Write-WD "recovery attempt $attempt FAILED exit=$($proc.ExitCode) stderr=$stderrTail"
        }
    } catch {
        Write-WD "recovery attempt $attempt EXCEPTION: $_"
    } finally {
        Remove-Item $stdoutFile -Force -ErrorAction SilentlyContinue
        Remove-Item $stderrFile -Force -ErrorAction SilentlyContinue
    }

    if ($recovered) { break }
    if ($attempt -lt $RecoveryMaxRetries) { Start-Sleep -Seconds $RecoveryRetryDelaySeconds }
}

$recoveryEnd = Get-Date
$durationSec = [int]($recoveryEnd - $recoveryStart).TotalSeconds
Remove-Item $LockFile -Force -ErrorAction SilentlyContinue

if ($recovered) {
    $recoveredTs = (Get-Date).ToUniversalTime().ToString('o')
    $state.last_recovery_ts = $recoveredTs
    $state.last_recovery_duration_seconds = $durationSec
    $state.recoveries_today += 1
    $state.total_recoveries += 1
    $state.consecutive_stale_checks = 0
    $state.mode = 'normal'

    $durArr = @($state.recent_recovery_durations) + @($durationSec)
    if ($durArr.Count -gt 20) { $durArr = $durArr[($durArr.Count - 20)..($durArr.Count - 1)] }
    $state.recent_recovery_durations = $durArr

    Write-WD "RECOVERED duration=${durationSec}s attempts=$attemptsUsed"
    Send-Telegram recovered @{ "duration-seconds" = $durationSec }
    Append-CrashLogMd $crashTs $cause $recoveredTs $durationSec 'OK'
    Append-CrashLogJson @{
        crash_ts = $crashTs
        cause = $cause
        recovered_ts = $recoveredTs
        duration_seconds = $durationSec
        attempts = $attemptsUsed
        status = 'OK'
    }
} else {
    $state.total_recovery_failures += 1
    $state.mode = 'failed'
    Write-WD "RECOVERY FAILED after $RecoveryMaxRetries attempts duration=${durationSec}s"
    Send-Telegram failed @{ attempts = $RecoveryMaxRetries }
    Append-CrashLogMd $crashTs $cause '' $durationSec "MANUAL after $RecoveryMaxRetries attempts"
    Append-CrashLogJson @{
        crash_ts = $crashTs
        cause = $cause
        recovered_ts = $null
        duration_seconds = $durationSec
        attempts = $RecoveryMaxRetries
        status = 'FAILED'
    }
}

Save-State $state
