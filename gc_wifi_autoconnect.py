# -*- coding: utf-8 -*-
"""
gc_wifi_autoconnect.py — 부팅·감시 시 Wi-Fi 켜기 + iptime 자동 연결

GC2/GC3 장비 PC · 차헌 데이터 PC 공통.
Windows 재부팅·절전 후 Wi-Fi 어댑터는 켜져 있어도 SSID 프로필이 없으면
iptime / iptime 2 / iptime_5G 에 다시 붙지 않습니다.

설정 (gc_automation.env):
  REQUIRED_HOTSPOT=iptime,iptime 2,iptime_5G
  IPTIME_WIFI_PSK=12121212          # 연구실 공용 (프로필 자동 등록)

로그:
  GC2/GC3: %USERPROFILE%\\Desktop\\KCH\\gc_wifi_autoconnect.log
  데이터 PC: %USERPROFILE%\\.cursor\\gc-runtime-temp\\data_pc_wifi.log
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
import xml.sax.saxutils as saxutils
from datetime import datetime

from gc_config import EXCEL_OUTPUT_DIR, REQUIRED_HOTSPOT_SSID

_SUBPROCESS_FLAGS = 0
if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW

_WIFI_INTERFACE = "Wi-Fi"
_DEFAULT_PSK = "12121212"
_DEFAULT_SSIDS = tuple(
    part.strip() for part in REQUIRED_HOTSPOT_SSID.split(",") if part.strip()
) or ("iptime_5G", "iptime", "iptime 2")
# 5GHz 우선
_CONNECT_ORDER = ("iptime_5G", "iptime", "iptime 2")


def _default_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _data_pc_home() -> str:
    return os.path.join(os.path.expanduser("~"), "Desktop", ".cursor")


def _is_data_pc_dir(script_dir: str) -> bool:
    calc = os.path.join(script_dir, "촉매 반응 계산.py")
    return os.path.isfile(calc)


def _log_path(script_dir: str) -> str:
    if _is_data_pc_dir(script_dir):
        path = os.path.join(
            os.path.expanduser("~"), ".cursor", "gc-runtime-temp", "data_pc_wifi.log"
        )
    else:
        out = EXCEL_OUTPUT_DIR
        try:
            from gc_profiles import resolve_excel_output_dir

            out = resolve_excel_output_dir(script_dir)
        except Exception:
            pass
        path = os.path.join(out, "gc_wifi_autoconnect.log")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def _log(script_dir: str, message: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}"
    try:
        with open(_log_path(script_dir), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _run(cmd: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=_SUBPROCESS_FLAGS,
    )


def _load_env(script_dir: str) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    if _is_data_pc_dir(script_dir):
        for name in (".env", "gc_automation.env"):
            path = os.path.join(script_dir, name)
            if os.path.isfile(path):
                load_dotenv(path)
        return
    try:
        from gc_mailer import load_dotenv_files

        out = EXCEL_OUTPUT_DIR
        try:
            from gc_profiles import resolve_excel_output_dir

            out = resolve_excel_output_dir(script_dir)
        except Exception:
            pass
        load_dotenv_files(script_dir, out)
    except ImportError:
        for base in (script_dir, EXCEL_OUTPUT_DIR):
            for name in (".env", "gc_automation.env"):
                path = os.path.join(base, name)
                if os.path.isfile(path):
                    load_dotenv(path)


def _load_config(script_dir: str) -> tuple[tuple[str, ...], str]:
    _load_env(script_dir)
    raw = (
        os.getenv("REQUIRED_HOTSPOT", "").strip()
        or os.getenv("REQUIRED_HOTSPOT_SSID", "").strip()
        or REQUIRED_HOTSPOT_SSID
    )
    ssids = tuple(part.strip() for part in raw.split(",") if part.strip()) or _DEFAULT_SSIDS
    psk = (
        os.getenv("IPTIME_WIFI_PSK", "").strip()
        or os.getenv("REQUIRED_HOTSPOT_PSK", "").strip()
        or _DEFAULT_PSK
    )
    return ssids, psk


def _connect_order(ssids: tuple[str, ...]) -> tuple[str, ...]:
    ordered = [s for s in _CONNECT_ORDER if s in ssids]
    for s in ssids:
        if s not in ordered:
            ordered.append(s)
    return tuple(ordered)


def _connected_ssid() -> str | None:
    if sys.platform != "win32":
        return None
    result = _run(["netsh", "wlan", "show", "interfaces"], timeout=15)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("SSID") and not stripped.startswith("BSSID"):
            _, _, value = stripped.partition(":")
            ssid = value.strip()
            if ssid:
                return ssid
    return None


def _saved_profiles() -> set[str]:
    result = _run(["netsh", "wlan", "show", "profiles"], timeout=15)
    if result.returncode != 0:
        return set()
    names: set[str] = set()
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        if "프로필" in key or "profile" in key.lower():
            name = value.strip().strip('"')
            if name:
                names.add(name)
    return names


def _enable_wifi_interface(script_dir: str) -> None:
    if sys.platform != "win32":
        return
    _run(["netsh", "interface", "set", "interface", _WIFI_INTERFACE, "admin=enabled"])
    _log(script_dir, f"[wifi] {_WIFI_INTERFACE} 어댑터 활성화")


def _disable_wifi_power_save(script_dir: str) -> None:
    if sys.platform != "win32":
        return
    ps = (
        f'$a = Get-NetAdapter -Name "{_WIFI_INTERFACE}" -ErrorAction SilentlyContinue; '
        "if ($a) { "
        "Set-NetAdapterPowerManagement -Name $a.Name "
        "-AllowComputerToTurnOffDevice Disabled -ErrorAction SilentlyContinue "
        "}"
    )
    try:
        _run(["powershell", "-NoProfile", "-Command", ps], timeout=8)
    except (subprocess.TimeoutExpired, OSError) as exc:
        _log(script_dir, f"[wifi] 전원 관리 설정 생략: {exc}")


def _profile_xml(ssid: str, psk: str) -> str:
    esc_ssid = saxutils.escape(ssid)
    esc_psk = saxutils.escape(psk)
    return f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{esc_ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{esc_ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{esc_psk}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>
"""


def _ensure_profiles(script_dir: str, ssids: tuple[str, ...], psk: str) -> None:
    if not psk:
        return
    existing = _saved_profiles()
    for ssid in ssids:
        if ssid in existing:
            _run(
                ["netsh", "wlan", "set", "profileparameter", f"name={ssid}", "connectionmode=auto"]
            )
            continue
        xml = _profile_xml(ssid, psk)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(xml)
            tmp_path = tmp.name
        try:
            result = _run(["netsh", "wlan", "add", "profile", f"filename={tmp_path}", "user=all"])
            if result.returncode == 0:
                _log(script_dir, f"[wifi] 프로필 등록: {ssid} (자동 연결)")
            else:
                detail = result.stderr.strip() or result.stdout.strip()
                _log(script_dir, f"[wifi] 프로필 등록 실패 {ssid}: {detail}")
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _try_connect(ssid: str) -> bool:
    result = _run(
        [
            "netsh",
            "wlan",
            "connect",
            f"name={ssid}",
            f"ssid={ssid}",
            f"interface={_WIFI_INTERFACE}",
        ],
        timeout=25,
    )
    if result.returncode != 0:
        return False
    for _ in range(12):
        time.sleep(2)
        if _connected_ssid() == ssid:
            return True
    return False


def ensure_wifi_connected(script_dir: str | None = None) -> bool:
    """Wi-Fi 켜기 + REQUIRED_HOTSPOT SSID 중 하나 연결. 이미 연결됐으면 True."""
    if sys.platform != "win32":
        return True

    script_dir = script_dir or _default_script_dir()
    ssids, psk = _load_config(script_dir)
    order = _connect_order(ssids)

    connected = _connected_ssid()
    if connected in ssids:
        _log(script_dir, f"[wifi] 이미 연결됨: {connected}")
        return True

    _enable_wifi_interface(script_dir)
    _disable_wifi_power_save(script_dir)
    _ensure_profiles(script_dir, ssids, psk)

    profiles = _saved_profiles()
    for ssid in order:
        if ssid not in profiles and not psk:
            continue
        _log(script_dir, f"[wifi] 연결 시도: {ssid}")
        if _try_connect(ssid):
            _log(script_dir, f"[wifi] 연결됨: {ssid}")
            return True

    _log(script_dir, "[wifi] iptime 연결 실패 — USB Wi-Fi·공유기 확인")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="iptime Wi-Fi 자동 연결 (GC2/GC3/데이터 PC)")
    parser.add_argument("--script-dir", default=_default_script_dir())
    args = parser.parse_args()
    ok = ensure_wifi_connected(args.script_dir)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
