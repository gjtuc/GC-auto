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

O9_LAST_EXTENDED_GATE = O9_EXTENDED_ORDER[-1]

P0_T_GATES: List[str] = [
    "P0-T-01-a-1",
    "P0-T-02-a-1",
    "P0-T-03-a-1",
    "P0-T-04-a-1",
    "P0-T-05-a-1",
    "P0-T-06-a-1",
]

P0_R_GATES: List[str] = [
    "P0-R-01-a-1",
    "P0-R-02-a-1",
    "P0-R-03-a-1",
    "P0-R-04-a-1",
]

P0_IMPLEMENTATION_ORDER: List[str] = list(P0_T_GATES) + list(P0_R_GATES)

P0_LAST_GATE = P0_IMPLEMENTATION_ORDER[-1]

P1_P_GATES: List[str] = [
    "P1-P-01-a-1",
    "P1-P-02-a-1",
    "P1-P-03-a-1",
    "P1-P-04-a-1",
    "P1-P-05-a-1",
    "P1-P-06-a-1",
    "P1-P-07-a-1",
    "P1-P-08-a-1",
]

P1_IMPLEMENTATION_ORDER: List[str] = list(P1_P_GATES)

P1_LAST_GATE = P1_IMPLEMENTATION_ORDER[-1]

P2_V_GATES: List[str] = [
    "P2-V-01-a-1",
    "P2-V-02-a-1",
]

P2_P_GATES: List[str] = [
    "P2-P-01-a-1",
]

P2_S_GATES: List[str] = [
    "P2-S-01-a-1",
    "P2-S-02-a-1",
]

P2_R_GATES: List[str] = [
    "P2-R-01-a-1",
]

P2_IMPLEMENTATION_ORDER: List[str] = (
    list(P2_V_GATES) + list(P2_P_GATES) + list(P2_S_GATES) + list(P2_R_GATES)
)

P2_LAST_GATE = P2_IMPLEMENTATION_ORDER[-1]

P3_S_GATES: List[str] = [
    "P3-S-01-a-1",
    "P3-S-02-a-1",
    "P3-S-03-a-1",
    "P3-S-04-a-1",
]

P3_IMPLEMENTATION_ORDER: List[str] = list(P3_S_GATES)

P3_LAST_GATE = P3_IMPLEMENTATION_ORDER[-1]

P4_O_GATES: List[str] = [
    "P4-O-01-a-1",
    "P4-O-02-a-1",
]

P4_M_GATES: List[str] = [
    "P4-M-01-a-1",
    "P4-M-02-a-1",
]

P4_R_GATES: List[str] = [
    "P4-R-01-a-1",
    "P4-R-02-a-1",
]

P4_IMPLEMENTATION_ORDER: List[str] = (
    list(P4_O_GATES) + list(P4_M_GATES) + list(P4_R_GATES)
)

P4_LAST_GATE = P4_IMPLEMENTATION_ORDER[-1]

P5_W_GATES: List[str] = [
    "P5-W-01-a-1",
    "P5-W-02-a-1",
    "P5-W-03-a-1",
    "P5-W-04-a-1",
    "P5-W-05-a-1",
]

P5_P_GATES: List[str] = [
    "P5-P-01-a-1",
]

P5_R_GATES: List[str] = [
    "P5-R-01-a-1",
    "P5-R-02-a-1",
    "P5-R-03-a-1",
]

P5_IMPLEMENTATION_ORDER: List[str] = (
    list(P5_W_GATES) + list(P5_P_GATES) + list(P5_R_GATES)
)

P5_LAST_GATE = P5_IMPLEMENTATION_ORDER[-1]

P6_A_GATES: List[str] = [
    "P6-A-01-a-1",
    "P6-A-02-a-1",
    "P6-A-03-a-1",
    "P6-A-04-a-1",
    "P6-A-05-a-1",
]

P6_R_GATES: List[str] = [
    "P6-R-01-a-1",
    "P6-R-02-a-1",
    "P6-R-03-a-1",
]

P6_IMPLEMENTATION_ORDER: List[str] = list(P6_A_GATES) + list(P6_R_GATES)

P7_M_GATES: List[str] = [
    "P7-M-01-a-1",
    "P7-M-02-a-1",
]

P7_R_GATES: List[str] = [
    "P7-R-01-a-1",
    "P7-R-02-a-1",
]

P7_IMPLEMENTATION_ORDER: List[str] = list(P7_M_GATES) + list(P7_R_GATES)

P7_LAST_GATE = P7_IMPLEMENTATION_ORDER[-1]

P8_B_GATES: List[str] = [
    "P8-B-01-a-1",
    "P8-B-02-a-1",
    "P8-B-03-a-1",
    "P8-B-04-a-1",
]

P8_IMPLEMENTATION_ORDER: List[str] = list(P8_B_GATES)

P8_LAST_GATE = P8_IMPLEMENTATION_ORDER[-1]

P9_L_GATES: List[str] = [
    "P9-L-01-a-1",
    "P9-L-02-a-1",
    "P9-L-03-a-1",
    "P9-L-04-a-1",
]

P9_LAST_L_GATE = P9_L_GATES[-1]

P10_F_GATES: List[str] = [
    "P10-F-01-a-1",
    "P10-F-02-a-1",
    "P10-F-03-a-1",
]

P10_M_GATES: List[str] = [
    "P10-M-01-a-1",
    "P10-M-02-a-1",
    "P10-M-03-a-1",
    "P10-M-04-a-1",
]

P10_IMPLEMENTATION_ORDER: List[str] = list(P10_F_GATES) + list(P10_M_GATES)

P11_K_GATES: List[str] = [
    "P11-K-01-a-1",
    "P11-K-02-a-1",
    "P11-K-03-a-1",
    "P11-K-04-a-1",
]

P11_IMPLEMENTATION_ORDER: List[str] = list(P11_K_GATES)

P12_F_GATES: List[str] = [
    "P12-F-01-a-1",
    "P12-F-02-a-1",
    "P12-F-03-a-1",
    "P12-F-04-a-1",
]

P12_IMPLEMENTATION_ORDER: List[str] = list(P12_F_GATES)

P13_I_GATES: List[str] = [
    "P13-I-01-a-1",
    "P13-I-02-a-1",
    "P13-I-03-a-1",
    "P13-I-04-a-1",
]

P13_M_GATES: List[str] = [
    "P13-M-01-a-1",
    "P13-M-02-a-1",
    "P13-M-03-a-1",
    "P13-M-04-a-1",
]

P13_IMPLEMENTATION_ORDER: List[str] = list(P13_I_GATES) + list(P13_M_GATES)

P14_R_GATES: List[str] = [
    "P14-R-01-a-1",
    "P14-R-02-a-1",
    "P14-R-03-a-1",
    "P14-R-04-a-1",
]

P14_J_GATES: List[str] = [
    "P14-J-01-a-1",
    "P14-J-02-a-1",
    "P14-J-03-a-1",
    "P14-J-04-a-1",
]

P14_IMPLEMENTATION_ORDER: List[str] = list(P14_R_GATES) + list(P14_J_GATES)

P15_S_GATES: List[str] = [
    "P15-S-01-a-1",
    "P15-S-02-a-1",
    "P15-S-03-a-1",
    "P15-S-04-a-1",
]

P15_H_GATES: List[str] = [
    "P15-H-01-a-1",
    "P15-H-02-a-1",
    "P15-H-03-a-1",
    "P15-H-04-a-1",
]

P15_IMPLEMENTATION_ORDER: List[str] = list(P15_S_GATES) + list(P15_H_GATES)

P16_W_GATES: List[str] = [
    "P16-W-01-a-1",
    "P16-W-02-a-1",
    "P16-W-03-a-1",
    "P16-W-04-a-1",
]

P16_H_GATES: List[str] = [
    "P16-H-01-a-1",
    "P16-H-02-a-1",
    "P16-H-03-a-1",
    "P16-H-04-a-1",
]

P16_IMPLEMENTATION_ORDER: List[str] = list(P16_W_GATES) + list(P16_H_GATES)

P17_E_GATES: List[str] = [
    "P17-E-01-a-1",
    "P17-E-02-a-1",
    "P17-E-03-a-1",
    "P17-E-04-a-1",
]

P17_H_GATES: List[str] = [
    "P17-H-01-a-1",
    "P17-H-02-a-1",
    "P17-H-03-a-1",
    "P17-H-04-a-1",
]

P17_IMPLEMENTATION_ORDER: List[str] = list(P17_E_GATES) + list(P17_H_GATES)

P18_P_GATES: List[str] = [
    "P18-P-01-a-1",
    "P18-P-02-a-1",
    "P18-P-03-a-1",
    "P18-P-04-a-1",
]

P18_L_GATES: List[str] = [
    "P18-L-01-a-1",
    "P18-L-02-a-1",
    "P18-L-03-a-1",
    "P18-L-04-a-1",
]

P18_IMPLEMENTATION_ORDER: List[str] = list(P18_P_GATES) + list(P18_L_GATES)

P19_V_GATES: List[str] = [
    "P19-V-01-a-1",
    "P19-V-02-a-1",
    "P19-V-03-a-1",
    "P19-V-04-a-1",
]

P19_R_GATES: List[str] = [
    "P19-R-01-a-1",
    "P19-R-02-a-1",
    "P19-R-03-a-1",
    "P19-R-04-a-1",
]

P19_IMPLEMENTATION_ORDER: List[str] = list(P19_V_GATES) + list(P19_R_GATES)

P20_M_GATES: List[str] = [
    "P20-M-01-a-1",
    "P20-M-02-a-1",
    "P20-M-03-a-1",
    "P20-M-04-a-1",
]

P20_H_GATES: List[str] = [
    "P20-H-01-a-1",
    "P20-H-02-a-1",
    "P20-H-03-a-1",
    "P20-H-04-a-1",
]

P20_IMPLEMENTATION_ORDER: List[str] = list(P20_M_GATES) + list(P20_H_GATES)

P21_C_GATES: List[str] = [
    "P21-C-01-a-1",
    "P21-C-02-a-1",
    "P21-C-03-a-1",
    "P21-C-04-a-1",
]

P21_H_GATES: List[str] = [
    "P21-H-01-a-1",
    "P21-H-02-a-1",
    "P21-H-03-a-1",
    "P21-H-04-a-1",
]

P21_IMPLEMENTATION_ORDER: List[str] = list(P21_C_GATES) + list(P21_H_GATES)

P22_A_GATES: List[str] = [
    "P22-A-01-a-1",
    "P22-A-02-a-1",
    "P22-A-03-a-1",
    "P22-A-04-a-1",
]

P22_H_GATES: List[str] = [
    "P22-H-01-a-1",
    "P22-H-02-a-1",
    "P22-H-03-a-1",
    "P22-H-04-a-1",
]

P22_IMPLEMENTATION_ORDER: List[str] = list(P22_A_GATES) + list(P22_H_GATES)

P23_G_GATES: List[str] = [
    "P23-G-01-a-1",
    "P23-G-02-a-1",
    "P23-G-03-a-1",
    "P23-G-04-a-1",
]

P23_H_GATES: List[str] = [
    "P23-H-01-a-1",
    "P23-H-02-a-1",
    "P23-H-03-a-1",
    "P23-H-04-a-1",
]

P23_IMPLEMENTATION_ORDER: List[str] = list(P23_G_GATES) + list(P23_H_GATES)

P24_O_GATES: List[str] = [
    "P24-O-01-a-1",
    "P24-O-02-a-1",
    "P24-O-03-a-1",
    "P24-O-04-a-1",
]

P24_H_GATES: List[str] = [
    "P24-H-01-a-1",
    "P24-H-02-a-1",
    "P24-H-03-a-1",
    "P24-H-04-a-1",
]

P24_IMPLEMENTATION_ORDER: List[str] = list(P24_O_GATES) + list(P24_H_GATES)

P25_N_GATES: List[str] = [
    "P25-N-01-a-1",
    "P25-N-02-a-1",
    "P25-N-03-a-1",
    "P25-N-04-a-1",
]

P25_H_GATES: List[str] = [
    "P25-H-01-a-1",
    "P25-H-02-a-1",
    "P25-H-03-a-1",
    "P25-H-04-a-1",
]

P25_IMPLEMENTATION_ORDER: List[str] = list(P25_N_GATES) + list(P25_H_GATES)

P26_W_GATES: List[str] = [
    "P26-W-01-a-1",
    "P26-W-02-a-1",
    "P26-W-03-a-1",
    "P26-W-04-a-1",
]

P26_H_GATES: List[str] = [
    "P26-H-01-a-1",
    "P26-H-02-a-1",
    "P26-H-03-a-1",
    "P26-H-04-a-1",
]

P26_IMPLEMENTATION_ORDER: List[str] = list(P26_W_GATES) + list(P26_H_GATES)

P27_G_GATES: List[str] = [
    "P27-G-01-a-1",
    "P27-G-02-a-1",
    "P27-G-03-a-1",
    "P27-G-04-a-1",
]

P27_H_GATES: List[str] = [
    "P27-H-01-a-1",
    "P27-H-02-a-1",
    "P27-H-03-a-1",
    "P27-H-04-a-1",
]

P27_IMPLEMENTATION_ORDER: List[str] = list(P27_G_GATES) + list(P27_H_GATES)

P28_M_GATES: List[str] = [
    "P28-M-01-a-1",
    "P28-M-02-a-1",
    "P28-M-03-a-1",
    "P28-M-04-a-1",
]

P28_H_GATES: List[str] = [
    "P28-H-01-a-1",
    "P28-H-02-a-1",
    "P28-H-03-a-1",
    "P28-H-04-a-1",
]

P28_IMPLEMENTATION_ORDER: List[str] = list(P28_M_GATES) + list(P28_H_GATES)

P29_G_GATES: List[str] = [
    "P29-G-01-a-1",
    "P29-G-02-a-1",
    "P29-G-03-a-1",
    "P29-G-04-a-1",
]

P29_H_GATES: List[str] = [
    "P29-H-01-a-1",
    "P29-H-02-a-1",
    "P29-H-03-a-1",
    "P29-H-04-a-1",
]

P29_IMPLEMENTATION_ORDER: List[str] = list(P29_G_GATES) + list(P29_H_GATES)

P30_G_GATES: List[str] = [
    "P30-G-01-a-1",
    "P30-G-02-a-1",
    "P30-G-03-a-1",
    "P30-G-04-a-1",
]

P30_H_GATES: List[str] = [
    "P30-H-01-a-1",
    "P30-H-02-a-1",
    "P30-H-03-a-1",
    "P30-H-04-a-1",
]

P30_IMPLEMENTATION_ORDER: List[str] = list(P30_G_GATES) + list(P30_H_GATES)

P31_M_GATES: List[str] = [
    "P31-M-01-a-1",
    "P31-M-02-a-1",
    "P31-M-03-a-1",
    "P31-M-04-a-1",
]

P31_H_GATES: List[str] = [
    "P31-H-01-a-1",
    "P31-H-02-a-1",
    "P31-H-03-a-1",
    "P31-H-04-a-1",
]

P31_IMPLEMENTATION_ORDER: List[str] = list(P31_M_GATES) + list(P31_H_GATES)

P32_G_GATES: List[str] = [
    "P32-G-01-a-1",
    "P32-G-02-a-1",
    "P32-G-03-a-1",
    "P32-G-04-a-1",
]

P32_H_GATES: List[str] = [
    "P32-H-01-a-1",
    "P32-H-02-a-1",
    "P32-H-03-a-1",
    "P32-H-04-a-1",
]

P32_IMPLEMENTATION_ORDER: List[str] = list(P32_G_GATES) + list(P32_H_GATES)

P33_G_GATES: List[str] = [
    "P33-G-01-a-1",
    "P33-G-02-a-1",
    "P33-G-03-a-1",
    "P33-G-04-a-1",
]

P33_H_GATES: List[str] = [
    "P33-H-01-a-1",
    "P33-H-02-a-1",
    "P33-H-03-a-1",
    "P33-H-04-a-1",
]

P33_IMPLEMENTATION_ORDER: List[str] = list(P33_G_GATES) + list(P33_H_GATES)

P34_G_GATES: List[str] = [
    "P34-G-01-a-1",
    "P34-G-02-a-1",
    "P34-G-03-a-1",
    "P34-G-04-a-1",
]

P34_H_GATES: List[str] = [
    "P34-H-01-a-1",
    "P34-H-02-a-1",
    "P34-H-03-a-1",
    "P34-H-04-a-1",
]

P34_IMPLEMENTATION_ORDER: List[str] = list(P34_G_GATES) + list(P34_H_GATES)

P35_G_GATES: List[str] = [
    "P35-G-01-a-1",
    "P35-G-02-a-1",
    "P35-G-03-a-1",
    "P35-G-04-a-1",
]

P35_H_GATES: List[str] = [
    "P35-H-01-a-1",
    "P35-H-02-a-1",
    "P35-H-03-a-1",
    "P35-H-04-a-1",
]

P35_IMPLEMENTATION_ORDER: List[str] = list(P35_G_GATES) + list(P35_H_GATES)

P36_G_GATES: List[str] = [
    "P36-G-01-a-1",
    "P36-G-02-a-1",
    "P36-G-03-a-1",
    "P36-G-04-a-1",
]

P36_H_GATES: List[str] = [
    "P36-H-01-a-1",
    "P36-H-02-a-1",
    "P36-H-03-a-1",
    "P36-H-04-a-1",
]

P36_IMPLEMENTATION_ORDER: List[str] = list(P36_G_GATES) + list(P36_H_GATES)

P37_G_GATES: List[str] = [
    "P37-G-01-a-1",
    "P37-G-02-a-1",
    "P37-G-03-a-1",
    "P37-G-04-a-1",
]

P37_H_GATES: List[str] = [
    "P37-H-01-a-1",
    "P37-H-02-a-1",
    "P37-H-03-a-1",
    "P37-H-04-a-1",
]

P37_IMPLEMENTATION_ORDER: List[str] = list(P37_G_GATES) + list(P37_H_GATES)

P38_G_GATES: List[str] = [
    "P38-G-01-a-1",
    "P38-G-02-a-1",
    "P38-G-03-a-1",
    "P38-G-04-a-1",
]

P38_H_GATES: List[str] = [
    "P38-H-01-a-1",
    "P38-H-02-a-1",
    "P38-H-03-a-1",
    "P38-H-04-a-1",
]

P38_IMPLEMENTATION_ORDER: List[str] = list(P38_G_GATES) + list(P38_H_GATES)

P39_G_GATES: List[str] = [
    "P39-G-01-a-1",
    "P39-G-02-a-1",
    "P39-G-03-a-1",
    "P39-G-04-a-1",
]

P39_H_GATES: List[str] = [
    "P39-H-01-a-1",
    "P39-H-02-a-1",
    "P39-H-03-a-1",
    "P39-H-04-a-1",
]

P39_IMPLEMENTATION_ORDER: List[str] = list(P39_G_GATES) + list(P39_H_GATES)

P_IMPLEMENTATION_ORDER: List[str] = (
    list(P0_IMPLEMENTATION_ORDER)
    + list(P1_IMPLEMENTATION_ORDER)
    + list(P2_IMPLEMENTATION_ORDER)
    + list(P3_IMPLEMENTATION_ORDER)
    + list(P4_IMPLEMENTATION_ORDER)
    + list(P5_IMPLEMENTATION_ORDER)
    + list(P6_IMPLEMENTATION_ORDER)
    + list(P7_IMPLEMENTATION_ORDER)
    + list(P8_IMPLEMENTATION_ORDER)
)

P9_EXTENDED_ORDER: List[str] = list(P_IMPLEMENTATION_ORDER) + list(P9_L_GATES)

P10_EXTENDED_ORDER: List[str] = list(P9_EXTENDED_ORDER) + list(P10_IMPLEMENTATION_ORDER)

P11_EXTENDED_ORDER: List[str] = list(P10_EXTENDED_ORDER) + list(P11_IMPLEMENTATION_ORDER)

P12_EXTENDED_ORDER: List[str] = list(P11_EXTENDED_ORDER) + list(P12_IMPLEMENTATION_ORDER)

P13_EXTENDED_ORDER: List[str] = list(P12_EXTENDED_ORDER) + list(P13_IMPLEMENTATION_ORDER)

P14_EXTENDED_ORDER: List[str] = list(P13_EXTENDED_ORDER) + list(P14_IMPLEMENTATION_ORDER)

P15_EXTENDED_ORDER: List[str] = list(P14_EXTENDED_ORDER) + list(P15_IMPLEMENTATION_ORDER)

P16_EXTENDED_ORDER: List[str] = list(P15_EXTENDED_ORDER) + list(P16_IMPLEMENTATION_ORDER)

P17_EXTENDED_ORDER: List[str] = list(P16_EXTENDED_ORDER) + list(P17_IMPLEMENTATION_ORDER)

P18_EXTENDED_ORDER: List[str] = list(P17_EXTENDED_ORDER) + list(P18_IMPLEMENTATION_ORDER)

P19_EXTENDED_ORDER: List[str] = list(P18_EXTENDED_ORDER) + list(P19_IMPLEMENTATION_ORDER)

P20_EXTENDED_ORDER: List[str] = list(P19_EXTENDED_ORDER) + list(P20_IMPLEMENTATION_ORDER)

P21_EXTENDED_ORDER: List[str] = list(P20_EXTENDED_ORDER) + list(P21_IMPLEMENTATION_ORDER)

P22_EXTENDED_ORDER: List[str] = list(P21_EXTENDED_ORDER) + list(P22_IMPLEMENTATION_ORDER)

P23_EXTENDED_ORDER: List[str] = list(P22_EXTENDED_ORDER) + list(P23_IMPLEMENTATION_ORDER)

P24_EXTENDED_ORDER: List[str] = list(P23_EXTENDED_ORDER) + list(P24_IMPLEMENTATION_ORDER)

P25_EXTENDED_ORDER: List[str] = list(P24_EXTENDED_ORDER) + list(P25_IMPLEMENTATION_ORDER)

P26_EXTENDED_ORDER: List[str] = list(P25_EXTENDED_ORDER) + list(P26_IMPLEMENTATION_ORDER)

P27_EXTENDED_ORDER: List[str] = list(P26_EXTENDED_ORDER) + list(P27_IMPLEMENTATION_ORDER)

P28_EXTENDED_ORDER: List[str] = list(P27_EXTENDED_ORDER) + list(P28_IMPLEMENTATION_ORDER)

P29_EXTENDED_ORDER: List[str] = list(P28_EXTENDED_ORDER) + list(P29_IMPLEMENTATION_ORDER)

P30_EXTENDED_ORDER: List[str] = list(P29_EXTENDED_ORDER) + list(P30_IMPLEMENTATION_ORDER)

P31_EXTENDED_ORDER: List[str] = list(P30_EXTENDED_ORDER) + list(P31_IMPLEMENTATION_ORDER)

P32_EXTENDED_ORDER: List[str] = list(P31_EXTENDED_ORDER) + list(P32_IMPLEMENTATION_ORDER)

P33_EXTENDED_ORDER: List[str] = list(P32_EXTENDED_ORDER) + list(P33_IMPLEMENTATION_ORDER)

P34_EXTENDED_ORDER: List[str] = list(P33_EXTENDED_ORDER) + list(P34_IMPLEMENTATION_ORDER)

P35_EXTENDED_ORDER: List[str] = list(P34_EXTENDED_ORDER) + list(P35_IMPLEMENTATION_ORDER)

P36_EXTENDED_ORDER: List[str] = list(P35_EXTENDED_ORDER) + list(P36_IMPLEMENTATION_ORDER)

P37_EXTENDED_ORDER: List[str] = list(P36_EXTENDED_ORDER) + list(P37_IMPLEMENTATION_ORDER)

P38_EXTENDED_ORDER: List[str] = list(P37_EXTENDED_ORDER) + list(P38_IMPLEMENTATION_ORDER)

P39_EXTENDED_ORDER: List[str] = list(P38_EXTENDED_ORDER) + list(P39_IMPLEMENTATION_ORDER)

P39_LAST_EXTENDED_GATE = P39_EXTENDED_ORDER[-1]

P38_LAST_EXTENDED_GATE = P38_EXTENDED_ORDER[-1]

P37_LAST_EXTENDED_GATE = P37_EXTENDED_ORDER[-1]

P36_LAST_EXTENDED_GATE = P36_EXTENDED_ORDER[-1]

P35_LAST_EXTENDED_GATE = P35_EXTENDED_ORDER[-1]

P34_LAST_EXTENDED_GATE = P34_EXTENDED_ORDER[-1]

P33_LAST_EXTENDED_GATE = P33_EXTENDED_ORDER[-1]

P32_LAST_EXTENDED_GATE = P32_EXTENDED_ORDER[-1]

P31_LAST_EXTENDED_GATE = P31_EXTENDED_ORDER[-1]

P30_LAST_EXTENDED_GATE = P30_EXTENDED_ORDER[-1]

P29_LAST_EXTENDED_GATE = P29_EXTENDED_ORDER[-1]

P28_LAST_EXTENDED_GATE = P28_EXTENDED_ORDER[-1]

P27_LAST_EXTENDED_GATE = P27_EXTENDED_ORDER[-1]

P26_LAST_EXTENDED_GATE = P26_EXTENDED_ORDER[-1]

P25_LAST_EXTENDED_GATE = P25_EXTENDED_ORDER[-1]

P24_LAST_EXTENDED_GATE = P24_EXTENDED_ORDER[-1]

P23_LAST_EXTENDED_GATE = P23_EXTENDED_ORDER[-1]

P22_LAST_EXTENDED_GATE = P22_EXTENDED_ORDER[-1]

P21_LAST_EXTENDED_GATE = P21_EXTENDED_ORDER[-1]

P20_LAST_EXTENDED_GATE = P20_EXTENDED_ORDER[-1]

P19_LAST_EXTENDED_GATE = P19_EXTENDED_ORDER[-1]

P18_LAST_EXTENDED_GATE = P18_EXTENDED_ORDER[-1]

P17_LAST_EXTENDED_GATE = P17_EXTENDED_ORDER[-1]

P16_LAST_EXTENDED_GATE = P16_EXTENDED_ORDER[-1]

P15_LAST_EXTENDED_GATE = P15_EXTENDED_ORDER[-1]

P14_LAST_EXTENDED_GATE = P14_EXTENDED_ORDER[-1]

P13_LAST_EXTENDED_GATE = P13_EXTENDED_ORDER[-1]

P12_LAST_EXTENDED_GATE = P12_EXTENDED_ORDER[-1]

P11_LAST_EXTENDED_GATE = P11_EXTENDED_ORDER[-1]

P10_LAST_EXTENDED_GATE = P10_EXTENDED_ORDER[-1]

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
P0_DEPS = _depends_chain(P0_IMPLEMENTATION_ORDER, head=O9_LAST_EXTENDED_GATE)
P1_DEPS = _depends_chain(P1_IMPLEMENTATION_ORDER, head=P0_LAST_GATE)
P2_DEPS = _depends_chain(P2_IMPLEMENTATION_ORDER, head=P1_LAST_GATE)
P3_DEPS = _depends_chain(P3_IMPLEMENTATION_ORDER, head=P2_LAST_GATE)
P4_DEPS = _depends_chain(P4_IMPLEMENTATION_ORDER, head=P3_LAST_GATE)
P5_DEPS = _depends_chain(P5_IMPLEMENTATION_ORDER, head=P4_LAST_GATE)
P6_DEPS = _depends_chain(P6_IMPLEMENTATION_ORDER, head=P5_LAST_GATE)
P7_DEPS = _depends_chain(P7_IMPLEMENTATION_ORDER, head=P6_IMPLEMENTATION_ORDER[-1])
P8_DEPS = _depends_chain(P8_IMPLEMENTATION_ORDER, head=P7_LAST_GATE)
P9_L_DEPS = _depends_chain(P9_L_GATES, head=P8_LAST_GATE)
P10_DEPS = _depends_chain(P10_IMPLEMENTATION_ORDER, head=P9_LAST_L_GATE)
P11_DEPS = _depends_chain(P11_IMPLEMENTATION_ORDER, head=P10_IMPLEMENTATION_ORDER[-1])
P12_DEPS = _depends_chain(P12_IMPLEMENTATION_ORDER, head=P11_IMPLEMENTATION_ORDER[-1])
P13_DEPS = _depends_chain(P13_IMPLEMENTATION_ORDER, head=P12_IMPLEMENTATION_ORDER[-1])
P14_DEPS = _depends_chain(P14_IMPLEMENTATION_ORDER, head=P13_IMPLEMENTATION_ORDER[-1])
P15_DEPS = _depends_chain(P15_IMPLEMENTATION_ORDER, head=P14_IMPLEMENTATION_ORDER[-1])
P16_DEPS = _depends_chain(P16_IMPLEMENTATION_ORDER, head=P15_IMPLEMENTATION_ORDER[-1])
P17_DEPS = _depends_chain(P17_IMPLEMENTATION_ORDER, head=P16_IMPLEMENTATION_ORDER[-1])
P18_DEPS = _depends_chain(P18_IMPLEMENTATION_ORDER, head=P17_IMPLEMENTATION_ORDER[-1])
P19_DEPS = _depends_chain(P19_IMPLEMENTATION_ORDER, head=P18_IMPLEMENTATION_ORDER[-1])
P20_DEPS = _depends_chain(P20_IMPLEMENTATION_ORDER, head=P19_IMPLEMENTATION_ORDER[-1])
P21_DEPS = _depends_chain(P21_IMPLEMENTATION_ORDER, head=P20_IMPLEMENTATION_ORDER[-1])
P22_DEPS = _depends_chain(P22_IMPLEMENTATION_ORDER, head=P21_IMPLEMENTATION_ORDER[-1])
P23_DEPS = _depends_chain(P23_IMPLEMENTATION_ORDER, head=P22_IMPLEMENTATION_ORDER[-1])
P24_DEPS = _depends_chain(P24_IMPLEMENTATION_ORDER, head=P23_IMPLEMENTATION_ORDER[-1])
P25_DEPS = _depends_chain(P25_IMPLEMENTATION_ORDER, head=P24_IMPLEMENTATION_ORDER[-1])
P26_DEPS = _depends_chain(P26_IMPLEMENTATION_ORDER, head=P25_IMPLEMENTATION_ORDER[-1])
P27_DEPS = _depends_chain(P27_IMPLEMENTATION_ORDER, head=P26_IMPLEMENTATION_ORDER[-1])
P28_DEPS = _depends_chain(P28_IMPLEMENTATION_ORDER, head=P27_IMPLEMENTATION_ORDER[-1])
P29_DEPS = _depends_chain(P29_IMPLEMENTATION_ORDER, head=P28_IMPLEMENTATION_ORDER[-1])
P30_DEPS = _depends_chain(P30_IMPLEMENTATION_ORDER, head=P29_IMPLEMENTATION_ORDER[-1])
P31_DEPS = _depends_chain(P31_IMPLEMENTATION_ORDER, head=P30_IMPLEMENTATION_ORDER[-1])
P32_DEPS = _depends_chain(P32_IMPLEMENTATION_ORDER, head=P31_IMPLEMENTATION_ORDER[-1])
P33_DEPS = _depends_chain(P33_IMPLEMENTATION_ORDER, head=P32_IMPLEMENTATION_ORDER[-1])
P34_DEPS = _depends_chain(P34_IMPLEMENTATION_ORDER, head=P33_IMPLEMENTATION_ORDER[-1])
P35_DEPS = _depends_chain(P35_IMPLEMENTATION_ORDER, head=P34_IMPLEMENTATION_ORDER[-1])
P36_DEPS = _depends_chain(P36_IMPLEMENTATION_ORDER, head=P35_IMPLEMENTATION_ORDER[-1])
P37_DEPS = _depends_chain(P37_IMPLEMENTATION_ORDER, head=P36_IMPLEMENTATION_ORDER[-1])
P38_DEPS = _depends_chain(P38_IMPLEMENTATION_ORDER, head=P37_IMPLEMENTATION_ORDER[-1])
P39_DEPS = _depends_chain(P39_IMPLEMENTATION_ORDER, head=P38_IMPLEMENTATION_ORDER[-1])

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
_O0_THROUGH_O9_EXT_PREFIX: List[str] = (
    _O0_THROUGH_O8_PREFIX + list(O9_EXTENDED_ORDER)
)
_O0_THROUGH_P0_PREFIX: List[str] = (
    _O0_THROUGH_O9_EXT_PREFIX + list(P0_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_P1_PREFIX: List[str] = (
    _O0_THROUGH_P0_PREFIX + list(P1_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_P2_PREFIX: List[str] = (
    _O0_THROUGH_P1_PREFIX + list(P2_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_P3_PREFIX: List[str] = (
    _O0_THROUGH_P2_PREFIX + list(P3_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_P4_PREFIX: List[str] = (
    _O0_THROUGH_P3_PREFIX + list(P4_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_P5_PREFIX: List[str] = (
    _O0_THROUGH_P4_PREFIX + list(P5_IMPLEMENTATION_ORDER)
)
_O0_THROUGH_P7_PREFIX: List[str] = (
    _O0_THROUGH_P5_PREFIX
    + list(P6_IMPLEMENTATION_ORDER)
    + list(P7_IMPLEMENTATION_ORDER)
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
    "P0-T": list(P0_T_GATES),
    "P0-R": list(P0_R_GATES),
    "P0": list(P0_IMPLEMENTATION_ORDER),
    "P1-P": list(P1_P_GATES),
    "P1": list(P1_IMPLEMENTATION_ORDER),
    "P2-V": list(P2_V_GATES),
    "P2-P": list(P2_P_GATES),
    "P2-S": list(P2_S_GATES),
    "P2-R": list(P2_R_GATES),
    "P2": list(P2_IMPLEMENTATION_ORDER),
    "P3-S": list(P3_S_GATES),
    "P3": list(P3_IMPLEMENTATION_ORDER),
    "P4-O": list(P4_O_GATES),
    "P4-M": list(P4_M_GATES),
    "P4-R": list(P4_R_GATES),
    "P4": list(P4_IMPLEMENTATION_ORDER),
    "P5-W": list(P5_W_GATES),
    "P5-P": list(P5_P_GATES),
    "P5-R": list(P5_R_GATES),
    "P5": list(P5_IMPLEMENTATION_ORDER),
    "P6-A": list(P6_A_GATES),
    "P6-R": list(P6_R_GATES),
    "P6": list(P6_IMPLEMENTATION_ORDER),
    "P7-M": list(P7_M_GATES),
    "P7-R": list(P7_R_GATES),
    "P7": list(P7_IMPLEMENTATION_ORDER),
    "P8-B": list(P8_B_GATES),
    "P8": list(P8_IMPLEMENTATION_ORDER),
    "P9-L": list(P9_L_GATES),
    "P9-EXT": list(P9_EXTENDED_ORDER),
    "P10-F": list(P10_F_GATES),
    "P10-M": list(P10_M_GATES),
    "P10": list(P10_IMPLEMENTATION_ORDER),
    "P10-EXT": list(P10_EXTENDED_ORDER),
    "P11-K": list(P11_K_GATES),
    "P11": list(P11_IMPLEMENTATION_ORDER),
    "P11-EXT": list(P11_EXTENDED_ORDER),
    "P12-F": list(P12_F_GATES),
    "P12": list(P12_IMPLEMENTATION_ORDER),
    "P12-EXT": list(P12_EXTENDED_ORDER),
    "P13-I": list(P13_I_GATES),
    "P13-M": list(P13_M_GATES),
    "P13": list(P13_IMPLEMENTATION_ORDER),
    "P13-EXT": list(P13_EXTENDED_ORDER),
    "P14-R": list(P14_R_GATES),
    "P14-J": list(P14_J_GATES),
    "P14": list(P14_IMPLEMENTATION_ORDER),
    "P14-EXT": list(P14_EXTENDED_ORDER),
    "P15-S": list(P15_S_GATES),
    "P15-H": list(P15_H_GATES),
    "P15": list(P15_IMPLEMENTATION_ORDER),
    "P15-EXT": list(P15_EXTENDED_ORDER),
    "P16-W": list(P16_W_GATES),
    "P16-H": list(P16_H_GATES),
    "P16": list(P16_IMPLEMENTATION_ORDER),
    "P16-EXT": list(P16_EXTENDED_ORDER),
    "P17-E": list(P17_E_GATES),
    "P17-H": list(P17_H_GATES),
    "P17": list(P17_IMPLEMENTATION_ORDER),
    "P17-EXT": list(P17_EXTENDED_ORDER),
    "P18-P": list(P18_P_GATES),
    "P18-L": list(P18_L_GATES),
    "P18": list(P18_IMPLEMENTATION_ORDER),
    "P18-EXT": list(P18_EXTENDED_ORDER),
    "P19-V": list(P19_V_GATES),
    "P19-R": list(P19_R_GATES),
    "P19": list(P19_IMPLEMENTATION_ORDER),
    "P19-EXT": list(P19_EXTENDED_ORDER),
    "P20-M": list(P20_M_GATES),
    "P20-H": list(P20_H_GATES),
    "P20": list(P20_IMPLEMENTATION_ORDER),
    "P20-EXT": list(P20_EXTENDED_ORDER),
    "P21-C": list(P21_C_GATES),
    "P21-H": list(P21_H_GATES),
    "P21": list(P21_IMPLEMENTATION_ORDER),
    "P21-EXT": list(P21_EXTENDED_ORDER),
    "P22-A": list(P22_A_GATES),
    "P22-H": list(P22_H_GATES),
    "P22": list(P22_IMPLEMENTATION_ORDER),
    "P22-EXT": list(P22_EXTENDED_ORDER),
    "P23-G": list(P23_G_GATES),
    "P23-H": list(P23_H_GATES),
    "P23": list(P23_IMPLEMENTATION_ORDER),
    "P23-EXT": list(P23_EXTENDED_ORDER),
    "P24-O": list(P24_O_GATES),
    "P24-H": list(P24_H_GATES),
    "P24": list(P24_IMPLEMENTATION_ORDER),
    "P24-EXT": list(P24_EXTENDED_ORDER),
    "P25-N": list(P25_N_GATES),
    "P25-H": list(P25_H_GATES),
    "P25": list(P25_IMPLEMENTATION_ORDER),
    "P25-EXT": list(P25_EXTENDED_ORDER),
    "P26-W": list(P26_W_GATES),
    "P26-H": list(P26_H_GATES),
    "P26": list(P26_IMPLEMENTATION_ORDER),
    "P26-EXT": list(P26_EXTENDED_ORDER),
    "P27-G": list(P27_G_GATES),
    "P27-H": list(P27_H_GATES),
    "P27": list(P27_IMPLEMENTATION_ORDER),
    "P27-EXT": list(P27_EXTENDED_ORDER),
    "P28-M": list(P28_M_GATES),
    "P28-H": list(P28_H_GATES),
    "P28": list(P28_IMPLEMENTATION_ORDER),
    "P28-EXT": list(P28_EXTENDED_ORDER),
    "P29-G": list(P29_G_GATES),
    "P29-H": list(P29_H_GATES),
    "P29": list(P29_IMPLEMENTATION_ORDER),
    "P29-EXT": list(P29_EXTENDED_ORDER),
    "P30-G": list(P30_G_GATES),
    "P30-H": list(P30_H_GATES),
    "P30": list(P30_IMPLEMENTATION_ORDER),
    "P30-EXT": list(P30_EXTENDED_ORDER),
    "P31-M": list(P31_M_GATES),
    "P31-H": list(P31_H_GATES),
    "P31": list(P31_IMPLEMENTATION_ORDER),
    "P31-EXT": list(P31_EXTENDED_ORDER),
    "P32-G": list(P32_G_GATES),
    "P32-H": list(P32_H_GATES),
    "P32": list(P32_IMPLEMENTATION_ORDER),
    "P32-EXT": list(P32_EXTENDED_ORDER),
    "P33-G": list(P33_G_GATES),
    "P33-H": list(P33_H_GATES),
    "P33": list(P33_IMPLEMENTATION_ORDER),
    "P33-EXT": list(P33_EXTENDED_ORDER),
    "P34-G": list(P34_G_GATES),
    "P34-H": list(P34_H_GATES),
    "P34": list(P34_IMPLEMENTATION_ORDER),
    "P34-EXT": list(P34_EXTENDED_ORDER),
    "P35-G": list(P35_G_GATES),
    "P35-H": list(P35_H_GATES),
    "P35": list(P35_IMPLEMENTATION_ORDER),
    "P35-EXT": list(P35_EXTENDED_ORDER),
    "P36-G": list(P36_G_GATES),
    "P36-H": list(P36_H_GATES),
    "P36": list(P36_IMPLEMENTATION_ORDER),
    "P36-EXT": list(P36_EXTENDED_ORDER),
    "P37-G": list(P37_G_GATES),
    "P37-H": list(P37_H_GATES),
    "P37": list(P37_IMPLEMENTATION_ORDER),
    "P37-EXT": list(P37_EXTENDED_ORDER),
    "P38-G": list(P38_G_GATES),
    "P38-H": list(P38_H_GATES),
    "P38": list(P38_IMPLEMENTATION_ORDER),
    "P38-EXT": list(P38_EXTENDED_ORDER),
    "P39-G": list(P39_G_GATES),
    "P39-H": list(P39_H_GATES),
    "P39": list(P39_IMPLEMENTATION_ORDER),
    "P39-EXT": list(P39_EXTENDED_ORDER),
    "P": list(P_IMPLEMENTATION_ORDER),
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
        elif gate_id in P0_DEPS:
            dep = P0_DEPS[gate_id]
        elif gate_id in P1_DEPS:
            dep = P1_DEPS[gate_id]
        elif gate_id in P2_DEPS:
            dep = P2_DEPS[gate_id]
        elif gate_id in P3_DEPS:
            dep = P3_DEPS[gate_id]
        elif gate_id in P4_DEPS:
            dep = P4_DEPS[gate_id]
        elif gate_id in P5_DEPS:
            dep = P5_DEPS[gate_id]
        elif gate_id in P6_DEPS:
            dep = P6_DEPS[gate_id]
        elif gate_id in P7_DEPS:
            dep = P7_DEPS[gate_id]
        elif gate_id in P8_DEPS:
            dep = P8_DEPS[gate_id]
        elif gate_id in P9_L_DEPS:
            dep = P9_L_DEPS[gate_id]
        elif gate_id in P10_DEPS:
            dep = P10_DEPS[gate_id]
        elif gate_id in P11_DEPS:
            dep = P11_DEPS[gate_id]
        elif gate_id in P12_DEPS:
            dep = P12_DEPS[gate_id]
        elif gate_id in P13_DEPS:
            dep = P13_DEPS[gate_id]
        elif gate_id in P14_DEPS:
            dep = P14_DEPS[gate_id]
        elif gate_id in P15_DEPS:
            dep = P15_DEPS[gate_id]
        elif gate_id in P16_DEPS:
            dep = P16_DEPS[gate_id]
        elif gate_id in P17_DEPS:
            dep = P17_DEPS[gate_id]
        elif gate_id in P18_DEPS:
            dep = P18_DEPS[gate_id]
        elif gate_id in P19_DEPS:
            dep = P19_DEPS[gate_id]
        elif gate_id in P20_DEPS:
            dep = P20_DEPS[gate_id]
        elif gate_id in P21_DEPS:
            dep = P21_DEPS[gate_id]
        elif gate_id in P22_DEPS:
            dep = P22_DEPS[gate_id]
        elif gate_id in P23_DEPS:
            dep = P23_DEPS[gate_id]
        elif gate_id in P24_DEPS:
            dep = P24_DEPS[gate_id]
        elif gate_id in P25_DEPS:
            dep = P25_DEPS[gate_id]
        elif gate_id in P26_DEPS:
            dep = P26_DEPS[gate_id]
        elif gate_id in P27_DEPS:
            dep = P27_DEPS[gate_id]
        elif gate_id in P28_DEPS:
            dep = P28_DEPS[gate_id]
        elif gate_id in P29_DEPS:
            dep = P29_DEPS[gate_id]
        elif gate_id in P30_DEPS:
            dep = P30_DEPS[gate_id]
        elif gate_id in P31_DEPS:
            dep = P31_DEPS[gate_id]
        elif gate_id in P32_DEPS:
            dep = P32_DEPS[gate_id]
        elif gate_id in P33_DEPS:
            dep = P33_DEPS[gate_id]
        elif gate_id in P34_DEPS:
            dep = P34_DEPS[gate_id]
        elif gate_id in P35_DEPS:
            dep = P35_DEPS[gate_id]
        elif gate_id in P36_DEPS:
            dep = P36_DEPS[gate_id]
        elif gate_id in P37_DEPS:
            dep = P37_DEPS[gate_id]
        elif gate_id in P38_DEPS:
            dep = P38_DEPS[gate_id]
        elif gate_id in P39_DEPS:
            dep = P39_DEPS[gate_id]
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
    if rollup_id == "P0-T":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P0_T_GATES)
    if rollup_id == "P0-R":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P0_IMPLEMENTATION_ORDER)
    if rollup_id == "P0":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P0_IMPLEMENTATION_ORDER)
    if rollup_id == "P1-P":
        return _O0_THROUGH_P0_PREFIX + list(P1_P_GATES)
    if rollup_id == "P1":
        return _O0_THROUGH_P0_PREFIX + list(P1_IMPLEMENTATION_ORDER)
    if rollup_id == "P2-V":
        return _O0_THROUGH_P1_PREFIX + list(P2_V_GATES)
    if rollup_id == "P2-P":
        return _O0_THROUGH_P1_PREFIX + list(P2_V_GATES) + list(P2_P_GATES)
    if rollup_id == "P2-S":
        return _O0_THROUGH_P1_PREFIX + list(P2_V_GATES) + list(P2_P_GATES) + list(P2_S_GATES)
    if rollup_id == "P2-R":
        return _O0_THROUGH_P1_PREFIX + list(P2_IMPLEMENTATION_ORDER)
    if rollup_id == "P2":
        return _O0_THROUGH_P1_PREFIX + list(P2_IMPLEMENTATION_ORDER)
    if rollup_id == "P3-S":
        return _O0_THROUGH_P2_PREFIX + list(P3_S_GATES)
    if rollup_id == "P3":
        return _O0_THROUGH_P2_PREFIX + list(P3_IMPLEMENTATION_ORDER)
    if rollup_id == "P4-O":
        return _O0_THROUGH_P3_PREFIX + list(P4_O_GATES)
    if rollup_id == "P4-M":
        return _O0_THROUGH_P3_PREFIX + list(P4_O_GATES) + list(P4_M_GATES)
    if rollup_id == "P4-R":
        return _O0_THROUGH_P3_PREFIX + list(P4_IMPLEMENTATION_ORDER)
    if rollup_id == "P4":
        return _O0_THROUGH_P3_PREFIX + list(P4_IMPLEMENTATION_ORDER)
    if rollup_id == "P5-W":
        return _O0_THROUGH_P4_PREFIX + list(P5_W_GATES)
    if rollup_id == "P5-P":
        return _O0_THROUGH_P4_PREFIX + list(P5_W_GATES) + list(P5_P_GATES)
    if rollup_id == "P5-R":
        return _O0_THROUGH_P4_PREFIX + list(P5_IMPLEMENTATION_ORDER)
    if rollup_id == "P5":
        return _O0_THROUGH_P4_PREFIX + list(P5_IMPLEMENTATION_ORDER)
    if rollup_id == "P6-A":
        return _O0_THROUGH_P5_PREFIX + list(P6_A_GATES)
    if rollup_id == "P6-R":
        return _O0_THROUGH_P5_PREFIX + list(P6_IMPLEMENTATION_ORDER)
    if rollup_id == "P6":
        return _O0_THROUGH_P5_PREFIX + list(P6_IMPLEMENTATION_ORDER)
    if rollup_id == "P7-M":
        return _O0_THROUGH_P5_PREFIX + list(P6_IMPLEMENTATION_ORDER) + list(P7_M_GATES)
    if rollup_id == "P7-R":
        return _O0_THROUGH_P5_PREFIX + list(P6_IMPLEMENTATION_ORDER) + list(P7_IMPLEMENTATION_ORDER)
    if rollup_id == "P7":
        return _O0_THROUGH_P5_PREFIX + list(P6_IMPLEMENTATION_ORDER) + list(P7_IMPLEMENTATION_ORDER)
    if rollup_id == "P8-B":
        return _O0_THROUGH_P7_PREFIX + list(P8_B_GATES)
    if rollup_id == "P8":
        return _O0_THROUGH_P7_PREFIX + list(P8_IMPLEMENTATION_ORDER)
    if rollup_id == "P9-L":
        return _O0_THROUGH_P7_PREFIX + list(P8_IMPLEMENTATION_ORDER) + list(P9_L_GATES)
    if rollup_id == "P9-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P9_EXTENDED_ORDER)
    if rollup_id == "P10-F":
        return _O0_THROUGH_P7_PREFIX + list(P8_IMPLEMENTATION_ORDER) + list(P9_L_GATES) + list(P10_F_GATES)
    if rollup_id == "P10-M":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_F_GATES)
            + list(P10_M_GATES)
        )
    if rollup_id == "P10":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P10-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P10_EXTENDED_ORDER)
    if rollup_id == "P11-K":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_K_GATES)
        )
    if rollup_id == "P11":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P11-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P11_EXTENDED_ORDER)
    if rollup_id == "P12-F":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_F_GATES)
        )
    if rollup_id == "P12":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P12-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P12_EXTENDED_ORDER)
    if rollup_id == "P13-I":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_I_GATES)
        )
    if rollup_id == "P13-M":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_I_GATES)
            + list(P13_M_GATES)
        )
    if rollup_id == "P13":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P13-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P13_EXTENDED_ORDER)
    if rollup_id == "P14-R":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_R_GATES)
        )
    if rollup_id == "P14-J":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P14":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P14-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P14_EXTENDED_ORDER)
    if rollup_id == "P15-S":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_S_GATES)
        )
    if rollup_id == "P15-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P15":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P15-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P15_EXTENDED_ORDER)
    if rollup_id == "P16-W":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_W_GATES)
        )
    if rollup_id == "P16-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P16":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P16-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P16_EXTENDED_ORDER)
    if rollup_id == "P17-E":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_E_GATES)
        )
    if rollup_id == "P17-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P17":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P17-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P17_EXTENDED_ORDER)
    if rollup_id == "P18-P":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_P_GATES)
        )
    if rollup_id == "P18-L":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P18":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P18-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P18_EXTENDED_ORDER)
    if rollup_id == "P19-V":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_V_GATES)
        )
    if rollup_id == "P19-R":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P19":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P19-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P19_EXTENDED_ORDER)
    if rollup_id == "P20-M":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_M_GATES)
        )
    if rollup_id == "P20-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P20":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P20-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P20_EXTENDED_ORDER)
    if rollup_id == "P21-C":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_C_GATES)
        )
    if rollup_id == "P21-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P21":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P21-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P21_EXTENDED_ORDER)
    if rollup_id == "P22-A":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_A_GATES)
        )
    if rollup_id == "P22-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P22":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P22-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P22_EXTENDED_ORDER)
    if rollup_id == "P23-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_G_GATES)
        )
    if rollup_id == "P23-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P23":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P23-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P23_EXTENDED_ORDER)
    if rollup_id == "P24-O":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_O_GATES)
        )
    if rollup_id == "P24-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P24":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P24-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P24_EXTENDED_ORDER)
    if rollup_id == "P25-N":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_N_GATES)
        )
    if rollup_id == "P25-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P25":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P25-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P25_EXTENDED_ORDER)
    if rollup_id == "P26-W":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_W_GATES)
        )
    if rollup_id == "P26-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P26":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P26-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P26_EXTENDED_ORDER)
    if rollup_id == "P27-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_G_GATES)
        )
    if rollup_id == "P27-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P27":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P27-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P27_EXTENDED_ORDER)
    if rollup_id == "P28-M":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_M_GATES)
        )
    if rollup_id == "P28-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P28":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P28-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P28_EXTENDED_ORDER)
    if rollup_id == "P29-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_G_GATES)
        )
    if rollup_id == "P29-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P29":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P30-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_G_GATES)
        )
    if rollup_id == "P30-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P30":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P31-M":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_M_GATES)
        )
    if rollup_id == "P31-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P31":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P32-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_G_GATES)
        )
    if rollup_id == "P32-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P32":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P33-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_G_GATES)
        )
    if rollup_id == "P33-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P33":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P34-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_G_GATES)
        )
    if rollup_id == "P34-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P34":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P35-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_G_GATES)
        )
    if rollup_id == "P35-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P35":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P36-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_G_GATES)
        )
    if rollup_id == "P36-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P36":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P37-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_G_GATES)
        )
    if rollup_id == "P37-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P37":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P38-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_G_GATES)
        )
    if rollup_id == "P38-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P38":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P39-G":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_IMPLEMENTATION_ORDER)
            + list(P39_G_GATES)
        )
    if rollup_id == "P39-H":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_IMPLEMENTATION_ORDER)
            + list(P39_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P39":
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_IMPLEMENTATION_ORDER)
            + list(P39_IMPLEMENTATION_ORDER)
        )
    if rollup_id == "P39-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P39_EXTENDED_ORDER)
    if rollup_id.startswith("P39-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + list(P38_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P38-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P38_EXTENDED_ORDER)
    if rollup_id.startswith("P38-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + list(P37_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P37-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P37_EXTENDED_ORDER)
    if rollup_id.startswith("P37-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + list(P36_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P36-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P36_EXTENDED_ORDER)
    if rollup_id.startswith("P36-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + list(P35_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P35-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P35_EXTENDED_ORDER)
    if rollup_id.startswith("P35-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + list(P34_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P34-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P34_EXTENDED_ORDER)
    if rollup_id.startswith("P34-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + list(P33_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P33-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P33_EXTENDED_ORDER)
    if rollup_id.startswith("P33-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + list(P32_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P32-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P32_EXTENDED_ORDER)
    if rollup_id.startswith("P32-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + list(P31_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P31-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P31_EXTENDED_ORDER)
    if rollup_id.startswith("P31-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + list(P30_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P30-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P30_EXTENDED_ORDER)
    if rollup_id.startswith("P30-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + list(P29_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id == "P29-EXT":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P29_EXTENDED_ORDER)
    if rollup_id.startswith("P29-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + list(P28_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P28-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + list(P27_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P27-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + list(P26_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P26-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + list(P25_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P25-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + list(P24_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P24-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + list(P23_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P23-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + list(P22_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P22-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + list(P21_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P21-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + list(P20_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P20-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + list(P19_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P19-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + list(P18_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P18-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + list(P17_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P17-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + list(P16_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P16-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + list(P15_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P15-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + list(P14_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P14-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + list(P13_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P13-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + list(P12_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P12-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + list(P11_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P11-"):
        return (
            _O0_THROUGH_P7_PREFIX
            + list(P8_IMPLEMENTATION_ORDER)
            + list(P9_L_GATES)
            + list(P10_IMPLEMENTATION_ORDER)
            + gates
        )
    if rollup_id.startswith("P10-"):
        return _O0_THROUGH_P7_PREFIX + list(P8_IMPLEMENTATION_ORDER) + list(P9_L_GATES) + gates
    if rollup_id == "P":
        return _O0_THROUGH_O9_EXT_PREFIX + list(P_IMPLEMENTATION_ORDER)
    if rollup_id.startswith("P8-"):
        return _O0_THROUGH_P7_PREFIX + gates
    if rollup_id.startswith("P7-"):
        return _O0_THROUGH_P5_PREFIX + list(P6_IMPLEMENTATION_ORDER) + gates
    if rollup_id.startswith("P6-"):
        return _O0_THROUGH_P5_PREFIX + gates
    if rollup_id.startswith("P5-"):
        return _O0_THROUGH_P4_PREFIX + gates
    if rollup_id.startswith("P4-"):
        return _O0_THROUGH_P3_PREFIX + gates
    if rollup_id.startswith("P3-"):
        return _O0_THROUGH_P2_PREFIX + gates
    if rollup_id.startswith("P2-"):
        return _O0_THROUGH_P1_PREFIX + gates
    if rollup_id.startswith("P1-"):
        return _O0_THROUGH_P0_PREFIX + gates
    if rollup_id.startswith("P0-"):
        return _O0_THROUGH_O9_EXT_PREFIX + gates
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
    if gate_id.startswith("P"):
        order = _O0_THROUGH_O9_EXT_PREFIX + list(P_IMPLEMENTATION_ORDER)
        idx = order.index(gate_id)
        return list(order[: idx + 1])
    order = FULL_IMPLEMENTATION_ORDER
    idx = order.index(gate_id)
    return list(order[: idx + 1])
