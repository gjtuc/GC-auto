# -*- coding: utf-8 -*-
"""
L2 — 게이트 (Ω.A.L2.*): export 잡 G-EX, 원자 G-ATOM pre/post.

설계: ``deploy/GC1_RUNTIME_DESIGN_PART1_L2.md`` §L2-G-EX, §L2-G-ATOM.
T24: G-EX 전량 + G-ATOM pre/post **stub** (probe 리스트 ∧ 만 평가).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

# ERR 한 줄 — PART1_L2 §ERR (게이트 실패 시 message)
_ERR_MESSAGES: dict[str, str] = {
    "E_IDENT_CROSS_PC": "이 PC에서는 Autochro를 실행하지 않습니다",
    "E_WIN_NONE": "Autochro 창을 찾지 못했습니다. Autochro를 켜 주세요",
    "E_MTD_MISSING": "바탕화면에 분석방법.MTD 가 없습니다",
    "E_PIPELINE_BUSY": "다른 작업이 진행 중입니다",
    "E_PRE_PROBE": "원자 실행 전 조건이 맞지 않습니다",
    "E_POST_PROBE": "원자 실행 후 검증에 실패했습니다",
}


class GateAction(str, Enum):
    """게이트 결과 — RUN 실행, SKIP 조건 미충족(오류 아님), BLOCK 실패."""

    RUN = "run"
    SKIP = "skip"
    BLOCK = "block"


@dataclass(frozen=True)
class ExportGateInput:
    """G-EX 평가 입력 — L0/L1/B-CFG 프로브 결과를 호출부가 모아 전달."""

    autochro_enabled: bool = False
    force: bool = False
    is_data_pc: bool = False
    prep_enabled: bool = True
    autochro_window_handles: int = 0
    mtd_path_exists: bool = True
    crm_export_needed: bool = True
    pipeline_locked: bool = False


@dataclass(frozen=True)
class GateVerdict:
    action: GateAction
    fail_code: str | None = None
    message: str = ""
    gate_id: str | None = None

    @property
    def ok_to_run(self) -> bool:
        return self.action == GateAction.RUN


@dataclass(frozen=True)
class AtomGateInput:
    """G-ATOM pre/post — probe ID는 호출부가 bool 로 해석해 전달 (T62+ 에서 L0 연동)."""

    pre_probes: tuple[bool, ...] = ()
    post_probes: tuple[bool, ...] = ()


class GateEvaluator:
    """Ω.A.L2.GEX + Ω.A.L2.GAT (stub)."""

    def evaluate_export(self, ctx: ExportGateInput) -> GateVerdict:
        """
        G-EX 순서 고정 (PART1_L2):
        G1 enabled|force → G2 IDENT → G3 WIN → G4 MTD(prep) → G5 crm|force → G6 lock.
        """
        # Ω.A.L2.GEX.01
        if not ctx.autochro_enabled and not ctx.force:
            return GateVerdict(
                action=GateAction.SKIP,
                gate_id="Ω.A.L2.GEX.01",
                message="AUTOCHRO_ENABLED=0 and not force",
            )

        # Ω.A.L2.GEX.02
        if ctx.is_data_pc:
            return self._block("Ω.A.L2.GEX.02", "E_IDENT_CROSS_PC")

        # Ω.A.L2.GEX.03
        if ctx.autochro_window_handles < 1:
            return self._block("Ω.A.L2.GEX.03", "E_WIN_NONE")

        # Ω.A.L2.GEX.04 — force 시 prep 없으면 F.02 로 G4 생략과 동일
        if ctx.prep_enabled and not ctx.mtd_path_exists:
            return self._block("Ω.A.L2.GEX.04", "E_MTD_MISSING")

        # Ω.A.L2.GEX.05 — force 시 F.03 crm fresh 생략
        if ctx.crm_export_needed and not ctx.force:
            pass  # need export
        elif not ctx.crm_export_needed and not ctx.force:
            return GateVerdict(
                action=GateAction.SKIP,
                gate_id="Ω.A.L2.GEX.05",
                message="CRM fresh, export not needed",
            )

        # Ω.A.L2.GEX.06
        if ctx.pipeline_locked:
            return self._block("Ω.A.L2.GEX.06", "E_PIPELINE_BUSY")

        # Ω.A.L2.GEX.07
        return GateVerdict(action=GateAction.RUN, gate_id="Ω.A.L2.GEX.07")

    def evaluate_atom_pre(self, probes: Sequence[bool] | AtomGateInput) -> GateVerdict:
        """Ω.A.L2.GAT.PRE.01 — ∧ pre_probe[] (status=running 은 L4 호출부 STW)."""
        flags = probes.pre_probes if isinstance(probes, AtomGateInput) else tuple(probes)
        if not flags or all(flags):
            return GateVerdict(action=GateAction.RUN, gate_id="Ω.A.L2.GAT.PRE.01")
        return self._block("Ω.A.L2.GAT.PRE.01", "E_PRE_PROBE")

    def evaluate_atom_post(self, probes: Sequence[bool] | AtomGateInput) -> GateVerdict:
        """Ω.A.L2.GAT.POST.01 — ∧ post_probe[] (status=ok 은 L4 호출부 STW)."""
        if isinstance(probes, AtomGateInput):
            flags = probes.post_probes
        else:
            flags = tuple(probes)
        if not flags or all(flags):
            return GateVerdict(action=GateAction.RUN, gate_id="Ω.A.L2.GAT.POST.01")
        return self._block("Ω.A.L2.GAT.POST.01", "E_POST_PROBE")

    def should_retry(self, attempt: int, max_attempt: int) -> bool:
        """Ω.A.L2.GAT.RTY.01 — stub."""
        return attempt < max_attempt

    @staticmethod
    def _block(gate_id: str, fail_code: str) -> GateVerdict:
        return GateVerdict(
            action=GateAction.BLOCK,
            fail_code=fail_code,
            message=_ERR_MESSAGES.get(fail_code, fail_code),
            gate_id=gate_id,
        )
