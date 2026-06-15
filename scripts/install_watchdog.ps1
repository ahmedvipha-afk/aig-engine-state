# install_watchdog.ps1 -- register the AIG-CC-Watchdog Windows Scheduled Task.
#
# One-time setup. Idempotent: re-running replaces an existing task with the
# same name. Mirrors a reference SKILL.md into ~/.claude/scheduled-tasks/
# so the install is visible alongside Cloud Routines.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_watchdog.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install_watchdog.ps1 -Uninstall
#
# Requires: Windows 10/11, PowerShell 5.1+, current user has rights to
# Register-ScheduledTask in their own scope (no admin needed for Limited
# RunLevel + Interactive LogonType).

[CmdletBinding()]
param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'

$TaskName       = 'AIG-CC-Watchdog'
$ProjectRoot    = 'C:\aig_engine'
$WatchdogScript = Join-Path $ProjectRoot 'scripts\cc_watchdog.ps1'
$RefDir         = "$env:USERPROFILE\.claude\scheduled-tasks\aig-cc-watchdog"
$RefSkill       = Join-Path $RefDir 'SKILL.md'

if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Output "Unregistered scheduled task: $TaskName"
    } else {
        Write-Output "Task $TaskName was not registered."
    }
    if (Test-Path $RefDir) {
        Remove-Item $RefDir -Recurse -Force
        Write-Output "Removed reference dir: $RefDir"
    }
    exit 0
}

if (-not (Test-Path $WatchdogScript)) {
    throw "Watchdog script not found at $WatchdogScript"
}

Write-Output "Registering scheduled task: $TaskName"
Write-Output "  Watchdog: $WatchdogScript"
Write-Output "  User:     $env:USERNAME"

$Action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WatchdogScript`""

# Two triggers: at logon, and every minute (Windows Task Scheduler minimum)
$TrigLogon = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$TrigEvery = New-ScheduledTaskTrigger `
    -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 1) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -Hidden

$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Output "Existing task found -- replacing."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger @($TrigLogon, $TrigEvery) `
    -Settings $Settings `
    -Principal $Principal `
    -Description 'AIG Claude Code crash watchdog -- 60s polling, sentinel + process detection, headless claude -p recovery.' | Out-Null

Write-Output "Task registered. Verifying..."
$task = Get-ScheduledTask -TaskName $TaskName
Write-Output "  State:           $($task.State)"
Write-Output "  Triggers:        $($task.Triggers.Count)"
$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Output "  Next run:        $($info.NextRunTime)"
Write-Output "  Last run:        $($info.LastRunTime)"
Write-Output "  Last result:     $($info.LastTaskResult)"

# Reference SKILL.md so the task is visible alongside Cloud Routines
if (-not (Test-Path $RefDir)) {
    New-Item -ItemType Directory -Path $RefDir -Force | Out-Null
}
# Build reference SKILL.md line by line to dodge here-string interaction with
# backticks and PowerShell parsing rules. The file is small; readability of
# the writer is fine.
$nl = "`r`n"
$lines = @(
    "---",
    "name: aig-cc-watchdog",
    "description: AIG CC crash watchdog reference (the actual scheduler is Windows Task Scheduler, not Cloud Routines). Detects REPL hangs and true crashes; spawns headless ``claude -p`` recovery.",
    "---",
    "",
    "# AIG CC Crash Watchdog (Windows Scheduled Task)",
    "",
    "This folder is a *reference* only. The watchdog is registered as a Windows",
    "Scheduled Task named ``$TaskName``, NOT a Cloud Routine.",
    "",
    "## What it does",
    "",
    "- Runs every 60 seconds (Task Scheduler minimum) in the user session.",
    "- Checks last_sprint_fire.txt age + claude.exe presence.",
    "- After 3 consecutive crash signals (3 min), spawns ``claude -p`` headless",
    "  recovery with the prompt in scripts/session_resume_prompt.txt.",
    "- Logs to crash_log.md / crash_log.json; Telegrams on detect / recover / fail.",
    "",
    "## Files",
    "",
    "- scripts/cc_watchdog.ps1         : the watchdog (this task invokes it)",
    "- scripts/cc_watchdog_telegram.py : Telegram message helper",
    "- scripts/session_resume_prompt.txt: prompt sent to the recovery session",
    "- scripts/cc_watchdog_state.json  : counters + mode",
    "- scripts/cc_watchdog.log         : invocation log",
    "- crash_log.md / crash_log.json   : per-incident history",
    "",
    "## Managing the task",
    "",
    "- Inspect:   Get-ScheduledTask -TaskName $TaskName",
    "- Run now:   Start-ScheduledTask -TaskName $TaskName",
    "- History:   Task Scheduler GUI > task > History tab",
    "- Uninstall: pwsh -File scripts\install_watchdog.ps1 -Uninstall"
)
$refContent = ($lines -join $nl) + $nl
Set-Content -Path $RefSkill -Value $refContent -Encoding utf8
Write-Output "Reference SKILL.md written: $RefSkill"

Write-Output ""
Write-Output "OK -- $TaskName installed."
Write-Output "Note: task only runs while $env:USERNAME is logged on (LogonType=Interactive)."
