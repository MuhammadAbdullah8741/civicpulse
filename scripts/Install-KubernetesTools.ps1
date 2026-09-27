$ErrorActionPreference = 'Stop'
$toolDir = Join-Path $env:USERPROFILE 'Tools\civicpulse'
New-Item -ItemType Directory -Force $toolDir | Out-Null
# Official release downloads; checksum verification precedes execution.
$k3dVersion = 'v5.8.3'
$kubectlVersion = 'v1.35.8'
$k3dBase = "https://github.com/k3d-io/k3d/releases/download/$k3dVersion"
Invoke-WebRequest "$k3dBase/k3d-windows-amd64.exe" -OutFile "$toolDir\k3d.exe" -UseBasicParsing
Invoke-WebRequest "$k3dBase/checksums.txt" -OutFile "$toolDir\k3d-checksums.txt" -UseBasicParsing
$line = Get-Content "$toolDir\k3d-checksums.txt" | Where-Object { $_ -match '\s+\*?(?:_dist/)?k3d-windows-amd64\.exe\s*$' }
if (-not $line) { throw 'Official k3d checksum entry was not found.' }
$expected = ($line -split '\s+')[0]
if ((Get-FileHash "$toolDir\k3d.exe" -Algorithm SHA256).Hash -ne $expected) { throw 'k3d checksum mismatch.' }
$kubectlBase = "https://dl.k8s.io/release/$kubectlVersion/bin/windows/amd64"
Invoke-WebRequest "$kubectlBase/kubectl.exe" -OutFile "$toolDir\kubectl.exe" -UseBasicParsing
Invoke-WebRequest "$kubectlBase/kubectl.exe.sha256" -OutFile "$toolDir\kubectl.sha256" -UseBasicParsing
if ((Get-FileHash "$toolDir\kubectl.exe" -Algorithm SHA256).Hash -ne (Get-Content "$toolDir\kubectl.sha256" -Raw).Trim()) { throw 'kubectl checksum mismatch.' }
$env:PATH = "$toolDir;$env:PATH"
& "$toolDir\k3d.exe" version
& "$toolDir\kubectl.exe" version --client
if ($LASTEXITCODE -ne 0) { throw 'Tool verification failed.' }

