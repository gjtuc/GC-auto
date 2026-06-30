# -*- coding: utf-8 -*-
"""
gc3_screen_read.py — GC3 Chem32 화면 영역 캡처·OCR **스켈레톤** (T83)

설계: ``deploy/GC3_SCREEN_REGION_READ.md``
설정: ``deploy/screen_regions.gc3.json``

GC3 **주 경로**는 ``gc_chem32.py`` → ``Report.TXT`` 파싱.
본 모듈은 UI 상태·검증·원격 디버그 **보조** — Win7 GC3 장비 PC에서 live OCR 확장 예정.

실행 (GC8860 / repo — Chem32 불필요):
  python gc3_screen_read.py --dry-run list
  python gc3_screen_read.py --dry-run read --region chem32_status_bar
  python gc3_screen_read.py --dry-run probe

live (GC3 PC, Tesseract·mss 필요 — ``requirements-screen.txt``):
  python gc3_screen_read.py read --region chem32_status_bar
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "deploy", "screen_regions.gc3.json")
DEFAULT_OUTPUT = os.path.join(os.path.expanduser("~"), ".cursor", "gc3-screen-capture")


@dataclass(frozen=True)
class Box:
    """화면 또는 창 내부 절대 픽셀 사각형."""

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
class ScreenReadResult:
    """영역 1회 읽기 결과 — dry-run·live 공통."""

    region_id: str
    plain_text: str
    dry_run: bool
    image_path: str = ""
    method: str = "ocr"
    scale: float = 1.0
    window_box: Optional[Box] = None
    region_box: Optional[Box] = None
    notes: List[str] = field(default_factory=list)


def _log(msg: str) -> None:
    print(msg, flush=True)


def load_config(path: str) -> dict:
    """정적 검증 — JSON 로드·최상위 ``regions`` 키 필수."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    if "regions" not in raw or not isinstance(raw["regions"], dict):
        raise ValueError(f"invalid config (missing regions): {path}")
    return raw


def list_region_ids(config: dict) -> List[str]:
    return sorted(config["regions"].keys())


def box_from_fraction(parent: Box, frac: Sequence[float]) -> Box:
    """창 내부 상대 좌표 (0~1) → 절대 Box."""
    x, y, w, h = frac
    return Box(
        parent.left + int(round(parent.width * x)),
        parent.top + int(round(parent.height * y)),
        max(1, int(round(parent.width * w))),
        max(1, int(round(parent.height * h))),
    )


def resolve_region_box(
    config: dict,
    region_id: str,
    window_box: Box,
) -> Tuple[Box, float]:
    """
    ``regions`` 체인(parent) 따라 절대 픽셀 box·scale 반환.

    Raises:
        KeyError: 알 수 없는 region_id
        ValueError: box 형식 오류
    """
    regions = config["regions"]
    if region_id not in regions:
        raise KeyError(region_id)

    chain: List[str] = []
    rid = region_id
    while rid:
        chain.append(rid)
        parent = regions[rid].get("parent")
        rid = parent if parent else None
    chain.reverse()

    current = window_box
    scale = 1.0
    for rid in chain:
        spec = regions[rid]
        frac = spec.get("box")
        if not frac or len(frac) != 4:
            raise ValueError(f"region {rid!r}: box must be [x,y,w,h] fractions")
        current = box_from_fraction(current, frac)
        scale = float(spec.get("scale", scale))
    return current, scale


def _dry_run_window_box(config: dict) -> Box:
    """dry-run — display_profile 기준 가상 Chem32 창."""
    prof = config.get("display_profile", {})
    w = int(prof.get("width", 1920))
    h = int(prof.get("height", 1080))
    return Box(0, 0, w, h)


def find_chem32_window_box(title_contains: str) -> Optional[Box]:
    """
    live — Chem32 창 rect (pywinauto win32).

    Returns:
        None: 창 없음 또는 pywinauto 미설치
    """
    try:
        import re

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


def _capture_box(box: Box):
    """live 캡처 — mss 우선, Pillow ImageGrab fallback."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Pillow 필요 — pip install Pillow (또는 requirements-screen.txt)"
        ) from exc
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


def _upscale_image(image, scale: float):
    if scale <= 1.0:
        return image
    from PIL import Image

    w, h = image.size
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return image.resize((nw, nh), Image.Resampling.LANCZOS)


def _ocr_image(image) -> str:
    """live OCR — pytesseract (gc_screen_read 와 동일 의존)."""
    try:
        import pytesseract
        from PIL import ImageEnhance, ImageOps
    except ImportError as exc:
        raise RuntimeError(
            "pytesseract·Pillow 필요 — pip install -r requirements-screen.txt"
        ) from exc

    cmd = os.getenv("TESSERACT_CMD", "").strip()
    if not cmd:
        for candidate in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if os.path.isfile(candidate):
                cmd = candidate
                break
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    lang = os.getenv("GC3_SCREEN_OCR_LANG", os.getenv("GC_SCREEN_OCR_LANG", "eng"))
    gray = ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(1.35)
    config = os.getenv("GC_SCREEN_TESSERACT_CONFIG", "--psm 6")
    return pytesseract.image_to_string(gray, lang=lang, config=config).strip()


def _ensure_output_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def read_region(
    config: dict,
    region_id: str,
    *,
    dry_run: bool = False,
    output_dir: Optional[str] = None,
) -> ScreenReadResult:
    """
    영역 1회 읽기.

    dry_run=True: Chem32·OCR 없이 ``dry_run_text`` 반환 (GC8860 unittest·에이전트 검증).
    dry_run=False: 창 탐색 → 캡처 → (scale) → OCR.
    """
    spec = config["regions"][region_id]
    method = str(spec.get("method", "ocr"))
    out_dir = _ensure_output_dir(output_dir or DEFAULT_OUTPUT)

    if dry_run:
        win = _dry_run_window_box(config)
        region_box, scale = resolve_region_box(config, region_id, win)
        text = str(spec.get("dry_run_text", f"[dry-run:{region_id}]"))
        return ScreenReadResult(
            region_id=region_id,
            plain_text=text,
            dry_run=True,
            method=method,
            scale=scale,
            window_box=win,
            region_box=region_box,
            notes=["dry-run: no capture/OCR"],
        )

    title = config.get("window_title_contains", "ChemStation")
    window_box = find_chem32_window_box(title)
    if window_box is None:
        raise RuntimeError(
            f"Chem32 창 없음 (title_contains={title!r}) — "
            "GC3 PC에서 Chem32 실행 후 재시도, 또는 --dry-run"
        )

    region_box, scale = resolve_region_box(config, region_id, window_box)
    image = _capture_box(region_box)
    image = _upscale_image(image, scale)

    image_path = os.path.join(out_dir, f"{region_id}.png")
    image.save(image_path)

    if method == "ocr":
        plain = _ocr_image(image)
    else:
        plain = ""

    return ScreenReadResult(
        region_id=region_id,
        plain_text=plain,
        dry_run=False,
        image_path=image_path,
        method=method,
        scale=scale,
        window_box=window_box,
        region_box=region_box,
    )


def env_dry_run() -> bool:
    return os.getenv("GC3_SCREEN_DRY_RUN", "").strip().lower() in ("1", "true", "yes")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="GC3 Chem32 화면 영역 읽기 (스켈레톤 — Report.TXT 보조)",
    )
    p.add_argument("--config", default=DEFAULT_CONFIG, help="screen_regions.gc3.json 경로")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Chem32·OCR 없이 config dry_run_text 만 반환",
    )
    p.add_argument("--output-dir", default=DEFAULT_OUTPUT, help="캡처 PNG 저장 폴더 (live)")

    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="설정에 등록된 region ID 목록")
    r = sub.add_parser("read", help="단일 영역 OCR")
    r.add_argument("--region", required=True)
    pr = sub.add_parser("probe", help="모든 region dry-run/read 요약")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    dry_run = args.dry_run or env_dry_run()
    config = load_config(args.config)

    if args.command == "list":
        for rid in list_region_ids(config):
            desc = config["regions"][rid].get("description", "")
            _log(f"{rid}\t{desc}")
        return 0

    if args.command == "read":
        result = read_region(
            config,
            args.region,
            dry_run=dry_run,
            output_dir=args.output_dir,
        )
        _log(f"[{result.region_id}] dry_run={result.dry_run} method={result.method}")
        if result.image_path:
            _log(f"  image: {result.image_path}")
        _log(f"  text: {result.plain_text!r}")
        return 0

    if args.command == "probe":
        ok = 0
        for rid in list_region_ids(config):
            try:
                result = read_region(
                    config,
                    rid,
                    dry_run=dry_run,
                    output_dir=args.output_dir,
                )
                _log(f"[OK] {rid}: {result.plain_text[:60]!r}")
                ok += 1
            except Exception as exc:
                _log(f"[FAIL] {rid}: {exc}")
        return 0 if ok == len(list_region_ids(config)) else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
