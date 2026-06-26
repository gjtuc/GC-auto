# -*- coding: utf-8 -*-
"""Gate registry — DAG, sibling order, rollups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Sequence

GateFn = Callable[[], None]


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    run: GateFn
    depends: FrozenSet[str] = frozenset()
    layer: str = "O0"


O0_K_GATES: List[str] = [
    "O0-K-01-a-1",
    "O0-K-01-b-1",
    "O0-K-01-c-1",
    "O0-K-01-d-1",
    "O0-K-01-e-1",
    "O0-K-01-f-1",
    "O0-K-01-g-1",
    "O0-K-02-a-1",
    "O0-K-02-b-1",
]

O0_I_GATES: List[str] = [
    "O0-I-01-a-1",
    "O0-I-01-b-1",
    "O0-I-01-c-1",
    "O0-I-01-d-1",
    "O0-I-01-e-1",
    "O0-I-01-f-1",
    "O0-I-01-g-1",
    "O0-I-02-a-1",
    "O0-I-02-b-1",
]

O0_C_GATES: List[str] = [
    "O0-C-01-a-1",
    "O0-C-01-b-1",
    "O0-C-01-c-1",
    "O0-C-01-d-1",
    "O0-C-01-e-1",
    "O0-C-02-a-1",
    "O0-C-02-b-1",
    "O0-C-02-c-1",
    "O0-C-02-d-1",
    "O0-C-02-e-1",
    "O0-C-03-a-1",
]

O0_S_GATES: List[str] = [
    "O0-S-01-a-1",
    "O0-S-01-b-1",
    "O0-S-01-c-1",
    "O0-S-01-d-1",
    "O0-S-02-a-1",
    "O0-S-02-b-1",
    "O0-S-02-c-1",
    "O0-S-03-a-1",
    "O0-S-03-b-1",
    "O0-S-04-a-1",
    "O0-S-04-b-1",
    "O0-S-05-a-1",
    "O0-S-05-b-1",
    "O0-S-05-c-1",
    "O0-S-06-a-1",
    "O0-S-06-b-1",
]

O0_M_GATES: List[str] = [
    "O0-M-01-a-1",
    "O0-M-01-b-1",
    "O0-M-01-c-1",
    "O0-M-02-a-1",
    "O0-M-02-b-1",
    "O0-M-02-c-1",
    "O0-M-02-d-1",
    "O0-M-02-e-1",
    "O0-M-03-a-1",
    "O0-M-03-b-1",
]

O0_T_GATES: List[str] = [
    "O0-T-01-a-1",
    "O0-T-01-b-1",
    "O0-T-02-a-1",
    "O0-T-02-b-1",
    "O0-T-03-a-1",
    "O0-T-04-a-1",
]

O0_IMPLEMENTATION_ORDER: List[str] = (
    O0_K_GATES + O0_I_GATES + O0_C_GATES + O0_S_GATES + O0_M_GATES + O0_T_GATES
)

O1_P_GATES: List[str] = [
    "O1-P-01-a-1",
    "O1-P-01-b-1",
    "O1-P-02-a-1",
    "O1-P-02-b-1",
    "O1-P-03-a-1",
    "O1-P-04-a-1",
    "O1-P-04-b-1",
    "O1-P-04-c-1",
    "O1-P-05-a-1",
    "O1-P-05-b-1",
    "O1-P-06-a-1",
    "O1-P-06-b-1",
    "O1-P-07-a-1",
    "O1-P-07-b-1",
    "O1-P-07-c-1",
]

O1_W_GATES: List[str] = [
    "O1-W-01-a-1",
    "O1-W-01-b-1",
    "O1-W-02-a-1",
    "O1-W-02-b-1",
    "O1-W-03-a-1",
    "O1-W-03-b-1",
    "O1-W-04-a-1",
]

O1_I_GATES: List[str] = [
    "O1-I-01-a-1",
    "O1-I-01-b-1",
    "O1-I-02-a-1",
    "O1-I-02-b-1",
    "O1-I-03-a-1",
]

O1_IMPLEMENTATION_ORDER: List[str] = O1_P_GATES + O1_W_GATES + O1_I_GATES

O1_LAST_GATE = O1_IMPLEMENTATION_ORDER[-1]

O2_E_GATES: List[str] = [
    "O2-E-01-a-1",
    "O2-E-01-b-1",
    "O2-E-02-a-1",
    "O2-E-02-b-1",
    "O2-E-03-a-1",
    "O2-E-04-a-1",
]

O2_L_GATES: List[str] = [
    "O2-L-01-a-1",
    "O2-L-01-b-1",
    "O2-L-01-c-1",
    "O2-L-02-a-1",
    "O2-L-03-a-1",
    "O2-L-04-a-1",
    "O2-L-04-b-1",
    "O2-L-04-c-1",
    "O2-L-05-a-1",
]

O2_G_GATES: List[str] = [
    "O2-G-01-a-1",
    "O2-G-02-a-1",
    "O2-G-03-a-1",
    "O2-G-04-a-1",
    "O2-G-05-a-1",
    "O2-G-06-a-1",
]

O2_IMPLEMENTATION_ORDER: List[str] = O2_E_GATES + O2_L_GATES + O2_G_GATES

O2_LAST_GATE = O2_IMPLEMENTATION_ORDER[-1]

O3_S_GATES: List[str] = [
    "O3-S-01-a-1",
    "O3-S-01-b-1",
    "O3-S-02-a-1",
    "O3-S-03-a-1",
    "O3-S-04-a-1",
    "O3-S-04-b-1",
    "O3-S-05-a-1",
    "O3-S-06-a-1",
]

O3_P_GATES: List[str] = [
    "O3-P-01-a-1",
    "O3-P-02-a-1",
    "O3-P-03-a-1",
    "O3-P-04-a-1",
]

O3_IMPLEMENTATION_ORDER: List[str] = O3_S_GATES + O3_P_GATES

O3_LAST_GATE = O3_IMPLEMENTATION_ORDER[-1]

O4_V_GATES: List[str] = [
    "O4-V-01-a-1",
]

O4_O_GATES: List[str] = [
    "O4-O-01-a-1",
    "O4-O-01-b-1",
    "O4-O-01-c-1",
    "O4-O-02-a-1",
]

O4_S_GATES: List[str] = [
    "O4-S-01-a-1",
    "O4-S-02-a-1",
]

O4_R_GATES: List[str] = [
    "O4-R-01-a-1",
]

O4_IMPLEMENTATION_ORDER: List[str] = (
    O4_V_GATES + O4_O_GATES + O4_S_GATES + O4_R_GATES
)

O4_LAST_GATE = O4_IMPLEMENTATION_ORDER[-1]

O5_I01_GATES: List[str] = [
    "O5-I-01-a-1",
    "O5-I-01-b-1",
    "O5-I-01-c-1",
    "O5-I-01-d-1",
    "O5-I-01-e-1",
    "O5-I-01-f-1",
    "O5-I-01-g-1",
    "O5-I-01-h-1",
    "O5-I-01-i-1",
    "O5-I-01-j-1",
    "O5-I-01-k-1",
    "O5-I-01-l-1",
]

O5_I02_GATES: List[str] = [
    "O5-I-02-a-1",
    "O5-I-02-b-1",
    "O5-I-02-c-1",
    "O5-I-02-d-1",
    "O5-I-02-e-1",
    "O5-I-02-f-1",
    "O5-I-02-g-1",
    "O5-I-02-h-1",
    "O5-I-02-i-1",
    "O5-I-02-j-1",
    "O5-I-02-k-1",
    "O5-I-02-l-1",
]

O5_I_GATES: List[str] = O5_I01_GATES + O5_I02_GATES

O5_T01_GATES: List[str] = [
    "O5-T-01-a-1",
    "O5-T-01-b-1",
    "O5-T-01-c-1",
    "O5-T-01-d-1",
    "O5-T-01-e-1",
]

O5_T02_GATES: List[str] = [
    "O5-T-02-a-1",
    "O5-T-02-b-1",
    "O5-T-02-c-1",
    "O5-T-02-d-1",
    "O5-T-02-e-1",
]

O5_T03_GATES: List[str] = [
    "O5-T-03-a-1",
    "O5-T-03-b-1",
    "O5-T-03-c-1",
    "O5-T-03-d-1",
    "O5-T-03-e-1",
]

O5_T04_GATES: List[str] = [
    "O5-T-04-a-1",
    "O5-T-04-b-1",
    "O5-T-04-c-1",
    "O5-T-04-d-1",
    "O5-T-04-e-1",
    "O5-T-04-f-1",
    "O5-T-04-g-1",
    "O5-T-04-h-1",
    "O5-T-04-i-1",
    "O5-T-04-j-1",
    "O5-T-04-k-1",
    "O5-T-04-l-1",
]

O5_T_GATES: List[str] = (
    O5_T01_GATES + O5_T02_GATES + O5_T03_GATES + O5_T04_GATES
)

O5_M01_GATES: List[str] = [f"O5-M-01-{s}-1" for s in "abcdefghijklmn"]
O5_M02_GATES: List[str] = [f"O5-M-02-{s}-1" for s in "abcdefghijklmn"]
O5_M03_GATES: List[str] = [
    "O5-M-03-a-1",
    "O5-M-03-b-1",
    "O5-M-03-c-1",
    "O5-M-03-d-1",
    "O5-M-03-e-1",
    "O5-M-03-f-1",
    "O5-M-03-g-1",
    "O5-M-03-h-1",
    "O5-M-03-i-1",
    "O5-M-03-j-1",
    "O5-M-03-k-1",
    "O5-M-03-l-1",
    "O5-M-03-m-1",
    "O5-M-03-n-1",
    "O5-M-03-o-1",
    "O5-M-03-p-1",
    "O5-M-03-q-1",
    "O5-M-03-r-1",
]

O5_M04_GATES: List[str] = [f"O5-M-04-{s}-1" for s in "abcdefgh"]

O5_M_GATES: List[str] = (
    O5_M01_GATES + O5_M02_GATES + O5_M03_GATES + O5_M04_GATES
)

O5_IMPLEMENTATION_ORDER: List[str] = (
    list(O5_I_GATES) + list(O5_T_GATES) + list(O5_M_GATES)
)

O5_DEBUG_GATES: List[str] = [
    "O5-DEBUG-01-a-1",
    "O5-DEBUG-02-a-1",
    "O5-DEBUG-03-a-1",
    "O5-DEBUG-04-a-1",
    "O5-DEBUG-05-a-1",
]

O5_E2E_GATES: List[str] = [
    "O5-E2E-01-a-1",
    "O5-E2E-02-a-1",
    "O5-E2E-03-a-1",
]

O5_R_GATES: List[str] = [
    "O5-R-01-a-1",
    "O5-R-02-a-1",
    "O5-R-03-a-1",
    "O5-R-04-a-1",
]

O5_META_IMPLEMENTATION_ORDER: List[str] = list(O5_E2E_GATES) + list(O5_R_GATES)

O5_LAST_CORE_GATE = O5_IMPLEMENTATION_ORDER[-1]
O5_LAST_META_GATE = O5_META_IMPLEMENTATION_ORDER[-1]

O6_S01_GATES: List[str] = [
    "O6-S-01-a-1",
    "O6-S-01-b-1",
]

O6_S02_GATES: List[str] = [
    "O6-S-02-a-1",
    "O6-S-02-b-1",
]

O6_S_GATES: List[str] = list(O6_S01_GATES) + list(O6_S02_GATES)

O6_F01_GATES: List[str] = [
    "O6-F-01-a-1",
    "O6-F-01-b-1",
]

O6_F02_GATES: List[str] = [
    "O6-F-02-a-1",
    "O6-F-02-b-1",
]

O6_F_GATES: List[str] = list(O6_F01_GATES) + list(O6_F02_GATES)

O6_P_GATES: List[str] = [
    "O6-P-01-a-1",
    "O6-P-02-a-1",
    "O6-P-03-a-1",
    "O6-P-04-a-1",
]

O6_I_GATES: List[str] = [
    "O6-I-01-a-1",
    "O6-I-01-b-1",
    "O6-I-02-a-1",
    "O6-I-02-b-1",
]

O6_R_GATES: List[str] = [
    "O6-R-01-a-1",
    "O6-R-01-b-1",
]

O6_IMPLEMENTATION_ORDER: List[str] = (
    list(O6_S_GATES)
    + list(O6_F_GATES)
    + list(O6_P_GATES)
    + list(O6_I_GATES)
    + list(O6_R_GATES)
)

O6_LAST_GATE = O6_IMPLEMENTATION_ORDER[-1]

O7_P_GATES: List[str] = [
    "O7-P-01-a-1",
    "O7-P-01-b-1",
    "O7-P-02-a-1",
]

O7_W_GATES: List[str] = [
    "O7-W-01-a-1",
    "O7-W-01-b-1",
    "O7-W-02-a-1",
    "O7-W-03-a-1",
]

O7_G_GATES: List[str] = [
    "O7-G-01-a-1",
    "O7-G-02-a-1",
]

O7_IMPLEMENTATION_ORDER: List[str] = (
    list(O7_P_GATES) + list(O7_W_GATES) + list(O7_G_GATES)
)

O7_LAST_GATE = O7_IMPLEMENTATION_ORDER[-1]

O8_C_GATES: List[str] = [
    "O8-C-01-a-1",
    "O8-C-02-a-1",
]

O8_J_GATES: List[str] = [
    "O8-J-01-a-1",
    "O8-J-02-a-1",
    "O8-J-03-a-1",
    "O8-J-04-a-1",
    "O8-J-05-a-1",
    "O8-J-06-a-1",
    "O8-J-07-a-1",
    "O8-J-08-a-1",
    "O8-J-09-a-1",
]

O8_IMPLEMENTATION_ORDER: List[str] = list(O8_C_GATES) + list(O8_J_GATES)

O8_LAST_GATE = O8_IMPLEMENTATION_ORDER[-1]

O9_F_GATES: List[str] = [
    "O9-F-01-a-1",
    "O9-F-02-a-1",
    "O9-F-03-a-1",
    "O9-F-04-a-1",
    "O9-F-05-a-1",
]

O9_E2E_GATES: List[str] = [
    "O9-E2E-01-a-1",
    "O9-E2E-02-a-1",
]

O9_P_GATES: List[str] = [
    "O9-P-01-a-1",
    "O9-P-02-a-1",
    "O9-P-03-a-1",
]

O9_L_GATES: List[str] = [
    "O9-L-01-a-1",
    "O9-L-02-a-1",
    "O9-L-03-a-1",
]

O9_IMPLEMENTATION_ORDER: List[str] = (
    list(O9_F_GATES) + list(O9_E2E_GATES) + list(O9_P_GATES)
)

O9_EXTENDED_ORDER: List[str] = list(O9_IMPLEMENTATION_ORDER) + list(O9_L_GATES)

FULL_IMPLEMENTATION_ORDER: List[str] = (
    O0_IMPLEMENTATION_ORDER
    + O1_IMPLEMENTATION_ORDER
    + O2_IMPLEMENTATION_ORDER
    + O3_IMPLEMENTATION_ORDER
    + O4_IMPLEMENTATION_ORDER
    + O5_IMPLEMENTATION_ORDER
    + O5_META_IMPLEMENTATION_ORDER
    + O6_IMPLEMENTATION_ORDER
    + O7_IMPLEMENTATION_ORDER
    + O8_IMPLEMENTATION_ORDER
    + O9_IMPLEMENTATION_ORDER
)

O0_LAST_GATE = O0_IMPLEMENTATION_ORDER[-1]


def _depends_chain(order: Sequence[str], head: Optional[str] = None) -> Dict[str, FrozenSet[str]]:
    deps: Dict[str, FrozenSet[str]] = {}
    prev: Optional[str] = head
    for gid in order:
        deps[gid] = frozenset([prev]) if prev else frozenset()
        prev = gid
    return deps


O0_DEPS = _depends_chain(O0_IMPLEMENTATION_ORDER)
O1_DEPS = _depends_chain(O1_IMPLEMENTATION_ORDER, head=O0_LAST_GATE)
O2_DEPS = _depends_chain(O2_IMPLEMENTATION_ORDER, head=O1_LAST_GATE)
O3_DEPS = _depends_chain(O3_IMPLEMENTATION_ORDER, head=O2_LAST_GATE)
O4_DEPS = _depends_chain(O4_IMPLEMENTATION_ORDER, head=O3_LAST_GATE)
O5_DEPS = _depends_chain(O5_IMPLEMENTATION_ORDER, head=O4_LAST_GATE)
O5_DEBUG_DEPS = _depends_chain(O5_DEBUG_GATES, head=O5_LAST_CORE_GATE)
O5_E2E_DEPS = _depends_chain(O5_E2E_GATES, head=O5_LAST_CORE_GATE)
O5_R_DEPS = _depends_chain(O5_R_GATES, head=O5_E2E_GATES[-1])
O6_DEPS = _depends_chain(O6_IMPLEMENTATION_ORDER, head=O5_LAST_META_GATE)
O7_DEPS = _depends_chain(O7_IMPLEMENTATION_ORDER, head=O6_LAST_GATE)
O8_DEPS = _depends_chain(O8_IMPLEMENTATION_ORDER, head=O7_LAST_GATE)
O9_DEPS = _depends_chain(O9_IMPLEMENTATION_ORDER, head=O8_LAST_GATE)
O9_L_DEPS = _depends_chain(O9_L_GATES, head=O9_IMPLEMENTATION_ORDER[-1])

_O0_O1_PREFIX: List[str] = list(O0_IMPLEMENTATION_ORDER) + list(O1_IMPLEMENTATION_ORDER)
_O0_O1_O2_PREFIX: List[str] = _O0_O1_PREFIX + list(O2_IMPLEMENTATION_ORDER)
_O0_O1_O2_O3_PREFIX: List[str] = _O0_O1_O2_PREFIX + list(O3_IMPLEMENTATION_ORDER)
_O0_O1_O2_O3_O4_PREFIX: List[str] = _O0_O1_O2_O3_PREFIX + list(O4_IMPLEMENTATION_ORDER)
_O0_O1_O2_O3_O4_O5_PREFIX: List[str] = (
    _O0_O1_O2_O3_O4_PREFIX + list(O5_IMPLEMENTATION_ORDER)
)
_O0_O1_O2_O3_O4_O5_META_PREFIX: List[str] = (
    _O0_O1_O2_O3_O4_O5_PREFIX + list(O5_META_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_O6_PREFIX: List[str] = (
    _O0_O1_O2_O3_O4_O5_META_PREFIX + list(O6_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_O7_PREFIX: List[str] = (
    _O0_THROUGH_O6_PREFIX + list(O7_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_O8_PREFIX: List[str] = (
    _O0_THROUGH_O7_PREFIX + list(O8_IMPLEMENTATION_ORDER)
)

ROLLUPS: Dict[str, List[str]] = {
    "O0-L1-K": list(O0_K_GATES),
    "O0-L1-I": list(O0_I_GATES),
    "O0-L1-C": list(O0_C_GATES),
    "O0-L1-S": list(O0_S_GATES),
    "O0-L1-M": list(O0_M_GATES),
    "O0-L1-T": list(O0_T_GATES),
    "O0": list(O0_IMPLEMENTATION_ORDER),
    "O1-P": list(O1_P_GATES),
    "O1-W": list(O1_W_GATES),
    "O1-I": list(O1_I_GATES),
    "O1": list(O1_IMPLEMENTATION_ORDER),
    "O2-E": list(O2_E_GATES),
    "O2-L": list(O2_L_GATES),
    "O2-G": list(O2_G_GATES),
    "O2": list(O2_IMPLEMENTATION_ORDER),
    "O3-S": list(O3_S_GATES),
    "O3-P": list(O3_P_GATES),
    "O3": list(O3_IMPLEMENTATION_ORDER),
    "O4-V": list(O4_V_GATES),
    "O4-O": list(O4_O_GATES),
    "O4-S": list(O4_S_GATES),
    "O4-R": list(O4_R_GATES),
    "O4": list(O4_IMPLEMENTATION_ORDER),
    "O5-L2-I01": list(O5_I01_GATES),
    "O5-L2-I02": list(O5_I02_GATES),
    "O5-L1-I": list(O5_I_GATES),
    "O5-I": list(O5_I_GATES),
    "O5-L2-T01": list(O5_T01_GATES),
    "O5-L2-T02": list(O5_T02_GATES),
    "O5-L2-T03": list(O5_T03_GATES),
    "O5-L2-T04": list(O5_T04_GATES),
    "O5-L1-T": list(O5_T_GATES),
    "O5-T": list(O5_T_GATES),
    "O5-L2-M01": list(O5_M01_GATES),
    "O5-L2-M02": list(O5_M02_GATES),
    "O5-L2-M03": list(O5_M03_GATES),
    "O5-L2-M04": list(O5_M04_GATES),
    "O5-L1-M": list(O5_M_GATES),
    "O5-M": list(O5_M_GATES),
    "O5-DEBUG": list(O5_DEBUG_GATES),
    "O5-E2E": list(O5_E2E_GATES),
    "O5-R": list(O5_R_GATES),
    "O5-META": list(O5_META_IMPLEMENTATION_ORDER),
    "O6-L2-S01": list(O6_S01_GATES),
    "O6-L2-S02": list(O6_S02_GATES),
    "O6-S": list(O6_S_GATES),
    "O6-L2-F01": list(O6_F01_GATES),
    "O6-L2-F02": list(O6_F02_GATES),
    "O6-F": list(O6_F_GATES),
    "O6-P": list(O6_P_GATES),
    "O6-I": list(O6_I_GATES),
    "O6-R": list(O6_R_GATES),
    "O6": list(O6_IMPLEMENTATION_ORDER),
    "O7-P": list(O7_P_GATES),
    "O7-W": list(O7_W_GATES),
    "O7-G": list(O7_G_GATES),
    "O7": list(O7_IMPLEMENTATION_ORDER),
    "O8-C": list(O8_C_GATES),
    "O8-J": list(O8_J_GATES),
    "O8": list(O8_IMPLEMENTATION_ORDER),
    "O9-F": list(O9_F_GATES),
    "O9-E2E": list(O9_E2E_GATES),
    "O9-P": list(O9_P_GATES),
    "O9-L": list(O9_L_GATES),
    "O9": list(O9_IMPLEMENTATION_ORDER),
    "O9-EXT": list(O9_EXTENDED_ORDER),
}

_REGISTRY: Dict[str, GateSpec] = {}


def register_gate(
    gate_id: str,
    run: GateFn,
    *,
    depends: Optional[Sequence[str] | FrozenSet[str]] = None,
    layer: str = "O0",
) -> None:
    if depends is None:
        if gate_id in O0_DEPS:
            dep = O0_DEPS[gate_id]
        elif gate_id in O1_DEPS:
            dep = O1_DEPS[gate_id]
        elif gate_id in O2_DEPS:
            dep = O2_DEPS[gate_id]
        elif gate_id in O3_DEPS:
            dep = O3_DEPS[gate_id]
        elif gate_id in O4_DEPS:
            dep = O4_DEPS[gate_id]
        elif gate_id in O5_DEPS:
            dep = O5_DEPS[gate_id]
        elif gate_id in O5_DEBUG_DEPS:
            dep = O5_DEBUG_DEPS[gate_id]
        elif gate_id in O5_E2E_DEPS:
            dep = O5_E2E_DEPS[gate_id]
        elif gate_id in O5_R_DEPS:
            dep = O5_R_DEPS[gate_id]
        elif gate_id in O6_DEPS:
            dep = O6_DEPS[gate_id]
        elif gate_id in O7_DEPS:
            dep = O7_DEPS[gate_id]
        elif gate_id in O8_DEPS:
            dep = O8_DEPS[gate_id]
        elif gate_id in O9_DEPS:
            dep = O9_DEPS[gate_id]
        elif gate_id in O9_L_DEPS:
            dep = O9_L_DEPS[gate_id]
        else:
            dep = frozenset()
    else:
        dep = frozenset(depends)
    _REGISTRY[gate_id] = GateSpec(gate_id=gate_id, run=run, depends=dep, layer=layer)


def get_gate(gate_id: str) -> GateSpec:
    if gate_id not in _REGISTRY:
        raise KeyError(f"unknown gate: {gate_id}")
    return _REGISTRY[gate_id]


def all_gate_ids() -> List[str]:
    return list(FULL_IMPLEMENTATION_ORDER)


def rollup_gate_ids(rollup_id: str) -> List[str]:
    if rollup_id not in ROLLUPS:
        raise KeyError(f"unknown rollup: {rollup_id}")
    gates = list(ROLLUPS[rollup_id])
    if rollup_id.startswith("O0-"):
        return gates
    if rollup_id == "O0":
        return gates
    if rollup_id.startswith("O1-"):
        return list(O0_IMPLEMENTATION_ORDER) + gates
    if rollup_id == "O1":
        return list(O0_IMPLEMENTATION_ORDER) + list(O1_IMPLEMENTATION_ORDER)
    if rollup_id.startswith("O2-"):
        return _O0_O1_PREFIX + gates
    if rollup_id == "O2":
        return _O0_O1_PREFIX + list(O2_IMPLEMENTATION_ORDER)
    if rollup_id.startswith("O3-"):
        return _O0_O1_O2_PREFIX + gates
    if rollup_id == "O3":
        return _O0_O1_O2_PREFIX + list(O3_IMPLEMENTATION_ORDER)
    if rollup_id.startswith("O4-"):
        return _O0_O1_O2_O3_PREFIX + gates
    if rollup_id == "O4":
        return _O0_O1_O2_O3_PREFIX + list(O4_IMPLEMENTATION_ORDER)
    if rollup_id == "O5-L1-I":
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I_GATES)
    if rollup_id == "O5-L1-T":
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I_GATES) + list(O5_T_GATES)
    if rollup_id == "O5-L1-M":
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_I_GATES)
            + list(O5_T_GATES)
            + list(O5_M_GATES)
        )
    if rollup_id == "O5-I":
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I_GATES)
    if rollup_id == "O5-T":
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I_GATES) + list(O5_T_GATES)
    if rollup_id == "O5-M":
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_I_GATES)
            + list(O5_T_GATES)
            + list(O5_M_GATES)
        )
    if rollup_id == "O5-L2-I01":
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I01_GATES)
    if rollup_id == "O5-L2-I02":
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I_GATES)
    if rollup_id.startswith("O5-L2-T"):
        return _O0_O1_O2_O3_O4_PREFIX + list(O5_I_GATES) + gates
    if rollup_id.startswith("O5-L2-M"):
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_I_GATES)
            + list(O5_T_GATES)
            + gates
        )
    if rollup_id == "O5-DEBUG":
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_IMPLEMENTATION_ORDER)
            + list(O5_DEBUG_GATES)
        )
    if rollup_id == "O5-E2E":
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_IMPLEMENTATION_ORDER)
            + list(O5_E2E_GATES)
        )
    if rollup_id == "O5-R":
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_IMPLEMENTATION_ORDER)
            + list(O5_META_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "O5-META":
        return (
            _O0_O1_O2_O3_O4_PREFIX
            + list(O5_IMPLEMENTATION_ORDER)
            + list(O5_META_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "O6-S":
        return _O0_O1_O2_O3_O4_O5_META_PREFIX + list(O6_S_GATES)
    if rollup_id == "O6-F":
        return _O0_O1_O2_O3_O4_O5_META_PREFIX + list(O6_S_GATES) + list(O6_F_GATES)
    if rollup_id == "O6-P":
        return (
            _O0_O1_O2_O3_O4_O5_META_PREFIX
            + list(O6_S_GATES)
            + list(O6_F_GATES)
            + list(O6_P_GATES)
        )
    if rollup_id == "O6-I":
        return (
            _O0_O1_O2_O3_O4_O5_META_PREFIX
            + list(O6_S_GATES)
            + list(O6_F_GATES)
            + list(O6_P_GATES)
            + list(O6_I_GATES)
        )
    if rollup_id == "O6-R":
        return _O0_O1_O2_O3_O4_O5_META_PREFIX + list(O6_IMPLEMENTATION_ORDER)
    if rollup_id == "O6":
        return _O0_O1_O2_O3_O4_O5_META_PREFIX + list(O6_IMPLEMENTATION_ORDER)
    if rollup_id == "O7-P":
        return _O0_THROUGH_O6_PREFIX + list(O7_P_GATES)
    if rollup_id == "O7-W":
        return _O0_THROUGH_O6_PREFIX + list(O7_P_GATES) + list(O7_W_GATES)
    if rollup_id == "O7-G":
        return _O0_THROUGH_O6_PREFIX + list(O7_IMPLEMENTATION_ORDER)
    if rollup_id == "O7":
        return _O0_THROUGH_O6_PREFIX + list(O7_IMPLEMENTATION_ORDER)
    if rollup_id == "O8-C":
        return _O0_THROUGH_O7_PREFIX + list(O8_C_GATES)
    if rollup_id == "O8-J":
        return _O0_THROUGH_O7_PREFIX + list(O8_IMPLEMENTATION_ORDER)
    if rollup_id == "O8":
        return _O0_THROUGH_O7_PREFIX + list(O8_IMPLEMENTATION_ORDER)
    if rollup_id == "O9-F":
        return _O0_THROUGH_O8_PREFIX + list(O9_F_GATES)
    if rollup_id == "O9-P":
        return _O0_THROUGH_O8_PREFIX + list(O9_IMPLEMENTATION_ORDER)
    if rollup_id == "O9-E2E":
        return _O0_THROUGH_O8_PREFIX + list(O9_F_GATES) + list(O9_E2E_GATES)
    if rollup_id == "O9":
        return _O0_THROUGH_O8_PREFIX + list(O9_IMPLEMENTATION_ORDER)
    if rollup_id == "O9-L":
        return _O0_THROUGH_O8_PREFIX + list(O9_IMPLEMENTATION_ORDER) + list(O9_L_GATES)
    if rollup_id == "O9-EXT":
        return _O0_THROUGH_O8_PREFIX + list(O9_EXTENDED_ORDER)
    if rollup_id.startswith("O9-"):
        return _O0_THROUGH_O8_PREFIX + gates
    if rollup_id.startswith("O8-"):
        return _O0_THROUGH_O7_PREFIX + gates
    if rollup_id.startswith("O7-"):
        return _O0_THROUGH_O6_PREFIX + gates
    if rollup_id.startswith("O6-"):
        return _O0_O1_O2_O3_O4_O5_META_PREFIX + gates
    if rollup_id.startswith("O5-"):
        return _O0_O1_O2_O3_O4_PREFIX + gates
    return gates


def is_registered(gate_id: str) -> bool:
    return gate_id in _REGISTRY


def locked_reason(gate_id: str, passed: FrozenSet[str]) -> Optional[str]:
    spec = get_gate(gate_id)
    missing = [d for d in spec.depends if d not in passed]
    if missing:
        return missing[0]
    return None


def implementation_prefix(gate_id: str) -> List[str]:
    """Run all gates up to and including gate_id (for --gate)."""
    order = FULL_IMPLEMENTATION_ORDER
    idx = order.index(gate_id)
    return list(order[: idx + 1])
