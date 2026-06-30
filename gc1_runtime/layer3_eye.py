# -*- coding: utf-8 -*-
"""
L3 Eye 채널 (Ω.A.L3.E.*) — ``gc_screen_read`` L0-SCR 래핑.

설계 §L3 E.01~E.05 · L0-TASK verify. Tesseract 없이 **geometry·token filter·task 판별**
단위 테스트 가능 (T41). 실제 캡처/OCR 은 ``gc_screen_read`` 위임·주입.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from gc_screen_read import (
    Box,
    OcrToken,
    box_from_fraction,
    find_text_tokens,
    load_config,
    resolve_region_box,
    stage_scale,
    token_screen_box,
    token_screen_center,
    upscale_image,
)

# gc_screen_read 내부 숫자 파서 — TASK verify 공유
from gc_screen_read import _numeric_values as numeric_values  # noqa: PLC2701

__all__ = [
    "Box",
    "EyeActuator",
    "EyeTaskVerdict",
    "OcrToken",
    "box_from_fraction",
    "filter_tokens_by_confidence",
    "find_text_tokens",
    "load_config",
    "parse_tesseract_token_dict",
    "resolve_region_box",
    "stage_scale",
    "token_screen_box",
    "token_screen_center",
    "upscale_image",
    "verify_active_tab_analysis",
    "verify_peak_table_cleared",
    "verify_peak_table_has_data",
    "verify_read_task",
    "default_eye_config",
    "evaluate_peak_table_task",
    "peak_table_plain_text",
    "read_region_plain_text",
]


@dataclass(frozen=True)
class EyeTaskVerdict:
    """L0-TASK / run_read_task 결과."""

    task_id: str
    passed: bool
    detail: str = ""


def filter_tokens_by_confidence(
    tokens: Iterable[OcrToken],
    *,
    min_confidence: float = 25.0,
) -> tuple[OcrToken, ...]:
    """Ω.A.L0.SCR.O.04d — conf < min 제외 (ocr_image 와 동일 임계)."""
    out: list[OcrToken] = []
    for tok in tokens:
        if tok.confidence < 0:
            out.append(tok)
            continue
        if tok.confidence >= min_confidence:
            out.append(tok)
    return tuple(out)


def parse_tesseract_token_dict(
    data: dict,
    *,
    min_confidence: float = 25.0,
) -> list[OcrToken]:
    """
  ocr_image 의 token 빌드 루프만 분리 — pytesseract 없이 단위 테스트.

  ``data`` = pytesseract ``image_to_data`` DICT 출력 형태.
    """
    tokens: list[OcrToken] = []
    texts = data.get("text", [])
    for i, raw in enumerate(texts):
        text = (raw or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError, KeyError):
            conf = -1.0
        if 0 <= conf < min_confidence:
            continue
        tokens.append(
            OcrToken(
                text=text,
                confidence=conf,
                box=Box(
                    int(data["left"][i]),
                    int(data["top"][i]),
                    max(1, int(data["width"][i])),
                    max(1, int(data["height"][i])),
                ),
            )
        )
    return tokens


def verify_contains(text: str, needles: Sequence[str]) -> bool:
    """read_tasks expect_contains."""
    return all(needle in text for needle in needles)


def verify_loose_tab(text: str, kind: str) -> bool:
    """탭 OCR — '분석'+'목록' 분리 인식 허용."""
    compact = re.sub(r"\s+", "", text or "")
    if kind == "analysis":
        return "분석목록" in compact or ("분석" in compact and "목록" in compact)
    if kind == "control":
        return "제어목록" in compact or ("제어" in compact and "목록" in compact)
    return False


_RAW_IN_TEXT_RX = re.compile(r"\d\s*[\.,]?\s*raw", re.IGNORECASE)


def verify_raw_in_text(text: str) -> bool:
    """시료 표 — ``2raw`` / ``1.raw`` 등 OCR 변형."""
    if _RAW_IN_TEXT_RX.search(text or ""):
        return True
    return "raw" in (text or "").lower()


def verify_numeric_min(text: str, minimum: int = 1) -> bool:
    """read_tasks expect_numeric_min — reject_if_mostly_zero 보조."""
    nums = [n for n in numeric_values(text) if abs(n) > 1e-6]
    return len(nums) >= minimum


def verify_mostly_zero(text: str, *, max_nonzero: int = 2, eps: float = 1e-3) -> bool:
    """read_tasks expect_mostly_zero — 피크 표 cleared."""
    nz = [n for n in numeric_values(text) if abs(n) > eps]
    return len(nz) <= max_nonzero


def verify_active_tab_analysis(plain_text: str) -> bool:
    """Ω.A.L0.TASK — 분석목록 탭 문자열."""
    return verify_contains(plain_text, ("분석목록",))


def verify_peak_table_has_data(plain_text: str) -> bool:
    """Ω.A.L0.TASK — 유효 숫자 >= 1."""
    return verify_numeric_min(plain_text, minimum=1)


def verify_peak_table_cleared(plain_text: str) -> bool:
    """Ω.A.L0.TASK — 0 비율 높음 (P3.06 post, zero ratio >= 0.85 근사)."""
    return verify_mostly_zero(plain_text, max_nonzero=2)


PeakTableTextProvider = Callable[[str], str]


def default_eye_config() -> dict:
    """``deploy/screen_regions.gc1.json`` — EyeActuator 기본 config."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return load_config(os.path.join(root, "deploy", "screen_regions.gc1.json"))


def read_region_plain_text(
    config: dict,
    region_id: str,
    *,
    window_box: Box | None = None,
) -> str:
    """
    피크 표·탭 등 region OCR plain text — ``gc_screen_read.read_region_hierarchical`` thin wrapper.

    live + ``GC1_RUNTIME_VERIFY_EYE=1`` 에서 P3/P4/P7 사후 TASK 가 사용.
    """
    from gc_screen_read import read_region_hierarchical  # noqa: PLC2701

    read = read_region_hierarchical(
        config,
        region_id,
        window_box=window_box,
        save_images=False,
    )
    return read.final_text or ""


def peak_table_plain_text(
    *,
    verify_eye: bool,
    dry_run: bool,
    task_id: str,
    fallback_text: str,
    eye: EyeActuator | None = None,
    text_provider: PeakTableTextProvider | None = None,
) -> str:
    """
    CL.TASK text 출처 — verify_eye 꺼짐이면 mock fallback, 켜짐이면 provider·OCR.

    ``text_provider`` — unittest/live mock (task_id → plain text).
    """
    if not verify_eye:
        return fallback_text
    if text_provider is not None:
        return text_provider(task_id)
    if eye is not None and not dry_run:
        tasks = eye.config.get("read_tasks") or {}
        task = tasks.get(task_id) or {}
        region_id = str(task.get("region") or "bottom_peak_table_fine")
        return read_region_plain_text(eye.config, region_id)
    return fallback_text


def evaluate_peak_table_task(
    *,
    verify_eye: bool,
    dry_run: bool,
    task_id: str,
    fallback_text: str,
    eye: EyeActuator | None = None,
    text_provider: PeakTableTextProvider | None = None,
) -> EyeTaskVerdict:
    """
    P3.06 / P4.08 / P6.06 / P7.05 — layer3_eye TASK + ``verify_eye`` 게이트 (T62).

    task_id: ``verify_peak_table_cleared`` | ``verify_peak_table_has_data``
    """
    text = peak_table_plain_text(
        verify_eye=verify_eye,
        dry_run=dry_run,
        task_id=task_id,
        fallback_text=fallback_text,
        eye=eye,
        text_provider=text_provider,
    )
    if task_id == "verify_peak_table_cleared":
        passed = verify_peak_table_cleared(text)
    elif task_id == "verify_peak_table_has_data":
        passed = verify_peak_table_has_data(text)
    else:
        passed = verify_read_task(eye.config if eye else {}, task_id, text).passed
    detail = "ok" if passed else f"TASK {task_id} failed"
    return EyeTaskVerdict(task_id, passed, detail)


def verify_read_task(config: dict, task_id: str, plain_text: str) -> EyeTaskVerdict:
    """
    ``gc_screen_read.run_read_task`` 판별 로직 — OCR 없이 text 만.

    hierarchical read 결과 ``final_text`` 에 적용.
    """
    tasks = config.get("read_tasks") or {}
    if task_id not in tasks:
        return EyeTaskVerdict(task_id, False, f"unknown task: {task_id}")
    task = tasks[task_id]
    if task.get("expect_loose_tab"):
        if not verify_loose_tab(plain_text, str(task["expect_loose_tab"])):
            return EyeTaskVerdict(task_id, False, "expect_loose_tab failed")
    elif task.get("expect_contains_raw"):
        if not verify_raw_in_text(plain_text):
            return EyeTaskVerdict(task_id, False, "expect_raw failed")
    elif task.get("expect_contains"):
        if not verify_contains(plain_text, task["expect_contains"]):
            return EyeTaskVerdict(task_id, False, "expect_contains failed")
    if task.get("reject_if_mostly_zero"):
        min_n = int(task.get("expect_numeric_min", 1))
        if not verify_numeric_min(plain_text, minimum=min_n):
            return EyeTaskVerdict(task_id, False, "numeric min failed")
    if task.get("expect_mostly_zero"):
        if not verify_mostly_zero(plain_text):
            return EyeTaskVerdict(task_id, False, "expect_mostly_zero failed")
    return EyeTaskVerdict(task_id, True, "ok")


@dataclass
class EyeActuator:
    """E 채널 facade — config + geometry + token + verify."""

    config: dict

    def resolve_region(self, region_id: str, window_box: Box) -> tuple[Box, list[str]]:
        """E.01 geo — region box + parent chain."""
        return resolve_region_box(self.config, region_id, window_box)

    def region_scale(self, region_id: str) -> tuple[str, float]:
        return stage_scale(self.config, region_id)

    def find_token(
        self,
        tokens: Iterable[OcrToken],
        query: str,
        *,
        partial: bool = True,
    ) -> list[OcrToken]:
        """E.02 find_token."""
        return find_text_tokens(tokens, query, partial=partial)

    def token_center(
        self,
        token: OcrToken,
        region_box: Box,
        scale: float,
    ) -> tuple[int, int]:
        """E.03 token center xy."""
        return token_screen_center(token, region_box, scale)

    def screen_box(
        self,
        token: OcrToken,
        region_box: Box,
        scale: float,
    ) -> Box:
        return token_screen_box(token, region_box, scale)

    def verify_task(self, task_id: str, plain_text: str) -> EyeTaskVerdict:
        return verify_read_task(self.config, task_id, plain_text)
