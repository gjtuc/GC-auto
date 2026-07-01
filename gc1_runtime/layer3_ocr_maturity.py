# -*- coding: utf-8 -*-
"""
OCR 스킬 성숙도 — 97% 이상이면 해당 스킬 학습 중단, 실패 시 재학습.

``maturity.json`` + ``policy.json`` (다음 런에서 유리한 방법 선택 확률).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from gc1_runtime.layer3_ocr_learn import learnings_dir

MATURITY_RATE = float(os.getenv("GC1_OCR_MATURITY_RATE", "0.97"))
MIN_ATTEMPTS = int(os.getenv("GC1_OCR_MATURITY_MIN_ATTEMPTS", "20"))
_MATURITY_NAME = "maturity.json"
_POLICY_NAME = "policy.json"
_OBS_NAME = "observations.jsonl"


def skill_key(step_id: str, region_id: str = "", action: str = "") -> str:
    return f"{step_id}|{region_id}|{action}"


def _maturity_path() -> Path:
    return learnings_dir() / _MATURITY_NAME


def _policy_path() -> Path:
    return learnings_dir() / _POLICY_NAME


def run_observations_path(run_id: str) -> Path:
    d = learnings_dir() / "runs" / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d / _OBS_NAME


def load_maturity() -> dict:
    path = _maturity_path()
    if not path.is_file():
        return {"threshold": MATURITY_RATE, "min_attempts": MIN_ATTEMPTS, "skills": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"threshold": MATURITY_RATE, "min_attempts": MIN_ATTEMPTS, "skills": {}}


def save_maturity(data: dict) -> None:
    data["threshold"] = MATURITY_RATE
    data["min_attempts"] = MIN_ATTEMPTS
    _maturity_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_policy() -> dict:
    path = _policy_path()
    if not path.is_file():
        return {"skills": {}, "updated": ""}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"skills": {}, "updated": ""}


def save_policy(data: dict) -> None:
    data["updated"] = datetime.now(timezone.utc).isoformat()
    _policy_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_skill_stats(key: str) -> dict:
    data = load_maturity()
    skills = data.setdefault("skills", {})
    return dict(
        skills.get(key)
        or {
            "attempts": 0,
            "successes": 0,
            "rate": 0.0,
            "mature": False,
            "mature_since": None,
            "last_failure": None,
        }
    )


def is_skill_mature(key: str) -> bool:
    stats = get_skill_stats(key)
    return bool(stats.get("mature"))


def should_learn_skill(key: str) -> bool:
    """성숙 스킬은 overlay·케이스 스터디 학습 생략."""
    return not is_skill_mature(key)


def record_outcome(
    key: str,
    *,
    success: bool,
    confidence: float = 0.0,
    method: str = "ocr",
) -> dict:
    """한 OCR/메뉴 시도 결과 — 성숙도·정책 갱신."""
    data = load_maturity()
    skills: Dict[str, Any] = data.setdefault("skills", {})
    st = dict(
        skills.get(key)
        or {
            "attempts": 0,
            "successes": 0,
            "rate": 0.0,
            "mature": False,
            "mature_since": None,
            "last_failure": None,
            "methods": {},
        }
    )
    st["attempts"] = int(st.get("attempts") or 0) + 1
    if success:
        st["successes"] = int(st.get("successes") or 0) + 1
    else:
        st["last_failure"] = datetime.now(timezone.utc).isoformat()
        st["mature"] = False
        st["mature_since"] = None

    att = st["attempts"]
    st["rate"] = round(st["successes"] / att, 6) if att else 0.0

    methods = dict(st.get("methods") or {})
    m = dict(methods.get(method) or {"attempts": 0, "successes": 0})
    m["attempts"] = int(m.get("attempts") or 0) + 1
    if success:
        m["successes"] = int(m.get("successes") or 0) + 1
    methods[method] = m
    st["methods"] = methods

    if att >= MIN_ATTEMPTS and st["rate"] >= MATURITY_RATE:
        if not st.get("mature"):
            st["mature_since"] = datetime.now(timezone.utc).isoformat()
        st["mature"] = True

    skills[key] = st
    save_maturity(data)
    _update_policy_method(key, methods)
    return st


def _update_policy_method(key: str, methods: dict) -> None:
    policy = load_policy()
    pskills = policy.setdefault("skills", {})
    best_method = "ocr"
    best_rate = -1.0
    for name, m in methods.items():
        att = int(m.get("attempts") or 0)
        if att < 3:
            continue
        rate = int(m.get("successes") or 0) / att
        if rate > best_rate:
            best_rate = rate
            best_method = name
    pskills[key] = {
        "preferred_method": best_method,
        "best_rate": round(best_rate, 4) if best_rate >= 0 else 0,
        "methods": methods,
    }
    save_policy(policy)


def get_preferred_method(key: str, default: str = "ocr") -> str:
    policy = load_policy()
    entry = (policy.get("skills") or {}).get(key) or {}
    return str(entry.get("preferred_method") or default)


def append_observation(
    run_id: str,
    *,
    step_id: str,
    region_id: str,
    action: str,
    success: bool,
    confidence: float = 0.0,
    method: str = "ocr",
    detail: str = "",
) -> None:
    from gc1_runtime.layer3_user_mouse_guard import learning_collection_allowed

    if not learning_collection_allowed():
        return
    path = run_observations_path(run_id)
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "skill_key": skill_key(step_id, region_id, action),
        "step_id": step_id,
        "region_id": region_id,
        "action": action,
        "success": success,
        "confidence": confidence,
        "method": method,
        "detail": detail[:200],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    record_outcome(
        row["skill_key"],
        success=success,
        confidence=confidence,
        method=method,
    )


def load_run_observations(run_id: str) -> List[dict]:
    path = run_observations_path(run_id)
    if not path.is_file():
        return []
    rows: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def demote_skills_from_failures(reports: List[dict]) -> List[str]:
    """실패 리포트 — 해당 스킬 성숙 해제."""
    notes: List[str] = []
    data = load_maturity()
    skills = data.setdefault("skills", {})
    for rep in reports:
        sid = str(rep.get("step_id") or "")
        task = str(rep.get("task_id") or rep.get("kind") or "")
        for reg in rep.get("regions") or []:
            rid = str(reg.get("region") or "")
            key = skill_key(sid, rid, task)
            if key in skills and skills[key].get("mature"):
                skills[key]["mature"] = False
                skills[key]["mature_since"] = None
                notes.append(f"demote {key}")
    if notes:
        save_maturity(data)
    return notes
