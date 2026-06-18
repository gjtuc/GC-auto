# sync_registry.ps1 - Record per-PC git push/pull + regenerate deploy/SYNC_STATUS.md
# Docs (Korean): docs/SYNC_TRACKING.md
#
# RULE: If another PC pushed to GitHub, every other PC must run gc_git_pull.bat
#       BEFORE editing and pushing again. Skipping pull can overwrite remote work.
#
# Usage:
#   powershell -File scripts/sync_registry.ps1 -Event push
#   powershell -File scripts/sync_registry.ps1 -Event pull
#   powershell -File scripts/sync_registry.ps1 -Event status

param(
    [ValidateSet('push', 'pull', 'status')]
    [string]$Event = 'status',
    [string]$RepoRoot = '',
    [string]$TriggeredBy = 'sync_registry.ps1'
)

$ErrorActionPreference = 'Stop'
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Get-GitExe {
    $p = 'C:\Program Files\Git\cmd\git.exe'
    if (Test-Path $p) { return $p }
    return 'git'
}

function Get-RepoRootPath {
    param([string]$Start)
    if ($Start -and (Test-Path $Start)) {
        return (Resolve-Path $Start).Path
    }
    $here = $PSScriptRoot
    if ($here) {
        return (Resolve-Path (Join-Path $here '..')).Path
    }
    return (Get-Location).Path
}

function Get-HeadInfo {
    param([string]$Git, [string]$Root)
    Push-Location $Root
    try {
        $sha = (& $Git rev-parse --short HEAD 2>$null).Trim()
        $full = (& $Git rev-parse HEAD 2>$null).Trim()
        $subject = (& $Git log -1 --format=%s 2>$null).Trim()
        $iso = (& $Git log -1 --format=%cI 2>$null).Trim()
        return @{ sha = $sha; full = $full; subject = $subject; at = $iso }
    } finally {
        Pop-Location
    }
}

function Find-MachineProfilePath {
    $desktop = [Environment]::GetFolderPath('Desktop')
    foreach ($dir in Get-ChildItem -LiteralPath $desktop -Directory -ErrorAction SilentlyContinue) {
        $candidate = Join-Path $dir.FullName 'machine_profile.json'
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $extra = @(
        (Join-Path $desktop '.cursor\KCH\machine_profile.json'),
        (Join-Path $desktop '.cursor\machine_profile.json')
    )
    foreach ($p in $extra) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function Get-PcIdentity {
    $computer = $env:COMPUTERNAME
    $user = $env:USERNAME
    $uuid = ''
    $mg = ''
    try {
        $uuid = (Get-CimInstance Win32_ComputerSystemProduct -ErrorAction SilentlyContinue).UUID
    } catch {}
    try {
        $mg = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography' -ErrorAction SilentlyContinue).MachineGuid
    } catch {}

    $role = 'unknown'
    $operator = ''
    $label = $computer

    $mp = Find-MachineProfilePath
    if ($mp) {
        try {
            $j = Get-Content -LiteralPath $mp -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($j.role) { $role = [string]$j.role }
            if ($j.label) { $label = [string]$j.label }
            if ($j.gc_assignment.operator) { $operator = [string]$j.gc_assignment.operator }
        } catch {}
    }

    if (-not $operator) { $operator = $user }

    return @{
        pc_id = $computer
        label = ('{0} ({1})' -f $computer, $role)
        role = $role
        operator = $user
        identifiers = @{
            computer_name = $computer
            windows_user = $user
            smbios_uuid = $uuid
            machine_guid = $mg
        }
    }
}

function Get-RegistryFile {
    param([string]$RegistryDir, [string]$PcId)
    $safe = ($PcId -replace '[\\/:*?"<>|]', '_')
    return Join-Path $RegistryDir ($safe + '.json')
}

function Load-Registry {
    param([string]$Path, [hashtable]$Identity)
    if (Test-Path -LiteralPath $Path) {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        return ($raw | ConvertFrom-Json)
    }
    $obj = [ordered]@{
        pc_id = $Identity.pc_id
        label = $Identity.label
        role = $Identity.role
        operator = $Identity.operator
        identifiers = $Identity.identifiers
        sync = [ordered]@{
            last_push_at = $null
            last_push_commit = $null
            last_push_by = $null
            last_pull_at = $null
            last_pull_commit = $null
            last_pull_by = $null
            repo_remote = 'https://github.com/gjtuc/GC-auto.git'
        }
        history = @()
    }
    return [pscustomobject]$obj
}

function Add-HistoryEntry {
    param($Reg, [string]$EventName, [hashtable]$Head, [string]$By)
    $entry = [ordered]@{
        event = $EventName
        at = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
        commit = $Head.sha
        subject = $Head.subject
        by = $By
        triggered_by = $TriggeredBy
    }
    $hist = @()
    if ($Reg.history) { $hist = @($Reg.history) }
    $hist = ,$entry + $hist
    if ($hist.Count -gt 20) { $hist = $hist[0..19] }
    $Reg.history = $hist
}

function Save-Registry {
    param($Reg, [string]$Path)
    $json = $Reg | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($Path, $json, $Utf8NoBom)
}

function Get-SyncStatusLabel {
    param([string]$PullC, [string]$PushC, [string]$HeadSha)
    if ($PullC -ne '-' -and $PullC -eq $HeadSha) { return '[OK] latest' }
    if ($PullC -eq '-' -and $PushC -eq $HeadSha) { return '[PUSH] pushed only' }
    if ($PullC -ne '-' -and $PullC -ne $HeadSha) { return '[WARN] need pull' }
    if ($PushC -ne '-' -and $PushC -ne $HeadSha) { return '[WARN] need pull' }
    return '[?] check'
}

function Write-SyncStatusMarkdown {
    param(
        [string]$DeployDir,
        [string]$RegistryDir,
        [hashtable]$Head
    )

    $expectedPath = Join-Path $RegistryDir 'EXPECTED_PCS.json'
    $expected = @()
    if (Test-Path -LiteralPath $expectedPath) {
        try {
            $ex = Get-Content -LiteralPath $expectedPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $expected = @($ex.pcs)
        } catch {}
    }

    $byPcId = @{}
    Get-ChildItem -LiteralPath $RegistryDir -Filter '*.json' -File | ForEach-Object {
        if ($_.Name -match '^(_template|EXPECTED_PCS)') { return }
        try {
            $r = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($r.pc_id) { $byPcId[[string]$r.pc_id] = $r }
        } catch {}
    }

    $allPcIds = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($e in $expected) {
        if ($e.pc_id) { [void]$allPcIds.Add([string]$e.pc_id) }
    }
    foreach ($k in $byPcId.Keys) { [void]$allPcIds.Add($k) }

    $now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('# PC sync status (auto-generated - do not edit)')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine("> Updated: $now | HEAD: ``$($Head.sha)`` | $($Head.subject)")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('## Summary (see docs/SYNC_TRACKING.md for Korean)')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('| PC | role | last push (who @ when) | push | last pull (who @ when) | pull | status |')
    [void]$sb.AppendLine('|----|------|-------------------------|------|-------------------------|------|--------|')

    foreach ($pcId in ($allPcIds | Sort-Object)) {
        $meta = $expected | Where-Object { $_.pc_id -eq $pcId } | Select-Object -First 1
        $reg = $byPcId[$pcId]
        $role = if ($meta) { $meta.role } elseif ($reg) { $reg.role } else { '?' }

        if (-not $reg) {
            [void]$sb.AppendLine("| ``$pcId`` | $role | - | - | - | - | [MISSING] run gc_git_pull.bat once |")
            continue
        }

        $s = $reg.sync
        $pushAt = if ($s.last_push_at) { $s.last_push_at } else { '-' }
        $pushBy = if ($s.last_push_by) { $s.last_push_by } else { '-' }
        $pushC = if ($s.last_push_commit) { $s.last_push_commit } else { '-' }
        $pullAt = if ($s.last_pull_at) { $s.last_pull_at } else { '-' }
        $pullBy = if ($s.last_pull_by) { $s.last_pull_by } else { '-' }
        $pullC = if ($s.last_pull_commit) { $s.last_pull_commit } else { '-' }
        $status = Get-SyncStatusLabel -PullC $pullC -PushC $pushC -HeadSha $Head.sha

        [void]$sb.AppendLine("| ``$pcId`` | $role | $pushBy @ $pushAt | ``$pushC`` | $pullBy @ $pullAt | ``$pullC`` | $status |")
    }

    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('## Commands')
    [void]$sb.AppendLine('- Start work: `gc_git_pull.bat`')
    [void]$sb.AppendLine('- Check only: `gc_git_status.bat`')
    [void]$sb.AppendLine('- Per-PC log: `deploy/sync_registry/COMPUTERNAME.json`')
    [void]$sb.AppendLine('')

    $out = Join-Path $DeployDir 'SYNC_STATUS.md'
    $legendPath = Join-Path $DeployDir 'sync_status_ko_legend.md'
    $content = $sb.ToString()
    if (Test-Path -LiteralPath $legendPath) {
        $content += "`n" + (Get-Content -LiteralPath $legendPath -Raw -Encoding UTF8)
    }
    [System.IO.File]::WriteAllText($out, $content, $Utf8NoBom)
}

# --- main ---
$root = Get-RepoRootPath -Start $RepoRoot
$git = Get-GitExe
$registryDir = Join-Path $root 'deploy\sync_registry'
$deployDir = Join-Path $root 'deploy'

if (-not (Test-Path -LiteralPath $registryDir)) {
    New-Item -ItemType Directory -Force -Path $registryDir | Out-Null
}

$identity = Get-PcIdentity
$head = Get-HeadInfo -Git $git -Root $root
$regPath = Get-RegistryFile -RegistryDir $registryDir -PcId $identity.pc_id
$reg = Load-Registry -Path $regPath -Identity $identity

$reg.label = $identity.label
$reg.role = $identity.role
$reg.operator = $identity.operator
$reg.identifiers = $identity.identifiers

$actor = $identity.pc_id + '\' + $identity.operator

if ($Event -eq 'push') {
    $reg.sync.last_push_at = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
    $reg.sync.last_push_commit = $head.sha
    $reg.sync.last_push_by = $actor
    Add-HistoryEntry -Reg $reg -EventName 'push' -Head $head -By $actor
}
elseif ($Event -eq 'pull') {
    $reg.sync.last_pull_at = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
    $reg.sync.last_pull_commit = $head.sha
    $reg.sync.last_pull_by = $actor
    Add-HistoryEntry -Reg $reg -EventName 'pull' -Head $head -By $actor
}

Save-Registry -Reg $reg -Path $regPath
Write-SyncStatusMarkdown -DeployDir $deployDir -RegistryDir $registryDir -Head $head

if ($Event -eq 'status') {
    Write-Host ('PC: {0} ({1})' -f $identity.pc_id, $identity.label)
    Write-Host ('HEAD: {0} - {1}' -f $head.sha, $head.subject)
    Write-Host ('Registry: {0}' -f $regPath)
    Write-Host 'Status: deploy\SYNC_STATUS.md'
}

exit 0
