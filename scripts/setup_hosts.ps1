# Setup hosts file for local development on Windows
# Run as Administrator

$hostsPath = "C:\Windows\System32\drivers\etc\hosts"

# Entry format: IP  hostname
$entries = @(
    "127.0.0.1  localhost",
    "127.0.0.1  public.localhost",
    "127.0.0.1  university.localhost",
    "127.0.0.1  location.localhost",
    "127.0.0.1  testshop.localhost",
    "::1  localhost"
)

# Check if running as administrator
$isAdmin = [System.Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains "S-1-5-32-544"
if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator" -ForegroundColor Red
    Write-Host "Please right-click this script and select 'Run as Administrator'"
    exit 1
}

Write-Host "Setting up local development hosts file..." -ForegroundColor Cyan
Write-Host "Hosts file: $hostsPath" -ForegroundColor Gray

$addedCount = 0
foreach ($entry in $entries) {
    $ipAndHost = $entry -split '\s+'
    $ip = $ipAndHost[0]
    $host = $ipAndHost[1]
    
    # Check if entry already exists
    $exists = Select-String -Path $hostsPath -Pattern "^\s*$ip\s+$host\s*$" -Quiet -ErrorAction SilentlyContinue
    
    if (-not $exists) {
        Add-Content -Path $hostsPath -Value $entry -Encoding ASCII
        Write-Host "  Added: $entry" -ForegroundColor Green
        $addedCount++
    } else {
        Write-Host "  Exists: $entry" -ForegroundColor Yellow
    }
}

if ($addedCount -gt 0) {
    Write-Host "" -ForegroundColor Cyan
    Write-Host "Successfully added $addedCount entries to hosts file!" -ForegroundColor Green
    Write-Host "" -ForegroundColor Cyan
    Write-Host "You can now access:" -ForegroundColor Cyan
    Write-Host "  - Public site:    http://localhost/" -ForegroundColor Gray
    Write-Host "  - University:     http://university.localhost/" -ForegroundColor Gray
    Write-Host "  - Location:       http://location.localhost/" -ForegroundColor Gray
    Write-Host "  - Test Shop:      http://testshop.localhost/" -ForegroundColor Gray
} else {
    Write-Host "" -ForegroundColor Cyan
    Write-Host "All entries already exist in hosts file." -ForegroundColor Yellow
}

Write-Host "" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
