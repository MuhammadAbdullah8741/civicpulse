param([ValidateSet('dev','prod')][string]$Overlay = 'dev')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PATH = "$(Join-Path $env:USERPROFILE 'Tools\civicpulse');$env:PATH"
$context = 'k3d-civicpulse'
function K {
    & kubectl --context $context @args
    if ($LASTEXITCODE -ne 0) { throw "kubectl failed: $args" }
}
function Apply-Text([string]$text) {
    $text | & kubectl --context $context apply -f -
    if ($LASTEXITCODE -ne 0) { throw 'Applying Kubernetes resources failed.' }
}
$dirty = & git status --porcelain
if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Commit the phase files before deploying; the image tag identifies that commit.' }
$tag = (& git rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot identify Git commit.' }
K get nodes
foreach ($name in @('backend','frontend')) {
    & docker build -t "civicpulse-${name}:$tag" "./$name"
    if ($LASTEXITCODE -ne 0) { throw "$name image build failed." }
    & k3d image import "civicpulse-${name}:$tag" -c civicpulse
    if ($LASTEXITCODE -ne 0) { throw "$name image import failed." }
}
K apply -f k8s/base/namespace.yaml
$existing = & kubectl --context $context -n civicpulse get secret civicpulse-secrets --ignore-not-found -o name
if ($LASTEXITCODE -ne 0) { throw 'Cannot check application Secret.' }
if (-not $existing) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $password = [Convert]::ToBase64String($bytes)
    $secret = @{apiVersion='v1';kind='Secret';metadata=@{name='civicpulse-secrets';namespace='civicpulse'};type='Opaque';stringData=@{POSTGRES_PASSWORD=$password;GROQ_API_KEY=''}}
    Apply-Text ($secret | ConvertTo-Json -Depth 8 -Compress)
    Remove-Variable password,secret,bytes
}
$rendered = & kubectl kustomize "k8s/overlays/$Overlay"
if ($LASTEXITCODE -ne 0) { throw 'Kustomize render failed.' }
$manifest = $rendered -join "`n"
foreach ($name in @('backend','frontend')) {
    $sourceTag = if ($Overlay -eq 'dev') { 'dev' } else { 'release-required' }
    $manifest = $manifest.Replace("image: civicpulse-${name}:$sourceTag", "image: civicpulse-${name}:$tag")
}
Apply-Text $manifest
K -n civicpulse rollout status statefulset/database --timeout=300s
K -n civicpulse rollout status deployment/cache --timeout=180s
# This disposable Job is rerun; PVCs and application records are preserved.
K -n civicpulse delete job civicpulse-migrate --ignore-not-found --wait=true
$migration = (Get-Content k8s/jobs/migrate.yaml -Raw).Replace('image: civicpulse-backend:dev', "image: civicpulse-backend:$tag")
Apply-Text $migration
try { K -n civicpulse wait --for=condition=complete job/civicpulse-migrate --timeout=300s }
catch { K -n civicpulse logs job/civicpulse-migrate; throw }
K -n civicpulse logs job/civicpulse-migrate
K -n civicpulse rollout status deployment/backend --timeout=300s
K -n civicpulse rollout status deployment/frontend --timeout=180s
K -n kube-system rollout status deployment/traefik --timeout=180s
K -n kube-system rollout status deployment/metrics-server --timeout=180s
K -n civicpulse get deployments,statefulsets,services,ingress,pvc,hpa,pdb
Write-Host 'Deployment finished. Open http://civicpulse.localhost:8082'
Write-Host 'Run the smoke check and capture evidence before marking the issue complete.'
