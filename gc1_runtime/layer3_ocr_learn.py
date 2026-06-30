# -*- coding: utf-8 -*-
"""
런별 OCR 학습 누적 — 케이스 스터디 JSON → 다음 런 region/zoom 반영.

``~/.cursor/gc-ocr-learnings/screen_regions.overlay.json`` 에 PC별 미세 조정 저장.
``load_config`` 가 repo JSON 위에 overlay 를 deep-merge 합니다.
"""
from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_LEARN_DIR_NAME = "gc-ocr-learnings"
_OVERLAY_NAME = "screen_regions.overlay.json"
_CURRENT_RUN = "current_run.json"
_CASE_DIR_NAME = "gc-ocr-case-study"


def learnings_dir() -> Path:
    d = Path(os.environ.get("USERPROFILE", ".")) / ".cursor" / _LEARN_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def overlay_path() -> Path:
    return learnings_dir() / _OVERLAY_NAME


def case_study_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", ".")) / ".cursor" / _CASE_DIR_NAME


def learnings_enabled() -> bool:
    return os.getenv("GC1_OCR_LEARN", "1").strip().lower() not in ("0", "false", "no", "off")


def _deep_merge(base: dict, patch: dict) -> dict:
    out = deepcopy(base)
    for key, val in patch.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = deepcopy(val)
    return out


def load_overlay() -> dict:
    path = overlay_path()
    if not path.is_file():
        return {"regions": {}, "runs": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"regions": {}, "runs": []}


def merge_config_with_learnings(config: dict) -> dict:
    """repo screen_regions + PC overlay (zoom_hints·box)."""
    if not learnings_enabled():
        return config
    overlay = load_overlay()
    region_patch = overlay.get("regions") or {}
    if not region_patch:
        return config
    merged = deepcopy(config)
    regions = merged.setdefault("regions", {})
    for rid, patch in region_patch.items():
        if rid not in regions:
            continue
        entry = deepcopy(regions[rid])
        if "box" in patch:
            entry["box"] = list(patch["box"])
        if "zoom_hints" in patch:
            zh = dict(entry.get("zoom_hints") or {})
            zh.update(patch["zoom_hints"])
            entry["zoom_hints"] = zh
        regions[rid] = entry
    return merged


def begin_ocr_run_session() -> str:
    """Autochro export 런 시작 — 케이스 스터디 세션 마커."""
    path = _current_run_path()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("pipeline"):
                return str(data.get("run_id") or "")
        except Exception:
            pass
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "run_id": run_id,
        "started": datetime.now(timezone.utc).isoformat(),
        "fail_reports": [],
    }
    if learnings_enabled():
        (learnings_dir() / _CURRENT_RUN).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return run_id


def _current_run_path() -> Path:
    return learnings_dir() / _CURRENT_RUN


def register_failure_report(report_path: str, step_id: str = "") -> None:
    """케이스 스터디 JSON 경로를 현재 런에 연결."""
    if not learnings_enabled():
        return
    path = _current_run_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        reports: List[str] = list(data.get("fail_reports") or [])
        if report_path not in reports:
            reports.append(report_path)
        data["fail_reports"] = reports
        if step_id:
            steps: List[str] = list(data.get("fail_steps") or [])
            steps.append(step_id)
            data["fail_steps"] = steps
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _collect_fail_json_since(started_iso: str) -> List[Path]:
    cdir = case_study_dir()
    if not cdir.is_dir():
        return []
    try:
        started = datetime.fromisoformat(started_iso.replace("Z", "+00:00"))
    except Exception:
        started = datetime.min.replace(tzinfo=timezone.utc)
    out: List[Path] = []
    for p in sorted(cdir.glob("fail_*.json"), key=lambda x: x.stat().st_mtime):
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        if mtime >= started.replace(tzinfo=timezone.utc):
            out.append(p)
    return out


def _best_explore_step(exploration: List[dict]) -> Optional[float]:
    best: Optional[float] = None
    best_hits = -1
    for ex in exploration:
        for sweep in ex.get("zoom_sweep") or []:
            hits = int(sweep.get("needle_hits") or 0)
            step = float(sweep.get("step") or 0)
            if hits > best_hits and step > 0:
                best_hits = hits
                best = step
    return best


def _apply_report_to_overlay(overlay: dict, report: dict) -> List[str]:
    """한 fail 리포트에서 보수적으로 zoom_hints 만 갱신."""
    notes: List[str] = []
    regions_overlay = overlay.setdefault("regions", {})
    exploration = list(report.get("exploration") or [])

    for ex in exploration:
        rid = ex.get("region")
        if not rid:
            continue
        best_step = _best_explore_step([ex])
        if best_step and best_step >= 1.5:
            entry = dict(regions_overlay.get(rid) or {})
            zh = dict(entry.get("zoom_hints") or {})
            old_min = float(zh.get("step_min") or 1.25)
            new_min = round(max(old_min, best_step - 0.15), 2)
            if new_min > old_min:
                zh["step_min"] = new_min
                entry["zoom_hints"] = zh
                entry["fail_count"] = int(entry.get("fail_count") or 0) + 1
                regions_overlay[rid] = entry
                notes.append(f"{rid}: step_min {old_min} -> {new_min}")

    for reg in report.get("regions") or []:
        rid = reg.get("region")
        if not rid or reg.get("ok"):
            continue
        entry = dict(regions_overlay.get(rid) or {})
        entry["fail_count"] = int(entry.get("fail_count") or 0) + 1
        if int(entry["fail_count"]) >= 3 and reg.get("box"):
            # 3회 이상 빈 OCR — box 는 유지, step_min 만 올림
            zh = dict(entry.get("zoom_hints") or {})
            zh["step_min"] = round(max(float(zh.get("step_min") or 1.5), 2.0), 2)
            entry["zoom_hints"] = zh
            notes.append(f"{rid}: repeated empty OCR — step_min -> {zh['step_min']}")
        regions_overlay[rid] = entry

    return notes


def _pipeline_run_active() -> bool:
    return os.getenv("GC1_PIPELINE_RUN_ACTIVE", "").strip() in ("1", "true", "yes")


def finalize_ocr_run_session(*, success: bool, message: str = "", log_fn=None) -> Dict[str, Any]:
    """
    런 종료 — 이번 세션 fail JSON 을 읽어 overlay 반영.

    ``GC1_PIPELINE_RUN_ACTIVE`` 이면 overlay·저널은 파이프라인 ``close_gc1_run_session`` 에서 처리.
    """
    _log = log_fn if log_fn is not None else (lambda _msg: None)

    summary: Dict[str, Any] = {
        "success": success,
        "message": message,
        "applied": [],
        "fail_count": 0,
        "deferred": _pipeline_run_active(),
    }
    if _pipeline_run_active():
        path = _current_run_path()
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["autochro_ok"] = success
                data["autochro_message"] = message[:500]
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
        return summary

    if not learnings_enabled():
        return summary

    path = _current_run_path()
    if not path.is_file():
        return summary

    try:
        run_data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return summary

    started = str(run_data.get("started") or "")
    fail_paths = _collect_fail_json_since(started)
    if not fail_paths:
        reports = run_data.get("fail_reports") or []
        fail_paths = [Path(p) for p in reports if Path(p).is_file()]

    summary["fail_count"] = len(fail_paths)
    overlay = load_overlay()
    all_notes: List[str] = []

    for fp in fail_paths:
        try:
            report = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        all_notes.extend(_apply_report_to_overlay(overlay, report))

    runs: List[dict] = list(overlay.get("runs") or [])
    runs.append(
        {
            "run_id": run_data.get("run_id"),
            "finished": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "fail_count": len(fail_paths),
            "applied_notes": all_notes[:20],
        }
    )
    overlay["runs"] = runs[-30:]  # 최근 30런
    overlay_path().write_text(json.dumps(overlay, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["applied"] = all_notes

    if all_notes:
        _log(f"[학습] overlay 갱신 — {len(all_notes)}건")
        for n in all_notes[:8]:
            _log(f"[학습]   {n}")
    elif fail_paths:
        _log(f"[학습] fail {len(fail_paths)}건 — 자동 patch 없음 (PNG·JSON 확인)")
    else:
        _log("[학습] 이번 런 OCR fail 없음")

    try:
        path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception:
        pass

    return summary
