# publish_update.ps1
# Usage: .\publish_update.ps1 "Add new A2 words - March 2026"

param(
    [string]$message = "Update vocabulary data and audio"
)

$APP_DIR = "C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder"
$AUDIO_DIR = "$APP_DIR\audio"

Write-Host "`n=== Step 1: Uploading new audio files to Cloudflare R2 ===" -ForegroundColor Cyan
rclone copy $AUDIO_DIR r2:greek-audio --progress

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: rclone upload failed. Aborting." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Step 2: Committing and pushing data updates to GitHub ===" -ForegroundColor Cyan
Set-Location $APP_DIR

git add data/
git status

$confirm = Read-Host "`nProceed with commit? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

git commit -m $message
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Done! Streamlit Cloud will redeploy automatically. ===" -ForegroundColor Green
} else {
    Write-Host "`nERROR: Git push failed." -ForegroundColor Red
}
