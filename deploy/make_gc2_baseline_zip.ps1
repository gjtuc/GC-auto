# GC2 역배포용 baseline zip
# · GC2/GC3 장비 PC에 풀어서 GC2/GC3가 동작하는 **통합 코드베이스** (GC1 모듈 포함, 삭제 금지)
# · __pycache__, .git, 비밀번호 env 원본, 상태/PDF/엑셀 산출물 제외
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$dest = Join-Path $PSScriptRoot 'GC2_baseline_chemstation-gc-automation.zip'
$staging = Join-Path $env:TEMP ("gc2_baseline_" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging -Force | Out-Null

$includeNames = @(
    '*.py', '*.bat', '*.txt', '*.md', '*.mdc', '.env.example', '.gitignore'
)
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

# deploy 안의 zip·로컬 비밀번호 env 제외 (통합 소스만)
Get-ChildItem -Path (Join-Path $staging 'deploy') -Filter '*.zip' -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
$localEnv = Join-Path $staging 'deploy\gc_automation.env'
if (Test-Path $localEnv) { Remove-Item $localEnv -Force }

Get-ChildItem -Path $staging -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path $dest) { Remove-Item $dest -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $dest -Force
Remove-Item $staging -Recurse -Force

$count = (Get-ChildItem -Path $dest).Count
$size = (Get-Item $dest).Length
Write-Host "Created $dest ($size bytes)"
