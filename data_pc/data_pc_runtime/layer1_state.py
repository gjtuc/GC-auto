# -*- coding: utf-8 -*-
"""
L1 — 상태 저장: 런타임의 **단일 진실 공급원**.

하위 단계:
  L1-P  경로 해석 (script_dir → KCH|.data_pc_runtime_*.json)
  L1-R  load  — JSON 읽기 (손상 시 빈 dict)
  L1-W  save  — temp 파일 + os.replace (원자적)
  L1-M  모델  — RuntimeState 필드 의미 고정
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_epoch(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw), "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


@dataclass
class RuntimePaths:
    """L1-P: 파일 위치."""

    script_dir: str
    storage_subdir: str = "KCH"

    @property
    def storage_dir(self) -> str:
        return os.path.join(self.script_dir, self.storage_subdir)

    @property
    def state_json(self) -> str:
        return os.path.join(self.storage_dir, ".data_pc_runtime_state.json")

    @property
    def status_json(self) -> str:
        return os.path.join(self.storage_dir, ".data_pc_runtime_status.json")

    @property
    def pipeline_lock(self) -> str:
        return os.path.join(self.storage_dir, ".data_pc_pipeline.lock")


@dataclass
class RuntimeState:
    """
    L1-M: 처리·쿨다운·G: 재시도 (레거시 .data_pc_watch_state.json 호환 키 유지).

    | 필드 | 의미 |
    |------|------|
    | last_pipeline_at | 마지막 파이프라인 **종료** 시각 (쿨다운 기준) |
    | last_pipeline_workflows | 그때 반영한 시료 수 (0이면 쿨다운 미적용 예정) |
    | gdrive_retry_pending | G: 잠금으로 3~4단계 미완 |
    | last_gdrive_attempt_at | G: 재시도 타이머 |
    """

    schema_version: int = 1
    last_pipeline_at: str | None = None
    last_pipeline_workflows: int = 0
    gdrive_retry_pending: bool = False
    last_gdrive_attempt_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeState:
        return cls(
            schema_version=int(data.get("schema_version", 1)),
            last_pipeline_at=data.get("last_pipeline_at"),
            last_pipeline_workflows=int(data.get("last_pipeline_workflows", 0)),
            gdrive_retry_pending=bool(data.get("gdrive_retry_pending", False)),
            last_gdrive_attempt_at=data.get("last_gdrive_attempt_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeStatus:
    """L1-M: 감시 heartbeat·현재 게이트 (UI/로그용)."""

    alive: bool = True
    status_code: str = "starting"
    message: str = ""
    pid: int = 0
    wifi_ssid: str | None = None
    wifi_ready: bool = False
    gate_detail: str = ""
    cooldown_remaining_sec: int = 0
    started_at: str = field(default_factory=_now_str)
    updated_at: str = field(default_factory=_now_str)
    last_heartbeat: str = field(default_factory=_now_str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeStatus:
        return cls(
            alive=bool(data.get("alive", False)),
            status_code=str(data.get("status_code", "unknown")),
            message=str(data.get("message", "")),
            pid=int(data.get("pid") or 0),
            wifi_ssid=data.get("wifi_ssid"),
            wifi_ready=bool(data.get("wifi_ready", False)),
            gate_detail=str(data.get("gate_detail", "")),
            cooldown_remaining_sec=int(data.get("cooldown_remaining_sec", 0)),
            started_at=str(data.get("started_at") or _now_str()),
            updated_at=str(data.get("updated_at") or _now_str()),
            last_heartbeat=str(data.get("last_heartbeat") or _now_str()),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateStore:
    """L1-R / L1-W"""

    def __init__(self, paths: RuntimePaths) -> None:
        self.paths = paths

    def load_state(self) -> RuntimeState:
        return RuntimeState.from_dict(self._load_json(self.paths.state_json))

    def save_state(self, state: RuntimeState) -> None:
        self._save_json(self.paths.state_json, state.to_dict())

    def load_status(self) -> RuntimeStatus:
        return RuntimeStatus.from_dict(self._load_json(self.paths.status_json))

    def save_status(self, status: RuntimeStatus) -> None:
        self._save_json(self.paths.status_json, status.to_dict())

    def mark_pipeline_finished(
        self,
        *,
        workflow_count: int,
        gdrive_retry: bool,
    ) -> RuntimeState:
        state = self.load_state()
        now = _now_str()
        if gdrive_retry:
            state.gdrive_retry_pending = True
            state.last_gdrive_attempt_at = now
            state.last_pipeline_workflows = workflow_count
        else:
            state.gdrive_retry_pending = False
            state.last_pipeline_at = now
            state.last_pipeline_workflows = workflow_count
        self.save_state(state)
        return state

    def cooldown_remaining_sec(
        self,
        *,
        cooldown_sec: int,
        gdrive_retry_sec: int,
        gdrive_available: bool,
    ) -> int:
        """L1-M + 시간 계산: G: 재시도 우선, workflow 0이면 쿨다운 0."""
        state = self.load_state()
        if state.gdrive_retry_pending:
            if gdrive_available:
                return 0
            last = _parse_epoch(state.last_gdrive_attempt_at)
            if last is None:
                return 0
            return max(0, int(gdrive_retry_sec - (datetime.now().timestamp() - last)))
        if state.last_pipeline_workflows <= 0:
            return 0
        last = _parse_epoch(state.last_pipeline_at)
        if last is None:
            return 0
        return max(0, int(cooldown_sec - (datetime.now().timestamp() - last)))

    @staticmethod
    def _load_json(path: str) -> dict[str, Any]:
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
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
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
