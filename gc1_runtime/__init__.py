# -*- coding: utf-8 -*-
"""
gc1_runtime — GC1 장비 PC Autochro export 런타임 (체질 C)

[사용자 관점] `gc_automation.py` / watch 가 Autochro 8단계 UI → PDF → parse → 메일까지
  수행할 때, leaf·게이트·원자 상태를 설계서(``deploy/GC1_RUNTIME_DESIGN.md``)대로 분리한다.
  기본은 ``GC1_USE_RUNTIME=0`` (기존 ``gc_autochro``). 1일 때 본 패키지 위임 (T61).

[규칙 R] Autochro 8단계·MTD·PDF verbatim·GC1 trim·PC 분리 — **변경 금지** (설계 §Ω-1).

레이어 의존 (§0-6 — **위는 아래만 import**):

  L8 표면 (gc_automation CLI, error_handler)
    → L7 세션 (watch, force)
      → L6 잡 (parse, trim, clean, mail) — 기존 gc_gc1·gc_pipeline
        → L5 페이즈 오케스트레이션
          → L4 원자 (P0~P9 atoms)
            → L3 액추에이터 (H/E/F/W)
              → L2 게이트 (G-EX, G-ATOM)
                → L1 팩트 (stem, path, fresh)
                  → L0 프로브 (WIN, TAB, DN, SCR, …)
                    → B 지하 (IDENT, HOST, CFG, STATE, CLK)

타워 B(은규 data_pc)는 SMTP xlsx 로만 접점. ``gc1_runtime`` 은 **GC1 장비 PC 전용**.

모듈 골격 (T20): ``layer0`` … ``layer4`` — 이후 T21+ 에서 leaf 구현 모듈 추가.
"""

from gc1_runtime import layer0, layer1, layer2, layer3, layer4
from gc1_runtime.layer0_config import ConfigReader, Gc1RuntimeConfig, load_gc1_runtime_config
from gc1_runtime.layer0_probes import DisplayMetrics, HostProbe, read_platform, read_python_bitness
from gc1_runtime.layer1_state import AtomRecord, AtomStatus, JobPaths, JobState, StateStore
from gc1_runtime.layer0_win import WinProbe, WinProbeResult, WindowRect, score_autochro_window
from gc1_runtime.layer2_gates import ExportGateInput, GateAction, GateEvaluator, GateVerdict

__all__ = [
    "AtomRecord",
    "AtomStatus",
    "ConfigReader",
    "DisplayMetrics",
    "ExportGateInput",
    "GateAction",
    "GateEvaluator",
    "GateVerdict",
    "Gc1RuntimeConfig",
    "HostProbe",
    "JobPaths",
    "JobState",
    "StateStore",
    "WinProbe",
    "WinProbeResult",
    "WindowRect",
    "score_autochro_window",
    "layer0",
    "layer1",
    "layer2",
    "layer3",
    "layer4",
    "load_gc1_runtime_config",
    "read_platform",
    "read_python_bitness",
]
