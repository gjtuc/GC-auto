# -*- coding: utf-8 -*-
"""
L2-lock — 파이프라인 단일 실행 락.

  L2-L1  lock 파일 O_CREAT|O_EXCL
  L2-L2  stale 판정 — 파일 안 PID 가 죽었으면 제거
  L2-L3  release — 정상 종료 시 삭제
"""

from __future__ import annotations

import os

from data_pc_runtime.layer0_probes import PidProbe


class PipelineLock:
    def __init__(self, lock_path: str) -> None:
        self.lock_path = lock_path
        self._held = False

    def try_acquire(self) -> bool:
        if self._held:
            return True
        if self._clear_stale():
            pass
        try:
            fd = os.open(
                self.lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except FileExistsError:
            return False
        try:
            os.write(fd, str(os.getpid()).encode("ascii"))
        finally:
            os.close(fd)
        self._held = True
        return True

    def release(self) -> None:
        if not self._held:
            return
        try:
            os.unlink(self.lock_path)
        except OSError:
            pass
        self._held = False

    def __enter__(self) -> PipelineLock:
        if not self.try_acquire():
            raise RuntimeError(f"pipeline lock busy: {self.lock_path}")
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()

    def _clear_stale(self) -> bool:
        if not os.path.isfile(self.lock_path):
            return False
        try:
            with open(self.lock_path, encoding="ascii") as f:
                raw = f.read().strip()
            pid = int(raw)
        except (OSError, ValueError):
            try:
                os.unlink(self.lock_path)
            except OSError:
                pass
            return True
        if PidProbe.alive(pid):
            return False
        try:
            os.unlink(self.lock_path)
        except OSError:
            pass
        return True
