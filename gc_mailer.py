# -*- coding: utf-8 -*-
"""
gc_mailer.py — 네이버 SMTP 메일 발송 (장비 PC → 데이터 PC)

[PC·메일 흐름]  docs/PC_NAMING.md
  장비 PC gc_automation.py 가 KCH 원본 xlsx 를 **데이터 PC** 로 보냄.
    GC1 장비 PC → MAIL_TO = **은규 PC** 네이버
    GC2/GC3 장비 PC → MAIL_TO = **차헌 PC** 네이버 (kimcha0809)

[설정]  gc_automation.env (장비 PC의 Desktop\\박은규 또는 KCH)
  NAVER_EMAIL, NAVER_APP_PASSWORD — 발송 계정 (장비 PC 또는 공용)
  MAIL_TO — 수신 = 상대방 **데이터 PC** 주소

[호출 경로]
  gc_pipeline._try_auto_email() — force 또는 GC1 은 슬롯 검사 생략
  gc_state.try_pending_email_retry() — 엑셀만 성공·메일 실패 후 재시도

[네트워크]  gc_wifi.wait_for_smtp_internet() — 핫스pot 직후 DNS 지연 대비
"""

from __future__ import annotations

import os
import socket
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Tuple

from gc_config import (
    NAVER_SMTP_HOST,
    NAVER_SMTP_PORT,
    SMTP_INTERNET_POLL_SEC,
    SMTP_INTERNET_WAIT_MAX_SEC,
    SMTP_SEND_RETRIES,
    SMTP_SEND_RETRY_DELAY_SEC,
    SMTP_SOCKET_TIMEOUT_SEC,
    TARGET_EMAIL,
)


def load_dotenv_files(script_dir: str, excel_output_dir: str) -> bool:
    """NAVER_EMAIL 등 환경 변수 로드. 실패 시 False."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[오류] python-dotenv 미설치: pip install python-dotenv")
        return False

    for base in (script_dir, excel_output_dir):
        for name in (".env", "gc_automation.env"):
            path = os.path.join(base, name)
            if os.path.isfile(path):
                load_dotenv(path)
    return True


def get_smtp_credentials(script_dir: str, excel_output_dir: str) -> Tuple[Optional[str], Optional[str], str]:
    """(sender, app_password, recipient)"""
    if not load_dotenv_files(script_dir, excel_output_dir):
        return None, None, TARGET_EMAIL

    sender = os.getenv("NAVER_EMAIL", "").strip()
    app_password = os.getenv("NAVER_APP_PASSWORD", "").strip()
    recipient = os.getenv("MAIL_TO", TARGET_EMAIL).strip() or TARGET_EMAIL
    return sender, app_password, recipient


def generate_email_body(
    sample_name: str,
    seq_date: str,
    cycle_count: int,
    peak_count: int,
    output_filename: str,
    total_injection_folders: int,
    skipped_first_info=None,
    missing_acam: Optional[List[str]] = None,
    chem32: bool = False,
    fid_cycles: int = 0,
    tcd_cycles: int = 0,
) -> str:
    """메일 본문 (플레인 텍스트)."""
    lines = [
        "GC ChemStation 자동 정리 결과를 첨부합니다.",
        "",
        f"분석 날짜: {seq_date}",
        f"시료: {sample_name}",
        f"첨부 파일: {output_filename}",
    ]
    if chem32:
        lines.append(f"시트 FID: {fid_cycles}주입 / 시트 TCD: {tcd_cycles}주입 / 피크 합계: {peak_count}개")
    else:
        lines.append(f"주입 폴더: {total_injection_folders}개 / 엑셀 적재: {cycle_count}개 / 피크: {peak_count}개")

    if skipped_first_info:
        lines.extend(
            [
                "",
                "[1주입 제외] startup 노이즈로 판단하여 제외함",
                f"  제외 주입: {skipped_first_info['label']}",
                f"  1주입 RT ({len(skipped_first_info['first_rts'])}피크): {skipped_first_info['first_rts']}",
                f"  2주입 RT ({len(skipped_first_info['reference_rts'])}피크): {skipped_first_info['reference_rts']}",
            ]
        )
    else:
        lines.extend(["", "[1주입 제외] 없음 (1·2주입 RT 패턴 일치)"])

    if missing_acam:
        lines.extend(["", f"[경고] sequence.acam_ 없음 ({len(missing_acam)}건)"])
        for name in missing_acam:
            lines.append(f"  - {name}")
    else:
        lines.extend(["", "[경고] sequence.acam_ 없음: 없음"])

    return "\n".join(lines) + "\n"


def _is_transient_smtp_error(exc: BaseException) -> bool:
    """DNS 미준비·일시 네트워크 끊김 등 재시도 가능 오류."""
    if isinstance(exc, (socket.gaierror, TimeoutError, ConnectionError, ConnectionResetError)):
        return True
    if isinstance(exc, OSError) and getattr(exc, "winerror", None) == 11001:
        return True
    if isinstance(exc, smtplib.SMTPServerDisconnected):
        return True
    text = str(exc).lower()
    transient_markers = (
        "getaddrinfo",
        "timed out",
        "timeout",
        "11001",
        "connection refused",
        "connection reset",
        "network is unreachable",
        "temporarily unavailable",
        "name or service not known",
    )
    return any(marker in text for marker in transient_markers)


def _smtp_send_once(
    sender: str,
    app_password: str,
    recipient: str,
    msg: MIMEMultipart,
) -> None:
    with smtplib.SMTP(NAVER_SMTP_HOST, NAVER_SMTP_PORT, timeout=SMTP_SOCKET_TIMEOUT_SEC) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender, app_password)
        server.sendmail(sender, [recipient], msg.as_string())


def send_email_via_smtp(
    excel_file_path: str,
    sample_name: str,
    seq_date: str,
    body_text: str,
    script_dir: str,
    excel_output_dir: str,
    *,
    smtp_wait_max_sec: Optional[int] = None,
    smtp_send_retries: Optional[int] = None,
) -> bool:
    """엑셀 첨부 네이버 SMTP 발송 — DNS/SMTP 준비 대기 + 일시 오류 재시도."""
    wait_max = smtp_wait_max_sec if smtp_wait_max_sec is not None else SMTP_INTERNET_WAIT_MAX_SEC
    retries = smtp_send_retries if smtp_send_retries is not None else SMTP_SEND_RETRIES
    sender, app_password, recipient = get_smtp_credentials(script_dir, excel_output_dir)
    if not sender or not app_password:
        env_hint = os.path.join(excel_output_dir, "gc_automation.env")
        print("\n[오류] 메일 설정 없음 — gc_automation.env 또는 .env 를 만드세요.")
        print(f"       경로 예: {env_hint}")
        return False

    subject = f"[{seq_date}] {sample_name} GC 분석 결과"
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    attach_name = os.path.basename(excel_file_path)
    with open(excel_file_path, "rb") as attach_file:
        part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        part.set_payload(attach_file.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", attach_name))
    msg.attach(part)

    from gc_wifi import wait_for_smtp_internet

    print(f"\n[진행] 네이버 SMTP 발송 ({sender} → {recipient})...")
    ready, reason = wait_for_smtp_internet(max_wait_sec=wait_max)
    if not ready:
        print(f"[오류] SMTP 인터넷 미준비 — {reason}")
        return False

    for attempt in range(1, retries + 1):
        try:
            _smtp_send_once(sender, app_password, recipient, msg)
            print(f"[성공] 이메일 발송 완료 → {recipient}")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[오류] SMTP 인증 실패 — 앱 비밀번호·IMAP/SMTP 사용 여부 확인")
            return False
        except Exception as exc:
            if attempt < retries and _is_transient_smtp_error(exc):
                print(f"[경고] SMTP 일시 오류 ({attempt}/{retries}): {exc}")
                wait_for_smtp_internet(
                    max_wait_sec=min(SMTP_SEND_RETRY_DELAY_SEC, wait_max),
                    poll_sec=SMTP_INTERNET_POLL_SEC,
                )
                time.sleep(SMTP_SEND_RETRY_DELAY_SEC)
                continue
            print(f"[오류] SMTP 발송 실패: {exc}")
            return False

    return False
