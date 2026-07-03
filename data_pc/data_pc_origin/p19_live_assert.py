# -*- coding: utf-8
"""P19 — production live artifact validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

MIN_ROW_COUNT = 100
MIN_SHEETS_UPDATED = 6

_SECRET_PATTERN = re.compile(
    r"(password|app_password|psk)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


@dataclass
class LiveValidationResult:
    ok: bool
    checks: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def assert_no_secrets(text: str) -> bool:
    return _SECRET_PATTERN.search(text) is None


def validate_imap_live_payload(payload: Mapping[str, Any]) -> LiveValidationResult:
    """`live_imap` / production imap block 검증."""
    checks: List[str] = []
    failures: List[str] = []

    status = str(payload.get("status", ""))
    if status == "ok":
        checks.append("status_ok")
    elif status == "skipped" and "no pending" in str(payload.get("reason", "")).lower():
        checks.append("skipped_no_pending")
        return LiveValidationResult(ok=True, checks=checks, failures=failures)
    else:
        failures.append(f"unexpected status={status!r}")

    if payload.get("workflow_ok") is True:
        checks.append("workflow_ok")
    elif status == "ok":
        failures.append("workflow_ok missing")

    row_count = payload.get("row_count")
    if isinstance(row_count, int) and row_count >= MIN_ROW_COUNT:
        checks.append(f"row_count>={MIN_ROW_COUNT}")
    elif status == "ok":
        failures.append(f"row_count={row_count!r}")

    sheets = payload.get("sheets_updated")
    if isinstance(sheets, int) and sheets >= MIN_SHEETS_UPDATED:
        checks.append(f"sheets>={MIN_SHEETS_UPDATED}")
    elif status == "ok":
        failures.append(f"sheets_updated={sheets!r}")

    save_path = str(payload.get("save_path", ""))
    if save_path:
        checks.append("save_path_set")
    if payload.get("save_path_exists") is True:
        checks.append("save_path_exists")

    mode = str(payload.get("mode", ""))
    if mode in ("full_archive", "FULL_ARCHIVE", ""):
        checks.append("mode_ok")
    elif mode:
        checks.append(f"mode={mode}")

    return LiveValidationResult(
        ok=not failures,
        checks=checks,
        failures=failures,
    )


def validate_production_run_result(result: Mapping[str, Any]) -> LiveValidationResult:
    """`live_production_e2e` / run harness JSON 검증."""
    checks: List[str] = []
    failures: List[str] = []

    blob = json.dumps(result, ensure_ascii=False)
    if assert_no_secrets(blob):
        checks.append("no_secrets")
    else:
        failures.append("secret pattern in artifact")

    mode = str(result.get("mode", ""))
    if mode in ("live", "dry_prep", "prep_live", "validate_fixture"):
        checks.append(f"mode={mode}")

    if mode == "live":
        imap = result.get("imap")
        if isinstance(imap, dict):
            nested = validate_imap_live_payload(imap)
            checks.extend(nested.checks)
            failures.extend(nested.failures)
        else:
            failures.append("imap block missing")
        validation = result.get("validation")
        if isinstance(validation, dict) and validation.get("ok") is True:
            checks.append("validation_ok")
        elif str(result.get("status")) == "ok":
            failures.append("validation not ok")

    elif mode == "validate_fixture":
        validation = result.get("validation")
        if isinstance(validation, dict) and validation.get("ok") is True:
            checks.append("fixture_validation_ok")
        else:
            failures.append("fixture validation failed")

    status = str(result.get("status", ""))
    if status in ("ok", "skipped", "dry_run"):
        checks.append(f"status={status}")
    elif not failures:
        failures.append(f"status={status}")

    return LiveValidationResult(
        ok=not failures,
        checks=checks,
        failures=failures,
    )


def fixture_ok_imap_payload() -> Dict[str, Any]:
    """과거 live 성공 기준 (161행 · 6 sheets)."""
    return {
        "status": "ok",
        "workflow_ok": True,
        "row_count": 161,
        "sheets_updated": 6,
        "save_path": "G:\\test\\sample.opju",
        "save_path_exists": True,
        "mode": "full_archive",
    }
