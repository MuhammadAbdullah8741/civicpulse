# One-command development quickstart. Preserves an existing .env and database volume.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path -LiteralPath '.env')) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $password = [Convert]::ToBase64String($bytes)
    @("POSTGRES_DB=civicpulse", "POSTGRES_USER=civicpulse", "POSTGRES_PASSWORD=$password", "TRIAGE_PROVIDER=simulated", "GROQ_MODEL=openai/gpt-oss-20b") | Set-Content -Encoding ascii .env
    Remove-Variable password,bytes
}
docker compose up -d --build --wait --wait-timeout 300
if ($LASTEXITCODE -ne 0) { throw 'Compose startup failed; inspect docker compose logs.' }
docker compose exec -T backend python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
docker compose exec -T backend python -m app.seed
if ($LASTEXITCODE -ne 0) { throw 'Seed failed.' }
Write-Host 'Open http://localhost:8080 ; backend docs: http://localhost:8000/docs'
