# -*- coding: utf-8
"""P13 — 네이버 IMAP adapter (촉매 importlib 위임)."""

from __future__ import annotations

import imaplib
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

PrintFn = Callable[[str], None]


@dataclass(frozen=True)
class ImapPrep:
    ready: bool
    reason: str
    email_masked: str
    has_password: bool
    inbox_dir: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "email_masked": self.email_masked,
            "has_password": self.has_password,
            "inbox_dir": self.inbox_dir,
        }


@dataclass(frozen=True)
class FetchedMail:
    attachment_path: str
    subject: str
    mail_key: str
    source: str
    filename: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "attachment_path": self.attachment_path,
            "subject": self.subject,
            "mail_key": self.mail_key,
            "source": self.source,
            "filename": self.filename,
        }


def mask_email(addr: str) -> str:
    addr = (addr or "").strip()
    if "@" not in addr:
        return ""
    local, domain = addr.split("@", 1)
    if len(local) <= 2:
        return f"{local[:1]}***@{domain}"
    return f"{local[:2]}***@{domain}"


def load_imap_catalyst() -> Any:
    from data_pc_origin.live_data import _load_catalyst_module

    return _load_catalyst_module()


def prepare_imap(*, catalyst: Any | None = None) -> ImapPrep:
    mod = catalyst if catalyst is not None else load_imap_catalyst()
    inbox = str(getattr(mod, "DATA_PC_INBOX_DIR", ""))
    if not mod._load_dotenv_files():
        return ImapPrep(False, "dotenv unavailable", "", False, inbox)
    email, pwd = mod._get_mail_credentials()
    masked = mask_email(email)
    if not email or not pwd:
        return ImapPrep(
            False,
            "NAVER_EMAIL / NAVER_APP_PASSWORD missing",
            masked,
            bool(pwd),
            inbox,
        )
    return ImapPrep(True, "ready", masked, True, inbox)


def _connect_imap(mod: Any) -> imaplib.IMAP4_SSL:
    email, pwd = mod._get_mail_credentials()
    if not email or not pwd:
        raise RuntimeError("mail credentials missing")
    mail = imaplib.IMAP4_SSL(mod.NAVER_IMAP_HOST, mod.NAVER_IMAP_PORT)
    mail.login(email, pwd)
    return mail


def gather_pending_counts(
    mod: Any | None = None,
    *,
    printer: PrintFn = print,
) -> Dict[str, object]:
    """IMAP login → pending GC mail counts (읽기·집계만)."""
    catalyst = mod if mod is not None else load_imap_catalyst()
    prep = prepare_imap(catalyst=catalyst)
    if not prep.ready:
        return {"ok": False, "reason": prep.reason, "prep": prep.to_dict()}

    mail = _connect_imap(catalyst)
    try:
        done_keys = catalyst._load_processed_mail_ids()
        inbox_pending = catalyst._gather_pending_from_folder(
            mail, "INBOX", done_keys, unseen_only=False
        )
        sent_mb = catalyst._find_sent_mailbox(mail)
        sent_pending: List[object] = []
        if sent_mb:
            sent_pending = catalyst._gather_pending_from_folder(
                mail, sent_mb, done_keys, unseen_only=True
            )
        self_mb = catalyst._find_self_mailbox(mail)
        self_pending: List[object] = []
        if self_mb:
            self_pending = catalyst._gather_pending_from_folder(
                mail, self_mb, done_keys, days=None, unseen_only=True
            )
        merged = catalyst._merge_pending_by_date(
            inbox_pending, sent_pending, self_pending
        )
        printer(
            f"IMAP pending: inbox={len(inbox_pending)} "
            f"sent={len(sent_pending)} self={len(self_pending)} total={len(merged)}"
        )
        return {
            "ok": True,
            "prep": prep.to_dict(),
            "inbox_pending": len(inbox_pending),
            "sent_pending": len(sent_pending),
            "self_pending": len(self_pending),
            "total_pending": len(merged),
        }
    finally:
        try:
            mail.logout()
        except Exception:  # noqa: BLE001
            pass


def fetch_oldest_pending(
    mod: Any | None = None,
    *,
    mark_seen: bool = False,
    printer: PrintFn = print,
) -> Optional[FetchedMail]:
    """가장 오래된 pending GC 메일 1건 → inbox xlsx 저장."""
    catalyst = mod if mod is not None else load_imap_catalyst()
    prep = prepare_imap(catalyst=catalyst)
    if not prep.ready:
        return None

    mail = _connect_imap(catalyst)
    try:
        done_keys = catalyst._load_processed_mail_ids()
        inbox_pending = catalyst._gather_pending_from_folder(
            mail, "INBOX", done_keys, unseen_only=False
        )
        sent_mb = catalyst._find_sent_mailbox(mail)
        sent_pending = (
            catalyst._gather_pending_from_folder(
                mail, sent_mb, done_keys, unseen_only=True
            )
            if sent_mb
            else []
        )
        self_mb = catalyst._find_self_mailbox(mail)
        self_pending = (
            catalyst._gather_pending_from_folder(
                mail, self_mb, done_keys, days=None, unseen_only=True
            )
            if self_mb
            else []
        )
        pending_all = catalyst._merge_pending_by_date(
            inbox_pending, sent_pending, self_pending
        )
        if not pending_all:
            return None

        item = pending_all[0]
        filename, payload = item["attachments"][0]
        path = catalyst._save_attachment_bytes(
            catalyst.DATA_PC_INBOX_DIR, filename, payload
        )
        identity = catalyst._experiment_identity_key(filename)
        catalyst._cleanup_inbox_duplicate_files(path, identity)
        printer(f"IMAP fetch: {filename} → {path}")

        if mark_seen:
            catalyst._mark_mail_seen_and_logged(mail, item, done_keys)

        return FetchedMail(
            attachment_path=path,
            subject=str(item.get("subject", "")),
            mail_key=str(item.get("mail_key", "")),
            source=str(item.get("source", "")),
            filename=filename,
        )
    finally:
        try:
            mail.logout()
        except Exception:  # noqa: BLE001
            pass
