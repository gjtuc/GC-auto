# -*- coding: utf-8 -*-
"""
L3 File 채널 (Ω.A.L3.F.*) + L0-PDF 프로브 (Ω.A.L0.PDF.01~05).

설계 §L3 F.01~F.08 · §L0-PDF · PART3 §PAR.00 — ``gc_gc1.wait_for_pdf_file_ready`` 및
``gc_autochro`` Hancom·저장 대화상자 로직을 **leaf 단위**로 분리 (T42).
WAIT(sleep) 은 호출부·L4 atom; 본 모듈은 injectable clock/sleep 으로 단위 테스트 가능.
"""

from __future__ import annotations

import glob
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from gc1_runtime.layer0_config import read_pdf_ready_wait_sec

ClockFn = Callable[[], float]
SleepFn = Callable[[float], None]
LogFn = Callable[[str], None]
FindWindowsFn = Callable[..., Sequence[int]]
ConnectWindowFn = Callable[[int], Any]

PDF_MAGIC = b"%PDF-"
PDF_READ_CHUNK = 4096  # Ω.A.L0.PDF.03.FS.read4k

SAVE_DIALOG_TITLE_RE = r"다른 이름으로 PDF 저장|PDF 저장|Save As"
OVERWRITE_DIALOG_TITLE_RE = r"다른 이름으로 저장 확인|Confirm Save As|덮어쓰|Replace"
HANCOM_TITLE_RE = r"한컴 PDF|Hancom PDF"

SAVE_BUTTON_TITLES: tuple[str, ...] = ("저장(&S)", "저장(S)", "저장", "Save", "&Save")
OVERWRITE_BUTTON_TITLES: tuple[str, ...] = ("예(&Y)", "예(Y)", "예", "Yes", "&Yes", "OK")
HANCOM_CLOSE_BUTTON_TITLES: tuple[str, ...] = (
    "닫기(&C)",
    "닫기(C)",
    "닫기",
    "Close",
    "&Close",
)

__all__ = [
    "ExportFileRecord",
    "FileActionRecord",
    "FileActuator",
    "HancomWaitResult",
    "PDF_MAGIC",
    "PDF_READ_CHUNK",
    "close_all_hancom_windows",
    "confirm_overwrite_if_present",
    "file_glob_pdfs_sorted",
    "file_makedirs",
    "file_unlink",
    "find_dialog_by_title_re",
    "find_filename_edit",
    "hancom_close_button_enabled",
    "hancom_is_complete",
    "hancom_progress_text",
    "pdf_header_is_valid",
    "pdf_is_locked",
    "pdf_is_readable",
    "pdf_page_count",
    "pdf_path_isfile",
    "pdf_path_mtime",
    "pdf_read_prefix",
    "pdf_stem_from_path",
    "set_filename_in_dialog",
    "wait_and_close_hancom_pdf",
    "wait_for_pdf_file_ready",
]


# ---------------------------------------------------------------------------
# Ω.A.L0.PDF.01~05 — 디스크·잠금·fitz (PAR.00 폴링에서 재사용)
# ---------------------------------------------------------------------------


def pdf_path_isfile(path: str) -> bool:
    """Ω.A.L0.PDF.01.FS.isfile."""
    return os.path.isfile(path)


def pdf_path_mtime(path: str) -> float | None:
    """Ω.A.L0.PDF.02.FS.mtime — 없으면 None."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def pdf_read_prefix(path: str, nbytes: int = PDF_READ_CHUNK) -> bytes | None:
    """Ω.A.L0.PDF.03.FS.read4k — rb 로 최대 nbytes 읽기."""
    try:
        with open(path, "rb") as handle:
            return handle.read(nbytes)
    except OSError:
        return None


def pdf_header_is_valid(prefix: bytes) -> bool:
    """PAR.00.5 — 헤더가 ``%PDF-`` 인지."""
    return len(prefix) >= 5 and prefix[:5] == PDF_MAGIC


def pdf_is_locked(path: str) -> bool:
    """Ω.A.L0.PDF.04.CMP.lock — PermissionError 이면 True(잠김)."""
    try:
        with open(path, "rb"):
            pass
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def pdf_page_count(path: str) -> int | None:
    """Ω.A.L0.PDF.05.FITZ.pages — page_count; 실패 시 None."""
    try:
        import fitz  # pymupdf
    except ImportError:
        return None
    try:
        doc = fitz.open(path)
        count = int(doc.page_count)
        doc.close()
        return count if count > 0 else None
    except Exception:
        return None


def pdf_is_readable(path: str) -> bool:
    """L0-PDF 01~05 조합 — ``gc_gc1._pdf_readable`` 와 동일 의미."""
    prefix = pdf_read_prefix(path, nbytes=5)
    if prefix is None or not pdf_header_is_valid(prefix):
        return False
    return pdf_page_count(path) is not None


def wait_for_pdf_file_ready(
    pdf_path: str,
    *,
    max_wait_sec: float | None = None,
    stable_sec: float = 2.0,
    poll_sec: float = 0.5,
    only_if_recent_sec: float | None = 300,
    log_fn: LogFn | None = None,
) -> bool:
    """
    PAR.00 thin wrapper — ``gc_gc1.wait_for_pdf_file_ready`` 위임.

    max_wait_sec 미지정 시 ``GC1_PDF_READY_WAIT_SEC`` (layer0_config).
    """
    from gc_gc1 import wait_for_pdf_file_ready as _gc_wait

    if max_wait_sec is None:
        max_wait_sec = float(read_pdf_ready_wait_sec())
    return _gc_wait(
        pdf_path,
        max_wait_sec=max_wait_sec,
        stable_sec=stable_sec,
        poll_sec=poll_sec,
        only_if_recent_sec=only_if_recent_sec,
        log_fn=log_fn,
    )


# ---------------------------------------------------------------------------
# Ω.A.L3.F.01~F.03 — 순수 FS
# ---------------------------------------------------------------------------


def file_makedirs(pdf_path: str) -> str:
    """F.01 — PDF 경로의 상위 디렉터리 생성. 반환: 디렉터리 경로."""
    directory = os.path.dirname(os.path.abspath(pdf_path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    return directory


def file_unlink(path: str) -> bool:
    """F.02 — 파일 삭제. 성공 True."""
    try:
        os.unlink(path)
        return True
    except OSError:
        return False


def file_glob_pdfs_sorted(folder: str) -> tuple[str, ...]:
    """F.03 — ``*.pdf`` mtime 내림차순."""
    pattern = os.path.join(folder, "*.pdf")
    paths = glob.glob(pattern)
    paths.sort(key=os.path.getmtime, reverse=True)
    return tuple(paths)


def pdf_stem_from_path(pdf_path: str) -> str:
    """저장 대화상자용 stem — ``.pdf`` 확장자 제거."""
    filename = os.path.basename(pdf_path)
    if filename.lower().endswith(".pdf"):
        return filename[:-4]
    return filename


# ---------------------------------------------------------------------------
# Ω.A.L3.F.04~F.07 — 저장·덮어쓰기 대화상자 (pywinauto wrapper mock 가능)
# ---------------------------------------------------------------------------


def find_dialog_by_title_re(
    pattern: str,
    *,
    find_windows: FindWindowsFn,
    connect_window: ConnectWindowFn,
    timeout: float = 2.0,
    clock: ClockFn | None = None,
    sleep: SleepFn | None = None,
    poll_interval: float = 0.3,
) -> Any | None:
    """F.04 — title_re 로 첫 핸들 연결."""
    now = clock or time.time
    wait = sleep or time.sleep
    deadline = now() + timeout
    while now() < deadline:
        try:
            handles = find_windows(title_re=pattern)
            if handles:
                return connect_window(int(handles[0]))
        except Exception:
            pass
        wait(poll_interval)
    return None


def find_filename_edit(dlg: Any) -> Any | None:
    """F.05 — PDF 저장 대화상자 filename Edit."""
    edits = dlg.descendants(class_name="Edit")
    for edit in edits:
        text = (edit.window_text() or "").strip()
        if ".pdf" in text.lower() or text:
            return edit
    return edits[0] if edits else None


def click_dialog_button(
    dlg: Any,
    button_titles: Sequence[str],
    *,
    exists_timeout: float = 0.3,
) -> bool:
    """F.06/F.07 공통 — Button title 순회 클릭."""
    for btn_title in button_titles:
        try:
            btn = dlg.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=exists_timeout):
                btn.click_input()
                return True
        except Exception:
            continue
    return False


def set_filename_in_dialog(
    dlg: Any,
    stem: str,
    *,
    send_keys_fn: Callable[..., None] | None = None,
    sleep: SleepFn | None = None,
) -> None:
    """F.05 — Edit set_edit_text 또는 ^a + type."""
    wait = sleep or time.sleep
    edit = find_filename_edit(dlg)
    if edit is not None:
        edit.set_focus()
        try:
            edit.set_edit_text(stem)
        except Exception:
            if send_keys_fn is not None:
                send_keys_fn("^a")
                send_keys_fn(stem, with_spaces=True)
    elif send_keys_fn is not None:
        send_keys_fn("^a")
        send_keys_fn(stem, with_spaces=True)
    wait(0.5)


def confirm_overwrite_if_present(
    *,
    find_windows: FindWindowsFn,
    connect_window: ConnectWindowFn,
    timeout: float = 5.0,
    clock: ClockFn | None = None,
    sleep: SleepFn | None = None,
    send_keys_fn: Callable[..., None] | None = None,
    log_fn: LogFn | None = None,
) -> bool:
    """F.07 — 덮어쓰기 확인 → 예(Y). 없으면 False."""
    dlg = find_dialog_by_title_re(
        OVERWRITE_DIALOG_TITLE_RE,
        find_windows=find_windows,
        connect_window=connect_window,
        timeout=timeout,
        clock=clock,
        sleep=sleep,
    )
    if dlg is None:
        return False
    if log_fn:
        log_fn("덮어쓰기 확인 → 예(Y) 클릭")
    dlg.set_focus()
    if click_dialog_button(dlg, OVERWRITE_BUTTON_TITLES):
        wait = sleep or time.sleep
        wait(0.3)
        return True
    if send_keys_fn is not None:
        send_keys_fn("%y")
        wait = sleep or time.sleep
        wait(0.3)
        return True
    return False


# ---------------------------------------------------------------------------
# Hancom PDF — P0/P9 leaf (gc_autochro 동작 분리)
# ---------------------------------------------------------------------------

_HANCOM_PAGE_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*페이지")
_HANCOM_GEN_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*페이지를\s*생성")


def hancom_progress_text(win: Any) -> str | None:
    """한컴 변환 진행 Static 텍스트."""
    try:
        for ctrl in win.descendants(class_name="Static"):
            text = (ctrl.window_text() or "").strip()
            if _HANCOM_PAGE_RE.search(text) or _HANCOM_GEN_RE.search(text):
                return text
        for ctrl in win.descendants():
            text = (ctrl.window_text() or "").strip()
            if _HANCOM_PAGE_RE.search(text) or _HANCOM_GEN_RE.search(text):
                return text
    except Exception:
        pass
    return None


def hancom_is_complete(win: Any) -> bool:
    """변환 완료 Static 감지."""
    try:
        for ctrl in win.descendants(class_name="Static"):
            text = (ctrl.window_text() or "").strip()
            if (
                "성공적으로 변환을 완료" in text
                or "변환을 완료" in text
                or "successfully" in text.lower()
            ):
                return True
    except Exception:
        pass
    return False


def hancom_close_button_enabled(win: Any) -> bool:
    """닫기(&C) 버튼 enabled — 열기(O) 는 사용하지 않음."""
    for btn_title in HANCOM_CLOSE_BUTTON_TITLES:
        try:
            btn = win.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=0.2) and btn.is_enabled():
                return True
        except Exception:
            continue
    return False


def close_hancom_window(win: Any, *, sleep: SleepFn | None = None) -> bool:
    """닫기 버튼만 클릭."""
    wait = sleep or time.sleep
    for btn_title in HANCOM_CLOSE_BUTTON_TITLES:
        try:
            btn = win.child_window(title=btn_title, class_name="Button")
            if btn.exists(timeout=0.3) and btn.is_enabled():
                btn.click_input()
                wait(0.3)
                return True
        except Exception:
            continue
    return False


def close_all_hancom_windows(
    windows: Iterable[Any],
    *,
    sleep: SleepFn | None = None,
) -> int:
    """완료·닫기 가능 창만 닫기. 닫은 개수 반환."""
    closed = 0
    for win in windows:
        if hancom_is_complete(win) or hancom_close_button_enabled(win):
            if close_hancom_window(win, sleep=sleep):
                closed += 1
    return closed


@dataclass(frozen=True)
class HancomWaitResult:
    """Hancom 대기 루프 결과 — StateStore.hancom_windows_seen 등에 사용."""

    all_closed: bool
    windows_seen: int
    timed_out: bool


def wait_and_close_hancom_pdf(
    *,
    hancom_wait_sec: float,
    get_hancom_windows: Callable[[], Sequence[Any]],
    clock: ClockFn | None = None,
    sleep: SleepFn | None = None,
    log_fn: LogFn | None = None,
) -> HancomWaitResult:
    """
    ``gc_autochro._wait_and_close_all_hancom_pdf`` leaf 분리.

    get_hancom_windows: L0-WIN.04 enum → connect 된 wrapper 목록.
    """
    now = clock or time.time
    wait = sleep or time.sleep

    def _log(msg: str) -> None:
        if log_fn:
            log_fn(msg)

    deadline = now() + hancom_wait_sec
    seen = False
    max_seen = 0
    last_progress = ""
    while now() < deadline:
        windows = list(get_hancom_windows())
        if not windows:
            if seen:
                _log("한컴 PDF 모든 창 닫힘")
                return HancomWaitResult(all_closed=True, windows_seen=max_seen, timed_out=False)
            wait(0.5)
            continue

        seen = True
        max_seen = max(max_seen, len(windows))
        converting = False
        for win in windows:
            if hancom_is_complete(win):
                _log("한컴 PDF 변환 완료 — 닫기 클릭")
                close_hancom_window(win, sleep=wait)
            elif hancom_close_button_enabled(win):
                _log("한컴 PDF 완료 창 — 닫기 클릭")
                close_hancom_window(win, sleep=wait)
            else:
                converting = True
                progress = hancom_progress_text(win)
                if progress and progress != last_progress:
                    _log(f"한컴 PDF 진행: {progress}")
                    last_progress = progress

        if not get_hancom_windows():
            _log("한컴 PDF 모든 창 닫힘")
            return HancomWaitResult(all_closed=True, windows_seen=max_seen, timed_out=False)
        if converting:
            wait(0.5)
            continue
        wait(0.3)

    remaining = list(get_hancom_windows())
    if remaining:
        _log(f"한컴 PDF 대기 시간 초과 — 남은 창 {len(remaining)}개 닫기 시도")
        for win in remaining:
            if hancom_is_complete(win) or hancom_close_button_enabled(win):
                close_hancom_window(win, sleep=wait)
        still = list(get_hancom_windows())
        return HancomWaitResult(
            all_closed=not still,
            windows_seen=max(max_seen, len(remaining)),
            timed_out=True,
        )
    _log("한컴 PDF 대기 시간 초과 - 파일 생성 여부 확인으로 진행")
    return HancomWaitResult(all_closed=True, windows_seen=max_seen, timed_out=True)


# ---------------------------------------------------------------------------
# FileActuator — F.01~F.08 묶음 + dry-run 로그
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExportFileRecord:
    """F.08 — 저장 계획·준비 상태 (L4 P9 post_probe 입력)."""

    pdf_path: str
    directory: str
    filename_stem: str
    dir_created: bool = False


@dataclass
class FileActionRecord:
    op: str
    detail: str = ""


@dataclass
class FileActuator:
    """File leaf 묶음 — find/connect/send_keys 주입으로 mock 테스트."""

    log: list[FileActionRecord] = field(default_factory=list)
    find_windows: FindWindowsFn | None = None
    connect_window: ConnectWindowFn | None = None
    send_keys_fn: Callable[..., None] | None = None
    clock: ClockFn | None = None
    sleep: SleepFn | None = None

    def _record(self, op: str, detail: str = "") -> None:
        self.log.append(FileActionRecord(op=op, detail=detail))

    def ensure_pdf_directory(self, pdf_path: str) -> str:
        """F.01."""
        directory = file_makedirs(pdf_path)
        self._record("makedirs", directory)
        return directory

    def glob_pdfs(self, folder: str) -> tuple[str, ...]:
        """F.03."""
        paths = file_glob_pdfs_sorted(folder)
        self._record("glob", folder)
        return paths

    def find_save_dialog(self, timeout: float = 120.0) -> Any | None:
        """F.04 — PDF 저장 대화상자."""
        if self.find_windows is None or self.connect_window is None:
            raise RuntimeError("find_windows/connect_window not configured")
        dlg = find_dialog_by_title_re(
            SAVE_DIALOG_TITLE_RE,
            find_windows=self.find_windows,
            connect_window=self.connect_window,
            timeout=timeout,
            clock=self.clock,
            sleep=self.sleep,
        )
        self._record("find_dialog", SAVE_DIALOG_TITLE_RE)
        return dlg

    def fill_save_filename(self, dlg: Any, pdf_path: str) -> str:
        """F.05."""
        stem = pdf_stem_from_path(pdf_path)
        set_filename_in_dialog(
            dlg,
            stem,
            send_keys_fn=self.send_keys_fn,
            sleep=self.sleep,
        )
        self._record("set_filename", stem)
        return stem

    def click_save(self, dlg: Any) -> bool:
        """F.06."""
        ok = click_dialog_button(dlg, SAVE_BUTTON_TITLES)
        if not ok and self.send_keys_fn is not None:
            self.send_keys_fn("%s")
            ok = True
        self._record("click_save", "ok" if ok else "fail")
        return ok

    def confirm_overwrite(self, timeout: float = 3.0) -> bool:
        """F.07."""
        if self.find_windows is None or self.connect_window is None:
            return False
        ok = confirm_overwrite_if_present(
            find_windows=self.find_windows,
            connect_window=self.connect_window,
            timeout=timeout,
            clock=self.clock,
            sleep=self.sleep,
            send_keys_fn=self.send_keys_fn,
        )
        self._record("confirm_overwrite", "yes" if ok else "skip")
        return ok

    def record_export(self, pdf_path: str, *, dir_created: bool = False) -> ExportFileRecord:
        """F.08 — L1 pdf_path_planned 과 병행 기록용."""
        directory = os.path.dirname(os.path.abspath(pdf_path))
        stem = pdf_stem_from_path(pdf_path)
        rec = ExportFileRecord(
            pdf_path=pdf_path,
            directory=directory,
            filename_stem=stem,
            dir_created=dir_created,
        )
        self._record("record_export", pdf_path)
        return rec

    def wait_pdf_ready(
        self,
        pdf_path: str,
        *,
        max_wait_sec: float | None = None,
        only_if_recent_sec: float | None = None,
        log_fn: LogFn | None = None,
    ) -> bool:
        """PAR.00 wrapper + 로그."""
        ok = wait_for_pdf_file_ready(
            pdf_path,
            max_wait_sec=max_wait_sec,
            only_if_recent_sec=only_if_recent_sec,
            log_fn=log_fn,
        )
        self._record("wait_pdf_ready", "ok" if ok else "timeout")
        return ok
