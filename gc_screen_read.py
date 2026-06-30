# -*- coding: utf-8 -*-
"""
gc_screen_read.py — GC1 Autochro 화면 읽기(눈) · 계층 OCR · 클릭

gc_autochro 와 분리 — 검증·캘리브레이션 전용 (병합은 나중).

계층 읽기 (기본):
  영역 캡처 → 1.5× 확대 → OCR → 토큰 중심 crop → 1.5× 반복 (max_depth)

설치: pip install -r requirements-screen.txt + Tesseract(kor)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, TypeVar

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "deploy", "screen_regions.gc1.json")
DEFAULT_OUTPUT = os.path.join(os.path.expanduser("~"), ".cursor", "gc-screen-capture")


@dataclass(frozen=True)
class Box:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


@dataclass
class OcrToken:
    text: str
    confidence: float
    box: Box


@dataclass
class ReadStageResult:
    stage: str
    scale: float
    region_id: str
    image_path: str
    tokens: List[OcrToken] = field(default_factory=list)
    plain_text: str = ""
    effective_scale: float = 1.0
    view_box: Optional[Box] = None


@dataclass
class HierarchicalReadResult:
    window_box: Optional[Box]
    stages: List[ReadStageResult] = field(default_factory=list)
    final_view_box: Optional[Box] = None

    @property
    def final_text(self) -> str:
        return self.stages[-1].plain_text if self.stages else ""

    @property
    def final_effective_scale(self) -> float:
        if not self.stages:
            return 1.0
        return self.stages[-1].effective_scale


def _log(msg: str) -> None:
    print(msg, flush=True)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _require_pillow():
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow 필요 — pip install -r requirements-screen.txt") from exc
    return Image


def capture_box(box: Box):
    Image = _require_pillow()
    try:
        import mss

        with mss.mss() as sct:
            shot = sct.grab(
                {
                    "left": box.left,
                    "top": box.top,
                    "width": box.width,
                    "height": box.height,
                }
            )
            return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    except ImportError:
        from PIL import ImageGrab

        return ImageGrab.grab(bbox=(box.left, box.top, box.right, box.bottom))


def upscale_image(image, scale: float):
    if scale <= 1.0:
        return image
    from PIL import Image

    w, h = image.size
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return image.resize((nw, nh), Image.Resampling.LANCZOS)


def _prepare_for_ocr(image):
    from PIL import ImageEnhance, ImageOps

    gray = ImageOps.grayscale(image)
    return ImageEnhance.Contrast(gray).enhance(1.35)


def _tesseract_cmd() -> Optional[str]:
    explicit = os.getenv("TESSERACT_CMD", "").strip()
    if explicit and os.path.isfile(explicit):
        return explicit
    for candidate in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if os.path.isfile(candidate):
            return candidate
    return None


def ocr_image(image, *, lang: Optional[str] = None) -> Tuple[str, List[OcrToken]]:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "pytesseract 필요 — pip install -r requirements-screen.txt"
        ) from exc

    cmd = _tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    elif not os.getenv("TESSERACT_CMD"):
        raise RuntimeError(
            "Tesseract 엔진 없음 — 설치 후 TESSERACT_CMD 환경변수 설정"
        )

    lang = lang or os.getenv("GC_SCREEN_OCR_LANG", "kor+eng")
    prepared = _prepare_for_ocr(image)
    config = os.getenv("GC_SCREEN_TESSERACT_CONFIG", "--psm 6")
    plain = pytesseract.image_to_string(prepared, lang=lang, config=config)
    data = pytesseract.image_to_data(
        prepared, lang=lang, config=config, output_type=pytesseract.Output.DICT
    )
    tokens: List[OcrToken] = []
    for i, raw in enumerate(data.get("text", [])):
        text = (raw or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1.0
        if 0 <= conf < 25:
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
    return plain.strip(), tokens


def find_autochro_window_box(title_contains: str) -> Optional[Box]:
    try:
        from pywinauto import Application, findwindows
    except ImportError:
        return None
    pattern = f".*{re.escape(title_contains)}.*"
    handles = findwindows.find_windows(title_re=pattern)
    if not handles:
        return None
    try:
        app = Application(backend="win32").connect(handle=handles[0])
        rect = app.window(handle=handles[0]).rectangle()
        return Box(int(rect.left), int(rect.top), int(rect.width()), int(rect.height()))
    except Exception:
        return None


def box_from_fraction(parent: Box, frac: Sequence[float]) -> Box:
    x, y, w, h = frac
    return Box(
        parent.left + int(round(parent.width * x)),
        parent.top + int(round(parent.height * y)),
        max(1, int(round(parent.width * w))),
        max(1, int(round(parent.height * h))),
    )


def resolve_region_box(config: dict, region_id: str, window_box: Box) -> Tuple[Box, List[str]]:
    regions = config["regions"]
    if region_id not in regions:
        raise KeyError(f"region 없음: {region_id}")
    stack: List[Tuple[str, dict]] = []
    rid: Optional[str] = region_id
    while rid:
        stack.append((rid, regions[rid]))
        rid = regions[rid].get("parent")
    stack.reverse()
    chain: List[str] = []
    current = window_box
    for name, spec in stack:
        chain.append(name)
        current = box_from_fraction(current, spec.get("box", [0, 0, 1, 1]))
    return current, chain


def stage_scale(config: dict, region_id: str) -> Tuple[str, float]:
    spec = config["regions"][region_id]
    stage = spec.get("stage", "panel")
    pipeline = config.get("zoom_pipeline", {})
    step = float(pipeline.get("step", pipeline.get("panel", 1.5)))
    return stage, step


def zoom_pipeline_settings(config: dict) -> dict:
    """1.5× 추적 확대 — ``zoom_pipeline`` 설정."""
    z = config.get("zoom_pipeline") or {}
    return {
        "step": float(z.get("step", z.get("panel", 1.5))),
        "max_depth": int(z.get("max_depth", 4)),
        "crop_frac": float(z.get("crop_frac", 0.55)),
        "min_confidence": float(z.get("min_confidence", 35)),
    }


def image_effective_scale(view: Box, image) -> float:
    w, _h = image.size
    return w / max(view.width, 1)


def pick_track_center(
    tokens: Sequence[OcrToken],
    img_w: int,
    img_h: int,
    *,
    min_confidence: float = 35.0,
) -> Optional[Tuple[int, int]]:
    """OCR 토큰 군집 중심 — 다음 1.5× crop 기준점."""
    good = [t for t in tokens if t.confidence >= min_confidence]
    pool = good if good else list(tokens)
    if not pool:
        return img_w // 2, img_h // 2
    if len(pool) == 1:
        t = pool[0]
        return t.box.left + t.box.width // 2, t.box.top + t.box.height // 2
    total_w = 0.0
    cx = 0.0
    cy = 0.0
    for t in pool:
        w = max(1.0, t.confidence)
        tcx = t.box.left + t.box.width / 2.0
        tcy = t.box.top + t.box.height / 2.0
        cx += tcx * w
        cy += tcy * w
        total_w += w
    return int(round(cx / total_w)), int(round(cy / total_w))


def crop_image_around_center(image, cx: int, cy: int, frac: float):
    """확대 이미지에서 중심 기준 frac 비율 crop → (crop, left, top)."""
    w, h = image.size
    cw = max(40, int(w * frac))
    ch = max(40, int(h * frac))
    left = max(0, min(int(cx) - cw // 2, w - cw))
    top = max(0, min(int(cy) - ch // 2, h - ch))
    return image.crop((left, top, left + cw, top + ch)), left, top


def screen_view_from_image_crop(
    parent_view: Box,
    image,
    crop_left: int,
    crop_top: int,
    crop_w: int,
    crop_h: int,
) -> Box:
    """확대 이미지 crop → 화면 좌표 view."""
    sx = image.size[0] / max(parent_view.width, 1)
    sy = image.size[1] / max(parent_view.height, 1)
    return Box(
        parent_view.left + int(round(crop_left / sx)),
        parent_view.top + int(round(crop_top / sy)),
        max(1, int(round(crop_w / sx))),
        max(1, int(round(crop_h / sy))),
    )


def read_track_zoom_on_box(
    screen_box: Box,
    config: dict,
    *,
    region_id: str = "",
    save_images: bool = True,
) -> HierarchicalReadResult:
    """
    1.5× 확대 → OCR → 토큰 중심 crop → 1.5× 반복.

    각 단계 ``view_box`` 에 빨간 포커스 네모 표시.
    """
    opts = zoom_pipeline_settings(config)
    step = opts["step"]
    max_depth = opts["max_depth"]
    crop_frac = opts["crop_frac"]
    min_conf = opts["min_confidence"]

    view = screen_box
    img = capture_box(view)
    stages: List[ReadStageResult] = []

    try:
        for depth in range(max_depth):

            def _ocr_step() -> Tuple[str, List[OcrToken]]:
                nonlocal img
                img = upscale_image(img, step)
                return ocr_image(img)

            plain, tokens = focus_stage(view, _ocr_step)
            eff = image_effective_scale(view, img)
            tag = f"{region_id or 'region'}_zoom{depth + 1}"
            stages.append(
                ReadStageResult(
                    stage=f"zoom_{depth + 1}",
                    scale=step,
                    region_id=region_id or "region",
                    image_path=save_debug_image(img, tag) if save_images else "",
                    tokens=tokens,
                    plain_text=plain,
                    effective_scale=eff,
                    view_box=view,
                )
            )

            if depth + 1 >= max_depth:
                break

            cx, cy = pick_track_center(
                tokens, img.size[0], img.size[1], min_confidence=min_conf
            )
            cropped, cl, ct = crop_image_around_center(img, cx, cy, crop_frac)
            view = screen_view_from_image_crop(
                view, img, cl, ct, cropped.size[0], cropped.size[1]
            )
            img = cropped
    finally:
        focus_hide()

    return HierarchicalReadResult(
        window_box=None,
        stages=stages,
        final_view_box=view,
    )


def ensure_output_dir() -> str:
    out = os.getenv("GC_SCREEN_CAPTURE_DIR", DEFAULT_OUTPUT)
    os.makedirs(out, exist_ok=True)
    return out


def focus_overlay_enabled() -> bool:
    """기본 ON — 끄려면 ``GC_SCREEN_SHOW_FOCUS=0``."""
    raw = os.getenv("GC_SCREEN_SHOW_FOCUS", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def focus_duration_ms() -> int:
    """단계당 네모 최소 표시 시간 (OCR이 더 길면 그동안 유지)."""
    raw = os.getenv("GC_SCREEN_FOCUS_MS", "").strip()
    if raw:
        try:
            return max(200, min(2000, int(raw)))
        except ValueError:
            pass
    return 800


_T = TypeVar("_T")


class FocusOverlay:
    """
    단계마다 하나의 빨간 네모만 표시.
    다음 단계로 넘어가면 이전 네모는 즉시 제거 후 새 영역에만 표시.
    """

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def hide(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._stop = threading.Event()
        self._thread = None

    def show(self, box: Box, *, border: int = 3, color: str = "red") -> None:
        if not focus_overlay_enabled():
            return
        self.hide()
        stop = self._stop

        def _run() -> None:
            import tkinter as tk

            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            chroma = "#010102"
            root.configure(bg=chroma)
            try:
                root.wm_attributes("-transparentcolor", chroma)
            except tk.TclError:
                pass
            w = max(1, box.width)
            h = max(1, box.height)
            root.geometry(f"{w}x{h}+{box.left}+{box.top}")
            canvas = tk.Canvas(root, width=w, height=h, bg=chroma, highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            pad = max(1, border)
            canvas.create_rectangle(
                pad,
                pad,
                w - pad,
                h - pad,
                outline=color,
                width=border,
                fill=chroma,
            )

            def _poll() -> None:
                if stop.is_set():
                    root.quit()
                    return
                root.after(40, _poll)

            _poll()
            root.mainloop()
            try:
                root.destroy()
            except tk.TclError:
                pass

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        time.sleep(0.04)

    def stage(self, box: Box, work: Callable[[], _T], *, min_ms: Optional[int] = None) -> _T:
        if not focus_overlay_enabled():
            return work()
        minimum = focus_duration_ms() if min_ms is None else min_ms
        t0 = time.perf_counter()
        self.show(box)
        try:
            return work()
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if elapsed_ms < minimum:
                time.sleep((minimum - elapsed_ms) / 1000.0)
            self.hide()


_FOCUS = FocusOverlay()


def focus_stage(box: Box, work: Callable[[], _T], *, min_ms: Optional[int] = None) -> _T:
    return _FOCUS.stage(box, work, min_ms=min_ms)


def focus_hide() -> None:
    _FOCUS.hide()


def flash_focus_box(
    box: Box,
    *,
    duration_ms: Optional[int] = None,
    border: int = 3,
    color: str = "red",
) -> None:
    """단일 영역 미리보기 (focus / calibrate 명령)."""
    if not focus_overlay_enabled():
        return
    ms = focus_duration_ms() if duration_ms is None else duration_ms
    _FOCUS.show(box, border=border, color=color)
    time.sleep(ms / 1000.0)
    _FOCUS.hide()


def flash_focus_point(
    x: int,
    y: int,
    *,
    size: int = 32,
    duration_ms: Optional[int] = None,
    color: str = "lime",
) -> None:
    """마우스 클릭·이동 지점 — 작은 네모 (OCR 영역 빨간 네모와 구분)."""
    if not focus_overlay_enabled():
        return
    half = max(8, size // 2)
    flash_focus_box(
        Box(int(x) - half, int(y) - half, size, size),
        duration_ms=duration_ms or min(500, focus_duration_ms()),
        border=2,
        color=color,
    )


def token_screen_box(token: OcrToken, region_box: Box, scale: float) -> Box:
    return Box(
        region_box.left + int(round(token.box.left / scale)),
        region_box.top + int(round(token.box.top / scale)),
        max(1, int(round(token.box.width / scale))),
        max(1, int(round(token.box.height / scale))),
    )


def save_debug_image(image, tag: str) -> str:
    out = ensure_output_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out, f"{ts}_{tag}.png")
    image.save(path)
    return path


def read_region_hierarchical(
    config: dict,
    region_id: str,
    *,
    window_box: Optional[Box] = None,
    save_images: bool = True,
) -> HierarchicalReadResult:
    title = config.get("window_title_contains", "Autochro")
    window_box = window_box or find_autochro_window_box(title)
    if window_box is None:
        from PIL import ImageGrab

        full = ImageGrab.grab()
        window_box = Box(0, 0, full.size[0], full.size[1])

    target_box, chain = resolve_region_box(config, region_id, window_box)
    opts = zoom_pipeline_settings(config)
    step = opts["step"]

    result = HierarchicalReadResult(window_box=window_box, final_view_box=target_box)

    # 창 전체 1회 coarse (1.5×) — 맥락용
    full_img = capture_box(window_box)

    def _window_coarse() -> Tuple[str, List[OcrToken]]:
        full_up = upscale_image(full_img, step)
        return ocr_image(full_up)

    full_text, full_tokens = focus_stage(window_box, _window_coarse)
    full_up = upscale_image(full_img, step)
    result.stages.append(
        ReadStageResult(
            "window_coarse",
            step,
            "autochro_window",
            save_debug_image(full_up, "full_window") if save_images else "",
            full_tokens,
            full_text,
            effective_scale=image_effective_scale(window_box, full_up),
            view_box=window_box,
        )
    )

    # 대상 영역 — 1.5× 추적 반복
    tracked = read_track_zoom_on_box(
        target_box,
        config,
        region_id=region_id,
        save_images=save_images,
    )
    result.stages.extend(tracked.stages)
    result.final_view_box = tracked.final_view_box

    _log(f"[눈] region={region_id} chain={' → '.join(chain)} track_zoom step={step}")
    for st in result.stages:
        preview = st.plain_text.replace("\n", " ")[:100]
        eff = st.effective_scale
        _log(f"  · {st.stage} x{st.scale:g} eff={eff:.2f} | {preview!r}")
        if st.image_path:
            _log(f"    png: {st.image_path}")
    return result


def _normalize_token(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def find_text_tokens(tokens: Iterable[OcrToken], query: str, *, partial: bool = True) -> List[OcrToken]:
    q = _normalize_token(query)
    hits: List[OcrToken] = []
    for tok in tokens:
        t = _normalize_token(tok.text)
        if not t:
            continue
        if (partial and q in t) or t == q:
            hits.append(tok)
    return hits


def token_screen_center(token: OcrToken, region_box: Box, scale: float) -> Tuple[int, int]:
    cx = token.box.left + token.box.width // 2
    cy = token.box.top + token.box.height // 2
    return (
        region_box.left + int(round(cx / scale)),
        region_box.top + int(round(cy / scale)),
    )


def click_screen(x: int, y: int, *, button: str = "left") -> None:
    flash_focus_point(x, y, color="lime")
    try:
        import pywinauto.mouse as mouse

        if button == "right":
            mouse.right_click(coords=(x, y))
        else:
            mouse.click(coords=(x, y))
    except Exception:
        import ctypes

        ctypes.windll.user32.SetCursorPos(x, y)
        down = 0x0008 if button == "right" else 0x0002
        up = 0x0010 if button == "right" else 0x0004
        ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)
    time.sleep(0.15)


def read_and_click_text(
    config: dict,
    region_id: str,
    text: str,
    *,
    button: str = "left",
    partial: bool = True,
) -> Tuple[int, int]:
    window_box = find_autochro_window_box(config.get("window_title_contains", "Autochro"))
    if window_box is None:
        raise RuntimeError("Autochro 창 없음")
    region_box, _ = resolve_region_box(config, region_id, window_box)
    tracked = read_track_zoom_on_box(region_box, config, region_id=region_id, save_images=True)
    if not tracked.stages:
        raise RuntimeError(f"OCR 단계 없음: {region_id}")
    last = tracked.stages[-1]
    view = tracked.final_view_box or region_box
    scale = last.effective_scale
    tokens = last.tokens
    hits = find_text_tokens(tokens, text, partial=partial)
    if not hits:
        path = last.image_path or ""
        raise RuntimeError(f"텍스트 없음: {text!r} — {path}")
    best = max(hits, key=lambda t: t.confidence)
    token_box = token_screen_box(best, view, scale)

    def _click() -> None:
        x, y = token_screen_center(best, view, scale)
        click_screen(x, y, button=button)

    focus_stage(token_box, _click, min_ms=200)
    x, y = token_screen_center(best, view, scale)
    _log(f"[클릭] {text!r} → ({x},{y}) conf={best.confidence:.0f}")
    return x, y


_NUMERIC_RE = re.compile(r"\d+\.?\d*")


def _numeric_values(text: str) -> List[float]:
    out: List[float] = []
    for m in _NUMERIC_RE.finditer(text.replace(",", "")):
        try:
            out.append(float(m.group()))
        except ValueError:
            pass
    return out


def run_read_task(config: dict, task_id: str) -> bool:
    task = config["read_tasks"][task_id]
    read = read_region_hierarchical(config, task["region"], save_images=True)
    text = read.final_text
    nums = _numeric_values(text)
    if task.get("expect_contains"):
        for needle in task["expect_contains"]:
            if needle not in text:
                _log(f"[FAIL] '{needle}' 없음")
                return False
    if task.get("reject_if_mostly_zero"):
        nz = [n for n in nums if abs(n) > 1e-6]
        if len(nz) < int(task.get("expect_numeric_min", 1)):
            _log(f"[FAIL] 유효 숫자 부족")
            return False
    if task.get("expect_mostly_zero"):
        nz = [n for n in nums if abs(n) > 1e-3]
        if len(nz) > 2:
            _log(f"[FAIL] 0이 아닌 값: {nz[:6]}")
            return False
    _log(f"[PASS] task={task_id}")
    return True


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GC1 Autochro 화면 읽기(눈)")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument(
        "--show-focus",
        action="store_true",
        help="OCR 전 속이 빈 빨간 네모로 영역 표시 (GC_SCREEN_SHOW_FOCUS=1)",
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("probe", help="주요 영역 OCR")
    r = sub.add_parser("read")
    r.add_argument("--region", required=True)
    t = sub.add_parser("task")
    t.add_argument("task_id")
    f = sub.add_parser("find")
    f.add_argument("--region", required=True)
    f.add_argument("--text", required=True)
    c = sub.add_parser("click")
    c.add_argument("--region", required=True)
    c.add_argument("--text", required=True)
    c.add_argument("--button", choices=("left", "right"), default="left")
    cal = sub.add_parser("calibrate")
    cal.add_argument("--region", required=True)
    fo = sub.add_parser("focus", help="영역 네모만 표시 (OCR 없음)")
    fo.add_argument("--region", required=True)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    if "--show-focus" in raw_argv:
        os.environ["GC_SCREEN_SHOW_FOCUS"] = "1"
        raw_argv = [a for a in raw_argv if a != "--show-focus"]
    args = build_parser().parse_args(raw_argv)
    config = load_config(args.config)
    if args.command == "probe":
        for rid in ("bottom_tabs", "left_analysis_tree", "top_sample_table", "bottom_peak_table_fine"):
            try:
                read_region_hierarchical(config, rid)
            except Exception as exc:
                _log(f"[오류] {rid}: {exc}")
        _log(f"캡처: {ensure_output_dir()}")
        return 0
    if args.command == "read":
        read_region_hierarchical(config, args.region)
        return 0
    if args.command == "task":
        return 0 if run_read_task(config, args.task_id) else 1
    if args.command == "find":
        read = read_region_hierarchical(config, args.region, save_images=False)
        hits = find_text_tokens(read.stages[-1].tokens, args.text)
        if not hits:
            _log(f"없음: {args.text!r}")
            return 1
        for h in hits:
            _log(f"  {h.text!r} conf={h.confidence:.0f}")
        return 0
    if args.command == "click":
        try:
            read_and_click_text(config, args.region, args.text, button=args.button)
            return 0
        except Exception as exc:
            _log(f"[오류] {exc}")
            return 1
    if args.command == "calibrate":
        win = find_autochro_window_box(config.get("window_title_contains", "Autochro"))
        if not win:
            return 1
        box, chain = resolve_region_box(config, args.region, win)
        flash_focus_box(box)
        path = save_debug_image(capture_box(box), f"calibrate_{args.region}")
        _log(f"{path} chain={' → '.join(chain)}")
        return 0
    if args.command == "focus":
        win = find_autochro_window_box(config.get("window_title_contains", "Autochro"))
        if not win:
            _log("Autochro 창 없음")
            return 1
        box, chain = resolve_region_box(config, args.region, win)
        _log(f"focus chain={' → '.join(chain)} box=({box.left},{box.top},{box.width},{box.height})")
        flash_focus_box(box)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
