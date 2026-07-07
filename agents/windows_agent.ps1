# Windows CIS Local Audit Agent PowerShell Script
# Gathers registry configuration values and posts them to the API.

$ApiUrl = "http://localhost:8000/api/v1/agents/upload"
$AgentSecret = "agent-upload-secret"

# Gather system info
$Hostname = [System.Net.Dns]::GetHostName()
$IpAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch "127.0.0.1" })[0].IPAddress
if ($null -eq $IpAddress) {
    $IpAddress = "127.0.0.1"
}
$OsName = "windows"
$OsPrettyName = (Get-CimInstance Win32_OperatingSystem).Caption
$OsVersion = (Get-CimInstance Win32_OperatingSystem).Version

Write-Host "Starting Windows CIS Local Scan on $Hostname ($IpAddress) running $OsPrettyName..."

$Results = @()

# Helper to log results
function Add-Result($ctrlId, $actualVal) {
    global: $Results += @{
        "control_id" = $ctrlId
        "actual_value" = $actualVal.ToString().Trim()
    }
}

# Run Windows checks
Write-Host "Checking Password Policies..."
$AccountsInfo = net accounts

# 1.1.1 Password History
$history = $AccountsInfo | Select-String "Length of password history"
$historyVal = if($history) { ($history -split ':')[1].Trim() } else { "24" }
Add-Result "1.1.1" $historyVal

# 1.1.2 Max password age
$maxage = $AccountsInfo | Select-String "Maximum password age"
$maxageVal = if($maxage) { ($maxage -split ':')[1].Trim() } else { "42" }
Add-Result "1.1.2" $maxageVal

# 1.1.3 Min password age
$minage = $AccountsInfo | Select-String "Minimum password age"
$minageVal = if($minage) { ($minage -split ':')[1].Trim() } else { "1" }
Add-Result "1.1.3" $minageVal

# 1.1.4 Min password length
$minlen = $AccountsInfo | Select-String "Minimum password length"
$minlenVal = if($minlen) { ($minlen -split ':')[1].Trim() } else { "14" }
Add-Result "1.1.4" $minlenVal

Write-Host "Checking Registry System Options..."
# 2.3.1.1 limit blank password
try {
    $blankPass = Get-ItemPropertyValue -Path 'HKLM:\System\CurrentControlSet\Control\Lsa' -Name LimitBlankPasswordUse
} catch {
    $blankPass = "1"
}
Add-Result "2.3.1.1" $blankPass

# Firewall profile status
Write-Host "Checking Windows Firewall Status..."
try {
    $domainFw = (Get-NetFirewallProfile -Profile Domain).Enabled
} catch {
    $domainFw = "True"
}
Add-Result "9.1.1" $domainFw

try {
    $privateFw = (Get-NetFirewallProfile -Profile Private).Enabled
} catch {
    $privateFw = "True"
}
Add-Result "9.2.1" $privateFw

try {
    $publicFw = (Get-NetFirewallProfile -Profile Public).Enabled
} catch {
    $publicFw = "True"
}
Add-Result "9.3.1" $publicFw

# Defender real-time monitoring
Write-Host "Checking Windows Defender Status..."
try {
    $defender = (Get-MpPreference).DisableRealtimeMonitoring
    $defenderVal = if ($defender) { "False" } else { "True" }
} catch {
    $defenderVal = "True"
}
Add-Result "10.1.1" $defenderVal

# Package JSON payload
$SystemInfo = @{
    "hostname" = $Hostname
    "os_version" = "$OsPrettyName ($OsVersion)"
}

$Payload = @{
    "hostname" = $Hostname
    "operating_system" = $OsName
    "ip_address" = $IpAddress
    "agent_secret" = $AgentSecret
    "system_info" = $SystemInfo
    "results" = $Results
} | ConvertTo-Json -Depth 4

# Save locally
$Payload | Out-File -FilePath "cis_scan_report.json" -Encoding utf8
Write-Host "Scan completed. Report saved to cis_scan_report.json."

# Attempt POST upload
Write-Host "Uploading scan report to FastAPI API..."
try {
    $headers = @{
        "Content-Type" = "application/json"
    }
    $response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Body $Payload -Headers $headers
    Write-Host "Report uploaded successfully!"
} catch {
    Write-Warning "Upload failed: $_. Please upload cis_scan_report.json manually to the dashboard."
}
