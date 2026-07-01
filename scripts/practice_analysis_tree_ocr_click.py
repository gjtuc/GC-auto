# -*- coding: utf-8 -*-
"""연습: 분석목록 트리 — 줄 단위 OCR + CRM 이름 매칭 → 마우스 이동."""
from __future__ import annotations

import ctypes
import os
import re
import sys
import time

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gc1_runtime.layer0_data import extract_date8_from_data_name, rank_tree_line_for_data_name
from gc1_runtime.layer3_eye_guide import AutochroStepEye
from gc_autochro import (
    connect_main_window,
    load_autochro_config,
    read_active_control_data_name,
    _select_analysis_tab,
)
from gc_mailer import load_dotenv_files
from gc_screen_read import DEFAULT_CONFIG, click_screen, load_config

SUB = ("적분", "검량", "보고", "지연", "비교", "통계")


def analysis_tree(win):
    for ctrl in win.descendants(class_name="SysTreeView32"):
        if "분석목록" in " ".join(ctrl.texts() or []):
            return ctrl
    raise RuntimeError("분석목록 트리 없음")


def is_sub_line(line: str) -> bool:
    s = (line or "").strip()
    return not s or any(k in s for k in SUB)


def is_header_line(line: str) -> bool:
    return "목록" in (line or "")


def folder_score(line: str, crm: str, tree_label: str) -> float:
    if is_sub_line(line) or is_header_line(line):
        return -1.0
    score = rank_tree_line_for_data_name(line, crm)
    if score < 0:
        return -1.0
    lc = re.sub(r"\s+", "", line.lower())
    tc = re.sub(r"\s+", "", tree_label.lower())
    if tc[:16] in lc or lc[:16] in tc:
        score += 40.0
    return score


def ocr_rows_from_tokens(tokens):
    rows: dict[int, list] = {}
    for tok in tokens:
        yk = round(tok.box.top / 14) * 14
        rows.setdefault(yk, []).append(tok)
    return [
        (yk, " ".join(t.text for t in sorted(rows[yk], key=lambda x: x.box.left)))
        for yk in sorted(rows.keys())
    ], rows


def row_screen_center(view, scale, rows_map, yk):
    toks = rows_map[yk]
    top = min(t.box.top for t in toks)
    bot = max(t.box.top + t.box.height for t in toks)
    left = min(t.box.left for t in toks)
    right = max(t.box.left + t.box.width for t in toks)
    sx = view.left + int(round((left + right) / 2 / scale))
    sy = view.top + int(round((top + bot) / 2 / scale))
    return sx, sy


def ocr_tree_row_strips(view, scale, *, row_h: int = 18):
    """트리 영역을 가로 띠로 잘라 줄마다 OCR (한 줄씩 확인)."""
    from gc_screen_read import capture_box, ocr_image

    strips: list[tuple[int, str]] = []
    h = max(view.height, row_h)
    y = 0
    while y < h:
        band_h = min(row_h, h - y)
        box = type(view)(view.left, view.top + y, view.width, band_h)
        img = capture_box(box)
        text, _ = ocr_image(img)
        line = " ".join((text or "").split())
        strips.append((y, line))
        y += row_h
    return strips


def strip_screen_center(view, scale, strip_y: int, row_h: int = 18):
    sy = view.top + strip_y + row_h // 2
    sx = view.left + view.width // 3
    return sx, sy


def find_folder_row_by_strip_ocr(eye, crm: str, tree_label: str):
    view, scale, _ = eye.ocr_region_tokens(
        "left_analysis_tree",
        needles=["2026", "dre"],
    )
    strips = ocr_tree_row_strips(view, scale)
    best_y = None
    best_score = -1.0
    best_line = ""

    print("--- strip OCR (one band per row) ---")
    for i, (strip_y, line) in enumerate(strips):
        if not line.strip():
            continue
        sc = folder_score(line, crm, tree_label)
        # 느슨 매칭: CRM 날짜 6자리(0630) + dre
        lc = re.sub(r"\s+", "", line.lower())
        yy6 = extract_date8_from_data_name(crm)[-6:]
        if sc < 0 and not is_sub_line(line) and yy6 in lc and "dre" in lc:
            if "20260629" not in lc or yy6 in lc:
                sc = 70.0
        mark = ""
        if sc >= 0:
            mark = "  <-- match?"
        print(f"  strip{i:2d} y={strip_y:3d} sub={is_sub_line(line)} score={sc:5.1f} | {line[:60]}{mark}")
        if sc > best_score:
            best_score, best_y, best_line = sc, strip_y, line

    if best_y is None or best_score < 0:
        return None
    sx, sy = strip_screen_center(view, scale, best_y)
    return sx, sy, best_line, "strip", best_score


def find_folder_row_by_ocr(eye, crm: str, tree_label: str):
    view, scale, tokens = eye.ocr_region_tokens(
        "left_analysis_tree",
        needles=["2026", "dre", "ni", "ce", "성형", "환원"],
    )
    ocr_rows, rows_map = ocr_rows_from_tokens(tokens)
    best_yk = None
    best_score = -1.0
    best_line = ""
    best_method = ""

    print("--- line-by-line OCR (top -> bottom) ---")
    for i, (yk, line) in enumerate(ocr_rows):
        sc = folder_score(line, crm, tree_label)
        mark = "  <-- best" if sc >= 0 and sc >= best_score else ""
        print(
            f"  row{i:2d} y={yk:3d} sub={is_sub_line(line)} score={sc:5.1f} | "
            f"{line[:65]}{mark}"
        )
        if sc > best_score:
            best_score, best_yk, best_line, best_method = sc, yk, line, "single"

    for i in range(len(ocr_rows)):
        if is_sub_line(ocr_rows[i][1]) or is_header_line(ocr_rows[i][1]):
            continue
        merged = ""
        for j in range(i, min(i + 4, len(ocr_rows))):
            part = ocr_rows[j][1]
            if is_sub_line(part):
                break
            merged = (merged + " " + part).strip()
            sc = folder_score(merged, crm, tree_label)
            if sc > best_score:
                best_score = sc
                best_yk = ocr_rows[i][0]
                best_line = merged
                best_method = f"merge{i}-{j}"

    if best_yk is None or best_score < 0:
        return None

    sx, sy = row_screen_center(view, scale, rows_map, best_yk)
    return sx, sy, best_line, best_method, best_score


def find_folder_by_visible_line_walk(tree, eye, crm: str, tree_label: str):
    """
    위→아래 한 줄씩 확인 (트리 texts 순서).
    CRM과 일치하는 **폴더 줄** 번호를 찾고, 그 줄 높이에 마우스.
    """
    visible = [
        (t or "").strip()
        for t in tree.texts()
        if (t or "").strip() and t.strip() != "Tree1"
    ]
    view, scale, _ = eye.ocr_region_tokens(
        "left_analysis_tree",
        needles=["2026", "dre", "ni"],
    )
    row_h = 18
    strips = ocr_tree_row_strips(view, scale, row_h=row_h)

    print("--- visible line walk (top -> bottom) ---")
    folder_idx = None
    for i, t in enumerate(visible):
        sub = is_sub_line(t)
        header = is_header_line(t)
        match = (not sub) and (not header) and rank_tree_line_for_data_name(t, crm) >= 0
        ocr_hint = strips[i][1][:40] if i < len(strips) else ""
        mark = "  <-- CRM folder" if match else ""
        print(f"  line{i:2d} sub={sub} match={match} | {t[:55]}{mark}")
        if match and folder_idx is None:
            folder_idx = i
            if i < len(strips):
                print(f"         strip OCR: {ocr_hint!r}")

    if folder_idx is None:
        return None

    strip_y = folder_idx * row_h
    sx, sy = strip_screen_center(view, scale, strip_y, row_h)
    return sx, sy, visible[folder_idx], f"visible_line_{folder_idx}", 100.0


def main():
    os.environ.setdefault("GC_SCREEN_SHOW_FOCUS", "1")
    excel = os.path.join(os.path.expanduser("~"), "Desktop", "박은규")
    load_dotenv_files(_REPO, excel)
    cfg = load_autochro_config(excel)
    _, win = connect_main_window(cfg)
    crm = read_active_control_data_name(win, cfg)
    _select_analysis_tab(win)
    time.sleep(0.6)
    ctypes.windll.user32.SetForegroundWindow(win.handle)

    tree = analysis_tree(win)
    visible = [
        (t or "").strip()
        for t in tree.texts()
        if (t or "").strip() and t.strip() != "Tree1"
    ]
    tree_label = next(
        t
        for t in visible
        if not is_sub_line(t)
        and not is_header_line(t)
        and rank_tree_line_for_data_name(t, crm) >= 0
    )

    eye = AutochroStepEye.from_window_rect(
        win.rectangle(), config=load_config(DEFAULT_CONFIG)
    )
    print("CRM:", crm)
    print("tree label:", tree_label)

    result = find_folder_row_by_strip_ocr(eye, crm, tree_label)
    if result is None:
        print("strip OCR scan failed — trying token rows...")
        result = find_folder_row_by_ocr(eye, crm, tree_label)
    if result is None:
        print("token OCR failed — visible line walk (CRM match per line)...")
        result = find_folder_by_visible_line_walk(tree, eye, crm, tree_label)
    if result is None:
        print("FAIL — CRM folder row not found")
        return 1

    sx, sy, best_line, method, score = result
    print(f"MATCH ({method}) score={score:.1f} | {best_line[:70]}")
    print("CLICK", sx, sy)
    click_screen(sx, sy, button="left")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
