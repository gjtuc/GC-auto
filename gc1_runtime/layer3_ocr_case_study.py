# -*- coding: utf-8 -*-
"""
OCR 인식 실패 시 막힌 단계에서 케이스 스터디 — 전체화면·탐색·학습 누적.

실패 구간:
  1) Autochro **전체화면** OCR (빨간 네모)
  2) 단계별 영역 + **확대/축소 스윕** (빨간 네모) + 라임 네모 커서 탐색
  3) JSON 저장 → 런 종료 시 overlay 반영

``ensure_ocr_focus_visible(case_study=True)`` — 사용자가 OCR 영역을 볼 수 있게 기본 ON.

워크플로 불명 시: ``layer3_workflow_gate`` — 사용자에게만 질문.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from gc_screen_read import (
    capture_box,
    ensure_ocr_focus_visible,
    flash_focus_box,
    flash_focus_point,
    focus_stage,
    ocr_image,
    read_region_hierarchical,
    read_track_zoom_on_box,
    resolve_region_box,
    token_screen_center,
    upscale_image,
    zoom_pipeline_settings,
)
from gc1_runtime.layer3_eye import verify_read_task
from gc1_runtime.layer3_ocr_learn import register_failure_report
from gc_screen_read import tokens_matching_needles

# step_id / task_id → 진단할 영역·needles
_STEP_PROFILES: Dict[str, Dict[str, Any]] = {
    "P1.tab_control": {
        "regions": ["bottom_tabs", "bottom_tab_labels", "control_sample_table", "top_sample_table"],
        "needles": {
            "bottom_tabs": ["제어", "목록", "분석목록", "제어목록"],
            "bottom_tab_labels": ["분석", "목록", "제어"],
            "control_sample_table": ["raw", "시료"],
            "top_sample_table": ["raw", "시료"],
        },
        "tasks": ["eye_active_tab_control", "eye_before_control_sync"],
    },
    "P1.after_sync": {
        "regions": ["top_sample_table", "left_analysis_tree"],
        "needles": {
            "top_sample_table": ["raw", "시료"],
            "left_analysis_tree": ["dre", "2026", "ni"],
        },
        "tasks": ["eye_after_sync_analysis_rows", "eye_sync_tree_name"],
    },
    "P2.before_ctrl_a": {
        "regions": ["top_sample_table"],
        "needles": {"top_sample_table": ["시료", "수집", "raw"]},
        "tasks": ["eye_before_sample_table"],
    },
    "P3.after_init": {
        "regions": ["bottom_peak_table_fine", "top_sample_table"],
        "needles": {"bottom_peak_table_fine": ["0.0", "합계", "H2"]},
        "tasks": ["eye_after_context_init"],
    },
    "P3.menu": {
        "regions": ["context_menu_popup", "top_sample_table"],
        "needles": {"context_menu_popup": ["초기화", "불러", "정량"]},
        "tasks": ["eye_after_menu_초기화"],
    },
    "P4.before_mtd": {
        "regions": ["left_analysis_tree", "bottom_tab_labels"],
        "needles": {
            "left_analysis_tree": ["dre", "2026", "ni"],
            "bottom_tab_labels": ["분석", "목록"],
        },
        "tasks": ["eye_active_tab_analysis"],
    },
    "P4.after_mtd": {
        "regions": ["bottom_peak_table_fine"],
        "needles": {"bottom_peak_table_fine": ["H2", "CH4", "RT", "면적"]},
        "tasks": ["eye_after_mtd_peak"],
    },
    "sync.raw_anchor": {
        "regions": ["top_sample_table", "control_sample_table"],
        "needles": {"top_sample_table": ["raw", ".raw"], "control_sample_table": ["raw"]},
        "tasks": ["eye_before_sync_dclick"],
    },
    "tree.anchor": {
        "regions": ["left_analysis_tree"],
        "needles": {"left_analysis_tree": ["dre", "2026", "ni"]},
        "tasks": [],
    },
}

_TASK_TO_STEP: Dict[str, str] = {}
for _sid, _prof in _STEP_PROFILES.items():
    for _tid in _prof.get("tasks") or []:
        _TASK_TO_STEP[_tid] = _sid

_EXPLORE_STEPS = (1.25, 1.5, 1.75, 2.0, 2.25)


def case_study_on_fail() -> bool:
    """실패 시 케이스 스터디 실행 여부."""
    if os.getenv("GC1_OCR_CASE_STUDY", "1").strip().lower() in ("0", "false", "no", "off"):
        return False
    try:
        from gc1_runtime.layer3_user_mouse_guard import learning_collection_allowed

        if not learning_collection_allowed():
            return False
    except ImportError:
        pass
    return True


def explore_on_fail() -> bool:
    """실패 시 확대/축소·마우스 탐색 (기본 ON)."""
    return os.getenv("GC1_OCR_EXPLORE", "1").strip().lower() not in ("0", "false", "no", "off")


def _out_dir() -> Path:
    d = Path(os.environ.get("USERPROFILE", ".")) / ".cursor" / "gc-ocr-case-study"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _stage_row(st) -> Dict[str, Any]:
    return {
        "stage": st.stage,
        "step": round(st.adaptive_step, 3),
        "crop": round(st.crop_frac, 3),
        "early": st.stopped_early,
        "tokens": len(st.tokens),
        "top": [
            {"text": t.text, "conf": round(t.confidence, 1)}
            for t in sorted(st.tokens, key=lambda x: -x.confidence)[:10]
        ],
    }


def _probe_move_cursor(x: int, y: int, *, log_fn) -> None:
    """탐색용 커서 이동 — 작은 라임 네모 (영역 빨간 네모와 구분)."""
    try:
        import ctypes

        ctypes.windll.user32.SetCursorPos(int(x), int(y))
    except Exception:
        pass
    flash_focus_point(x, y, color="lime", duration_ms=450)
    log_fn(f"[탐색] cursor -> ({x},{y})")
    time.sleep(0.15)


def _zoom_sweep_region(
    eye,
    region_id: str,
    needles: Sequence[str],
    *,
    log_fn,
) -> Dict[str, Any]:
    """고정 배율 스윕 + 빨간 네모 OCR + needle 위치 마우스 탐색."""
    row: Dict[str, Any] = {"region": region_id, "zoom_sweep": [], "probe_points": []}
    try:
        rb, _ = resolve_region_box(eye.config, region_id, eye.window_box)
        opts = zoom_pipeline_settings(eye.config, region_id)
        min_conf = float(opts.get("min_confidence", 35))
        img = capture_box(rb)
        for step in _EXPLORE_STEPS:
            step_val = step

            def _ocr_at_step(s: float = step_val) -> tuple:
                scaled = upscale_image(img, s)
                return ocr_image(scaled)

            plain, tokens = focus_stage(rb, _ocr_at_step)
            hits = tokens_matching_needles(tokens, needles, min_confidence=min_conf)
            row["zoom_sweep"].append(
                {
                    "step": step_val,
                    "token_count": len(tokens),
                    "needle_hits": len(hits),
                    "preview": plain[:120],
                    "top": [
                        {"text": t.text, "conf": round(t.confidence, 1)}
                        for t in sorted(tokens, key=lambda x: -x.confidence)[:6]
                    ],
                }
            )
            if explore_on_fail() and hits:
                for tok in sorted(hits, key=lambda t: -t.confidence)[:3]:
                    x, y = token_screen_center(tok, rb, step_val)
                    row["probe_points"].append({"text": tok.text, "screen": [x, y], "step": step_val})
                    _probe_move_cursor(x, y, log_fn=log_fn)
    except Exception as exc:
        row["error"] = str(exc)
    finally:
        from gc_screen_read import focus_hide

        focus_hide()
    return row


def _probe_full_window(eye, *, log_fn) -> Dict[str, Any]:
    """실패 시 Autochro 전체화면 OCR."""
    log_fn("[케이스] 전체화면 OCR 시작")
    row: Dict[str, Any] = {"region": "autochro_window"}
    try:
        tracked = read_track_zoom_on_box(
            eye.window_box,
            eye.config,
            region_id="autochro_window",
            save_images=True,
            needles=["분석", "제어", "raw", "시료", "초기화"],
        )
        row["stages"] = [_stage_row(s) for s in tracked.stages]
        if tracked.stages:
            last = tracked.stages[-1]
            row["plain_preview"] = (last.plain_text or "")[:400]
            row["token_count"] = len(last.tokens)
            row["top_tokens"] = [
                {"text": t.text, "conf": round(t.confidence, 1)}
                for t in sorted(last.tokens, key=lambda x: -x.confidence)[:15]
            ]
        read = read_region_hierarchical(
            eye.config, "autochro_window", window_box=eye.window_box, save_images=False
        )
        row["final_preview"] = (read.final_text or "")[:400]
        row["ok"] = bool((read.final_text or "").strip())
    except Exception as exc:
        row["error"] = str(exc)
        row["ok"] = False
    return row


def _probe_region(eye, region_id: str, needles: Sequence[str]) -> Dict[str, Any]:
    row: Dict[str, Any] = {"region": region_id}
    try:
        rb, chain = resolve_region_box(eye.config, region_id, eye.window_box)
        row["box"] = [rb.left, rb.top, rb.width, rb.height]
        row["chain"] = chain
        flash_focus_box(rb, color="red")
        tracked = read_track_zoom_on_box(
            rb,
            eye.config,
            region_id=region_id,
            save_images=True,
            needles=list(needles),
        )
        row["stages"] = [_stage_row(s) for s in tracked.stages]
        if tracked.stages:
            last = tracked.stages[-1]
            row["plain_preview"] = (last.plain_text or "")[:280]
            row["token_count"] = len(last.tokens)
        read = read_region_hierarchical(
            eye.config, region_id, window_box=eye.window_box, save_images=False
        )
        row["final_preview"] = (read.final_text or "")[:280]
        row["ok"] = bool((read.final_text or "").strip())
    except Exception as exc:
        row["error"] = str(exc)
        row["ok"] = False
    return row


def _hints_for_report(step_id: str, regions: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> List[str]:
    hints: List[str] = []
    for t in tasks:
        if not t.get("passed", True):
            hints.append(f"task {t.get('task')}: {t.get('detail')} — region={t.get('region')}")
    for r in regions:
        rid = r.get("region", "")
        if not r.get("ok"):
            hints.append(f"region {rid}: OCR empty or error — box={r.get('box')}")
            continue
        preview = (r.get("final_preview") or "").replace("\n", " ")
        if "tab" in rid and not re.search(r"(분석|제어).{0,4}목록|목록", preview):
            hints.append(f"region {rid}: tab labels weak — zoom_sweep·bottom_tab_labels 확인")
        if rid == "left_analysis_tree" and not re.search(r"\d{8}|dre", preview, re.I):
            hints.append(f"region {rid}: tree data name not visible — scroll tree")
        if rid in ("top_sample_table", "control_sample_table"):
            if not re.search(r"raw", preview, re.I):
                hints.append(f"region {rid}: no raw token — scroll or sync row")
    if not hints:
        hints.append("PNG: .cursor/gc-screen-capture/ — 런 후 overlay 자동 갱신")
    return hints


def resolve_profile(step_id: str, task_id: str = "") -> Dict[str, Any]:
    if step_id in _STEP_PROFILES:
        return dict(_STEP_PROFILES[step_id])
    if task_id and task_id in _TASK_TO_STEP:
        return dict(_STEP_PROFILES[_TASK_TO_STEP[task_id]])
    return {"regions": [], "needles": {}, "tasks": [task_id] if task_id else []}


def run_failure_case_study(
    eye,
    *,
    step_id: str,
    reason: str,
    task_id: str = "",
    kind: str = "verify",
    log_fn=None,
) -> Dict[str, Any]:
    _log = log_fn or print
    ensure_ocr_focus_visible(case_study=True)
    profile = resolve_profile(step_id, task_id)
    regions_ids: List[str] = list(profile.get("regions") or [])
    needles_map: Dict[str, List[str]] = dict(profile.get("needles") or {})
    task_ids: List[str] = list(profile.get("tasks") or [])
    if task_id and task_id not in task_ids:
        task_ids.insert(0, task_id)

    if not regions_ids and task_id:
        tasks_cfg = eye.config.get("read_tasks") or {}
        if task_id in tasks_cfg:
            regions_ids = [str(tasks_cfg[task_id].get("region") or "top_sample_table")]

    report: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "step_id": step_id,
        "task_id": task_id,
        "kind": kind,
        "reason": reason,
        "full_window": {},
        "exploration": [],
        "regions": [],
        "tasks": [],
        "hints": [],
    }

    report["full_window"] = _probe_full_window(eye, log_fn=_log)

    for rid in regions_ids:
        ndls = needles_map.get(rid, [])
        report["regions"].append(_probe_region(eye, rid, ndls))
        if explore_on_fail():
            report["exploration"].append(_zoom_sweep_region(eye, rid, ndls, log_fn=_log))

    for tid in task_ids:
        if not tid:
            continue
        tasks_cfg = eye.config.get("read_tasks") or {}
        entry: Dict[str, Any] = {"task": tid}
        if tid not in tasks_cfg:
            entry["skip"] = "unknown"
        else:
            entry["region"] = tasks_cfg[tid].get("region")
            try:
                text = eye.ocr_region(str(entry["region"]), label=f"fail:{tid}")
                verdict = verify_read_task(eye.config, tid, text)
                entry["passed"] = verdict.passed
                entry["detail"] = verdict.detail
                entry["preview"] = text[:160]
            except Exception as exc:
                entry["passed"] = False
                entry["error"] = str(exc)
        report["tasks"].append(entry)

    report["hints"] = _hints_for_report(step_id, report["regions"], report["tasks"])
    slug = re.sub(r"[^\w\-]+", "_", step_id)[:40]
    out_path = _out_dir() / f"fail_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["path"] = str(out_path)
    register_failure_report(str(out_path), step_id=step_id)
    _log(f"[케이스] {step_id} ({kind}) — {reason}")
    for hint in report["hints"][:5]:
        _log(f"[케이스] hint: {hint}")
    _log(f"[케이스] saved {out_path}")
    return report
