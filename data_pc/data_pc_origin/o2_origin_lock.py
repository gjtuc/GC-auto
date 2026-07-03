# -*- coding: utf-8 -*-
"""O2 — Origin 업데이트 직렬화 락."""

from __future__ import annotations

import os
import time

from data_pc_origin.o2_pipeline_lock import pid_alive


class OriginLock:
    def __init__(self, lock_path: str, *, timeout_sec: float = 0.0) -> None:
        self.lock_path = lock_path
        self.timeout_sec = timeout_sec
        self._held = False

    def _clear_stale(self) -> bool:
        if not os.path.isfile(self.lock_path):
            return False
        try:
            with open(self.lock_path, encoding="ascii") as f:
                pid = int(f.read().strip())
        except (OSError, ValueError):
            try:
                os.unlink(self.lock_path)
            except OSError:
                pass
            return True
        if pid_alive(pid):
            return False
        try:
            os.unlink(self.lock_path)
        except OSError:
            pass
        return True

    def try_acquire(self) -> bool:
        if self._held:
            return True
        deadline = time.monotonic() + self.timeout_sec
        while True:
            self._clear_stale()
            try:
                fd = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
            except FileExistsError:
                if self.timeout_sec <= 0 or time.monotonic() >= deadline:
                    return False
                time.sleep(0.05)
                continue
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

    def __enter__(self) -> OriginLock:
        if not self.try_acquire():
            raise RuntimeError(f"origin lock busy: {self.lock_path}")
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()
