# sprint_task_launcher.ps1 -- Task Scheduler entry point for the AIG Mode-1
# sprint (Windows scheduled task "AIG-Mode1-Sprint", cron-equivalent
# 12,27,42,57 * * * * with RandomDelay PT347S).
#
# Driver history (decision_log entry 43, 2026-06-11): the original
# aig-mode1-sprint ran as a Claude scheduled routine; a platform change split
# routines into cloud (1-hour minimum, no local filesystem) and Desktop-local
# (registration lost; requires the Desktop app open). This launcher is
# Option A2: OS-level Task Scheduler -> headless `claude -p`, reboot-safe,
# no Desktop dependency. It mirrors cc_watchdog.ps1's recovery-spawn harness:
# hard timeout + process-tree kill + logging. `claude -p` exits when the turn
# completes (structural fix for the stream-json zombie pattern, Bug A).
#
# The SKILL stays the single source of truth: this launcher only points the
# headless session at it, so SKILL edits take effect on the next fire with no
# task changes (same property the Desktop scheduler had).
#
# Encoding: ASCII-only on purpose (PS 5.1 reads no-BOM .ps1 as Windows-1252).

$ErrorActionPreference = 'Continue'

$ProjectRoot    = 'C:\Users\ahmed\OneDrive\Documents\Projects\stocks\Ahmed group\Working Area\aig_engine'
$SkillFile      = "$env:USERPROFILE\.claude\scheduled-tasks\aig-mode1-sprint\SKILL.md"
$LogFile        = Join-Path $ProjectRoot 'scripts\sprint_task.log'
$CronPausedFlag = Join-Path $ProjectRoot 'scripts\cron_paused.flag'
# 90 min (raised from 65 on 2026-06-13): the SKILL now runs TWO detectors
# per iteration (divergence slot 1 + trb50 slot 2, entry 50) and a catch-up
# burst of several ~21-min iterations was clipping at 65 min on a moderate-
# RAM-pressure host. The scheduled task's own ExecutionTimeLimit (raised
# PT75M -> PT95M to match) backstops THIS script, so the launcher always
# gets to do the logging + tree-kill itself.
$TimeoutSeconds = 5400

$ClaudeExe = "$env:USERPROFILE\.local\bin\claude.exe"
if (-not (Test-Path $ClaudeExe)) {
    $ClaudeExe = "$env:USERPROFILE\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\bin\claude.exe"
}

function Log([string]$msg) {
    $ts = (Get-Date).ToUniversalTime().ToString('o')
    try { Add-Content -Path $LogFile -Value "$ts $msg" -Encoding utf8 } catch {}
}

# Honor the same intentional-pause flag the watchdog honors, so one flag
# stops BOTH the driver and the recovery layer (the 2026-05-23 false-fire
# loop happened precisely because the driver paused and the watchdog didn't
# know; see decision_log entries 16/19).
if (Test-Path $CronPausedFlag) {
    Log 'skip: cron_paused.flag present (intentional pause)'
    exit 0
}

if (-not (Test-Path $SkillFile)) {
    Log "ABORT: SKILL not found at $SkillFile"
    exit 1
}

# F2 (2026-06-12): explicit headless preamble. The 2026-06-11 17:12Z fire
# failed because the worker backgrounded a retry and ended its turn to
# "wait" -- in -p mode that exits the process before steps 3-5 ran.
$prompt = "You are headless claude -p -- the process exits when your turn ends, and background-task notifications never arrive. Complete ALL steps in this single turn. No background tasks; run every retry foreground. Execute the sprint defined in $SkillFile. Read that file first and follow it exactly."

try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $ClaudeExe
    $escaped = $prompt.Replace('"', '\"')
    # Pin the headless worker to claude-sonnet-4-6: the global settings.json
    # default (claude-fable-5[1m]) is NOT entitled for headless `claude -p`,
    # which made every fire exit 1 in ~5s after the 2026-06-12 CLI update
    # (proven by failed-worker transcripts; decision_log + sprint_task.log).
    # Scoped here only — interactive/Desktop sessions keep their default.
    $psi.Arguments = "-p --model claude-sonnet-4-6 `"$escaped`""
    $psi.WorkingDirectory = $ProjectRoot
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    # Prefer IPv4 for the headless worker ONLY (decision_log, 2026-06-14
    # regression). The IPv6 address of api.anthropic.com (2607:6bc0::10)
    # began black-holing PAST the TCP handshake ~10:14Z: the socket reached
    # ESTABLISHED but no response data ever streamed, so every -p worker hung
    # on its first model call (~0 CPU, no transcript ever written) and the
    # launcher killed it at the cap -- 6 consecutive fires dead over 5.5h.
    # Interactive/Desktop sessions on IPv4 (160.79.104.10) were unaffected.
    # --dns-result-order=ipv4first prefers the working IPv4 path WITH failover
    # (chosen over a hosts pin so it survives Anthropic rotating the IPv4 IP).
    # EnvironmentVariables is honored because UseShellExecute=$false; scoped to
    # this worker process only. Append, don't clobber any inherited NODE_OPTIONS.
    $existingNodeOpts = $psi.EnvironmentVariables['NODE_OPTIONS']
    if ($existingNodeOpts) {
        $psi.EnvironmentVariables['NODE_OPTIONS'] = "$existingNodeOpts --dns-result-order=ipv4first"
    } else {
        $psi.EnvironmentVariables['NODE_OPTIONS'] = '--dns-result-order=ipv4first'
    }

    # Per-tool timeout (defense-in-depth, decision_log 2026-06-14): bound shell
    # tool-calls so a stalled probe (e.g. a git/file op on a slow volume) fails
    # fast and the model can retry, instead of one blocked call wedging the turn.
    # NOTE: covers Bash tool-calls only; the primary 2026-06-14 hang was a
    # file-hydration/read wait on the OneDrive volume, which this does NOT bound
    # -- the real cure is relocating the repo off OneDrive. The verify-kill reap
    # loop below is the load-bearing part of this fix.
    $psi.EnvironmentVariables['BASH_DEFAULT_TIMEOUT_MS'] = '300000'

    $proc = [System.Diagnostics.Process]::Start($psi)
    $workerPid = $proc.Id
    Log "spawned claude -p pid=$workerPid"
    # Close stdin immediately so claude doesn't wait the piped-input grace period.
    $proc.StandardInput.Close()

    $stdoutBuilder = [System.Text.StringBuilder]::new()
    $stderrBuilder = [System.Text.StringBuilder]::new()
    $proc.add_OutputDataReceived({ if ($EventArgs.Data) { [void]$stdoutBuilder.AppendLine($EventArgs.Data) } })
    $proc.add_ErrorDataReceived({ if ($EventArgs.Data) { [void]$stderrBuilder.AppendLine($EventArgs.Data) } })
    $proc.BeginOutputReadLine()
    $proc.BeginErrorReadLine()

    $exited = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $exited) {
        Log "TIMEOUT after $TimeoutSeconds s; killing tree pid=$workerPid"
        # VERIFY-KILL LOOP (decision_log 2026-06-14): a worker wedged in an
        # uninterruptible kernel I/O wait survives a single taskkill -- it dies
        # only once the wait aborts (observed 10-25s later). The OLD code issued
        # one taskkill then exited immediately, so the still-alive worker
        # ORPHANED and -- with MultipleInstances=IgnoreNew -- jammed every
        # subsequent fire for hours. Loop: kill, wait, confirm dead, retry.
        # 12 x 5s = 60s max; 90min cap + 60s < 95min task ExecutionTimeLimit.
        $reaped = $false
        for ($attempt = 1; $attempt -le 12; $attempt++) {
            & taskkill /PID $workerPid /T /F 2>&1 | ForEach-Object { Log "taskkill[$attempt]: $_" }
            Start-Sleep -Seconds 5
            if (-not (Get-Process -Id $workerPid -ErrorAction SilentlyContinue)) {
                $reaped = $true
                Log "reaped pid=$workerPid after $attempt attempt(s)"
                break
            }
            Log "pid=$workerPid still alive after attempt $attempt (wedged in kernel wait); retrying"
        }
        if (-not $reaped) {
            Log "WARNING: pid=$workerPid NOT reaped after 12 attempts (~60s) -- may orphan and jam the IgnoreNew slot; operator check needed"
        }
        exit 2
    }

    $exitCode = $proc.ExitCode
    $tail = $stdoutBuilder.ToString()
    $tail = if ($tail.Length -gt 400) { $tail.Substring($tail.Length - 400) } else { $tail }
    $tail = $tail -replace "`r?`n", ' / '
    if ($exitCode -eq 0) {
        Log "fire complete pid=$workerPid exit=0 stdout_tail=$tail"
    } else {
        $errTail = $stderrBuilder.ToString()
        $errTail = if ($errTail.Length -gt 400) { $errTail.Substring(0, 400) } else { $errTail }
        Log "fire FAILED pid=$workerPid exit=$exitCode stderr=$($errTail -replace "`r?`n", ' / ')"
    }
    exit $exitCode
} catch {
    Log "EXCEPTION: $_"
    exit 3
}
