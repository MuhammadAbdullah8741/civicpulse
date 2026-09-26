# Dot-source this script so image variables remain in your PowerShell session.
# Builds local images; does not commit, push, start containers, or modify .env.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$changes = git status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Git status.' }
if ($changes) { throw 'Commit the Phase 7 files first. The build must match a clean Git commit.' }
$commit = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Git commit.' }
$env:IMAGE_TAG = 'sha-' + $commit.Trim()
$env:BACKEND_IMAGE_REPOSITORY = 'civicpulse-backend'
$env:FRONTEND_IMAGE_REPOSITORY = 'civicpulse-frontend'
$env:FRONTEND_PORT = '8081'
# Rehearsal is deterministic and does not spend hosted API quota.
$env:TRIAGE_PROVIDER = 'simulated'

function Get-PinnedImage([string]$ImageName) {
    $raw = docker image ls --quiet $ImageName
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect $ImageName" }
    if (-not $raw) {
        docker pull $ImageName | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "Cannot pull $ImageName" }
    }
    $digest = docker image inspect $ImageName --format '{{index .RepoDigests 0}}'
    if ($LASTEXITCODE -ne 0 -or $digest -notmatch '@sha256:[a-f0-9]{64}$') {
        throw "No registry digest for $ImageName. Pull that image, then retry."
    }
    return $digest.Trim()
}

$env:POSTGRES_IMAGE = Get-PinnedImage 'postgres:16'
$env:REDIS_IMAGE = Get-PinnedImage 'redis:7-alpine'

docker build --tag "${env:BACKEND_IMAGE_REPOSITORY}:${env:IMAGE_TAG}" ./backend
if ($LASTEXITCODE -ne 0) { throw 'Backend image build failed.' }
docker build --tag "${env:FRONTEND_IMAGE_REPOSITORY}:${env:IMAGE_TAG}" ./frontend
if ($LASTEXITCODE -ne 0) { throw 'Frontend image build failed.' }

Write-Host "Prepared image tag: $env:IMAGE_TAG"
Write-Host "PostgreSQL: $env:POSTGRES_IMAGE"
Write-Host "Redis: $env:REDIS_IMAGE"
Write-Host 'Keep using this PowerShell window for the deployment commands.'
