# GC3 장비 PC (Win7) 배포 zip — USB 복사용
# · GC8860(Cursor)에서 개발 후 gc3_make_deploy_zip.bat 실행
# · __pycache__, .git, 비밀번호 env, data_pc 산출물 제외
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$dest = Join-Path $PSScriptRoot 'GC3_chem32-gc-automation.zip'
$staging = Join-Path $env:TEMP ("gc3_deploy_" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging -Force | Out-Null

Get-ChildItem -Path $root -File | Where-Object {
    $n = $_.Name
    $n -match '\.(py|bat|txt|md)$' -or $n -eq '.env.example' -or $n -eq '.gitignore'
} | ForEach-Object { Copy-Item $_.FullName -Destination $staging }

foreach ($d in @('.cursor', 'deploy', 'test_fixtures')) {
    $src = Join-Path $root $d
    if (Test-Path $src) {
        Copy-Item $src -Destination (Join-Path $staging $d) -Recurse -Force
    }
}

# deploy: zip·로컬 비밀 env 제외
$deployStaging = Join-Path $staging 'deploy'
Get-ChildItem -Path $deployStaging -Filter '*.zip' -ErrorAction SilentlyContinue |
    Remove-Item -Force -ErrorAction SilentlyContinue
$localEnv = Join-Path $deployStaging 'gc_automation.env'
if (Test-Path $localEnv) { Remove-Item $localEnv -Force }

# data_pc 폴더는 GC3에 불필요 (용량 절약)
$dataPc = Join-Path $staging 'data_pc'
if (Test-Path $dataPc) { Remove-Item $dataPc -Recurse -Force }

Get-ChildItem -Path $staging -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path $dest) { Remove-Item $dest -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $dest -Force
Remove-Item $staging -Recurse -Force

$size = (Get-Item $dest).Length
Write-Host "Created $dest ($size bytes)"
