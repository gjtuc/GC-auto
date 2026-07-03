# o3_ui_win32.ps1 — Origin GUI 폴백 (차헌 PC · 은규 PC 공통)
# o3_session.py 가 COM project.save / lt_exec('exit') 실패 시 호출한다.
# AnswerSaveYes: "Save changes to project?" 대화상자 [예]
# CtrlS: 메인 창에 Ctrl+S 전송
# 배포: data_pc_origin/ 폴더와 함께 script_dir 로 복사 (port_eungyu_data_pc.ps1)
# 상세: docs/DATA_PC_ORIGIN_SAVE.md

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('AnswerSaveYes', 'CtrlS')]
    [string]$Action
)

Add-Type @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public class O3Win {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@

Add-Type -AssemblyName System.Windows.Forms

if ($Action -eq 'AnswerSaveYes') {
    $answered = $false
    [O3Win]::EnumWindows({
        param($hWnd, $lParam)
        $sb = New-Object System.Text.StringBuilder 512
        [void][O3Win]::GetWindowText($hWnd, $sb, 512)
        $title = $sb.ToString()
        if ($title -like 'OriginPro*' -and $title -notlike '*.opju*' -and $title -notlike '*.opj*') {
            [void][O3Win]::SetForegroundWindow($hWnd)
            $script:answered = $true
        }
        return $true
    }, [IntPtr]::Zero) | Out-Null
    if ($answered) {
        [System.Windows.Forms.SendKeys]::SendWait('y')
        Start-Sleep -Milliseconds 300
        [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
        Write-Output 'answered'
    } else {
        Write-Output 'none'
    }
    exit 0
}

$proc = Get-Process Origin64, Origin -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -like '*.opju*' -or $_.MainWindowTitle -like '*.opj*' } |
    Select-Object -First 1
if (-not $proc) {
    Write-Output 'no_window'
    exit 1
}
[void][O3Win]::SetForegroundWindow($proc.MainWindowHandle)
Start-Sleep -Milliseconds 400
[System.Windows.Forms.SendKeys]::SendWait('^s')
Write-Output 'sent'
