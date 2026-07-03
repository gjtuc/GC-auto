# -*- coding: utf-8 -*-
"""
L1 — 상태 저장: ``.gc_autochro_job.json`` 단일 진실 공급원 (Ω.A.B.STATE).

atom 레코드 7필드 (설계 §B-STATE):
  status, attempt, channel_used, fail_code,
  probe_snapshot, started_at, ended_at

L1-R load / L1-W save (temp + os.replace) — ``data_pc_runtime.layer1_state`` 와 동일 패턴.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal

AtomChannel = Literal["H", "E", "F", "W"]


class AtomStatus(str, Enum):
    """Ω.A.B.STATE.atoms.{id}.status"""

    PENDING = "pending"
    RUNNING = "running"
    OK = "ok"
    FAIL = "fail"
    SKIP = "skip"


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class AtomRecord:
    """atom 7필드 — L4 실행 시 STW 단위."""

    status: AtomStatus = AtomStatus.PENDING
    attempt: int = 0
    channel_used: AtomChannel | None = None
    fail_code: str | None = None
    probe_snapshot: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None
    ended_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AtomRecord:
        if not data:
            return cls()
        raw_status = str(data.get("status", AtomStatus.PENDING.value))
        try:
            status = AtomStatus(raw_status)
        except ValueError:
            status = AtomStatus.PENDING
        channel = data.get("channel_used")
        channel_used: AtomChannel | None
        if channel in ("H", "E", "F", "W"):
            channel_used = channel
        else:
            channel_used = None
        snap = data.get("probe_snapshot")
        return cls(
            status=status,
            attempt=int(data.get("attempt", 0)),
            channel_used=channel_used,
            fail_code=data.get("fail_code"),
            probe_snapshot=dict(snap) if isinstance(snap, dict) else {},
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "attempt": self.attempt,
            "channel_used": self.channel_used,
            "fail_code": self.fail_code,
            "probe_snapshot": self.probe_snapshot,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


@dataclass
class JobState:
    """`.gc_autochro_job.json` 루트 — 설계 예시·T14 스키마."""

    job_id: str = ""
    started_at: str | None = None
    data_name: str = ""
    pdf_path_planned: str = ""
    prep_enabled: bool = True
    phase_current: str = "P0"
    atom_current: str | None = None
    resume_from: str | None = None
    force: bool = False
    hancom_windows_seen: int = 0
    atoms: dict[str, AtomRecord] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobState:
        atoms_raw = data.get("atoms") or {}
        atoms: dict[str, AtomRecord] = {}
        if isinstance(atoms_raw, dict):
            for atom_id, rec in atoms_raw.items():
                atoms[str(atom_id)] = AtomRecord.from_dict(
                    rec if isinstance(rec, dict) else {}
                )
        return cls(
            job_id=str(data.get("job_id") or ""),
            started_at=data.get("started_at"),
            data_name=str(data.get("data_name") or ""),
            pdf_path_planned=str(data.get("pdf_path_planned") or ""),
            prep_enabled=bool(data.get("prep_enabled", True)),
            phase_current=str(data.get("phase_current") or "P0"),
            atom_current=data.get("atom_current"),
            resume_from=data.get("resume_from"),
            force=bool(data.get("force", False)),
            hancom_windows_seen=int(data.get("hancom_windows_seen", 0)),
            atoms=atoms,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "started_at": self.started_at,
            "data_name": self.data_name,
            "pdf_path_planned": self.pdf_path_planned,
            "prep_enabled": self.prep_enabled,
            "phase_current": self.phase_current,
            "atom_current": self.atom_current,
            "resume_from": self.resume_from,
            "force": self.force,
            "hancom_windows_seen": self.hancom_windows_seen,
            "atoms": {aid: rec.to_dict() for aid, rec in self.atoms.items()},
        }

    @classmethod
    def new_job(
        cls,
        *,
        data_name: str = "",
        pdf_path_planned: str = "",
        prep_enabled: bool = True,
        atom_ids: tuple[str, ...] = (),
    ) -> JobState:
        """P0.06 — job_id·started_at·atoms pending 초기화."""
        now = _iso_now()
        atoms = {aid: AtomRecord() for aid in atom_ids}
        return cls(
            job_id=str(uuid.uuid4()),
            started_at=now,
            data_name=data_name,
            pdf_path_planned=pdf_path_planned,
            prep_enabled=prep_enabled,
            phase_current="P0",
            atoms=atoms,
        )


@dataclass(frozen=True)
class JobPaths:
    """L1-P: job JSON 경로."""

    output_dir: str

    @property
    def job_json(self) -> str:
        return os.path.join(self.output_dir, ".gc_autochro_job.json")


class StateStore:
    """L1-R / L1-W — ``JobState`` 원자 저장."""

    def __init__(self, paths: JobPaths) -> None:
        self.paths = paths

    def load(self) -> JobState:
        return JobState.from_dict(self._load_json(self.paths.job_json))

    def save(self, state: JobState) -> None:
        self._save_json(self.paths.job_json, state.to_dict())

    def stw_atom(
        self,
        state: JobState,
        atom_id: str,
        *,
        status: AtomStatus | None = None,
        attempt: int | None = None,
        channel_used: AtomChannel | None = None,
        fail_code: str | None = None,
        probe_snapshot: dict[str, Any] | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
        save: bool = True,
    ) -> JobState:
        """Ω.A.B.STATE.atoms.* — 필드 단위 STW 후 선택적 persist."""
        rec = state.atoms.get(atom_id, AtomRecord())
        if status is not None:
            rec.status = status
        if attempt is not None:
            rec.attempt = attempt
        if channel_used is not None:
            rec.channel_used = channel_used
        if fail_code is not None:
            rec.fail_code = fail_code
        if probe_snapshot is not None:
            rec.probe_snapshot = dict(probe_snapshot)
        if started_at is not None:
            rec.started_at = started_at
        if ended_at is not None:
            rec.ended_at = ended_at
        state.atoms[atom_id] = rec
        state.atom_current = atom_id
        if save:
            self.save(state)
        return state

    @staticmethod
    def _load_json(path: str) -> dict[str, Any]:
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _save_json(path: str, payload: dict[str, Any]) -> None:
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            suffix=".tmp",
            prefix=Path(path).name + ".",
            dir=directory,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
