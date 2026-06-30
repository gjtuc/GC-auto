# -*- coding: utf-8 -*-
"""
gc1_runtime.layer3_eye_guide — Autochro 단계마다 OCR 눈 (T98)

``GC1_AUTOCHRO_EYE=1`` (live 기본) 일 때 각 UI 단계 전후로:
  · 영역 캡처 + 계층 OCR
  · 토큰 위치로 마우스 이동·클릭 (제어목록 .raw 동기화 앵커 등)
  · read_tasks 로 단계 검증

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
    click_screen,
    find_text_tokens,
    flash_focus_point,
    load_config,
    read_region_hierarchical,
    read_track_zoom_on_box,
    resolve_region_box,
    token_screen_center,
)
from gc1_runtime.layer3_eye import EyeActuator, default_eye_config, verify_read_task

_LOG = print
_RAW_TOKEN_RX = re.compile(r"(\d+)\s*[\.,]?\s*raw", re.IGNORECASE)


def autochro_eye_enabled(*, dry_run: bool = False) -> bool:
    """live Autochro 에서 OCR 눈 사용 여부. dry_run 이면 항상 False."""
    if dry_run:
        return False
    enabled = os.getenv("GC1_AUTOCHRO_EYE", "1").strip().lower() in ("1", "true", "yes")
    if enabled and os.getenv("GC_SCREEN_SHOW_FOCUS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    ):
        os.environ.setdefault("GC_SCREEN_SHOW_FOCUS", "1")
    return enabled


def _normalize_tok(text: str) -> str:
    return re.sub(r"\s+", "", (text or "")).lower()


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

    def _log(self, msg: str) -> None:
        safe = msg.replace("\u2014", "-").replace("\u2192", "->")
        self.log_fn(f"[눈] {safe}")

    def ocr_region(self, region_id: str, *, label: str = "") -> str:
        """영역 OCR plain text (계층 read 마지막 단계)."""
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

    def ocr_region_tokens(self, region_id: str) -> Tuple[Box, float, List[OcrToken]]:
        """영역 추적 1.5× OCR — 토큰·view·effective_scale (클릭 좌표용)."""
        try:
            region_box, _ = resolve_region_box(self.config, region_id, self.window_box)
            tracked = read_track_zoom_on_box(
                region_box,
                self.config,
                region_id=region_id,
                save_images=True,
            )
            if not tracked.stages:
                return region_box, 1.0, []
            last = tracked.stages[-1]
            view = tracked.final_view_box or region_box
            return view, last.effective_scale, last.tokens
        except RuntimeError as exc:
            raise RuntimeError(f"OCR 엔진 필요 (Tesseract): {exc}") from exc

    def verify_task(self, task_id: str, *, step_id: str, phase: str = "after") -> bool:
        """screen_regions read_tasks 검증."""
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
        return verdict.passed

    def scan_between(
        self,
        step_id: str,
        region_id: str,
        *,
        task_id: str | None = None,
    ) -> None:
        """단계 사이 눈 스캔 — OCR 읽기 + (선택) read_tasks 검증."""
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
        """단계 사이 검증 — 실패해도 경고만 (다음 단계 시도)."""
        try:
            self.verify_task(task_id, step_id=step_id, phase="between")
        except Exception as exc:
            self._log(f"checkpoint warn - {step_id}: {exc}")

    def find_raw_anchor_screen_xy(
        self,
        region_id: str = "control_sample_table",
    ) -> Optional[Tuple[int, int]]:
        """
        제어목록 표에서 ``.raw`` 행 OCR — **가장 위**에 보이는 토큰 중심 (동기화 앵커).

        1.raw 라벨이 스크롤로 사라져도 **고정 슬롯 첫 행**에 보이는 .raw 를 찾음.
        """
        try:
            region_box, scale, tokens = self.ocr_region_tokens(region_id)
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
            return None
        # OCR 이미지에서 top 이 작을수록 표 상단(첫 가시 행)
        best = min(raw_tokens, key=lambda t: (t.box.top, -t.confidence))
        x, y = token_screen_center(best, region_box, scale)
        self._log(f"sync anchor '{best.text}' -> screen ({x},{y}) conf={best.confidence:.0f}")
        return x, y

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
        """사용자가 커서 이동을 볼 수 있게 ListView 위로 이동 (화면 좌표 fallback)."""
        rect = sample_list.rectangle()
        screen_x = int(rect.left) + int(rel_x)
        screen_y = int(rect.top) + int(rel_y)
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
            region_box, scale, tokens = self.ocr_region_tokens(region_id)
        except Exception as exc:
            self._log(f"sample table OCR skip: {exc}")
            return fallback_rel
        raw_tokens = [t for t in tokens if token_looks_like_raw(t)]
        if raw_tokens:
            best = min(raw_tokens, key=lambda t: (t.box.top, -t.confidence))
            x, y = token_screen_center(best, region_box, scale)
            rel = self.list_rel_coords_from_screen(sample_list, (x, y))
            self._log(f"sample row OCR '{best.text}' -> rel={rel}")
            return rel
        for needle in ("수집", "시료", "일시"):
            hits = find_text_tokens(tokens, needle, partial=True)
            if hits:
                best = max(hits, key=lambda t: t.confidence)
                x, y = token_screen_center(best, region_box, scale)
                rel = self.list_rel_coords_from_screen(sample_list, (x, y))
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
        """제어목록 동기화 — 단계 사이 OCR + 마우스 이동 + 더블클릭 좌표 반환."""
        self.scan_between("P1.before_sync", "control_sample_table", task_id=EYE_TASK_BEFORE_SYNC)
        rel_x, rel_y = self.resolve_sync_double_click_rel(
            sample_list, fallback_rel=fallback_rel
        )
        self.move_mouse_on_list(sample_list, rel_x, rel_y)
        self.scan_between("P1.mouse_on_sync", "control_sample_table")
        return rel_x, rel_y

    def guided_focus_for_ctrl_a(self, sample_list) -> Tuple[int, int]:
        """Ctrl+A 전 — OCR 로 클릭 위치 잡고 마우스 이동."""
        self.checkpoint("P2.before_ctrl_a", EYE_TASK_BEFORE_TABLE)
        rel_x, rel_y = self.resolve_sample_table_rel(sample_list)
        self.move_mouse_on_list(sample_list, rel_x, rel_y)
        self.scan_between("P2.mouse_before_ctrl_a", "top_sample_table")
        return rel_x, rel_y

    def guided_after_ctrl_a(self) -> None:
        """Ctrl+A 직후 검증."""
        self.checkpoint("P2.after_ctrl_a", EYE_TASK_AFTER_CTRL_A)

    def click_context_menu_ocr(
        self,
        needle: str,
        *,
        forbid: Sequence[str] = (),
        region_id: str = "context_menu_popup",
    ) -> None:
        """우클릭 후 뜬 메뉴를 OCR 로 읽고 항목 클릭."""
        region_box, scale, tokens = self.ocr_region_tokens(region_id)
        hits: List[OcrToken] = []
        for tok in tokens:
            text = tok.text or ""
            if needle not in text:
                continue
            if any(f in text for f in forbid):
                continue
            hits.append(tok)
        if not hits:
            hits = find_text_tokens(tokens, needle, partial=True)
            hits = [t for t in hits if not any(f in t.text for f in forbid)]
        if not hits:
            plain = self.ocr_region(region_id, label="menu_miss")
            raise RuntimeError(
                f"OCR menu missing {needle!r} - preview={plain[:80]!r}"
            )
        best = max(hits, key=lambda t: t.confidence)
        x, y = token_screen_center(best, region_box, scale)
        self._log(f"menu OCR click {needle!r} -> ({x},{y})")
        click_screen(x, y, button="left")

    def guided_right_click_then_menu(
        self,
        sample_list,
        menu_needle: str,
        *,
        forbid: Sequence[str] = ("정량", "검량"),
        neutral_rel: Tuple[int, int] | None = None,
    ) -> None:
        """마우스 위치 OCR 조정 -> 우클릭 -> OCR 로 메뉴 클릭."""
        if neutral_rel is None:
            neutral_rel = _neutral_list_rel(sample_list)
        rel_x, rel_y = self.resolve_sample_table_rel(
            sample_list, fallback_rel=neutral_rel
        )
        self.scan_between("P3.before_right_click", "top_sample_table", task_id=EYE_TASK_BEFORE_TABLE)
        self.move_mouse_on_list(sample_list, rel_x, rel_y)
        self._log(f"우클릭 rel=({rel_x},{rel_y})")
        sample_list.click_input(button="right", coords=(rel_x, rel_y))
        time.sleep(0.45)
        self.scan_between("P3.menu_open", "context_menu_popup")
        self.click_context_menu_ocr(menu_needle, forbid=forbid)
        self.checkpoint("P3.after_menu_click", EYE_TASK_AFTER_MENU_INIT)


def _neutral_list_rel(sample_list) -> Tuple[int, int]:
    """gc_autochro._neutral_list_coords 와 동일 (순환 import 방지)."""
    raw_frac = os.getenv("AUTOCHRO_LIST_NEUTRAL_X_FRAC", "0.78").strip()
    try:
        x_frac = float(raw_frac)
    except ValueError:
        x_frac = 0.78
    x_frac = min(max(x_frac, 0.55), 0.92)
    rect = sample_list.rectangle()
    width = max(rect.width(), 400)
    height = max(rect.height(), 80)
    rel_x = int(width * x_frac)
    rel_y = max(16, min(32, height // 10))
    return rel_x, rel_y


# read_tasks 키 — screen_regions.gc1.json 과 동기화
EYE_TASK_BEFORE_CONTROL = "eye_before_control_sync"
EYE_TASK_BEFORE_SYNC = "eye_before_sync_dclick"
EYE_TASK_AFTER_SYNC = "eye_after_sync_analysis_rows"
EYE_TASK_BEFORE_TABLE = "eye_before_sample_table"
EYE_TASK_AFTER_CTRL_A = "eye_after_ctrl_a"
EYE_TASK_AFTER_INIT = "eye_after_context_init"
EYE_TASK_AFTER_MENU_INIT = "eye_after_menu_초기화"
