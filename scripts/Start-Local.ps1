# Starts an isolated local installation without deleting existing data.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

function Invoke-Compose {
    & docker compose -p $script:ProjectName @args
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed. Stop here and inspect the preceding error."
    }
}

# Check Docker before creating local configuration.
& docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) {
    throw 'Start Docker Desktop and wait until its engine is running.'
}

& docker compose version
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Compose is required.'
}

# Create credentials only when no local environment file exists.
if (-not (Test-Path -LiteralPath '.env')) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()

    try {
        $rng.GetBytes($bytes)
    }
    finally {
        $rng.Dispose()
    }

    $password = [Convert]::ToBase64String($bytes)

    @(
        'POSTGRES_DB=civicpulse'
        'POSTGRES_USER=civicpulse'
        "POSTGRES_PASSWORD=$password"
        'TRIAGE_PROVIDER=simulated'
        'GROQ_MODEL=openai/gpt-oss-20b'
    ) | Set-Content -LiteralPath '.env' -Encoding ascii

    Remove-Variable password,bytes
}

# Keep a stable project name for this installation.
# Different fresh clones receive different project names and volumes.
$projectLines = @(
    Get-Content -LiteralPath '.env' |
        Where-Object { $_ -match '^\s*COMPOSE_PROJECT_NAME\s*=' }
)

if ($projectLines.Count -gt 1) {
    throw 'Multiple COMPOSE_PROJECT_NAME entries exist in .env. Keep exactly one.'
}

if ($projectLines.Count -eq 1) {
    $script:ProjectName = (
        $projectLines[0] -split '=', 2
    )[1].Trim()
}
else {
    $suffix = [Guid]::NewGuid().ToString('N')
    $script:ProjectName = "civicpulse-local-$suffix"

    Add-Content -LiteralPath '.env' `
        -Value "`r`nCOMPOSE_PROJECT_NAME=$script:ProjectName" `
        -Encoding ascii

    Write-Host 'Created an isolated local project. Existing project volumes remain untouched.'
}

if ($script:ProjectName -notmatch '^[a-z0-9][a-z0-9_-]*$') {
    throw 'COMPOSE_PROJECT_NAME must use lowercase letters, numbers, hyphens or underscores.'
}

# Explicit -p makes every script command use the selected installation.
Write-Host "Starting Docker project: $script:ProjectName"
Write-Host 'Ports 8000 and 8080 must be available.'
Write-Host 'If another installation uses them, stop that installation first.'

Invoke-Compose up -d --build --wait --wait-timeout 300
Invoke-Compose exec -T backend python -m alembic upgrade head
Invoke-Compose exec -T backend python -m app.seed

# A process healthcheck alone does not establish database connectivity.
Invoke-Compose exec -T backend python -c `
    "import urllib.request; r = urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=15); print('Readiness:', r.status); print(r.read().decode())"

Write-Host ''
Write-Host 'Application: http://localhost:8080'
Write-Host 'API documentation: http://localhost:8000/docs'
Write-Host "Later commands: docker compose -p $script:ProjectName ps"
Write-Host "Stop safely: docker compose -p $script:ProjectName stop"