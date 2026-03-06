param(
  [string]$BaseUrl = "http://localhost:8000",
  [int]$StartupTimeoutSec = 120,
  [switch]$KeepRunning
)

$ErrorActionPreference = "Stop"

function Wait-ForApi {
  param([string]$Url,[int]$TimeoutSec)

  $start = Get-Date
  while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSec) {
    try {
      Invoke-RestMethod -Uri "$Url/health" -Method Get | Out-Null
      return $true
    } catch {
      Start-Sleep -Seconds 2
    }
  }
  return $false
}

Write-Host "[1/5] Starting docker compose services..."
docker compose up -d --build | Out-Null

Write-Host "[2/5] Waiting for API to become healthy..."
if (-not (Wait-ForApi -Url $BaseUrl -TimeoutSec $StartupTimeoutSec)) {
  Write-Error "API did not become healthy within $StartupTimeoutSec seconds."
}

Write-Host "[3/5] Waiting for scheduler+worker to process data..."
Start-Sleep -Seconds 20

$checks = @(
  @{ name = "health"; url = "$BaseUrl/health"; assert = { param($r) $r.status -eq "ok" } },
  @{ name = "metrics"; url = "$BaseUrl/metrics"; assert = { param($r) $null -ne $r.counters } },
  @{ name = "observations"; url = "$BaseUrl/observations?limit=5"; assert = { param($r) $r.Count -ge 1 } },
  @{ name = "anomalies"; url = "$BaseUrl/anomalies?limit=5"; assert = { param($r) $r -is [System.Array] } },
  @{ name = "report"; url = "$BaseUrl/report/summary"; assert = { param($r) $r.total_observations -ge 1 } }
)

Write-Host "[4/5] Running endpoint checks..."
foreach ($c in $checks) {
  $resp = Invoke-RestMethod -Uri $c.url -Method Get
  if (-not (& $c.assert $resp)) {
    Write-Error "Check failed: $($c.name)"
  }
  Write-Host "PASS: $($c.name)"
}

Write-Host "[5/5] E2E check passed."

if (-not $KeepRunning) {
  Write-Host "Stopping docker compose services..."
  docker compose down | Out-Null
} else {
  Write-Host "Services left running because -KeepRunning was provided."
}
