# cc_watchdog_test.ps1 — sacrificial end-to-end test of the watchdog.
#
# Disables the scheduled task, swaps the resume prompt for a short test
# prompt, backdates the sentinel, runs the watchdog 3 times (1st+2nd build
# the consecutive_stale counter, 3rd triggers recovery via `claude -p`),
# restores the prompt + sentinel + task. Marks the crash_log entry [TEST].
# Sends the final "🛡️ Watchdog tested" Telegram.
#
# Safe to re-run.

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

$ProjectRoot   = 'C:\Users\ahmed\OneDrive\Documents\Projects\stocks\Ahmed group\Working Area\aig_engine'
$ScriptsDir    = Join-Path $ProjectRoot 'scripts'
$Watchdog      = Join-Path $ScriptsDir 'cc_watchdog.ps1'
$ResumePrompt  = Join-Path $ScriptsDir 'session_resume_prompt.txt'
$SentinelFile  = Join-Path $ProjectRoot 'last_sprint_fire.txt'
$StateFile     = Join-Path $ScriptsDir 'cc_watchdog_state.json'
$CrashLogMd    = Join-Path $ProjectRoot 'crash_log.md'
$CrashLogJson  = Join-Path $ProjectRoot 'crash_log.json'
$TelegramHelper = Join-Path $ScriptsDir 'cc_watchdog_telegram.py'
$TaskName      = 'AIG-CC-Watchdog'

Write-Output "=== AIG CC Watchdog sacrificial test ==="

# 1. Disable scheduled task so it can't collide
Write-Output "1. Disabling $TaskName"
try { Disable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null; Write-Output "   disabled" } catch { Write-Output "   warn: $_" }

# 2. Backup
Write-Output "2. Backing up sentinel + prompt + state"
$origSentinel = Get-Content $SentinelFile -Raw -ErrorAction SilentlyContinue
$origPrompt   = Get-Content $ResumePrompt -Raw -ErrorAction SilentlyContinue
$origState    = if (Test-Path $StateFile) { Get-Content $StateFile -Raw } else { $null }
$origCrashMd  = if (Test-Path $CrashLogMd) { (Get-Item $CrashLogMd).Length } else { 0 }

# 3. Substitute test prompt (very short, deterministic, fast)
Write-Output "3. Installing test prompt"
$testPrompt = "Watchdog sacrificial test. Reply only with: WATCHDOG TEST RECOVERY OK"
Set-Content -Path $ResumePrompt -Value $testPrompt -Encoding utf8

# 4. Backdate sentinel by 35 min so the watchdog sees stale
Write-Output "4. Backdating sentinel by 35 min"
$staleTs = ((Get-Date).ToUniversalTime().AddMinutes(-35)).ToString('o')
Set-Content -Path $SentinelFile -Value $staleTs -Encoding utf8

# 5. Reset consecutive_stale_checks so the test starts from 0
Write-Output "5. Resetting state counters"
if (Test-Path $StateFile) {
    try {
        $st = Get-Content $StateFile -Raw | ConvertFrom-Json
        $st.consecutive_stale_checks = 0
        $st.mode = 'normal'
        $st | ConvertTo-Json -Depth 4 | Set-Content $StateFile -Encoding utf8
    } catch { Write-Output "   state reset warn: $_" }
}

# 6. Drive the watchdog 3 times. The 3rd should trigger recovery via claude -p.
Write-Output "6. Driving watchdog 3 times (the 3rd should trigger recovery)"
$testStart = Get-Date
for ($i = 1; $i -le 3; $i++) {
    Write-Output "   tick $i ..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Watchdog -VerboseLog 2>&1 | ForEach-Object {
        Write-Output "     $_"
    }
}
$testEnd = Get-Date
$durationSec = [int]($testEnd - $testStart).TotalSeconds
Write-Output "   wall-clock: ${durationSec}s"

# 7. Restore prompt + sentinel
Write-Output "7. Restoring prompt + sentinel"
if ($null -ne $origPrompt) { Set-Content -Path $ResumePrompt -Value $origPrompt.TrimEnd() -Encoding utf8 }
if ($null -ne $origSentinel) { Set-Content -Path $SentinelFile -Value $origSentinel.Trim() -Encoding utf8 }

# 8. Tag the new crash_log.md entry as [TEST]
Write-Output "8. Tagging crash_log entry as [TEST]"
if (Test-Path $CrashLogMd) {
    $lines = Get-Content $CrashLogMd
    # Mark the LAST line (the one this test just appended) with [TEST]
    if ($lines.Count -gt 0) {
        $lastIdx = $lines.Count - 1
        $lastLine = $lines[$lastIdx]
        if ($lastLine -like "- *" -and $lastLine -notlike "*[TEST]*") {
            $lines[$lastIdx] = $lastLine + ' [TEST sacrificial]'
            Set-Content -Path $CrashLogMd -Value $lines -Encoding utf8
        }
    }
}
# Same for crash_log.json — mark the last entry test=true
if (Test-Path $CrashLogJson) {
    try {
        $jl = @(Get-Content $CrashLogJson -Raw | ConvertFrom-Json)
        if ($jl.Count -gt 0) {
            $jl[-1] | Add-Member -NotePropertyName 'test' -NotePropertyValue $true -Force
            $jl | ConvertTo-Json -Depth 4 | Set-Content $CrashLogJson -Encoding utf8
        }
    } catch { Write-Output "   crash_log.json tag warn: $_" }
}

# 9. Re-enable scheduled task
Write-Output "9. Re-enabling $TaskName"
try { Enable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null; Write-Output "   enabled" } catch { Write-Output "   warn: $_" }

# 10. Send the final confirmation Telegram per CEO directive
Write-Output "10. Sending tested confirmation Telegram"
& python $TelegramHelper tested --duration-seconds $durationSec 2>&1 | ForEach-Object { Write-Output "    $_" }

Write-Output ""
Write-Output "=== Test complete in ${durationSec}s ==="
Write-Output "State file: $StateFile"
Write-Output "Crash log:  $CrashLogMd"
Write-Output "Watchdog log: $ScriptsDir\cc_watchdog.log"
