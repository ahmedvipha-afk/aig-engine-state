Set-Location C:\aig_engine
$env:GCM_INTERACTIVE = "never"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GIT_ASKPASS = ""
git push origin main 2>&1
Write-Output "Push exit: $LASTEXITCODE"
