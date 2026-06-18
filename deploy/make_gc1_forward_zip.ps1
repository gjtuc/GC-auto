# GC1 forward 배포 zip (GC2/GC3 장비 PC → GC1 장비 PC)
# · GC1이 보냈던 baseline + GC2 운영 중 추가 수정이 모두 포함된 통합 코드베이스
# · __pycache__, .git, 비밀번호 env 원본, 상태/PDF/엑셀 산출물 제외
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$dest = Join-Path $PSScriptRoot 'GC1_forward_chemstation-gc-automation.zip'
$staging = Join-Path $env:TEMP ("gc1_forward_" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging -Force | Out-Null

$includeDirs = @('.cursor', 'deploy')

Get-ChildItem -Path $root -File | Where-Object {
    $n = $_.Name
    $n -match '\.(py|bat|txt|md)$' -or $n -eq '.env.example' -or $n -eq '.gitignore'
} | ForEach-Object { Copy-Item $_.FullName -Destination $staging }

foreach ($d in $includeDirs) {
    $src = Join-Path $root $d
    if (Test-Path $src) {
        Copy-Item $src -Destination (Join-Path $staging $d) -Recurse -Force
    }
}

# deploy 안의 zip·로컬 비밀번호 env 제외
Get-ChildItem -Path (Join-Path $staging 'deploy') -Filter '*.zip' -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
$localEnv = Join-Path $staging 'deploy\gc_automation.env'
if (Test-Path $localEnv) { Remove-Item $localEnv -Force }

Get-ChildItem -Path $staging -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path $dest) { Remove-Item $dest -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $dest -Force
Remove-Item $staging -Recurse -Force

$size = (Get-Item $dest).Length
Write-Host "Created $dest ($size bytes)"
