param(
  [string]$BaseUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"

Write-Host "EnvPulse demo checks against $BaseUrl"

$endpoints = @(
  "/health",
  "/metrics",
  "/observations?limit=5",
  "/anomalies?limit=5",
  "/report/summary"
)

foreach ($path in $endpoints) {
  $url = "$BaseUrl$path"
  Write-Host "Checking $url"
  $resp = Invoke-RestMethod -Uri $url -Method Get
  $resp | ConvertTo-Json -Depth 6
}

Write-Host "Demo checks completed."
