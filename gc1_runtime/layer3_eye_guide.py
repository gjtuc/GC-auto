# -*- coding: utf-8 -*-
"""
gc1_runtime.layer3_eye_guide — Autochro 단계마다 OCR 눈 (T98)

``GC1_AUTOCHRO_EYE=1`` (live 기본) 일 때 각 UI 단계 전후로:
  · 영역 캡처 + 적응 확대 OCR
  · 토큰 위치로 마우스 이동·클릭 (제어목록 .raw 동기화 앵커 등)
  · read_tasks 로 단계 검증 (실패해도 ``GC1_AUTOCHRO_EYE_ADAPT=1`` 이면 fallback 후 계속)

케이스 스터디: 실패 시 ``layer3_ocr_case_study`` (전체화면·탐색) → 런 후 ``layer3_ocr_learn`` overlay
워크플로 불명: ``layer3_workflow_gate`` — 사용자에게만 질문 (OCR/조작은 자체 학습)

pywinauto 좌표만 쓰면 제어목록 고정 위치에 커서가 안 가는 문제가 있어
동기화 더블클릭은 OCR ``.raw`` 행을 우선 찾습니다.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from gc_screen_read import (
    Box,
    OcrToken,
    box_around_screen_point,
    click_screen,
    double_click_screen,
    find_menu_needle_tokens,
    find_text_tokens,
    flash_focus_point,
    load_config,
    read_region_hierarchical,
    read_track_zoom_on_box,
    resolve_region_box,
    token_screen_center,
)
from gc1_runtime.layer3_eye import EyeActuator, default_eye_config, verify_read_task
from gc1_runtime.layer3_ocr_case_study import case_study_on_fail
from gc1_runtime.layer3_coord_learn import (
    get_learned_x_frac,
    list_rel_from_purpose,
    ocr_rel_is_safe,
    record_coord_click,
)
from gc1_runtime.layer3_ocr_maturity import skill_key

_LOG = print
_RAW_TOKEN_RX = re.compile(r"(\d+)\s*[\.,]?\s*raw", re.IGNORECASE)


def autochro_eye_strict() -> bool:
    """OCR 검증 실패 시 단계 중단 (기본 OFF — 적응 학습)."""
    return os.getenv("GC1_AUTOCHRO_EYE_STRICT", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def autochro_eye_adaptive() -> bool:
    """OCR 우선 + pywinauto·좌표 fallback 허용 (기본 ON)."""
    return os.getenv("GC1_AUTOCHRO_EYE_ADAPT", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def eye_gate_should_raise() -> bool:
    """OCR 게이트 실패 시 RuntimeError — strict 이고 adaptive 가 아닐 때만."""
    return autochro_eye_strict() and not autochro_eye_adaptive()


def autochro_eye_coord_only() -> bool:
    """
    OCR은 제어목록 데이터명·분석목록 트리 시료명 매칭만.
    나머지(표 클릭·메뉴·탭)는 고정 좌표 + win32/단축키 (기본 ON).
    """
    raw = os.getenv("GC1_AUTOCHRO_EYE_COORD_ONLY", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def autochro_mouse_only() -> bool:
    """
    Autochro 내부 컨트롤(SysListView/SysTreeView/탭)에 pywinauto click/select 금지.

    창·컨트롤 ``rectangle()`` 으로 좌표만 읽고 ``click_screen`` 으로 조작.
    팝업 메뉴(#32768)·상단 메뉴바·파일 대화상자는 Win32/키보드 유지.
    """
    raw = os.getenv("GC1_AUTOCHRO_MOUSE_ONLY", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def autochro_eye_enabled(*, dry_run: bool = False) -> bool:
    """live Autochro 에서 OCR 눈 사용 여부. dry_run 이면 항상 False."""
    if dry_run:
        return False
    enabled = os.getenv("GC1_AUTOCHRO_EYE", "1").strip().lower() in ("1", "true", "yes")
    if enabled:
        os.environ.setdefault("GC_SCREEN_SHOW_FOCUS", "0")
        os.environ.setdefault("GC_SCREEN_SHOW_CURSOR", "1")
    return enabled


def _normalize_tok(text: str) -> str:
    return re.sub(r"\s+", "", (text or "")).lower()


_TREE_CHILD_LABELS = (
    "시료정보",
    "시료정보",
    "분석결과",
    "분석보고서",
    "시료보고서",
    "원본정보",
    "열기",
    "비교화면",
    "통계분석",
)


def _score_tree_name_token(tok: OcrToken, data_name: str) -> float:
    """트리 데이터명 앵커 — 한 글자·메뉴 잡음·다른 날짜 시료 제외."""
    tok_c = _normalize_tok(tok.text)
    name_c = _normalize_tok(data_name)
    if len(tok_c) < 5:
        return -1.0
    if any(lbl in tok_c for lbl in _TREE_CHILD_LABELS):
        return -1.0
    if re.fullmatch(r"20\d{6}", tok_c):
        return -1.0
    if "분석목록" in tok_c or "제어목록" in tok_c:
        return -1.0
    from gc1_runtime.layer0_data import extract_date8_from_data_name

    target_date = extract_date8_from_data_name(data_name)
    tok_dates = re.findall(r"20\d{6}", tok_c)
    if target_date and tok_dates and target_date not in tok_dates:
        return -1.0
    score = float(tok.confidence)
    if target_date and target_date in tok_c:
        score += 80.0
    prefix = name_c[: min(14, len(name_c))]
    if prefix in tok_c:
        score += 40.0
    elif tok_c in name_c:
        score += 25.0
    if "dre" in name_c and "dre" not in tok_c:
        return -1.0
    if name_c[:10] not in tok_c and tok_c not in name_c:
        if not (target_date and target_date in tok_c and len(tok_c) >= 12):
            return -1.0
    if re.search(r"\d\($", tok_c) or tok_c.endswith("("):
        return -1.0
    if len(tok_c) < max(12, len(name_c) // 2):
        return -1.0
    if "dre" in name_c and "dre" in tok_c and target_date and target_date in tok_c:
        score += 10.0
    return score


def _pick_tree_name_token(tokens: Sequence[OcrToken], data_name: str) -> Optional[OcrToken]:
    scored = [(t, _score_tree_name_token(t, data_name)) for t in tokens]
    scored = [(t, s) for t, s in scored if s >= 0]
    if not scored:
        return None
    best_score = max(s for _, s in scored)
    tier = [t for t, s in scored if s >= best_score - 8.0]
    # 같은 점수대 — 화면 위쪽(부모 시료명 행) 우선, 하위 '시료 정보' 등은 아래
    return min(tier, key=lambda t: (t.box.top, -t.confidence))


def token_looks_like_raw(tok: OcrToken) -> bool:
    """``1.raw`` / ``4.raw`` OCR 변형 허용."""
    t = _normalize_tok(tok.text)
    if not t:
        return False
    if _RAW_TOKEN_RX.search(t):
        return True
    return t.endswith("raw") and any(ch.isdigit() for ch in t)


@dataclass
class EyeStepRecord:
    step_id: str
    phase: str
    ok: bool
    detail: str = ""
    ocr_preview: str = ""


@dataclass
class AutochroStepEye:
    """
    Autochro export 1회 동안 유지하는 OCR 가이드.

    ``window_box`` 는 pywinauto 창 rectangle 과 동기화.
    """

    config: dict
    window_box: Box
    eye: EyeActuator
    log_fn: Callable[[str], None] = _LOG
    records: List[EyeStepRecord] = field(default_factory=list)
    _menu_anchor_screen: Optional[Tuple[int, int]] = field(default=None, repr=False)

    @classmethod
    def from_window_rect(
        cls,
        rect,
        *,
        log_fn: Callable[[str], None] | None = None,
        config: dict | None = None,
    ) -> AutochroStepEye:
        cfg = config or default_eye_config()
        box = Box(int(rect.left), int(rect.top), int(rect.width()), int(rect.height()))
        return cls(
            config=cfg,
            window_box=box,
            eye=EyeActuator(cfg),
            log_fn=log_fn or _LOG,
        )

    def _current_run_id(self) -> str:
        try:
            from gc1_runtime.layer3_ocr_learn import _current_run_path

            path = _current_run_path()
            if path.is_file():
                import json

                data = json.loads(path.read_text(encoding="utf-8"))
                return str(data.get("run_id") or "")
        except Exception:
            pass
        return ""

    def _record_skill_outcome(
        self,
        step_id: str,
        region_id: str,
        action: str,
        *,
        success: bool,
        confidence: float = 0.0,
        method: str = "ocr",
        detail: str = "",
    ) -> None:
        run_id = self._current_run_id()
        if not run_id:
            return
        try:
            from gc1_runtime.layer3_ocr_maturity import append_observation

            append_observation(
                run_id,
                step_id=step_id,
                region_id=region_id,
                action=action,
                success=success,
                confidence=confidence,
                method=method,
                detail=detail,
            )
        except Exception:
            pass

    def _log(self, msg: str) -> None:
        safe = msg.replace("\u2014", "-").replace("\u2192", "->")
        self.log_fn(f"[눈] {safe}")

    def ocr_region(self, region_id: str, *, label: str = "") -> str:
        """영역 OCR plain text (계층 read 마지막 단계)."""
        from gc_screen_read import ensure_ocr_focus_visible

        ensure_ocr_focus_visible()
        tag = label or region_id
        self._log(f"OCR start - {tag} ({region_id})")
        read = read_region_hierarchical(
            self.config,
            region_id,
            window_box=self.window_box,
            save_images=True,
        )
        text = read.final_text or ""
        preview = text.replace("\n", " ")[:120]
        self._log(f"OCR done - {tag}: {preview!r}")
        return text

    def ocr_region_tokens(
        self,
        region_id: str,
        *,
        needles: Optional[Sequence[str]] = None,
    ) -> Tuple[Box, float, List[OcrToken]]:
        """영역 적응 확대 OCR — 토큰·view·effective_scale (클릭 좌표용)."""
        region_box, _ = resolve_region_box(self.config, region_id, self.window_box)
        return self._ocr_tokens_on_box(
            region_box, region_id=region_id, needles=needles, log_tag=region_id
        )

    def _ocr_tokens_on_box(
        self,
        region_box: Box,
        *,
        region_id: str,
        needles: Optional[Sequence[str]] = None,
        log_tag: str = "",
    ) -> Tuple[Box, float, List[OcrToken]]:
        try:
            tracked = read_track_zoom_on_box(
                region_box,
                self.config,
                region_id=region_id,
                save_images=True,
                needles=needles,
            )
            if not tracked.stages:
                return region_box, 1.0, []
            last = tracked.stages[-1]
            view = tracked.final_view_box or region_box
            tag = log_tag or region_id
            self._log(
                f"OCR zoom done {tag} steps={len(tracked.stages)} "
                f"step={last.adaptive_step:.2f} crop={last.crop_frac:.2f}"
            )
            return view, last.effective_scale, last.tokens
        except RuntimeError as exc:
            raise RuntimeError(f"OCR 엔진 필요 (Tesseract): {exc}") from exc

    def verify_task(self, task_id: str, *, step_id: str, phase: str = "after") -> bool:
        """screen_regions read_tasks 검증."""
        if autochro_eye_coord_only():
            return True
        tasks = self.config.get("read_tasks") or {}
        if task_id not in tasks:
            self._log(f"skip unknown task {task_id}")
            return True
        region_id = str(tasks[task_id].get("region") or "top_sample_table")
        try:
            text = self.ocr_region(region_id, label=f"verify:{task_id}")
        except RuntimeError as exc:
            self._log(f"verify skip (no OCR) - {step_id}: {exc}")
            return True
        verdict = verify_read_task(self.config, task_id, text)
        self.records.append(
            EyeStepRecord(step_id, phase, verdict.passed, verdict.detail, text[:80])
        )
        if verdict.passed:
            self._log(f"verify OK - {step_id} / {task_id}")
        else:
            self._log(f"verify FAIL - {step_id} / {task_id}: {verdict.detail}")
            self._on_ocr_miss(
                step_id,
                kind="verify",
                reason=verdict.detail,
                task_id=task_id,
            )
        return verdict.passed

    def _on_ocr_miss(
        self,
        step_id: str,
        *,
        kind: str,
        reason: str,
        task_id: str = "",
    ) -> None:
        """인식 실패 시 막힌 단계에서 OCR 케이스 스터디."""
        if not case_study_on_fail():
            return
        try:
            from gc1_runtime.layer3_ocr_maturity import should_learn_skill, skill_key

            reg = ""
            tasks_cfg = self.config.get("read_tasks") or {}
            if task_id in tasks_cfg:
                reg = str(tasks_cfg[task_id].get("region") or "")
            if reg and not should_learn_skill(skill_key(step_id, reg, task_id or kind)):
                self._log(f"case-study skip (mature) - {step_id}")
                return
        except ImportError:
            pass
        try:
            from gc_screen_read import ensure_ocr_focus_visible
            from gc1_runtime.layer3_ocr_case_study import run_failure_case_study

            ensure_ocr_focus_visible(case_study=True)
            run_failure_case_study(
                self,
                step_id=step_id,
                reason=reason,
                task_id=task_id,
                kind=kind,
                log_fn=self._log,
            )
        except Exception as exc:
            self._log(f"case-study warn: {exc}")

    def require_task(self, step_id: str, task_id: str, *, phase: str = "after") -> None:
        """OCR 검증 — adaptive 이면 경고만, strict+비적응이면 중단."""
        if autochro_eye_coord_only():
            return
        ok = self.verify_task(task_id, step_id=step_id, phase=phase)
        if not ok and eye_gate_should_raise():
            raise RuntimeError(f"OCR gate fail: {step_id} / {task_id}")
        if not ok and autochro_eye_adaptive():
            self._log(f"gate warn (adaptive continue) - {step_id} / {task_id}")

    def verify_tree_data_name(self, data_name: str, *, step_id: str) -> bool:
        """분석목록 왼쪽 트리 OCR — 제어목록 데이터명과 일치."""
        from gc_autochro import tree_label_matches_data_name

        try:
            text = self.ocr_region("left_analysis_tree", label=f"{step_id}_tree")
        except RuntimeError as exc:
            self._log(f"tree OCR skip: {exc}")
            return not eye_gate_should_raise()
        compact = re.sub(r"\s+", "", text.lower())
        name_c = re.sub(r"\s+", "", data_name.lower())
        if name_c and name_c[: min(len(name_c), 16)] in compact:
            self._log(f"tree name OK - {data_name!r}")
            return True
        from gc1_runtime.layer0_data import tree_fuzzy_matches_data_name

        if tree_fuzzy_matches_data_name(text, data_name):
            self._log(f"tree name OK (fuzzy) - {data_name!r}")
            return True
        for line in text.splitlines():
            line = line.strip()
            if line and tree_label_matches_data_name(line, data_name):
                self._log(f"tree name OK (line) - {line!r}")
                return True
        self._log(f"tree name FAIL - want {data_name!r} in {text[:80]!r}")
        self._on_ocr_miss(
            step_id,
            kind="verify",
            reason=f"tree name {data_name!r}",
            task_id="eye_sync_tree_name",
        )
        if eye_gate_should_raise():
            raise RuntimeError(f"OCR tree name mismatch: {data_name!r}")
        return False

    def require_tree_data_name(self, data_name: str, *, step_id: str) -> None:
        self.verify_tree_data_name(data_name, step_id=step_id)

    def scan_between(
        self,
        step_id: str,
        region_id: str,
        *,
        task_id: str | None = None,
    ) -> None:
        """단계 사이 눈 스캔 — coord-only 모드에서는 생략."""
        if autochro_eye_coord_only():
            self._log(f"between-step skip (coord-only): {step_id}")
            return
        self._log(f"between-step: {step_id} ({region_id})")
        try:
            self.ocr_region(region_id, label=step_id)
            if task_id:
                self.verify_task(task_id, step_id=step_id, phase="between")
        except RuntimeError as exc:
            self._log(f"between-step skip (no OCR): {exc}")
        except Exception as exc:
            self._log(f"between-step warn: {exc}")

    def checkpoint(self, step_id: str, task_id: str) -> None:
        """단계 검증 — strict 이면 실패 시 중단."""
        try:
            self.require_task(step_id, task_id, phase="between")
        except Exception as exc:
            if eye_gate_should_raise():
                raise
            self._log(f"checkpoint warn - {step_id}: {exc}")

    def find_raw_anchor_screen_xy(
        self,
        region_id: str = "top_sample_table",
    ) -> Optional[Tuple[int, int]]:
        """
        오른쪽 위 시료 표에서 ``.raw`` OCR (제어목록·분석목록 동일 화면 위치).

        1.raw 라벨이 스크롤로 사라져도 **고정 슬롯 첫 행**에 보이는 .raw 를 찾음.
        """
        try:
            region_box, scale, tokens = self.ocr_region_tokens(
                region_id, needles=["raw", ".raw", "1.raw"]
            )
        except RuntimeError as exc:
            self._log(str(exc))
            return None
        raw_tokens = [t for t in tokens if token_looks_like_raw(t)]
        if not raw_tokens:
            # partial ".raw" / "raw"
            for q in (".raw", "raw"):
                raw_tokens.extend(find_text_tokens(tokens, q, partial=True))
        if not raw_tokens:
            self._log("sync anchor .raw not found - coord fallback")
            self._on_ocr_miss(
                "sync.raw_anchor",
                kind="anchor",
                reason="no .raw token",
                task_id="eye_before_sync_dclick",
            )
            return None
        # OCR 이미지에서 top 이 작을수록 표 상단(첫 가시 행)
        best = min(raw_tokens, key=lambda t: (t.box.top, -t.confidence))
        x, y = token_screen_center(best, region_box, scale)
        self._log(f"sync anchor '{best.text}' -> screen ({x},{y}) conf={best.confidence:.0f}")
        return x, y

    def find_tree_name_screen_xy(
        self,
        data_name: str,
        *,
        region_id: str = "left_analysis_tree",
    ) -> Optional[Tuple[int, int]]:
        """분석목록 트리 — 데이터명 OCR 토큰 중심 (우클릭 위치)."""
        try:
            from gc1_runtime.layer0_data import extract_date8_from_data_name

            date8 = extract_date8_from_data_name(data_name)
            needles = [data_name[:14], date8 or "2026", "dre"]
            view, scale, tokens = self.ocr_region_tokens(
                region_id,
                needles=needles,
            )
        except RuntimeError as exc:
            self._log(f"tree OCR skip: {exc}")
            return None
        best = _pick_tree_name_token(tokens, data_name)
        if best is None:
            name_c = re.sub(r"\s+", "", data_name.lower())
            hits = find_text_tokens(tokens, data_name[:12], partial=True)
            hits = [t for t in hits if len(_normalize_tok(t.text)) >= 5]
            if not hits:
                m = re.match(r"(\d{8})", name_c)
                if m:
                    hits = [
                        t
                        for t in find_text_tokens(tokens, m.group(1), partial=True)
                        if len(_normalize_tok(t.text)) >= 8
                    ]
            if hits:
                best = max(hits, key=lambda t: t.confidence)
        if best is None:
            self._log(f"tree anchor not found for {data_name!r}")
            self._on_ocr_miss(
                "tree.anchor",
                kind="anchor",
                reason=f"no token for {data_name!r}",
            )
            return None
        x, y = token_screen_center(best, view, scale)
        self._log(f"tree anchor '{best.text}' -> screen ({x},{y}) conf={best.confidence:.0f}")
        return x, y

    def right_click_tree_data_name_ocr(self, data_name: str) -> Optional[Tuple[int, int]]:
        """
        트리 시료명 — OCR 화면좌표 찾아 우클릭.

        트리 펼침·스크롤마다 Y 가 바뀌므로 매 P4 마다 OCR 로 위치를 읽음.
        """
        anchor = self.find_tree_name_screen_xy(data_name)
        if anchor is None:
            return None
        x, y = anchor
        flash_focus_point(x, y, color="lime")
        click_screen(x, y, button="right")
        self._menu_anchor_screen = (x, y)
        time.sleep(0.55)
        self._log(f"tree OCR right-click ({x},{y})")
        return anchor

    def guided_tree_right_click_data_name(self, data_name: str) -> bool:
        """OCR 로 트리 데이터명 찾아 우클릭. 성공 여부 반환."""
        self.scan_between("P4.locate_tree", "left_analysis_tree")
        anchor = self.find_tree_name_screen_xy(data_name)
        if anchor is None:
            if eye_gate_should_raise():
                raise RuntimeError(f"OCR tree anchor missing: {data_name!r}")
            self._log(f"tree OCR miss — caller may fallback: {data_name!r}")
            return False
        x, y = anchor
        flash_focus_point(x, y, color="lime")
        click_screen(x, y, button="right")
        self._menu_anchor_screen = (x, y)
        time.sleep(0.55)
        self._log(f"tree OCR right-click ({x},{y})")
        return True

    def guided_sync_execute_double_click(
        self,
        sample_list,
        *,
        fallback_rel: Tuple[int, int],
    ) -> None:
        """coord-only: 고정 좌표 더블클릭. 그 외 OCR .raw 앵커 시도."""
        rel_x, rel_y = self.guided_sync_double_click(sample_list, fallback_rel=fallback_rel)
        rect = sample_list.rectangle()
        screen_x = int(rect.left) + int(rel_x)
        screen_y = int(rect.top) + int(rel_y)
        if autochro_mouse_only() or autochro_eye_coord_only():
            self.move_mouse_on_list(sample_list, rel_x, rel_y)
            double_click_screen(screen_x, screen_y)
            self._log(f"sync screen double-click ({screen_x},{screen_y})")
            return
        anchor = self.find_raw_anchor_screen_xy()
        if anchor is not None:
            self._log(f"sync OCR double-click screen {anchor}")
            double_click_screen(anchor[0], anchor[1])
        else:
            self.move_mouse_on_list(sample_list, rel_x, rel_y)
            if autochro_mouse_only():
                double_click_screen(screen_x, screen_y)
            else:
                sample_list.double_click_input(coords=(rel_x, rel_y))

    def list_rel_coords_from_screen(
        self,
        sample_list,
        screen_xy: Tuple[int, int],
    ) -> Tuple[int, int]:
        rect = sample_list.rectangle()
        rel_x = int(screen_xy[0]) - int(rect.left)
        rel_y = int(screen_xy[1]) - int(rect.top)
        rel_x = max(4, min(rel_x, max(4, rect.width() - 4)))
        rel_y = max(4, min(rel_y, max(4, rect.height() - 4)))
        return rel_x, rel_y

    def resolve_sync_double_click_rel(
        self,
        sample_list,
        *,
        fallback_rel: Tuple[int, int],
    ) -> Tuple[int, int]:
        """OCR 앵커 → ListView 상대 좌표. 실패 시 fallback."""
        anchor = self.find_raw_anchor_screen_xy()
        if anchor is None:
            self._log(f"fallback 더블클릭 rel={fallback_rel}")
            return fallback_rel
        rel = self.list_rel_coords_from_screen(sample_list, anchor)
        self._log(f"OCR 더블클릭 rel={rel}")
        return rel

    def move_mouse_on_list(self, sample_list, rel_x: int, rel_y: int) -> None:
        """사용자가 커서 이동을 볼 수 있게 ListView 위로 이동 (화면 좌표)."""
        rect = sample_list.rectangle()
        screen_x = int(rect.left) + int(rel_x)
        screen_y = int(rect.top) + int(rel_y)
        try:
            from gc1_runtime.layer3_user_mouse_guard import notify_automation_cursor_at

            notify_automation_cursor_at(screen_x, screen_y)
        except Exception:
            pass
        if not autochro_mouse_only():
            try:
                sample_list.set_focus()
                sample_list.move_mouse_input(coords=(rel_x, rel_y))
            except Exception as exc:
                self._log(f"move_mouse_input warn: {exc}")
        try:
            import pywinauto.mouse as mouse

            mouse.move(coords=(screen_x, screen_y))
        except Exception:
            try:
                import ctypes

                ctypes.windll.user32.SetCursorPos(screen_x, screen_y)
            except Exception as exc2:
                self._log(f"SetCursorPos warn: {exc2}")
        flash_focus_point(screen_x, screen_y, color="lime")
        time.sleep(0.35)
        self._log(f"cursor list rel=({rel_x},{rel_y}) screen=({screen_x},{screen_y})")

    def resolve_sample_table_rel(
        self,
        sample_list,
        *,
        region_id: str = "top_sample_table",
        fallback_rel: Tuple[int, int] | None = None,
    ) -> Tuple[int, int]:
        """
        분석목록 시료 표 — OCR 로 첫 가시 행(.raw 등) 또는 안전 열 위치.

        실패 시 ``_neutral_list_rel`` (수집 일시 열 쪽).
        """
        if fallback_rel is None:
            fallback_rel = _neutral_list_rel(sample_list)
        try:
            region_box, scale, tokens = self.ocr_region_tokens(
                region_id, needles=["raw", "시료", "수집", "일시"]
            )
        except Exception as exc:
            self._log(f"sample table OCR skip: {exc}")
            return fallback_rel
        raw_tokens = [t for t in tokens if token_looks_like_raw(t)]
        if raw_tokens:
            best = min(raw_tokens, key=lambda t: (t.box.top, -t.confidence))
            x, y = token_screen_center(best, region_box, scale)
            rel = self.list_rel_coords_from_screen(sample_list, (x, y))
            if ocr_rel_is_safe(sample_list, rel[0], rel[1], best.text):
                self._log(f"sample row OCR '{best.text}' -> rel={rel}")
                return rel
            self._log(f"sample row OCR unsafe (미지시료·열) — row fallback")
        for needle in ("수집", "일시"):
            hits = find_text_tokens(tokens, needle, partial=True)
            if hits:
                best = max(hits, key=lambda t: t.confidence)
                x, y = token_screen_center(best, region_box, scale)
                rel = self.list_rel_coords_from_screen(sample_list, (x, y))
                if ocr_rel_is_safe(sample_list, rel[0], rel[1], best.text):
                    self._log(f"sample header OCR '{best.text}' -> rel={rel}")
                    return rel
        self._log(f"sample table OCR miss - neutral rel={fallback_rel}")
        return fallback_rel

    def guided_sync_double_click(
        self,
        sample_list,
        *,
        fallback_rel: Tuple[int, int],
    ) -> Tuple[int, int]:
        """제어목록 동기화 — coord-only: 고정 좌표만."""
        if autochro_eye_coord_only():
            rel_x, rel_y = fallback_rel
            self.move_mouse_on_list(sample_list, rel_x, rel_y)
            self._log(
                f"sync coord-only x_frac={get_learned_x_frac('sync_raw'):.3f} "
                f"rel=({rel_x},{rel_y})"
            )
            return rel_x, rel_y
        self.scan_between("P1.before_sync", "top_sample_table", task_id=EYE_TASK_BEFORE_SYNC)
        rel_x, rel_y = self.resolve_sync_double_click_rel(
            sample_list, fallback_rel=fallback_rel
        )
        self.move_mouse_on_list(sample_list, rel_x, rel_y)
        self.scan_between("P1.mouse_on_sync", "top_sample_table")
        return rel_x, rel_y

    def guided_focus_for_ctrl_a(self, sample_list) -> Tuple[int, int]:
        """Ctrl+A 전 — 행 번호 열(시료종류·미지시료 드롭다운 회피)."""
        if autochro_eye_coord_only():
            rel_x, rel_y = list_rel_from_purpose(sample_list, "row")
            self.move_mouse_on_list(sample_list, rel_x, rel_y)
            self._log(
                f"Ctrl+A focus row x_frac={get_learned_x_frac('row'):.3f} rel=({rel_x},{rel_y})"
            )
            return rel_x, rel_y
        if eye_gate_should_raise():
            self.require_task("P2.before_ctrl_a", EYE_TASK_BEFORE_TABLE)
        else:
            self.verify_task("P2.before_ctrl_a", step_id="P2.before_ctrl_a", phase="before")
        rel_x, rel_y = self.resolve_sample_table_rel(sample_list)
        self.move_mouse_on_list(sample_list, rel_x, rel_y)
        self.scan_between("P2.mouse_before_ctrl_a", "top_sample_table")
        return rel_x, rel_y

    def guided_after_ctrl_a(self) -> None:
        """Ctrl+A 직후 — coord-only 에서도 좌표 성숙도 기록."""
        if autochro_eye_coord_only():
            record_coord_click(
                "row",
                get_learned_x_frac("row"),
                success=True,
                step_id="P2.after_ctrl_a",
            )
            return
        if eye_gate_should_raise():
            self.require_task("P2.after_ctrl_a", EYE_TASK_AFTER_CTRL_A)
        else:
            self.verify_task("P2.after_ctrl_a", step_id="P2.after_ctrl_a", phase="after")

    def try_click_context_menu_ocr(
        self,
        needle: str,
        *,
        forbid: Sequence[str] = (),
        region_id: str = "context_menu_popup",
        step_id: str = "P3.menu",
    ) -> bool:
        """우클릭 메뉴 OCR 클릭 — 실패 시 False (adaptive fallback 용)."""
        try:
            self.click_context_menu_ocr(
                needle, forbid=forbid, region_id=region_id, step_id=step_id
            )
            return True
        except Exception as exc:
            self._log(f"menu OCR miss — fallback allowed: {exc}")
            self._record_skill_outcome(
                step_id,
                region_id,
                needle,
                success=False,
                method="ocr_click",
                detail=str(exc)[:120],
            )
            self._on_ocr_miss(
                step_id,
                kind="menu",
                reason=str(exc),
                task_id=EYE_TASK_AFTER_MENU_INIT,
            )
            return False

    def _try_click_popup_menu_win32(
        self, needle: str, *, forbid: Sequence[str], step_id: str = "P3.menu"
    ) -> bool:
        """#32768 팝업 메뉴 — OCR 전/후 보조."""
        from gc1_runtime.layer3_hand import menu_popup_pick

        def matcher(text: str) -> bool:
            if needle not in text:
                return False
            return not any(f in text for f in forbid)

        try:
            result = menu_popup_pick(matcher, timeout=8.0)
            self._log(f"menu win32 click {result.matched_text!r}")
            self._record_skill_outcome(
                step_id,
                "context_menu_popup",
                needle,
                success=True,
                method="win32_menu",
            )
            return True
        except Exception as exc:
            self._log(f"menu win32 miss: {exc}")
            self._record_skill_outcome(
                step_id,
                "context_menu_popup",
                needle,
                success=False,
                method="win32_menu",
                detail=str(exc)[:120],
            )
            return False

    def click_context_menu_ocr(
        self,
        needle: str,
        *,
        forbid: Sequence[str] = (),
        region_id: str = "context_menu_popup",
        step_id: str = "P3.menu",
    ) -> None:
        """우클릭 후 뜬 메뉴를 OCR 로 읽고 항목 클릭 (클릭점 근처 박스 우선)."""
        boxes: List[Tuple[str, Box]] = []
        if self._menu_anchor_screen is not None:
            ax, ay = self._menu_anchor_screen
            menu_box = box_around_screen_point(ax, ay, clip=self.window_box)
            boxes.append(("menu@click", menu_box))
        region_box, _ = resolve_region_box(self.config, region_id, self.window_box)
        boxes.append((region_id, region_box))

        hits: List[OcrToken] = []
        region_box_used = region_box
        scale = 1.0
        for tag, box in boxes:
            region_box_used, scale, tokens = self._ocr_tokens_on_box(
                box,
                region_id=region_id,
                needles=[needle, "초기화", "불러", "초기", "불러오기"],
                log_tag=tag,
            )
            hits = find_menu_needle_tokens(tokens, needle, forbid=forbid)
            if hits:
                break

        if not hits:
            plain = ""
            try:
                plain = self.ocr_region(region_id, label="menu_miss")
            except RuntimeError:
                pass
            raise RuntimeError(
                f"OCR menu missing {needle!r} - preview={plain[:80]!r}"
            )
        best = max(hits, key=lambda t: t.confidence)
        x, y = token_screen_center(best, region_box_used, scale)
        self._log(f"menu OCR click {needle!r} -> ({x},{y}) token={best.text!r}")
        click_screen(x, y, button="left")
        self._record_skill_outcome(
            step_id,
            region_id,
            needle,
            success=True,
            confidence=float(best.confidence),
            method="ocr_click",
        )

    def guided_right_click_then_menu(
        self,
        sample_list,
        menu_needle: str,
        *,
        forbid: Sequence[str] = ("정량", "검량"),
        neutral_rel: Tuple[int, int] | None = None,
    ) -> bool:
        """우클릭 → 메뉴. coord-only: 시료이름 열 좌표 + win32/단축키 (OCR 메뉴 생략)."""
        if neutral_rel is None:
            neutral_rel = list_rel_from_purpose(sample_list, "name")
        if autochro_eye_coord_only():
            rel_x, rel_y = neutral_rel
            self.move_mouse_on_list(sample_list, rel_x, rel_y)
            rect = sample_list.rectangle()
            screen_x = int(rect.left) + int(rel_x)
            screen_y = int(rect.top) + int(rel_y)
            self._log(
                f"우클릭 name x_frac={get_learned_x_frac('name'):.3f} "
                f"screen=({screen_x},{screen_y})"
            )
            click_screen(screen_x, screen_y, button="right")
            self._menu_anchor_screen = (screen_x, screen_y)
            time.sleep(0.55)
            clicked = self._try_click_popup_menu_win32(
                menu_needle, forbid=forbid, step_id="P3.menu"
            )
            if not clicked and menu_needle.startswith("초기"):
                try:
                    from pywinauto.keyboard import send_keys

                    send_keys("n")
                    clicked = True
                    self._log("menu shortcut N (coord-only)")
                except Exception:
                    pass
            if clicked:
                record_coord_click(
                    "name",
                    get_learned_x_frac("name"),
                    success=True,
                    step_id="P3.after_menu_click",
                )
            else:
                record_coord_click(
                    "name",
                    get_learned_x_frac("name"),
                    success=False,
                    step_id="P3.after_menu_click",
                )
            return clicked
        rel_x, rel_y = self.resolve_sample_table_rel(
            sample_list, fallback_rel=neutral_rel
        )
        self.scan_between("P3.before_right_click", "top_sample_table", task_id=EYE_TASK_BEFORE_TABLE)
        self.move_mouse_on_list(sample_list, rel_x, rel_y)
        self._log(f"우클릭 rel=({rel_x},{rel_y})")
        rect = sample_list.rectangle()
        screen_x = int(rect.left) + int(rel_x)
        screen_y = int(rect.top) + int(rel_y)
        if autochro_mouse_only():
            click_screen(screen_x, screen_y, button="right")
        else:
            sample_list.click_input(button="right", coords=(rel_x, rel_y))
        self._menu_anchor_screen = (screen_x, screen_y)
        time.sleep(0.55)
        self.scan_between("P3.menu_open", "context_menu_popup")
        sk = skill_key("P3.menu", "context_menu_popup", menu_needle)
        try:
            from gc1_runtime.layer3_ocr_maturity import get_preferred_method

            pref = get_preferred_method(sk, "ocr_click")
        except ImportError:
            pref = "ocr_click"

        clicked = False
        if pref == "win32_menu":
            clicked = self._try_click_popup_menu_win32(
                menu_needle, forbid=forbid, step_id="P3.menu"
            )
        if not clicked:
            clicked = self.try_click_context_menu_ocr(
                menu_needle, forbid=forbid, step_id="P3.menu"
            )
        if not clicked:
            clicked = self._try_click_popup_menu_win32(
                menu_needle, forbid=forbid, step_id="P3.menu"
            )
        if eye_gate_should_raise():
            self.require_task("P3.after_menu_click", EYE_TASK_AFTER_MENU_INIT)
        elif clicked:
            self.verify_task("P3.after_menu_click", step_id="P3.after_menu", phase="after")
        return clicked


def _list_frac_rel(sample_list, x_frac: float) -> Tuple[int, int]:
    rect = sample_list.rectangle()
    width = max(rect.width(), 400)
    height = max(rect.height(), 80)
    rel_x = max(8, int(width * x_frac))
    rel_y = max(16, min(32, height // 10))
    return rel_x, rel_y


def _list_row_index_rel(sample_list) -> Tuple[int, int]:
    """행 번호 열 — Ctrl+A 전 포커스 (시료종류·미지시료 드롭다운 회피)."""
    return list_rel_from_purpose(sample_list, "row")


def _list_rightclick_rel(sample_list) -> Tuple[int, int]:
    """시료이름 열 — 우클릭 (미지시료·시료종류 열 회피)."""
    return list_rel_from_purpose(sample_list, "name")


def _neutral_list_rel(sample_list) -> Tuple[int, int]:
    """gc_autochro._list_row_index_coords 와 동일."""
    return _list_row_index_rel(sample_list)


# read_tasks 키 — screen_regions.gc1.json 과 동기화
EYE_TASK_BEFORE_CONTROL = "eye_before_control_sync"
EYE_TASK_BEFORE_SYNC = "eye_before_sync_dclick"
EYE_TASK_AFTER_SYNC = "eye_after_sync_analysis_rows"
EYE_TASK_BEFORE_TABLE = "eye_before_sample_table"
EYE_TASK_AFTER_CTRL_A = "eye_after_ctrl_a"
EYE_TASK_AFTER_INIT = "eye_after_context_init"
EYE_TASK_AFTER_MTD = "eye_after_mtd_peak"
EYE_TASK_AFTER_MENU_INIT = "eye_after_menu_초기화"
