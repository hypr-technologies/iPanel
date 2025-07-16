# PowerShell script to remove external dependencies from bt.cn and aapanel.com
# This script will replace all references with GitHub-based alternatives

Write-Host "Removing external dependencies from iPanel..." -ForegroundColor Green

# Define replacement URLs
$GITHUB_REPO = "https://github.com/hypr-technologies/iPanel"
$GITHUB_RAW = "https://raw.githubusercontent.com/hypr-technologies/iPanel/main"
$GITHUB_RELEASES = "https://github.com/hypr-technologies/iPanel/releases/latest/download"
$GITHUB_CDN = "https://cdn.jsdelivr.net/gh/hypr-technologies/iPanel@main"

# Function to replace bt.cn references
function Replace-BtCnReferences {
    param([string]$filePath)
    
    if (Test-Path $filePath) {
        $content = Get-Content $filePath -Raw
        
        # Replace bt.cn download URLs
        $content = $content -replace 'http://download\.bt\.cn', $GITHUB_RELEASES
        $content = $content -replace 'https://download\.bt\.cn', $GITHUB_RELEASES
        $content = $content -replace 'http://www\.bt\.cn', $GITHUB_REPO
        $content = $content -replace 'https://www\.bt\.cn', $GITHUB_REPO
        $content = $content -replace 'http://dg[0-9]\.bt\.cn', $GITHUB_RELEASES
        $content = $content -replace 'https://dg[0-9]\.bt\.cn', $GITHUB_RELEASES
        $content = $content -replace 'http://node\.bt\.cn', $GITHUB_RELEASES
        $content = $content -replace 'https://node\.bt\.cn', $GITHUB_RELEASES
        
        # Replace API calls
        $content = $content -replace '/Api/getIpAddress', '/ip'
        $content = $content -replace '/api/index/get_time', ''
        $content = $content -replace '/api/panel/notpro', ''
        
        Set-Content -Path $filePath -Value $content
        Write-Host "Updated bt.cn references in $filePath" -ForegroundColor Yellow
    }
}

# Function to replace aapanel.com references
function Replace-AapanelReferences {
    param([string]$filePath)
    
    if (Test-Path $filePath) {
        $content = Get-Content $filePath -Raw
        
        # Replace aapanel.com URLs
        $content = $content -replace 'https://www\.aapanel\.com', $GITHUB_REPO
        $content = $content -replace 'http://www\.aapanel\.com', $GITHUB_REPO
        $content = $content -replace 'https://brandnew\.aapanel\.com', $GITHUB_REPO
        $content = $content -replace 'https://console\.aapanel\.com', $GITHUB_REPO
        $content = $content -replace 'https://node\.aapanel\.com', $GITHUB_RELEASES
        $content = $content -replace 'http://node\.aapanel\.com', $GITHUB_RELEASES
        
        # Replace API endpoints
        $content = $content -replace '/api/common/getClientIP', ''
        $content = $content -replace '/api/setupCount/setupPanel', ''
        $content = $content -replace '/Api/SetupCount', ''
        
        Set-Content -Path $filePath -Value $content
        Write-Host "Updated aapanel.com references in $filePath" -ForegroundColor Yellow
    }
}

# Function to update text references
function Replace-TextReferences {
    param([string]$filePath)
    
    if (Test-Path $filePath) {
        $content = Get-Content $filePath -Raw
        
        # Replace text references in language files
        $content = $content -replace '"bt\.cn"', '"GitHub"'
        $content = $content -replace '"www\.bt\.cn"', '"github.com/hypr-technologies/iPanel"'
        $content = $content -replace '"aapanel\.com"', '"github.com/hypr-technologies/iPanel"'
        $content = $content -replace '"forum\.aapanel\.com"', '"github.com/hypr-technologies/iPanel/issues"'
        
        # Replace branding
        $content = $content -replace '"aaPanel"', '"iPanel"'
        $content = $content -replace '"BT-Panel"', '"iPanel"'
        $content = $content -replace '"宝塔"', '"iPanel"'
        
        Set-Content -Path $filePath -Value $content
        Write-Host "Updated text references in $filePath" -ForegroundColor Yellow
    }
}

# Main processing
Write-Host "Processing language files..." -ForegroundColor Cyan
Get-ChildItem -Path ".\BTPanel\static\vite\lang" -Recurse -Filter "*.json" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
    Replace-TextReferences $_.FullName
}

Write-Host "Processing configuration files..." -ForegroundColor Cyan
Get-ChildItem -Path ".\config" -Recurse -Filter "*.json" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
}

Write-Host "Processing data files..." -ForegroundColor Cyan
Get-ChildItem -Path ".\data" -Recurse -Filter "*.json" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
}

Write-Host "Processing shell scripts..." -ForegroundColor Cyan
Get-ChildItem -Path "." -Recurse -Filter "*.sh" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
}

Write-Host "Processing Python files..." -ForegroundColor Cyan
Get-ChildItem -Path "." -Recurse -Filter "*.py" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
}

Write-Host "Processing PHP files..." -ForegroundColor Cyan
Get-ChildItem -Path "." -Recurse -Filter "*.php" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
}

Write-Host "Processing HTML/JS files..." -ForegroundColor Cyan
Get-ChildItem -Path "." -Recurse -Include "*.html", "*.js" | ForEach-Object {
    Replace-BtCnReferences $_.FullName
    Replace-AapanelReferences $_.FullName
}

Write-Host "External dependencies removal complete!" -ForegroundColor Green
Write-Host "All references to bt.cn and aapanel.com have been replaced with GitHub alternatives." -ForegroundColor Green
