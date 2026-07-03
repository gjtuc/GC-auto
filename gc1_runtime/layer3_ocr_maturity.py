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

MATURITY_RATE = float(os.getenv("GC1_OCR_MATURITY_RATE", "0.99"))
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


def _run_snapshot_dir(run_id: str) -> Path:
    d = learnings_dir() / "runs" / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def snapshot_learning_state(run_id: str) -> None:
    """
    런 시작 시 maturity·policy 백업.

    인간 마우스로 오염된 런은 종료 시(또는 감지 즉시) 이 스냅샷으로 복원.
    """
    import shutil

    from gc1_runtime.layer3_ocr_learn import learnings_enabled

    if not learnings_enabled() or not run_id:
        return
    snap = _run_snapshot_dir(run_id)
    mp = _maturity_path()
    pp = _policy_path()
    if mp.is_file():
        shutil.copy2(mp, snap / "maturity_snapshot.json")
    else:
        (snap / "maturity_snapshot.json").write_text(
            json.dumps(
                {"threshold": MATURITY_RATE, "min_attempts": MIN_ATTEMPTS, "skills": {}},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    if pp.is_file():
        shutil.copy2(pp, snap / "policy_snapshot.json")
    else:
        (snap / "policy_snapshot.json").write_text(
            json.dumps({"skills": {}, "updated": ""}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _restore_learning_snapshots(run_id: str) -> tuple[bool, bool]:
    import shutil

    snap = _run_snapshot_dir(run_id)
    mat_restored = False
    pol_restored = False
    mat_snap = snap / "maturity_snapshot.json"
    pol_snap = snap / "policy_snapshot.json"
    if mat_snap.is_file():
        shutil.copy2(mat_snap, _maturity_path())
        mat_restored = True
    if pol_snap.is_file():
        shutil.copy2(pol_snap, _policy_path())
        pol_restored = True
    return mat_restored, pol_restored


def _current_pipeline_run_id() -> str:
    from gc1_runtime.layer3_ocr_learn import _current_run_path

    path = _current_run_path()
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("run_id") or "")
    except Exception:
        return ""


def invalidate_run_learning_on_contamination(*, reason: str = "") -> dict:
    """
    인간 마우스 감지 직후 — 이번 런 관측·성숙도 갱신을 즉시 무효화.

    케이스 스터디 JSON 은 런 종료 시 한꺼번에 삭제.
    """
    run_id = _current_pipeline_run_id()
    result: Dict[str, Any] = {
        "run_id": run_id,
        "reason": reason,
        "observations_deleted": 0,
        "maturity_restored": False,
        "policy_restored": False,
    }
    if not run_id:
        return result

    obs_path = run_observations_path(run_id)
    if obs_path.is_file():
        result["observations_deleted"] = len(
            [ln for ln in obs_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        )
        obs_path.unlink(missing_ok=True)  # type: ignore[arg-type]

    mat_ok, pol_ok = _restore_learning_snapshots(run_id)
    result["maturity_restored"] = mat_ok
    result["policy_restored"] = pol_ok

    from gc1_runtime.layer3_ocr_learn import _current_run_path

    cur = _current_run_path()
    if cur.is_file():
        try:
            data = json.loads(cur.read_text(encoding="utf-8"))
            data["learning_contaminated"] = True
            data["learning_contaminate_reason"] = reason
            data["learning_contaminated_at"] = datetime.now(timezone.utc).isoformat()
            cur.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    return result


def discard_contaminated_run_learning(
    run_id: str,
    *,
    run_data: Optional[dict] = None,
    reports: Optional[List[dict]] = None,
    reason: str = "",
) -> Dict[str, Any]:
    """
    오염 런 종료 처리 — 관측·성숙도·케이스 스터디 전부 폐기.
    """
    from gc1_runtime.layer3_ocr_learn import _collect_fail_json_since, case_study_dir

    result: Dict[str, Any] = {
        "discarded": True,
        "run_id": run_id,
        "reason": reason,
        "observations_deleted": 0,
        "case_study_deleted": 0,
        "maturity_restored": False,
        "policy_restored": False,
    }
    if not run_id:
        return result

    obs_path = run_observations_path(run_id)
    if obs_path.is_file():
        result["observations_deleted"] = len(
            [ln for ln in obs_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        )
        obs_path.unlink(missing_ok=True)  # type: ignore[arg-type]

    mat_ok, pol_ok = _restore_learning_snapshots(run_id)
    result["maturity_restored"] = mat_ok
    result["policy_restored"] = pol_ok

    paths_to_delete: set[Path] = set()
    if run_data:
        for p in run_data.get("fail_reports") or []:
            if p:
                paths_to_delete.add(Path(str(p)))
        started = str(run_data.get("started") or "")
        if started:
            paths_to_delete.update(_collect_fail_json_since(started))
    if reports:
        for rep in reports:
            p = rep.get("path")
            if p:
                paths_to_delete.add(Path(str(p)))

    cdir = case_study_dir()
    for fp in paths_to_delete:
        try:
            if fp.is_file() and (not cdir.is_dir() or fp.parent.resolve() == cdir.resolve()):
                fp.unlink()
                result["case_study_deleted"] += 1
        except Exception:
            continue

    return result


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
