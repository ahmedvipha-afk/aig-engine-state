Set-Location C:\aig_engine
git push origin main 2>&1
Write-Output "Push exit: $LASTEXITCODE"
