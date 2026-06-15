# cc_watchdog.ps1 -- AIG Claude Code crash watchdog.
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
#
# v1.2 (2026-05-23): five correctness fixes + two testing affordances after
# the 25-recovery cascade on 2026-05-22 left a 49-process claude.exe orphan
# pile overnight. See diff vs. v1.0:
#   1. Pre-spawn Stop-StaleClaudeSessions: kill any existing claude.exe +
#      descendants before launching a recovery (root cause: prior recoveries
#      stacked on top of the hung REPL instead of replacing it).
#   2. Cause-string distinguishes hung-repl-* (claude alive) from
#      sentinel-stale-* (claude absent) for crash-log clarity. Recovery
#      kills existing claude.exe in either case -- there is no "claude alive
#      but skip recovery" branch.
#   3. $RecoveriesMaxPerDay cascade brake (5/UTC-day). Trips state.mode =
#      'capped' until the next UTC day or operator clears it.
#   4. Post-recovery descendant reap: claude.exe forks Node workers/MCP
#      children that do not die with the parent (no Job Object binding).
#      Kill anything started since $recoveryStart at the end of the run.
#   5. Stop-ProcessTree replaces $proc.Kill($true): PS 5.1 / .NET Framework
#      has no Kill(bool entireProcessTree) overload; the old call threw
#      MethodNotFoundException that the empty catch{} silently swallowed.
# Testing affordances (v1.2):
#   - -IgnorePause: bypass cron_paused.flag for dry-runs / manual recovery
#   - -PreserveForegroundParent <PID>: exclude PID + its descendants from
#     pre-spawn kill AND post-recovery reap. Used by supervised live runs so
#     we don't terminate the operator's foreground CC session that's
#     watching us. The crash-log entry inherits the same exclude flagging.
#   - [DRYRUN] cause-string prefix when -DryRun is set, so crash_log.md /
#     crash_log.json end-to-end exercise is distinguishable from real
#     incidents (operator filters/moves these after testing).
#
# v1.3 (2026-05-23): command-line scoping. Stop-StaleClaudeSessions and the
# process check now use Get-ClaudeCodeCliProcesses, which filters
# Get-Process claude by CommandLine substring 'claude-code' or the explicit
# npm path '\@anthropic-ai\claude-code\'. Excludes Claude Desktop (the
# consumer chat client, MSIX install) from kill/reap. Without this, v1.2's
# Get-Process -Name claude matched both `claude.exe` (CC CLI) and
# `Claude.exe` (Desktop) case-insensitively, so a real recovery would
# terminate the user's Desktop conversation alongside the CC CLI.
#
# v1.4 (2026-05-23): two-part correctness fix to v1.3's preserve-set
# wiring. Observed in v1.3 supervised live run 2026-05-23T08:58Z and
# isolated in v1.4 Phase D direct-binder test.
#   Root cause: Get-ProcessDescendants returned `,$descendants` to "prevent
#     single-element unwrapping". The wrapping caused
#     @(Get-ProcessDescendants ...) at call sites to produce a NESTED
#     Object[] (one element of which was itself an Object[]). The nested
#     Object[] could not be cast to Int32, surfacing as either
#     ParameterArgumentTransformationError (when bound to [int[]]
#     $PreservePids) or InvalidCastException (when explicitly cast via
#     [int[]] at construction).
#   Fix 1 (the actual fix): Get-ProcessDescendants now uses a strongly-typed
#     List[int], returns [int[]]$descendants.ToArray(), and lets the
#     pipeline unroll naturally.
#   Fix 2 (defense in depth): preserve-set construction explicitly casts to
#     [int[]] so binding remains robust if a future helper regresses.
# Bug only manifested in the live (non-DryRun) branch where
# Stop-StaleClaudeSessions is invoked; the dry-run path branches around it.
#
# v1.5 (2026-06-11): post-mortem fixes for the 2026-05-27 runaway (17 hung
# orphans; cron_paused.flag MANUAL MODE). Two changes:
#   1. Get-ClaudeCodeCliProcesses: v1.3's CommandLine substring match
#      ('claude-code' / npm path) matched NOTHING once the CLI moved to the
#      native installer (~\.local\bin\claude.exe), and silently spared
#      processes with unreadable command lines -- 13/17 orphans escaped the
#      pre-spawn reap on 2026-05-27. Now classifies by ExecutablePath
#      (Desktop excluded by its \WindowsApps\ install path), always spares
#      the --remote-control listener, includes headless -p/--print spawns
#      (what this watchdog launches), and for bare/unreadable command lines
#      falls back to PID-tree state: reap only if the parent process is dead
#      (a live interactive session keeps its powershell parent and is
#      spared; a watchdog spawn whose tick exited is a true orphan).
#   2. $ClaudeExe: prefer the native installer path. Both v1.3 npm paths are
#      gone from disk, so every real recovery spawn would have failed.
#
# Encoding note: this file is ASCII-only on purpose. PowerShell 5.1 reads
# no-BOM .ps1 files as Windows-1252; em-dashes (U+2014) inside string
# literals corrupt under that decode and break parsing. Stick to ASCII.

[CmdletBinding()]
param(
    [switch]$VerboseLog,
    [switch]$DryRun,
    [switch]$IgnorePause,
    [int]$PreserveForegroundParent = 0
)

$ErrorActionPreference = 'Continue'

# --- Paths -------------------------------------------------------------------
$ProjectRoot   = 'C:\aig_engine'
$ScriptsDir    = Join-Path $ProjectRoot 'scripts'
$StateFile     = Join-Path $ScriptsDir 'cc_watchdog_state.json'
$LockFile      = Join-Path $ScriptsDir 'cc_watchdog_recovery.lock'
$CronPausedFlag = Join-Path $ScriptsDir 'cron_paused.flag'
$WatchdogLog   = Join-Path $ScriptsDir 'cc_watchdog.log'
$SentinelFile  = Join-Path $ProjectRoot 'last_sprint_fire.txt'
$ResumePrompt  = Join-Path $ScriptsDir 'session_resume_prompt.txt'
$CrashLogMd    = Join-Path $ProjectRoot 'crash_log.md'
$CrashLogJson  = Join-Path $ProjectRoot 'crash_log.json'
$TelegramHelper = Join-Path $ScriptsDir 'cc_watchdog_telegram.py'
# Use the direct .exe rather than the .cmd wrapper so Process.Start handles
# argv reliably (.cmd routes through cmd.exe with its own quoting quirks).
# v1.5: native installer path first -- the npm install was removed when the
# CLI migrated to the native installer, leaving both legacy paths dangling.
$ClaudeExe     = "$env:USERPROFILE\.local\bin\claude.exe"
if (-not (Test-Path $ClaudeExe)) {
    $ClaudeExe = "$env:USERPROFILE\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
}
if (-not (Test-Path $ClaudeExe)) {
    # Fallback to the .cmd wrapper if the unwrapped binary ever moves.
    $ClaudeExe = "$env:USERPROFILE\AppData\Roaming\npm\claude.cmd"
}

# --- Thresholds (mirror these in CRASH_RECOVERY.md if you change them) -------
$SentinelStaleSecondsHard = 1800   # 30 min: primary crash signal
$SentinelStaleSecondsSoft = 900    # 15 min: secondary (paired with no-process)
$ConsecutiveChecksRequired = 3     # 3 ticks of 60s each => 3 min confirmation
$RecoveryMaxRetries = 3
$RecoveryRetryDelaySeconds = 30
$RecoveryTimeoutSeconds = 600      # 10 min cap per attempt
$RecoveriesMaxPerDay = 5           # cascade brake; 25 in one day on 2026-05-22

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

# --- Process-tree helpers (added 2026-05-23) ---------------------------------
# Replaces the v1.0 reliance on Process.Kill(bool entireProcessTree), which
# doesn't exist on .NET Framework 4.x (powershell.exe 5.1). The watchdog
# task invokes powershell.exe so the old $proc.Kill($true) threw
# MethodNotFoundException and the empty catch{} swallowed it silently.
function Get-ProcessDescendants {
    param([int]$ParentId)
    # v1.4: return as [int[]] and let the pipeline unroll. The v1.1-v1.3
    # `return ,$descendants` wrapped the result in an outer 1-element array
    # to "prevent single-element unwrapping" -- but it caused
    # @(Get-ProcessDescendants ...) at call sites to produce a NESTED
    # Object[] (one element of which was itself an Object[]), which then
    # broke [int[]] casts upstream with a Object[]->Int32 conversion error
    # (observed in v1.3 supervised live run 2026-05-23T08:58Z and in v1.4
    # Phase D when the cast was moved earlier). Pipeline-unroll is the
    # natural PowerShell idiom; both call sites (Stop-ProcessTree's
    # `$descendants | Sort-Object` foreach, and the preserve-set builder's
    # `@(Get-ProcessDescendants ...)` + cast) handle empty/1/many uniformly.
    [System.Collections.Generic.List[int]]$descendants = New-Object 'System.Collections.Generic.List[int]'
    $stack = New-Object System.Collections.Generic.Stack[int]
    $stack.Push($ParentId)
    $seen = @{ $ParentId = $true }
    while ($stack.Count -gt 0) {
        $current = $stack.Pop()
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$current" -ErrorAction SilentlyContinue)
        foreach ($child in $children) {
            $childPid = [int]$child.ProcessId
            if ($seen.ContainsKey($childPid)) { continue }
            $seen[$childPid] = $true
            $descendants.Add($childPid)
            $stack.Push($childPid)
        }
    }
    return [int[]]$descendants.ToArray()
}

function Stop-ProcessTree {
    param(
        [int]$ProcessId,
        [string]$Reason = ''
    )
    # Snapshot before killing: once the parent exits, ParentProcessId rows on
    # children become a stale PID that Windows may have recycled.
    $descendants = Get-ProcessDescendants -ParentId $ProcessId
    foreach ($descPid in ($descendants | Sort-Object -Unique -Descending)) {
        try {
            Stop-Process -Id $descPid -Force -ErrorAction Stop
            Write-WD "killed descendant pid=$descPid (reason=$Reason)"
        } catch {
            Write-WD "kill descendant pid=$descPid skipped: $($_.Exception.Message)"
        }
    }
    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        Write-WD "killed parent pid=$ProcessId (reason=$Reason)"
    } catch {
        Write-WD "kill parent pid=$ProcessId skipped (likely already exited): $($_.Exception.Message)"
    }
}

function Get-ClaudeCodeCliProcesses {
    # v1.5: classify by ExecutablePath + orphan state, not CommandLine
    # substring. The v1.3 match spared every native-install CLI process and
    # every unreadable command line (13/17 orphans escaped on 2026-05-27).
    # Returns reap-candidate Process objects (possibly empty):
    #   EXCLUDE Claude Desktop (MSIX): path under \WindowsApps\Claude...;
    #     its Electron helpers also carry --type=.
    #   EXCLUDE the always-on remote-control listener (--remote-control).
    #   INCLUDE explicit CC CLI spawns: legacy npm-path match, or headless
    #     -p/--print invocations (what this watchdog launches).
    #   Bare or unreadable command line: fall back to PID-tree state --
    #     INCLUDE only if the parent process is dead or provably recycled
    #     (parent younger than child). A live interactive session keeps its
    #     powershell/terminal parent and is spared.
    $all = @(Get-Process -Name claude -ErrorAction SilentlyContinue)
    $cli = @()
    foreach ($p in $all) {
        $wmi = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue
        if (-not $wmi) { continue }
        $cl = $wmi.CommandLine
        $exePath = $wmi.ExecutablePath
        if ($exePath -match '\\WindowsApps\\Claude' -or
            $cl -match '\\WindowsApps\\Claude' -or
            $cl -match '--type=') { continue }
        if ($cl -match '--remote-control') { continue }
        # NOTE: do NOT match the bare substring 'claude-code' here. Claude
        # Desktop's local-agent-mode sessions run from
        # Roaming\Claude\claude-code\<ver>\claude.exe with Desktop as their
        # live parent; the broad substring would mark them for reaping. They
        # are governed by the parent-alive fallback below instead (reaped
        # only if Desktop itself died and orphaned them).
        if ($cl -match '\\@anthropic-ai\\claude-code\\' -or
            $cl -match '(^|\s)-p(\s|$)|--print') {
            $cli += $p
            continue
        }
        # Bare/unreadable command line: orphan iff parent is gone. Bias to
        # sparing -- only flag recycling when both CreationDates are readable.
        $parentAlive = $false
        try {
            $par = Get-CimInstance Win32_Process -Filter "ProcessId=$($wmi.ParentProcessId)" -ErrorAction SilentlyContinue
            if ($par) {
                $parentAlive = $true
                if ($par.CreationDate -and $wmi.CreationDate -and
                    $par.CreationDate -gt $wmi.CreationDate) { $parentAlive = $false }
            }
        } catch {}
        if (-not $parentAlive) { $cli += $p }
    }
    # v1.5: plain return + pipeline unroll, same fix v1.4 applied to
    # Get-ProcessDescendants. `return ,$cli` handed callers a 1-element
    # array CONTAINING the result array, so @(...).Count at every call
    # site was 1 regardless of how many processes matched.
    return $cli
}

function Stop-StaleClaudeSessions {
    param(
        [string]$Reason = 'pre-recovery cleanup',
        [int[]]$PreservePids = @()
    )
    $stale = @(Get-ClaudeCodeCliProcesses)
    if ($stale.Count -eq 0) {
        Write-WD "stale-cleanup: no claude.exe present ($Reason)"
        return 0
    }
    $killing = @($stale | Where-Object { $PreservePids -notcontains $_.Id })
    $preserved = @($stale | Where-Object { $PreservePids -contains $_.Id })
    if ($preserved.Count -gt 0) {
        Write-WD "stale-cleanup: preserving pids=$(($preserved | Select-Object -ExpandProperty Id) -join ',') ($Reason)"
    }
    if ($killing.Count -eq 0) {
        Write-WD "stale-cleanup: nothing to terminate after preserve filter ($Reason)"
        return 0
    }
    Write-WD "stale-cleanup: terminating $($killing.Count) claude.exe + descendants ($Reason)"
    foreach ($p in $killing) {
        Stop-ProcessTree -ProcessId $p.Id -Reason $Reason
    }
    return $killing.Count
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
    # Use the Python helper so the file stays a clean JSON array. PowerShell
    # 5.1 ConvertTo-Json on a mixed Hashtable/PSCustomObject pipeline tends
    # to emit a wrapped {value, Count} object which the dashboard widget
    # can't parse.
    #
    # Pass via TEMP FILE not argv: PowerShell argv handling of strings with
    # curly braces / quotes mangles the JSON in transit (the failure mode
    # observed 2026-05-22 was "Expecting property name enclosed in double
    # quotes: line 1 column 2" on every recovery's crash_log.json append).
    $json = $entry | ConvertTo-Json -Depth 4 -Compress
    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText(
            $tmp, $json, [System.Text.UTF8Encoding]::new($false)
        )
        & python "$ScriptsDir\crash_log_append.py" --file $tmp 2>&1 | ForEach-Object {
            Write-WD "crash_log: $_"
        }
    } catch {
        Write-WD "crash_log append exception: $_"
    } finally {
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    }
}

function Load-State {
    # Plain hashtable so $state.key access works (OrderedDictionary doesn't
    # expose property-style access; we trade key ordering in the JSON output
    # for the simpler $state.foo syntax everywhere else).
    $default = @{
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
        watchdog_version               = '1.5'
    }
    if (Test-Path $StateFile) {
        try {
            $loaded = Get-Content $StateFile -Raw | ConvertFrom-Json
            foreach ($k in @($default.Keys)) {
                if ($loaded.PSObject.Properties.Name -contains $k) {
                    $default[$k] = $loaded.$k
                }
            }
        } catch { Write-WD "state load failed: $_" }
    }
    # Script version wins over whatever the state file recorded.
    $default.watchdog_version = '1.5'
    return $default
}

function Save-State($state) {
    try {
        $state | ConvertTo-Json -Depth 4 | Set-Content -Path $StateFile -Encoding utf8
    } catch { Write-WD "state save failed: $_" }
}

# --- Intentional-pause check (root-cause fix for false-fire loop) ------------
# When the operator intentionally pauses the sprint cron (e.g., during a
# framework directive transition), the sentinel naturally ages because nothing
# is touching it. Without this check, the watchdog interprets the silence as
# a crash and runs costly `claude -p` recoveries on a 3-5 minute cycle that
# don't actually fix anything (the recovery completes "successfully" but the
# cron is still paused, sentinel still ages, loop repeats).
#
# Workflow:
#   - Pause cron: create scripts/cron_paused.flag with an explanation
#   - Re-enable cron: delete the flag (operator action; no auto-resume)
#   - -IgnorePause: bypass the flag for dry-runs / manual recovery
if (Test-Path $CronPausedFlag) {
    if ($IgnorePause) {
        Write-WD "pause flag present but -IgnorePause set: continuing"
    } else {
        $reason = (Get-Content $CronPausedFlag -Raw -ErrorAction SilentlyContinue) -replace "`r?`n", ' / '
        if (-not $reason) { $reason = '(no reason text)' }
        Write-WD "skip: cron intentionally paused (flag exists). reason=$reason"
        # Update last_check_ts so the dashboard widget shows the watchdog is alive,
        # but don't advance crash counters and don't run recovery.
        $state = Load-State
        $state.last_check_ts = (Get-Date).ToUniversalTime().ToString('o')
        $state.mode = 'monitoring_paused'
        $state.consecutive_stale_checks = 0
        Save-State $state
        exit 0
    }
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
    # New UTC day: release any 'capped' mode so we start fresh.
    if ($state.mode -eq 'capped') { $state.mode = 'normal' }
}
$state.last_check_ts = (Get-Date).ToUniversalTime().ToString('o')

# --- Daily cap (cascade brake) ----------------------------------------------
# 25 cascaded recoveries on 2026-05-22 spent ~9 hours of CPU "succeeding"
# without ever advancing the sentinel. After $RecoveriesMaxPerDay recoveries
# in one UTC day, refuse to run another and require manual intervention
# (operator deletes the flag / resets counter / or waits for UTC midnight).
if ($state.recoveries_today -ge $RecoveriesMaxPerDay) {
    if ($state.mode -ne 'capped') {
        Write-WD "DAILY-CAP REACHED ($($state.recoveries_today)/$RecoveriesMaxPerDay): refusing further recoveries today. Operator must intervene."
        # Reuse the existing 'failed' Telegram kind so the helper schema is unchanged.
        Send-Telegram failed @{ attempts = 0 }
    } else {
        Write-WD "skip: daily cap still in effect ($($state.recoveries_today)/$RecoveriesMaxPerDay)"
    }
    $state.mode = 'capped'
    $state.consecutive_stale_checks = 0
    Save-State $state
    exit 0
}

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
# Use Get-ClaudeCodeCliProcesses so "claude alive?" reflects CC CLI presence
# only; Claude Desktop running alongside doesn't count for sprint-cron purposes.
$claudeProcs = @(Get-ClaudeCodeCliProcesses)
$claudeAlive = $claudeProcs.Count -gt 0

# --- Classify ---------------------------------------------------------------
# The classifier still fires on stale sentinel even when claude is alive
# (that's the hung-REPL scenario), but the recovery path now always starts
# with Stop-StaleClaudeSessions, so the orphan-stacking pattern is broken
# regardless of which branch fires. The cause string is annotated so
# crash_log.md makes the two scenarios distinguishable post-hoc.
$crashed = $false
$cause = ''
if ($null -ne $sentinelAge -and $sentinelAge -gt $SentinelStaleSecondsHard) {
    $crashed = $true
    if ($claudeAlive) {
        $cause = "hung-repl-sentinel-$([int]($sentinelAge/60))min-procs-$($claudeProcs.Count)"
    } else {
        $cause = "sentinel-stale-$([int]($sentinelAge/60))min"
    }
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

# --- CRASH CONFIRMED -- RECOVERY --------------------------------------------
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

# --- Build preserve set -----------------------------------------------------
# -PreserveForegroundParent + all its descendants are excluded from both the
# pre-spawn kill and the post-recovery reap. Used by supervised live runs so
# we don't terminate the operator's foreground CC session that's watching us.
$preservePids = [int[]]@()
if ($PreserveForegroundParent -gt 0) {
    # v1.4: explicit [int[]] cast. Without it, @(int) + @(Get-ProcessDescendants)
    # gives Object[] which fails PS 5.1's binder to [int[]]$PreservePids on
    # Stop-StaleClaudeSessions. See v1.3 supervised-live-run bug 2026-05-23T08:58Z.
    $preservePids = [int[]](@($PreserveForegroundParent) + @(Get-ProcessDescendants -ParentId $PreserveForegroundParent))
    Write-WD "preserve-foreground: PID $PreserveForegroundParent + $($preservePids.Count - 1) descendant(s) excluded from kill/reap"
}

# --- Pre-spawn cleanup ------------------------------------------------------
# Kill any existing claude.exe + descendants BEFORE spawning the recovery
# instance. Without this, a hung REPL keeps running while the recovery
# stacks a fresh headless claude on top, AND the prior session's tool/MCP
# children survive unsupervised. This was the orphan-accumulation engine
# before 2026-05-23.
#
# In DryRun, log what we *would* terminate but don't actually kill anything
# (the dry-run must be safe to invoke with a live foreground REPL).
if ($DryRun) {
    $would = @(Get-ClaudeCodeCliProcesses | Where-Object { $preservePids -notcontains $_.Id })
    Write-WD "DRYRUN pre-spawn cleanup would terminate $($would.Count) claude-code CLI process(es) + descendants (preserve=$($preservePids.Count) pids)"
} else {
    $killed = Stop-StaleClaudeSessions -Reason 'pre-recovery' -PreservePids $preservePids
    if ($killed -gt 0) {
        # Give Windows ~2s to release handles before respawning.
        Start-Sleep -Seconds 2
    }
}

for ($attempt = 1; $attempt -le $RecoveryMaxRetries; $attempt++) {
    $attemptsUsed = $attempt
    Write-WD "recovery attempt $attempt/$RecoveryMaxRetries"

    if ($DryRun) {
        $preview = if ($resumeText.Length -gt 80) { $resumeText.Substring(0, 80) + '...' } else { $resumeText }
        Write-WD "DRYRUN would run: $ClaudeExe -p `"$preview`""
        $recovered = $true
        break
    }

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    $recoveryPid = $null
    try {
        # Build ProcessStartInfo directly to (a) explicitly redirect stdin
        # to silence claude's 3s "no stdin received" warning, (b) pass the
        # prompt as a single argv element, and (c) get a reliable ExitCode
        # via the .exe path (the .cmd wrapper hides the real process).
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $ClaudeExe
        # Manual argv quoting: wrap prompt in double quotes, backslash-escape
        # any embedded double quotes. PowerShell 5.1 ProcessStartInfo only
        # supports the .Arguments single-string form.
        $escaped = $resumeText.Replace('"', '\"')
        $psi.Arguments = "-p `"$escaped`""
        $psi.WorkingDirectory = $ProjectRoot
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardInput = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true

        $proc = [System.Diagnostics.Process]::Start($psi)
        $recoveryPid = $proc.Id
        # Close stdin immediately so claude doesn't wait the 3s grace period
        # for piped input.
        $proc.StandardInput.Close()

        $stdoutBuilder = [System.Text.StringBuilder]::new()
        $stderrBuilder = [System.Text.StringBuilder]::new()
        $proc.add_OutputDataReceived({ if ($EventArgs.Data) { [void]$stdoutBuilder.AppendLine($EventArgs.Data) } })
        $proc.add_ErrorDataReceived({ if ($EventArgs.Data) { [void]$stderrBuilder.AppendLine($EventArgs.Data) } })
        $proc.BeginOutputReadLine()
        $proc.BeginErrorReadLine()

        $exited = $proc.WaitForExit($RecoveryTimeoutSeconds * 1000)
        if (-not $exited) {
            # PS 5.1 / .NET Framework has no Kill(bool) overload: use the
            # process-tree helper. The old $proc.Kill($true) threw
            # MethodNotFoundException, silently swallowed.
            Write-WD "recovery attempt $attempt TIMEOUT after $RecoveryTimeoutSeconds s; killing tree pid=$recoveryPid"
            Stop-ProcessTree -ProcessId $recoveryPid -Reason 'recovery-timeout'
        } else {
            $exitCode = $proc.ExitCode
            $stdoutLen = $stdoutBuilder.Length
            if ($exitCode -eq 0) {
                $recovered = $true
                Write-WD "recovery attempt $attempt SUCCESS exit=0 stdout_bytes=$stdoutLen"
            } else {
                $stderrTail = $stderrBuilder.ToString()
                $stderrTail = if ($stderrTail) { $stderrTail.Substring(0, [Math]::Min(500, $stderrTail.Length)) } else { '' }
                Write-WD "recovery attempt $attempt FAILED exit=$exitCode stderr=$stderrTail"
            }
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

# --- Post-recovery descendant reap ------------------------------------------
# Even on a clean exit (exit=0), claude.exe's Node workers / MCP child
# processes do not terminate with the parent (no Win32 Job Object binding
# in v1.0). Enumerate any claude.exe that started at or after $recoveryStart
# and kill its tree. Filtering by StartTime avoids ever touching a foreground
# REPL the operator might have launched in the meantime. -PreserveForegroundParent
# adds an explicit PID exclude (belt-and-suspenders: foreground starts before
# $recoveryStart anyway).
if (-not $DryRun) {
    $leaked = @(Get-ClaudeCodeCliProcesses | Where-Object {
        try { ($_.StartTime -ge $recoveryStart) -and ($preservePids -notcontains $_.Id) } catch { $false }
    })
    if ($leaked.Count -gt 0) {
        Write-WD "post-recovery reap: $($leaked.Count) claude.exe started since recovery; terminating tree(s)"
        foreach ($leak in $leaked) {
            Stop-ProcessTree -ProcessId $leak.Id -Reason 'post-recovery-reap'
        }
    } else {
        Write-WD "post-recovery reap: no surviving claude.exe to clean up"
    }
} else {
    Write-WD "DRYRUN post-recovery reap skipped"
}

$recoveryEnd = Get-Date
$durationSec = [int]($recoveryEnd - $recoveryStart).TotalSeconds
Remove-Item $LockFile -Force -ErrorAction SilentlyContinue

# Tag crash-log entries with [DRYRUN] prefix when running under -DryRun so
# the end-to-end test entries are distinguishable from real incidents.
# Operator moves these to crash_log_dryrun.md / crash_log_dryrun.json after
# testing (cleanup is operator-side; the script never auto-strips).
$loggedCause = if ($DryRun) { "[DRYRUN] $cause" } else { $cause }

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
    Append-CrashLogMd $crashTs $loggedCause $recoveredTs $durationSec 'OK'
    Append-CrashLogJson @{
        crash_ts = $crashTs
        cause = $loggedCause
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
    Append-CrashLogMd $crashTs $loggedCause '' $durationSec "MANUAL after $RecoveryMaxRetries attempts"
    Append-CrashLogJson @{
        crash_ts = $crashTs
        cause = $loggedCause
        recovered_ts = $null
        duration_seconds = $durationSec
        attempts = $RecoveryMaxRetries
        status = 'FAILED'
    }
}

Save-State $state
