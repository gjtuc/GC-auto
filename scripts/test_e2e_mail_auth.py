# -*- coding: utf-8 -*-
"""test_e2e_mail_auth.py — Step 8 SMTP/IMAP 로그인만 검사 (메일 발송·수신 없음)

GC1 장비 env: Desktop\\박은규\\gc_automation.env  (SMTP)
데이터 PC env: Desktop\\.cursor\\gc_automation.env (IMAP)

Usage:
  python scripts/test_e2e_mail_auth.py
  python scripts/test_e2e_mail_auth.py --smtp-only
  python scripts/test_e2e_mail_auth.py --imap-only
"""
from __future__ import annotations

import argparse
import imaplib
import os
import smtplib
import sys

NAVER_SMTP_HOST = "smtp.naver.com"
NAVER_SMTP_PORT = 587
NAVER_IMAP_HOST = "imap.naver.com"
NAVER_IMAP_PORT = 993


def _load_env(path: str) -> bool:
    if not os.path.isfile(path):
        print(f"[FAIL] env 없음: {path}")
        return False
    try:
        from dotenv import load_dotenv
    except ImportError:
        print("[FAIL] pip install python-dotenv")
        return False
    load_dotenv(path, override=True)
    return True


def _creds(label: str) -> tuple[str, str] | None:
    email = os.getenv("NAVER_EMAIL", "").strip()
    pw = os.getenv("NAVER_APP_PASSWORD", "").strip()
    if not email or not pw:
        print(f"[FAIL] {label}: NAVER_EMAIL / NAVER_APP_PASSWORD 비어 있음")
        return None
    return email, pw


def test_smtp(env_path: str) -> bool:
    print(f"\n--- SMTP (GC1 send) ---\n  env: {env_path}")
    if not _load_env(env_path):
        return False
    creds = _creds("SMTP")
    if not creds:
        return False
    email, pw = creds
    mail_to = os.getenv("MAIL_TO", email).strip() or email
    try:
        with smtplib.SMTP(NAVER_SMTP_HOST, NAVER_SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(email, pw)
        print(f"[OK] SMTP login: {email} -> MAIL_TO={mail_to}")
        return True
    except Exception as exc:
        print(f"[FAIL] SMTP: {exc}")
        return False


def test_imap(env_path: str) -> bool:
    print(f"\n--- IMAP (data PC receive) ---\n  env: {env_path}")
    if not _load_env(env_path):
        return False
    creds = _creds("IMAP")
    if not creds:
        return False
    email, pw = creds
    try:
        mail = imaplib.IMAP4_SSL(NAVER_IMAP_HOST, NAVER_IMAP_PORT)
        mail.login(email, pw)
        typ, data = mail.select("INBOX", readonly=True)
        count = int(data[0]) if typ == "OK" and data else 0
        mail.logout()
        print(f"[OK] IMAP login: {email}  INBOX messages: {count}")
        return True
    except Exception as exc:
        print(f"[FAIL] IMAP: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Step 8 mail auth check (no send/receive)")
    parser.add_argument("--smtp-only", action="store_true")
    parser.add_argument("--imap-only", action="store_true")
    args = parser.parse_args()

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    gc1_env = os.path.join(desktop, "박은규", "gc_automation.env")
    data_env = os.path.join(desktop, ".cursor", "gc_automation.env")

    print("=== Step 8 - mail authentication ===")
    ok = True
    if not args.imap_only:
        ok = test_smtp(gc1_env) and ok
    if not args.smtp_only:
        ok = test_imap(data_env) and ok

    print()
    if ok:
        print("[PASS] Mail auth OK - Step 8.3/8.4 ready")
        return 0
    print("[FAIL] Mail auth - check env, app password, network")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
