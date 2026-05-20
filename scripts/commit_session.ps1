# AIG session-end commit + push helper.
# Idempotent: safe to call every session. Refuses to commit if any secret-ish
# file slipped through .gitignore.
#
# Usage:
#   pwsh -File scripts/commit_session.ps1
#   pwsh -File scripts/commit_session.ps1 -Message "Custom message"
#   pwsh -File scripts/commit_session.ps1 -DryRun

[CmdletBinding()]
param(
    [string]$Message = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Ensure gh is on PATH for any later auth check
$ghBin = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe"
if (Test-Path $ghBin) {
    $env:Path = (Split-Path $ghBin) + ';' + $env:Path
}

if (-not (Test-Path .git)) {
    Write-Output 'ERROR: No git repo here. Run `git init` first.'
    exit 1
}

# Stage explicit safe paths. Use git directly (suppress LF/CRLF warnings).
$paths = @(
    'ceo_brain.md', 'strategy_register.md', 'README.md', '.gitignore',
    'config.py', 'run_validation.py', 'requirements.txt',
    'aig', 'tests', 'pine', 'universe', 'scripts'
)
foreach ($p in $paths) {
    if (Test-Path $p) { git add $p 2>$null | Out-Null }
}
# Glob patterns separately
Get-ChildItem -Filter 'findings_*.md' | ForEach-Object { git add $_.Name 2>$null | Out-Null }
Get-ChildItem -Filter 'analyze_*.py' | ForEach-Object { git add $_.Name 2>$null | Out-Null }
Get-ChildItem -Filter 'validation_*.json' | ForEach-Object { git add $_.Name 2>$null | Out-Null }
Get-ChildItem -Filter 'tv_strategy_tester_*.json' | ForEach-Object { git add $_.Name 2>$null | Out-Null }

# Safety: refuse to commit if .env or token-shaped files staged anywhere
$staged = git diff --cached --name-only 2>$null
$dangerous = $staged | Where-Object { $_ -match '(?i)\.env$|token|secret|credential' }
if ($dangerous) {
    Write-Output ("ABORT: dangerous staged files (potential secrets): " + ($dangerous -join ', '))
    git reset HEAD $dangerous 2>$null | Out-Null
    exit 2
}

# Anything actually staged?
$shortstat = git diff --cached --shortstat 2>$null
if (-not $shortstat) {
    Write-Output 'Nothing to commit (working tree clean against HEAD).'
    exit 0
}

if (-not $Message) {
    $date = Get-Date -Format 'yyyy-MM-dd HH:mm GST'
    $stats = ($shortstat | Out-String).Trim()
    $Message = "Session snapshot $date | $stats"
}

Write-Output "Commit: $Message"
Write-Output "Staged:"
git diff --cached --stat 2>$null | Out-Host

if ($DryRun) {
    Write-Output 'DRY RUN — unstaging.'
    git reset HEAD 2>$null | Out-Null
    exit 0
}

git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    Write-Output "git commit failed (code $LASTEXITCODE)"
    exit $LASTEXITCODE
}

# Push if a remote exists
$remotes = git remote 2>$null
if ($remotes) {
    git push 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Output "git push failed (code $LASTEXITCODE). Commit is local; will retry next session."
    } else {
        Write-Output "Pushed to: $remotes"
    }
} else {
    Write-Output 'No remote configured. Commit is local-only.'
}
