# -*- coding: utf-8 -*-
"""
gc_autochro.py — 영린 Autochro-3000 UI 자동화 (GC1 PDF 내보내기)

=============================================================================
[이 모듈의 역할 — GC1 전용]
=============================================================================

GC2/GC3는 Agilent ChemStation sequence.acam_ / Report 를 파싱합니다.
GC1(박은규, YL6500GC)은 ChemStation 경로가 아니라 **Autochro-3000 UI** 에서
「인쇄 → Hancom PDF」로 보고서를 만든 뒤, gc_gc1.py 가 PDF 텍스트를 파싱합니다.

  Repo: data_pc/ 와 별개. **GC1 장비 PC만** 실행 (은규 PC에서 실행 금지). GitHub: gjtuc/GC-auto

본 모듈은 **PDF 파일을 Autochro 화면 조작으로 생성**하는 단계만 담당합니다.

=============================================================================
[UI 흐름]  (run_autochro_export)
=============================================================================

  1) 제어목록 탭 → 하단 시료 표 **고정 위치** 더블클릭 → 분석목록과 동기화
     (``1.raw`` 텍스트가 아님 — 주입이 쌓이면 라벨은 스크롤되어 사라짐)
  2) 분석목록 시료 표 Ctrl+A
  3) 시료 표 우클릭 → 초기화
  4) 왼쪽 트리(제어목록 데이터명과 동일) 우클릭 → 분석방법 불러오기 → {YYYYMMDD} 분석방법.MTD
  5) Ctrl+A → 우클릭 초기화 (아래 피크 표 0)
  6) Ctrl+A → 메뉴 「시료목록 → 초기화+정량」 — 적분 대기
  7) Ctrl+P 인쇄 → Hancom PDF
  8) PDF 저장

  GC1_AUTOCHRO_PREP_STEPS=0 이면 3~5 생략 (구버전: 2→6만).

=============================================================================
[PDF 파일명 — 하드코딩 금지]
=============================================================================

  저장 stem 은 gc_automation.env 의 AUTOCHRO_DATA_NAME 이 아니라,
  **제어목록 왼쪽 트리에서 파란 선택된 실험 데이터명** + 창 제목에서 읽습니다.
  읽은 문자열을 **그대로** PDF 파일명으로 쓰며 (날짜·@·공백 재조합 없음),
  Windows 금지문자만 제거합니다.

=============================================================================
[UI 자동화 함정 — pywinauto win32]
=============================================================================

  · **창 위치**: 표/트리 탐색에 화면 절대좌표를 쓰면 창을 옆으로 밀면 실패합니다.
    connect_main_window() 직후 _prepare_autochro_window() 로 복원·(옵션) 이동하고,
    SysListView32 / SysTreeView32 는 **창 내부 상대 위치**로 고릅니다.

  · **Ctrl+A**: 분석목록 「소유자 ID」열(관리자 드롭다운) 위에 마우스가 있으면
    셀 편집 모드 → Ctrl+A 불가 → PDF 3페이지(1시료)만 저장됩니다.
    _focus_list_for_ctrl_a() 가 「수집 일시」열과 같은 가로 위치(~78%)에 클릭합니다.

  · **GC1_AUTOCHRO_EYE** (기본 live=1): 단계마다 OCR 로 영역 읽기·클릭·검증.
    제어목록 동기화는 ``.raw`` 토큰 위치로 더블클릭. 우클릭 메뉴는 OCR 클릭.
    끄기: ``GC1_AUTOCHRO_EYE=0`` · Tesseract: requirements-screen.txt

  · **32-bit Autochro**: 64-bit Python 으로도 동작하지만 pywinauto 경고가 납니다.
    GC1 장비 PC 배포 시 32-bit Python 권장.

  · **Hancom PDF**: 저장 후 변환 창이 남으면 다음 실행이 막힐 수 있음.
    _wait_and_close_all_hancom_pdf() + AUTOCHRO_HANCOM_WAIT_SEC

=============================================================================
[watch / pipeline 과의 관계]
=============================================================================

  ensure_gc1_pdf_exported() — watch·pipeline 진입점
    · should_export_crm(): Documents\\*.CRM mtime vs state (force 시 무시)
    · watch GC1: 핫스pot **세션당 1회** force=True 로 PDF 재생성
    · pipeline force: config.force → Autochro 재내보내기
    · GC1_SKIP_AUTOCHRO_EXPORT=1 이면 pipeline 이 중복 export 방지

  record_autochro_export() — last_autochro_crm_mtime 갱신

=============================================================================
[주요 환경 변수]
=============================================================================

  AUTOCHRO_ENABLED, AUTOCHRO_WINDOW_TITLE_PATTERN, AUTOCHRO_DATA_NAME(CRM 경로용)
  AUTOCHRO_AUTO_POSITION, AUTOCHRO_WINDOW_X/Y
  AUTOCHRO_LIST_NEUTRAL_X_FRAC  — Ctrl+A 전 클릭 가로 위치 (기본 0.78)
  AUTOCHRO_ANALYSIS_METHOD_DIR    — {YYYYMMDD} 분석방법.MTD 폴더 (기본 바탕화면)
  GC1_AUTOCHRO_PREP_STEPS         — 1=적분 준비(초기화·MTD) 포함 (기본), 0=생략
  GC1_USE_RUNTIME                 — 1=``gc1_runtime.layer4_job`` 위임 (기본 0, 기존 UI 경로)
  GC1_AUTOCHRO_EYE               — 1=단계마다 OCR 눈 (live 기본 1, dry_run 제외)
  AUTOCHRO_HANCOM_WAIT_SEC, AUTOCHRO_QUANTIFY_WAIT_SEC
  GC1_PDF_READY_WAIT_SEC — gc_gc1 쪽 PDF 잠금 해제 대기

테스트: Desktop\\박은규\\GC1_데이터갱신.bat  또는  python gc_autochro.py --export --force
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from gc_sanitize import sanitize_sample_name
from gc_state import load_send_state, save_send_state


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# 제어목록(파란 선택) 데이터명 → PDF 파일명 stem
_DATA_NAME_DATE_RE = re.compile(r"^\d{6}")


def format_data_name_for_pdf_filename(raw: str) -> str:
    """
    Autochro 데이터명 → PDF 저장 stem.

    UI·창 제목에서 읽은 문자열을 변환하지 않고 그대로 쓰고,
    Windows 파일명 금지문자만 제거합니다.
    """
    text = raw.strip().split(".")[0].strip()
    if not text:
        raise ValueError("Autochro 데이터명이 비어 있음")
    return sanitize_sample_name(text)


@dataclass(frozen=True)
class AutochroConfig:
    enabled: bool
    window_title_pattern: str
    crm_path: str
    pdf_output_dir: str
    pdf_name_template: str
    quantify_wait_sec: int
    print_wait_sec: int
    dialog_wait_sec: int
    hancom_wait_sec: int
    dry_run: bool


def _fallback_data_name(cfg: AutochroConfig) -> str:
    explicit = os.getenv("AUTOCHRO_DATA_NAME", "").strip()
    if explicit:
        return explicit
    if cfg.crm_path:
        return os.path.splitext(os.path.basename(cfg.crm_path))[0]
    return ""


def build_export_pdf_path(
    cfg: AutochroConfig,
    when: Optional[datetime] = None,
    data_name_raw: Optional[str] = None,
) -> str:
    source = (data_name_raw or "").strip() or _fallback_data_name(cfg)
    if not source:
        raise ValueError("Autochro 데이터명을 찾지 못함 — 제어목록 또는 AUTOCHRO_DATA_NAME 확인")
    stem = format_data_name_for_pdf_filename(source)
    explicit_template = os.getenv("GC1_PDF_EXPORT_NAME", "").strip()
    if explicit_template and "{suffix}" in explicit_template:
        dt = when or datetime.now()
        suffix = stem.split(" ", 1)[1] if " " in stem else stem
        stem = explicit_template.format(
            yymmdd=dt.strftime("%y%m%d"),
            yyyymmdd=dt.strftime("%Y%m%d"),
            date=dt.strftime("%Y-%m-%d"),
            suffix=suffix,
            experiment=stem,
            data_name=source,
        ).strip()
    if not stem.lower().endswith(".pdf"):
        stem += ".pdf"
    return os.path.join(cfg.pdf_output_dir, stem)


def load_autochro_config(excel_output_dir: str) -> AutochroConfig:
    pdf_dir = os.getenv("GC1_PDF_DIR", "").strip() or os.getenv("AUTOCHRO_PDF_DIR", "").strip()
    if not pdf_dir:
        pdf_dir = excel_output_dir
    crm_path = resolve_crm_path()
    return AutochroConfig(
        enabled=_env_bool("AUTOCHRO_ENABLED", False),
        window_title_pattern=os.getenv("AUTOCHRO_WINDOW_TITLE_PATTERN", "Autochro-3000").strip()
        or "Autochro-3000",
        crm_path=crm_path,
        pdf_output_dir=os.path.normpath(os.path.expanduser(pdf_dir)),
        pdf_name_template=os.getenv("GC1_PDF_EXPORT_NAME", "").strip(),
        quantify_wait_sec=_env_int("AUTOCHRO_QUANTIFY_WAIT_SEC", 180),
        print_wait_sec=_env_int("AUTOCHRO_PRINT_WAIT_SEC", 600),
        dialog_wait_sec=_env_int("AUTOCHRO_DIALOG_WAIT_SEC", 30),
        hancom_wait_sec=_env_int("AUTOCHRO_HANCOM_WAIT_SEC", 180),
        dry_run=_env_bool("AUTOCHRO_DRY_RUN", False),
    )


def is_autochro_enabled() -> bool:
    return _env_bool("AUTOCHRO_ENABLED", False)


def resolve_crm_path() -> str:
    explicit = os.getenv("AUTOCHRO_CRM_PATH", "").strip()
    if explicit:
        return os.path.normpath(os.path.expanduser(explicit))
    data_name = os.getenv("AUTOCHRO_DATA_NAME", "").strip()
    if not data_name:
        data_name = os.getenv("AUTOCHRO_WINDOW_TITLE_PATTERN", "").split("-")[0].strip()
    if not data_name:
        # Documents 에서 최신 .CRM
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        crms = glob.glob(os.path.join(docs, "*.CRM")) + glob.glob(os.path.join(docs, "*.crm"))
        if crms:
            return max(crms, key=os.path.getmtime)
        return ""
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    for ext in (".CRM", ".crm"):
        path = os.path.join(docs, data_name + ext)
        if os.path.isfile(path):
            return path
    return os.path.join(docs, data_name + ".CRM")


def get_crm_mtime(crm_path: str) -> Optional[float]:
    try:
        return os.path.getmtime(crm_path)
    except OSError:
        return None


def pdf_fresh_skip_sec() -> int:
    return _env_int("AUTOCHRO_PDF_FRESH_SEC", 120)


def is_pdf_recently_exported(pdf_path: str, max_age_sec: Optional[int] = None) -> bool:
    """방금 내보낸 PDF면 Autochro 재실행 생략 (이중 저장 방지)."""
    age = pdf_fresh_skip_sec() if max_age_sec is None else max_age_sec
    try:
        return os.path.isfile(pdf_path) and (time.time() - os.path.getmtime(pdf_path)) < age
    except OSError:
        return False


def should_export_crm(state_path: str, crm_path: str, force: bool = False) -> Tuple[bool, str]:
    if force or _env_bool("AUTOCHRO_ALWAYS_EXPORT", False):
        return True, "force" if force else "매번 내보내기(AUTOCHRO_ALWAYS_EXPORT)"
    mtime = get_crm_mtime(crm_path)
    if mtime is None:
        return False, f"CRM 없음: {crm_path}"
    state = load_send_state(state_path)
    last = state.get("last_autochro_crm_mtime")
    if last is None:
        return True, "CRM 최초 감지"
    if mtime > float(last):
        return True, "CRM 갱신됨"
    return False, "CRM 변경 없음"


def record_autochro_export(state_path: str, crm_path: str, pdf_path: str) -> None:
    state = load_send_state(state_path)
    crm_mtime = get_crm_mtime(crm_path)
    if crm_mtime is not None:
        state["last_autochro_crm_mtime"] = crm_mtime
    state["last_autochro_export_pdf"] = pdf_path
    state["last_autochro_export_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_send_state(state_path, state)


def _log(msg: str) -> None:
    safe = msg.replace("\u2014", "-").replace("\u2192", "->")
    print(f"[Autochro] {safe}", flush=True)


def _require_pywinauto():
    try:
        from pywinauto import Application  # noqa: F401
        from pywinauto.keyboard import send_keys  # noqa: F401
    except ImportError as exc:
        raise ImportError("pywinauto 미설치 - pip install pywinauto") from exc


def _score_autochro_window(win) -> int:
    score = 0
    try:
        if win.is_visible():
            score += 100
    except Exception:
        pass
    try:
        rect = win.rectangle()
        score += min(rect.width() * rect.height() // 1000, 500)
    except Exception:
        pass
    try:
        if win.descendants(class_name="SysTreeView32"):
            score += 200
    except Exception:
        pass
    try:
        if win.descendants(class_name="SysListView32"):
            score += 100
    except Exception:
        pass
    return score


def connect_main_window(cfg: AutochroConfig):
    _require_pywinauto()
    from pywinauto import Application, findwindows

    pattern = re.escape(cfg.window_title_pattern)
    title_re = f".*{pattern}.*"
    _log(f"창 연결: {title_re}")
    handles = findwindows.find_windows(title_re=title_re)
    if not handles:
        raise RuntimeError(f"Autochro 창 없음 — {cfg.window_title_pattern}")
    if len(handles) == 1:
        app = Application(backend="win32").connect(handle=handles[0])
        win = app.window(handle=handles[0])
    else:
        _log(f"Autochro 창 {len(handles)}개 — 메인 창 선택")
        best = None
        best_score = -1
        for handle in handles:
            try:
                app = Application(backend="win32").connect(handle=handle)
                candidate = app.window(handle=handle)
                score = _score_autochro_window(candidate)
                if score > best_score:
                    best_score = score
                    best = candidate
            except Exception:
                continue
        if best is None:
            raise RuntimeError(f"Autochro 창 연결 실패 — {cfg.window_title_pattern}")
        app = Application(backend="win32").connect(handle=best.handle)
        win = best
    _prepare_autochro_window(win, cfg)
    return app, win


def _prepare_autochro_window(win, cfg: AutochroConfig) -> None:
    """
    Autochro 연결 직후 창 상태 정리.

    절대 화면좌표(rect.top>500 등)로 컨트롤을 찾던 초기 버전은 창을 옆으로 밀면
    실패했습니다. 이 함수로 먼저 화면 안으로 옮긴 뒤, list/tree 는 창 상대 좌표 사용.
    AUTOCHRO_AUTO_POSITION=0 이면 위치 이동만 끔.
    """
    try:
        win.restore()
    except Exception:
        pass
    try:
        win.set_focus()
    except Exception:
        pass

    if _env_bool("AUTOCHRO_AUTO_POSITION", True):
        rect = win.rectangle()
        width = max(rect.width(), 1200)
        height = max(rect.height(), 800)
        x = _env_int("AUTOCHRO_WINDOW_X", 40)
        y = _env_int("AUTOCHRO_WINDOW_Y", 40)
        try:
            win.move_window(x=x, y=y, width=width, height=height, repaint=True)
            _log(f"Autochro 창 위치 정리 ({x},{y}) {width}x{height}")
        except Exception as exc:
            _log(f"Autochro 창 이동 실패(계속 시도): {exc}")
        time.sleep(0.6)

    try:
        win.set_focus()
    except Exception:
        pass


def _window_rect(win):
    try:
        return win.rectangle()
    except Exception:
        return None


def _read_data_name_from_window_title(win) -> str:
    title = (win.window_text() or "").strip()
    match = re.search(r"\s[-–]\s+.*[Aa]utochro", title)
    if match:
        name = title[: match.start()].strip().split(".")[0].strip()
        if _DATA_NAME_DATE_RE.match(name):
            return name
    return ""


def _read_data_name_from_control_tree(win) -> str:
    """제어목록 왼쪽 트리 — YL6500 GC 0 바로 위(파란 선택) 데이터명."""
    instrument_markers = ("YL6500 GC", "YL6500GC")
    win_rect = _window_rect(win)
    for ctrl in win.descendants(class_name="SysTreeView32"):
        try:
            rect = ctrl.rectangle()
        except Exception:
            continue
        if win_rect is not None:
            rel_left = rect.left - win_rect.left
            if rel_left > win_rect.width() * 0.5:
                continue
        items: list[str] = []
        try:
            for text in ctrl.texts():
                line = (text or "").strip()
                if line:
                    items.append(line)
        except Exception:
            continue
        for idx, line in enumerate(items):
            if any(marker in line for marker in instrument_markers) and idx > 0:
                candidate = items[idx - 1].strip().split(".")[0].strip()
                if _DATA_NAME_DATE_RE.match(candidate):
                    return candidate
        try:
            selected = ctrl.get_selected()
            if selected:
                candidate = str(selected[0]).strip().split(".")[0].strip()
                if _DATA_NAME_DATE_RE.match(candidate):
                    return candidate
        except Exception:
            pass
    return ""


def read_active_control_data_name(win, cfg: AutochroConfig) -> str:
    _select_control_tab(win)
    time.sleep(0.3)
    for reader in (_read_data_name_from_window_title, _read_data_name_from_control_tree):
        name = reader(win)
        if name:
            return name
    fallback = _fallback_data_name(cfg)
    if fallback:
        _log(f"제어목록 데이터명 UI 읽기 실패 — AUTOCHRO_DATA_NAME 사용: {fallback}")
        return fallback
    raise RuntimeError("제어목록 데이터명을 찾지 못함 — Autochro 창·제어목록 탭 확인")


def _click_text_button(parent, texts: Tuple[str, ...], timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for text in texts:
            try:
                btn = parent.child_window(title=text, class_name_re="Button")
                if btn.exists(timeout=0.5):
                    btn.click_input()
                    return True
            except Exception:
                continue
        time.sleep(0.3)
    return False


def _bottom_tabs(win):
    return win.child_window(class_name="SysTabControl32", title="Tab1")


def _menu_top_texts(win) -> list[str]:
    texts: list[str] = []
    for item in win.menu_items():
        if isinstance(item, dict):
            texts.append(item.get("text", ""))
    return texts


def _on_analysis_tab(win) -> bool:
    return any("분석목록" in text for text in _menu_top_texts(win))


def _on_control_tab(win) -> bool:
    return any("제어목록" in text for text in _menu_top_texts(win))


def _select_tab_index(win, index: int) -> None:
    tabs = _bottom_tabs(win)
    tabs.select(index)
    time.sleep(0.8)


def _select_control_tab(win) -> None:
    if not _on_control_tab(win):
        _select_tab_index(win, 1)


def _select_analysis_tab(win) -> None:
    if not _on_analysis_tab(win):
        _select_tab_index(win, 0)


def _sample_table_candidates(win, *, prefer: str = "any"):
    """
    SysListView32 후보 — 화면 절대좌표 대신 Autochro 창 안 위치로 판별.
    prefer: 'lower' 제어목록 하단 표, 'upper' 분석목록 상단 표, 'any'
    """
    win_rect = _window_rect(win)
    win_h = max(win_rect.height(), 200) if win_rect else 800
    candidates = []
    for ctrl in win.descendants(class_name="SysListView32"):
        try:
            rect = ctrl.rectangle()
            count = int(ctrl.item_count())
        except Exception:
            continue
        if count <= 0:
            continue
        if rect.height() < 60 or rect.width() < 180:
            continue
        if win_rect is not None:
            rel_mid_y = ((rect.top + rect.bottom) / 2) - win_rect.top
            frac = rel_mid_y / win_h
        else:
            frac = 0.5
        if prefer == "lower" and frac < 0.30:
            continue
        if prefer == "upper" and frac > 0.72:
            continue
        candidates.append((ctrl, count, frac))
    if not candidates and prefer != "any":
        return _sample_table_candidates(win, prefer="any")
    return [item[0] for item in candidates]


def _pick_listview(win, *, prefer: str, purpose: str):
    win_rect = _window_rect(win)
    win_h = max(win_rect.height(), 200) if win_rect else 800
    scored: list[tuple[float, object]] = []
    for ctrl in _sample_table_candidates(win, prefer=prefer):
        try:
            rect = ctrl.rectangle()
            count = int(ctrl.item_count())
        except Exception:
            continue
        if win_rect is not None:
            frac = (((rect.top + rect.bottom) / 2) - win_rect.top) / win_h
        else:
            frac = 0.5
        if purpose == "control":
            score = count + frac * 50
        else:
            score = count - frac * 10
        scored.append((score, ctrl))
    if not scored:
        raise RuntimeError(f"{purpose} 시료 표를 찾지 못함 — Autochro 창이 가려지지 않았는지 확인")
    return max(scored, key=lambda item: item[0])[1]


def _control_sync_list(win):
    return _pick_listview(win, prefer="lower", purpose="제어목록")


def _analysis_sample_table(win):
    return _pick_listview(win, prefer="upper", purpose="분석목록")


def _analysis_tree_view(win):
    """분석목록 왼쪽 트리 — 노란 아이콘·시료명."""
    win_rect = _window_rect(win)
    for ctrl in win.descendants(class_name="SysTreeView32"):
        try:
            rect = ctrl.rectangle()
        except Exception:
            continue
        if win_rect is not None:
            rel_left = rect.left - win_rect.left
            if rel_left > win_rect.width() * 0.5:
                continue
        return ctrl
    raise RuntimeError("분석목록 왼쪽 트리 없음")


def _right_click_sample_table(sample_list) -> None:
    rel_x, rel_y = _neutral_list_coords(sample_list)
    sample_list.set_focus()
    sample_list.click_input(button="right", coords=(rel_x, rel_y))
    time.sleep(0.35)


def _click_popup_menu_item(
    matcher: Callable[[str], bool],
    *,
    timeout: float = 5.0,
) -> str:
    _require_pywinauto()
    from pywinauto import Desktop

    deadline = time.time() + timeout
    seen: List[str] = []
    while time.time() < deadline:
        for menu_win in Desktop(backend="win32").windows(class_name="#32768"):
            try:
                wrapper = menu_win.wrapper_object()
                for item in wrapper.menu().items():
                    text = item if isinstance(item, str) else str(item)
                    seen.append(text)
                    if matcher(text):
                        wrapper.menu_item(text).click_input()
                        return text
            except Exception:
                continue
        time.sleep(0.12)
    preview = ", ".join(seen[:10])
    raise RuntimeError(f"컨텍스트 메뉴 항목 없음 (seen: {preview})")


def _click_context_initialize() -> None:
    _click_popup_menu_item(
        lambda t: "초기화" in t and "정량" not in t and "검량" not in t,
    )
    _log("  → 초기화 클릭")


def _click_context_load_analysis_method() -> None:
    _click_popup_menu_item(
        lambda t: "분석방법" in t and "불러" in t,
    )
    _log("  → 분석방법 불러오기 클릭")


def _open_path_in_file_dialog(
    dialog_title_re: str,
    file_path: str,
    *,
    timeout: float = 30.0,
) -> None:
    dlg = _find_window_title_re(dialog_title_re, timeout=timeout)
    if dlg is None:
        raise RuntimeError(f"파일 대화상자 없음 — {dialog_title_re}")
    dlg.set_focus()
    norm_path = os.path.normpath(os.path.abspath(file_path))
    edit = _find_filename_edit(dlg)
    if edit is not None:
        edit.set_focus()
        try:
            edit.set_edit_text(norm_path)
        except Exception:
            from pywinauto.keyboard import send_keys

            send_keys("^a")
            send_keys(norm_path, with_spaces=True)
    else:
        from pywinauto.keyboard import send_keys

        send_keys("^a")
        send_keys(norm_path, with_spaces=True)
    time.sleep(0.4)
    for btn_title in ("열기(&O)", "열기(O)", "열기", "Open", "&Open"):
        try:
            btn = dlg.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=0.3):
                btn.click_input()
                return
        except Exception:
            continue
    from pywinauto.keyboard import send_keys

    send_keys("%o")
    time.sleep(0.3)


def _select_tree_data_name(win, data_name: str) -> str:
    tree = _analysis_tree_view(win)
    candidates: List[str] = []
    try:
        for text in tree.texts():
            line = (text or "").strip()
            if line:
                candidates.append(line)
    except Exception:
        pass
    for line in candidates:
        if tree_label_matches_data_name(line, data_name):
            chosen = line.split(".")[0].strip()
            for select_arg in (chosen, [chosen], line):
                try:
                    tree.select(select_arg)
                    time.sleep(0.25)
                    return chosen
                except Exception:
                    continue
    raise RuntimeError(
        f"분석목록 트리에 제어목록 데이터명 없음: {data_name!r} "
        f"(후보 {len(candidates)}개)"
    )


def _right_click_tree_data_name(win, data_name: str) -> None:
    chosen = _select_tree_data_name(win, data_name)
    tree = _analysis_tree_view(win)
    rect = tree.rectangle()
    rel_x = max(24, min(rect.width() // 3, 80))
    rel_y = max(16, min(28, rect.height() // 6))
    tree.click_input(button="right", coords=(rel_x, rel_y))
    time.sleep(0.35)
    _log(f"  트리 우클릭: {chosen}")


def _neutral_list_coords(sample_list) -> tuple[int, int]:
    """
    분석목록 시료 표에서 Ctrl+A 전 클릭 좌표.
    '소유자 ID' 열은 드롭다운 선택 모드 → Ctrl+A 불가.
    '수집 일시' 열과 같은 가로 위치(표 우측)를 사용.
    """
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


def _focus_list_for_ctrl_a(sample_list) -> None:
    """분석목록에서 Ctrl+A 전 — 소유자 ID 드롭다운 회피용 클릭 (수집 일시 열 쪽)."""
    rel_x, rel_y = _neutral_list_coords(sample_list)
    sample_list.set_focus()
    try:
        sample_list.move_mouse_input(coords=(rel_x, rel_y))
        time.sleep(0.12)
    except Exception:
        pass
    sample_list.click_input(coords=(rel_x, rel_y))
    time.sleep(0.25)


def _largest_sample_list(win):
    """하위 호환 — 분석목록 상단 시료 표."""
    return _analysis_sample_table(win)


def _prep_steps_enabled() -> bool:
    return os.getenv("GC1_AUTOCHRO_PREP_STEPS", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def normalize_tree_label(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def tree_label_matches_data_name(tree_line: str, data_name: str) -> bool:
    """분석목록 트리 시료명 ↔ 제어목록 데이터명 (접미사 -상온 등 허용)."""
    line = normalize_tree_label(tree_line)
    name = normalize_tree_label(data_name)
    if not line or not name:
        return False
    if line == name:
        return True
    if line.startswith(name + " ") or line.startswith(name + "-"):
        return True
    compact_line = re.sub(r"\s+", "", line)
    compact_name = re.sub(r"\s+", "", name)
    return compact_line == compact_name or compact_line.startswith(compact_name)


def resolve_analysis_method_mtd_path(data_name: str) -> str:
    """바탕화면(또는 AUTOCHRO_ANALYSIS_METHOD_DIR) 의 {YYYYMMDD} 분석방법.MTD"""
    compact = re.sub(r"\s+", "", (data_name or "").strip())
    match8 = re.match(r"^(\d{8})", compact)
    if match8:
        date = match8.group(1)
    else:
        match6 = re.match(r"^(\d{6})", compact)
        if not match6:
            raise ValueError(f"데이터명에서 날짜 추출 실패: {data_name!r}")
        date = f"20{match6.group(1)}"
    filename = f"{date} 분석방법.MTD"
    base = os.getenv("AUTOCHRO_ANALYSIS_METHOD_DIR", "").strip()
    if not base:
        base = os.path.join(os.path.expanduser("~"), "Desktop")
    path = os.path.join(os.path.normpath(os.path.expanduser(base)), filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"분석방법 MTD 없음: {path}")
    return path


def _menu_select_by_suffix(win, top_suffix: str, item_text: str) -> None:
    """top_suffix 예: '시료목록', item_text 예: '초기화+정량'."""
    for top in win.menu_items():
        if not isinstance(top, dict):
            continue
        top_text = top.get("text", "")
        if top_suffix not in top_text:
            continue
        for sub in top.get("menu_items", {}).get("menu_items", []):
            sub_text = sub.get("text", "")
            if sub_text == item_text or sub_text.startswith(item_text):
                win.menu_select(f"{top_text}->{sub_text}")
                return
    raise RuntimeError(f"메뉴 없음: {top_suffix} -> {item_text}")


def _listview_item_count(ctrl) -> int:
    try:
        return max(0, int(ctrl.item_count()))
    except Exception:
        return 0


def _autochro_eye_enabled(cfg: AutochroConfig) -> bool:
    from gc1_runtime.layer3_eye_guide import autochro_eye_enabled

    return autochro_eye_enabled(dry_run=cfg.dry_run)


def _make_step_eye(win, cfg: AutochroConfig):
    if not _autochro_eye_enabled(cfg):
        return None
    from gc1_runtime.layer3_eye_guide import AutochroStepEye

    return AutochroStepEye.from_window_rect(win.rectangle(), log_fn=_log)


def step_sync_control_to_analysis(win, cfg: AutochroConfig) -> None:
    _log("제어목록 탭 -> 시료 더블클릭 -> 분석목록")
    if cfg.dry_run:
        return
    from gc1_runtime.layer0_sync import evaluate_sync_post_check, sync_double_click_coords

    eye = _make_step_eye(win, cfg)
    if eye:
        eye.scan_between("P1.start", "control_sample_table", task_id="eye_before_control_sync")
    _select_control_tab(win)
    sample_list = _control_sync_list(win)
    control_count = _listview_item_count(sample_list)
    sample_list.set_focus()
    sample_list.click_input()
    rect = sample_list.rectangle()
    fallback = sync_double_click_coords(rect.width(), rect.height())
    if eye:
        rel_x, rel_y = eye.guided_sync_double_click(sample_list, fallback_rel=fallback)
    else:
        rel_x, rel_y = fallback
        try:
            sample_list.move_mouse_input(coords=(rel_x, rel_y))
            time.sleep(0.25)
        except Exception:
            pass
    sample_list.double_click_input(coords=(rel_x, rel_y))
    time.sleep(1.5)
    if eye:
        eye.scan_between("P1.after_dclick", "top_sample_table")
    _select_analysis_tab(win)
    if not _on_analysis_tab(win):
        raise RuntimeError("분석목록 탭 전환 실패 - Autochro 창 상태 확인")
    analysis_count = _listview_item_count(_analysis_sample_table(win))
    post = evaluate_sync_post_check(control_count, analysis_count)
    if not post.ok:
        raise RuntimeError(
            f"{post.operator_hint} "
            f"(제어목록 {post.control_item_count}행, 분석목록 {post.analysis_item_count}행)"
        )
    _log(
        f"제어목록->분석목록 동기화 OK - "
        f"제어 {post.control_item_count}행 / 분석 {post.analysis_item_count}행"
    )
    if eye:
        eye.checkpoint("P1.after_sync", "eye_after_sync_analysis_rows")


def step_context_initialize_samples(win, cfg: AutochroConfig) -> None:
    """분석목록 시료 표 우클릭 -> 초기화 (적분·초기화+정량 아님)."""
    _log("시료 표 우클릭 -> 초기화")
    if cfg.dry_run:
        return
    eye = _make_step_eye(win, cfg)
    _select_analysis_tab(win)
    sample_list = _analysis_sample_table(win)
    if eye:
        try:
            eye.guided_right_click_then_menu(sample_list, "초기화", forbid=("정량", "검량"))
        except Exception as ocr_exc:
            _log(f"OCR menu fail - pywinauto fallback: {ocr_exc}")
            rel_x, rel_y = _neutral_list_coords(sample_list)
            eye.move_mouse_on_list(sample_list, rel_x, rel_y)
            sample_list.click_input(button="right", coords=(rel_x, rel_y))
            time.sleep(0.35)
            _click_context_initialize()
        eye.checkpoint("P3.after_init", "eye_after_context_init")
    else:
        _right_click_sample_table(sample_list)
        _click_context_initialize()
    time.sleep(0.8)


def step_load_analysis_method(win, cfg: AutochroConfig, data_name: str) -> None:
    """왼쪽 트리 시료명 우클릭 -> 분석방법 불러오기 -> MTD."""
    mtd_path = resolve_analysis_method_mtd_path(data_name)
    _log(f"분석방법 MTD: {os.path.basename(mtd_path)}")
    if cfg.dry_run:
        return
    eye = _make_step_eye(win, cfg)
    if eye:
        eye.scan_between("P4.before_tree", "left_analysis_tree")
    _select_analysis_tab(win)
    _right_click_tree_data_name(win, data_name)
    if eye:
        eye.scan_between("P4.after_tree_menu", "context_menu_popup")
    _click_context_load_analysis_method()
    _open_path_in_file_dialog(r"분석방법 불러오기", mtd_path, timeout=cfg.dialog_wait_sec)
    time.sleep(2.0)


def step_select_all_samples(win, cfg: AutochroConfig) -> None:
    _log("시료 전체 선택 (Ctrl+A)")
    if cfg.dry_run:
        return
    eye = _make_step_eye(win, cfg)
    _select_analysis_tab(win)
    sample_list = _analysis_sample_table(win)
    from pywinauto.keyboard import send_keys

    if eye:
        rel_x, rel_y = eye.guided_focus_for_ctrl_a(sample_list)
        sample_list.click_input(coords=(rel_x, rel_y))
        time.sleep(0.2)
    else:
        _focus_list_for_ctrl_a(sample_list)
    send_keys("^a")
    time.sleep(0.5)
    if eye:
        eye.guided_after_ctrl_a()


def step_initialize_quantify(win, cfg: AutochroConfig) -> None:
    _log("시료목록 -> 초기화+정량")
    if cfg.dry_run:
        return
    eye = _make_step_eye(win, cfg)
    if eye:
        eye.scan_between("P6.before_quantify", "bottom_peak_table_fine")
    _select_analysis_tab(win)
    try:
        _menu_select_by_suffix(win, "시료목록", "초기화+정량")
    except Exception as exc:
        try:
            win.menu_select("시료목록(T)->초기화+정량")
        except Exception as exc2:
            raise RuntimeError(f"초기화+정량 메뉴 실행 실패: {exc2}") from exc
    _log(f"적분 대기 ({cfg.quantify_wait_sec}초 이내)...")
    time.sleep(3.0)
    deadline = time.time() + cfg.quantify_wait_sec
    while time.time() < deadline:
        if not _find_window_title_re(r"(적분|정량|처리|Progress|진행|Printing)", timeout=0.5):
            if time.time() > deadline - cfg.quantify_wait_sec + 5:
                break
        time.sleep(1.0)


def step_print_pdf(win, cfg: AutochroConfig) -> None:
    _log("분석목록 -> 인쇄 (Ctrl+P)")
    if cfg.dry_run:
        return
    from pywinauto.keyboard import send_keys

    eye = _make_step_eye(win, cfg)
    _select_analysis_tab(win)
    sample_list = _analysis_sample_table(win)
    if eye:
        rel_x, rel_y = eye.guided_focus_for_ctrl_a(sample_list)
        sample_list.click_input(coords=(rel_x, rel_y))
        time.sleep(0.2)
    else:
        _focus_list_for_ctrl_a(sample_list)
    win.set_focus()
    send_keys("^a")
    time.sleep(0.3)
    send_keys("^p")
    time.sleep(1.0)
    _confirm_print_dialog(cfg)
    _wait_for_printing(cfg)


def _find_window_title_re(pattern: str, timeout: float = 2.0):
    _require_pywinauto()
    from pywinauto import findwindows

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            handles = findwindows.find_windows(title_re=pattern)
            if handles:
                from pywinauto import Application

                app = Application(backend="win32").connect(handle=handles[0])
                return app.window(handle=handles[0])
        except Exception:
            pass
        time.sleep(0.3)
    return None


def _confirm_print_dialog(cfg: AutochroConfig) -> None:
    dlg = _find_window_title_re(r"인쇄|Print", timeout=cfg.dialog_wait_sec)
    if dlg is None:
        from pywinauto.keyboard import send_keys

        send_keys("{ENTER}")
        return
    _log("인쇄 대화상자 확인 클릭")
    for btn_title in ("확인", "OK", "&OK"):
        try:
            dlg.child_window(title=btn_title, class_name="Button").click_input()
            return
        except Exception:
            continue
    dlg.type_keys("{ENTER}")


def _wait_for_printing(cfg: AutochroConfig) -> None:
    _log("PDF 저장 대화상자 대기...")
    deadline = time.time() + cfg.print_wait_sec
    while time.time() < deadline:
        save_dlg = _find_window_title_re(r"다른 이름으로 PDF 저장|PDF 저장|Save As", timeout=0.3)
        if save_dlg is not None:
            _log("PDF 저장 대화상자 감지")
            return
        time.sleep(0.5)
    _log("저장 대화상자 미감지 - 저장 단계에서 재시도")


def _hancom_progress_text(win) -> Optional[str]:
    page_re = re.compile(r"(\d+)\s*/\s*(\d+)\s*페이지")
    gen_re = re.compile(r"(\d+)\s*/\s*(\d+)\s*페이지를\s*생성")
    try:
        for ctrl in win.descendants(class_name="Static"):
            text = (ctrl.window_text() or "").strip()
            if page_re.search(text) or gen_re.search(text):
                return text
        for ctrl in win.descendants():
            text = (ctrl.window_text() or "").strip()
            if page_re.search(text) or gen_re.search(text):
                return text
    except Exception:
        pass
    return None


def _hancom_is_complete(win) -> bool:
    try:
        for ctrl in win.descendants(class_name="Static"):
            text = (ctrl.window_text() or "").strip()
            if "성공적으로 변환을 완료" in text or "변환을 완료" in text or "successfully" in text.lower():
                return True
    except Exception:
        pass
    return False


def _find_all_hancom_pdf_windows() -> list:
    _require_pywinauto()
    from pywinauto import Application, findwindows

    windows = []
    try:
        handles = findwindows.find_windows(title_re=r"한컴 PDF|Hancom PDF")
    except Exception:
        handles = []
    for handle in handles:
        try:
            app = Application(backend="win32").connect(handle=handle)
            windows.append(app.window(handle=handle))
        except Exception:
            continue
    return windows


def _hancom_close_button_enabled(win) -> bool:
    for btn_title in ("닫기(&C)", "닫기(C)", "닫기", "Close", "&Close"):
        try:
            btn = win.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=0.2) and btn.is_enabled():
                return True
        except Exception:
            continue
    return False


def _close_hancom_window(win) -> bool:
    """닫기(&C)만 클릭 — 열기(O)는 절대 클릭하지 않음."""
    for btn_title in ("닫기(&C)", "닫기(C)", "닫기", "Close", "&Close"):
        try:
            btn = win.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=0.3) and btn.is_enabled():
                btn.click_input()
                time.sleep(0.3)
                return True
        except Exception:
            continue
    return False


def close_all_hancom_pdf_windows() -> int:
    """열린 한컴 PDF 완료 창을 모두 닫기 (닫기만)."""
    closed = 0
    for win in _find_all_hancom_pdf_windows():
        if _hancom_is_complete(win) or _hancom_close_button_enabled(win):
            if _close_hancom_window(win):
                closed += 1
    return closed


def _wait_and_close_all_hancom_pdf(cfg: AutochroConfig) -> None:
    """저장+덮어쓰기 후 한컴 PDF 변환 대기 → 완료 창마다 닫기 → 창 0개까지 반복."""
    _log(f"한컴 PDF 생성 대기 (최대 {cfg.hancom_wait_sec}초)...")
    deadline = time.time() + cfg.hancom_wait_sec
    seen = False
    last_progress = ""
    while time.time() < deadline:
        windows = _find_all_hancom_pdf_windows()
        if not windows:
            if seen:
                _log("한컴 PDF 모든 창 닫힘")
                return
            time.sleep(0.5)
            continue

        seen = True
        converting = False
        for win in windows:
            if _hancom_is_complete(win):
                _log("한컴 PDF 변환 완료 — 닫기 클릭")
                _close_hancom_window(win)
            elif _hancom_close_button_enabled(win):
                _log("한컴 PDF 완료 창 — 닫기 클릭")
                _close_hancom_window(win)
            else:
                converting = True
                progress = _hancom_progress_text(win)
                if progress and progress != last_progress:
                    _log(f"한컴 PDF 진행: {progress}")
                    last_progress = progress

        if not _find_all_hancom_pdf_windows():
            _log("한컴 PDF 모든 창 닫힘")
            return
        if converting:
            time.sleep(0.5)
            continue
        time.sleep(0.3)

    remaining = _find_all_hancom_pdf_windows()
    if remaining:
        _log(f"한컴 PDF 대기 시간 초과 — 남은 창 {len(remaining)}개 닫기 시도")
        for win in remaining:
            if _hancom_is_complete(win) or _hancom_close_button_enabled(win):
                _close_hancom_window(win)
    else:
        _log("한컴 PDF 대기 시간 초과 - 파일 생성 여부 확인으로 진행")


def _find_filename_edit(dlg):
    edits = dlg.descendants(class_name="Edit")
    for edit in edits:
        text = edit.window_text() or ""
        if ".pdf" in text.lower() or text.strip():
            return edit
    return edits[0] if edits else None


def _confirm_overwrite_if_present(timeout: float = 5.0) -> bool:
    """동일 파일명 덮어쓰기 확인창 → 예(Y) 클릭."""
    dlg = _find_window_title_re(
        r"다른 이름으로 저장 확인|Confirm Save As|덮어쓰|Replace",
        timeout=timeout,
    )
    if dlg is None:
        return False
    _log("덮어쓰기 확인 → 예(Y) 클릭")
    dlg.set_focus()
    for btn_title in ("예(&Y)", "예(Y)", "예", "Yes", "&Yes", "OK"):
        try:
            dlg.child_window(title=btn_title, class_name="Button").click_input()
            time.sleep(0.3)
            return True
        except Exception:
            continue
    from pywinauto.keyboard import send_keys

    send_keys("%y")
    time.sleep(0.3)
    return True


def step_save_pdf(cfg: AutochroConfig, pdf_path: str) -> None:
    _log(f"5/5 PDF 저장: {pdf_path}")
    if cfg.dry_run:
        return
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    dlg = _find_window_title_re(
        r"다른 이름으로 PDF 저장|PDF 저장|Save As",
        timeout=max(cfg.dialog_wait_sec, 120),
    )
    if dlg is None:
        raise RuntimeError("PDF 저장 대화상자를 찾지 못함")
    dlg.set_focus()
    filename = os.path.basename(pdf_path)
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
    edit = _find_filename_edit(dlg)
    if edit is not None:
        edit.set_focus()
        try:
            edit.set_edit_text(stem)
        except Exception:
            from pywinauto.keyboard import send_keys

            send_keys("^a")
            send_keys(stem, with_spaces=True)
    else:
        from pywinauto.keyboard import send_keys

        send_keys("^a")
        send_keys(stem, with_spaces=True)
    time.sleep(0.5)
    save_clicked = False
    for btn_title in ("저장(&S)", "저장(S)", "저장", "Save", "&Save"):
        try:
            btn = dlg.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=0.3):
                btn.click_input()
                save_clicked = True
                break
        except Exception:
            continue
    if not save_clicked:
        from pywinauto.keyboard import send_keys

        send_keys("%s")
        save_clicked = True
    if not save_clicked:
        raise RuntimeError("PDF 저장 버튼 클릭 실패")
    _confirm_overwrite_if_present(timeout=3.0)
    _wait_and_close_all_hancom_pdf(cfg)
    from gc_gc1 import wait_for_pdf_file_ready

    settle_sec = _env_int("GC1_PDF_READY_WAIT_SEC", 90)
    if wait_for_pdf_file_ready(
        pdf_path,
        max_wait_sec=float(settle_sec),
        only_if_recent_sec=None,
        log_fn=_log,
    ):
        _log("PDF 저장·잠금 해제 완료")
        return
    folder = os.path.dirname(pdf_path)
    recent = sorted(glob.glob(os.path.join(folder, "*.pdf")), key=os.path.getmtime, reverse=True)
    if recent and time.time() - os.path.getmtime(recent[0]) < 120:
        alt = recent[0]
        if wait_for_pdf_file_ready(
            alt,
            max_wait_sec=float(settle_sec),
            only_if_recent_sec=None,
            log_fn=_log,
        ):
            _log(f"PDF 저장됨(이름 확인): {alt}")
            return
    raise RuntimeError(
        f"PDF 파일 미생성 또는 잠금 해제 실패 — {settle_sec}초 후에도 열 수 없음: {pdf_path}"
    )


def _gc1_use_runtime() -> bool:
    """Ω.A.B.CFG.15 — 기본 0: 기존 step_* 경로. 1: ``gc1_runtime.layer4_job`` (T61)."""
    return os.getenv("GC1_USE_RUNTIME", "0").strip().lower() in ("1", "true", "yes")


def run_autochro_export(
    excel_output_dir: str,
    state_path: str,
    force: bool = False,
) -> Tuple[bool, Optional[str], str]:
    """
    Autochro UI 로 PDF 내보내기.

    Returns:
        (ok, pdf_path, message)
    """
    if _gc1_use_runtime():
        from gc1_runtime.layer4_job import ExportJobContext, run_autochro_export as _runtime_export

        return _runtime_export(
            excel_output_dir,
            state_path,
            force=force,
            job_ctx=ExportJobContext(
                excel_output_dir=excel_output_dir,
                send_state_path=state_path,
                force=force,
                log_fn=_log,
            ),
        )

    cfg = load_autochro_config(excel_output_dir)
    if not cfg.enabled and not force:
        return False, None, "AUTOCHRO_ENABLED=0"
    if not cfg.crm_path:
        return False, None, "AUTOCHRO_CRM_PATH / AUTOCHRO_DATA_NAME 미설정"
    need, reason = should_export_crm(state_path, cfg.crm_path, force=force)
    if not need and not force:
        return True, None, reason
    _log(f"시작 - {reason}")
    try:
        if cfg.dry_run:
            source = _fallback_data_name(cfg)
            pdf_path = build_export_pdf_path(cfg, data_name_raw=source or None)
            _log(f"PDF 저장 이름: {os.path.basename(pdf_path)}")
            _log("[DRY RUN] UI 단계만 로그")
            for label in (
                "1 제어목록 → 분석목록",
                "2 Ctrl+A → 우클릭 초기화",
                "3 트리 → 분석방법 MTD",
                "4 Ctrl+A → 우클릭 초기화",
                "5 Ctrl+A → 초기화+정량",
                "6 인쇄",
                "7 PDF 저장",
            ):
                _log(label)
            return True, pdf_path, "dry-run"
        stale_closed = close_all_hancom_pdf_windows()
        if stale_closed:
            _log(f"이전 한컴 PDF 완료 창 {stale_closed}개 닫음")
        _, win = connect_main_window(cfg)
        data_name = read_active_control_data_name(win, cfg)
        pdf_path = build_export_pdf_path(cfg, data_name_raw=data_name)
        _log(f"제어목록 데이터명: {data_name}")
        _log(f"PDF 저장 이름: {os.path.basename(pdf_path)}")
        if not force and is_pdf_recently_exported(pdf_path):
            return True, pdf_path, f"방금 PDF 내보냄 — Autochro 재실행 생략 ({pdf_fresh_skip_sec()}초 이내)"
        step_sync_control_to_analysis(win, cfg)
        if _prep_steps_enabled():
            step_select_all_samples(win, cfg)
            step_context_initialize_samples(win, cfg)
            step_load_analysis_method(win, cfg, data_name)
            step_select_all_samples(win, cfg)
            step_context_initialize_samples(win, cfg)
            step_select_all_samples(win, cfg)
        else:
            step_select_all_samples(win, cfg)
        step_initialize_quantify(win, cfg)
        step_print_pdf(win, cfg)
        step_save_pdf(cfg, pdf_path)
        if not os.path.isfile(pdf_path):
            folder_pdfs = sorted(
                glob.glob(os.path.join(cfg.pdf_output_dir, "*.pdf")),
                key=os.path.getmtime,
                reverse=True,
            )
            if folder_pdfs:
                pdf_path = folder_pdfs[0]
        from gc_gc1 import cleanup_superseded_gc1_files

        removed, pdf_path = cleanup_superseded_gc1_files(cfg.pdf_output_dir, pdf_path, log_fn=_log)
        if removed:
            _log(f"잘못된 출력 파일 {removed}개 정리")
        record_autochro_export(state_path, cfg.crm_path, pdf_path)
        return True, pdf_path, os.path.basename(pdf_path)
    except Exception as exc:
        return False, None, str(exc)


def ensure_gc1_pdf_exported(
    excel_output_dir: str,
    state_path: str,
    force: bool = False,
) -> Tuple[bool, Optional[str], str]:
    """watch/pipeline 진입 — 필요 시 Autochro PDF 생성."""
    if not is_autochro_enabled() and not force:
        return True, None, "Autochro 자동화 비활성"
    skip = os.getenv("GC1_SKIP_AUTOCHRO_EXPORT", "").strip().lower() in ("1", "true", "yes")
    if skip and not force:
        cfg = load_autochro_config(excel_output_dir)
        pdf_path = build_export_pdf_path(cfg, data_name_raw=_fallback_data_name(cfg) or None)
        if is_pdf_recently_exported(pdf_path):
            return True, pdf_path, "watch에서 이미 PDF 내보냄 — 재실행 생략"
    return run_autochro_export(excel_output_dir, state_path, force=force)


def main(argv: Optional[list] = None) -> int:
    from gc_console import setup_console_encoding

    setup_console_encoding()
    from gc_profiles import resolve_profile

    parser = argparse.ArgumentParser(description="Autochro-3000 PDF 자동 내보내기 (GC1)")
    parser.add_argument("--export", action="store_true", help="PDF 내보내기 실행")
    parser.add_argument("--force", action="store_true", help="CRM 변경 여부 무시")
    parser.add_argument("--dry-run", action="store_true", help="UI 조작 없이 로그만")
    args = parser.parse_args(argv)
    if args.dry_run:
        os.environ["AUTOCHRO_DRY_RUN"] = "1"
    if not args.export:
        parser.print_help()
        return 2
    profile = resolve_profile()
    paths = __import__("gc_profiles", fromlist=["paths_for_output_dir"]).paths_for_output_dir(
        profile.excel_output_dir
    )
    os.environ.setdefault("AUTOCHRO_ENABLED", "1")
    ok, pdf_path, msg = run_autochro_export(
        profile.excel_output_dir,
        paths["send_state"],
        force=args.force,
    )
    if ok:
        print(f"[완료] {msg}" + (f" → {pdf_path}" if pdf_path else ""))
        return 0
    print(f"[실패] {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
