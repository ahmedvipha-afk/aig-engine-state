Set-Location C:\aig_engine
$ghTokenFile = "$env:USERPROFILE\.claude\credentials\gh_token"
if ((Test-Path $ghTokenFile) -and -not $env:GH_TOKEN) {
    $env:GH_TOKEN = (Get-Content $ghTokenFile -Raw).Trim()
}
git push origin main 2>&1
Write-Output "Push exit: $LASTEXITCODE"
