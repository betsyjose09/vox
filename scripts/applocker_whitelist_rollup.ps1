# Whitelist Rollup native binary for Antigravity project
# Run this script in an elevated PowerShell window (Run as Administrator)

# Path to the native binary that AppLocker blocks
$binaryPath = "D:\quirri\frontend\node_modules\@rollup\rollup-win32-x64-msvc\rollup.win32-x64-msvc.node"

# Create an AppLocker path rule that allows the file for all users
# Requires the AppLocker module (available on Windows 10/11 Pro/Edu/Enterprise)
New-AppLockerFileRule -Path $binaryPath -User "Everyone" -Action Allow -RuleType Path -Name "AllowRollupNodeBinary"

# Force policy refresh so the rule takes effect immediately
gpupdate /force

# Verify the rule was added
Get-AppLockerFileRule | Where-Object { $_.Path -like "*rollup.win32-x64-msvc.node*" }

Write-Host "\n---\nAppLocker whitelist rule applied. You can now reinstall the frontend dependencies and run the dev server.\n"

# Optional: reinstall the frontend packages (comment out if you prefer to run manually)
# Set-Location "D:\quirri\frontend"
# npm ci
# npm run dev

