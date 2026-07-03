# -*- coding: utf-8
"""P1-P L4 gate bodies."""

from __future__ import annotations

from data_pc_origin.gates.registry import P1_DEPS, register_gate
from data_pc_origin.o0_mapping import DEFAULT_ORIGIN_MAPPING
from data_pc_origin.p0_types import Stage2Artifacts, WorkflowMode
from data_pc_origin.p1_payload import (
    PayloadValidationError,
    Stage2Metadata,
    assemble_stage2_metadata,
    build_payload_from_stage2,
    mapping_subset_for_df,
    payload_mapping_col_count,
    skipped_mapping_columns,
    validate_identity_key,
    validate_sample_name,
)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


class _FakeDf:
    def __init__(self, columns: list[str], n: int = 108) -> None:
        self.columns = columns
        self._n = n

    def __len__(self) -> int:
        return self._n


_DRE_COLS = [
    "C2H6 Conversion (%)",
    "CO2 Conversion (%)",
    "H2 Yield (%)",
    "CO Yield (%)",
    "CH4 (%)",
    "C2H4 (%)",
]


def _gate_p1_p_01_a_1() -> None:
    m = Stage2Metadata("n", ("20260620", "k"), r"G:\x.xlsx")
    _assert(m.sample_name == "n")
    _assert(m.saved_excel.endswith(".xlsx"))


def _gate_p1_p_02_a_1() -> None:
    _assert(validate_sample_name(" 20260620 DRE ") == "20260620 DRE")
    try:
        validate_sample_name("  ")
        _assert(False, "expected PayloadValidationError")
    except PayloadValidationError:
        pass


def _gate_p1_p_03_a_1() -> None:
    k = validate_identity_key(("20260620", "dre ni5"))
    _assert(k[0] == "20260620")
    try:
        validate_identity_key(("only",))  # type: ignore[arg-type]
        _assert(False)
    except PayloadValidationError:
        pass


def _gate_p1_p_04_a_1() -> None:
    df = _FakeDf(list(DEFAULT_ORIGIN_MAPPING.keys()))
    subset, skipped = mapping_subset_for_df(df)
    _assert(len(subset) == 8)
    _assert(skipped == [])
    _assert("H2 Yield (%)" in subset)


def _gate_p1_p_05_a_1() -> None:
    df = _FakeDf(_DRE_COLS)
    _assert(payload_mapping_col_count(df) == 6)


def _gate_p1_p_06_a_1() -> None:
    df = _FakeDf(_DRE_COLS)
    skipped = skipped_mapping_columns(df)
    _assert("CH4 Conversion (%)" in skipped)
    _assert("C2H6 (%)" in skipped)
    _assert(len(skipped) == 2)


def _gate_p1_p_07_a_1() -> None:
    m = assemble_stage2_metadata(
        sample_name="20260620 DRE(1.5)@600°C Ni5",
        identity_key=("20260620", "dre ni5"),
        saved_excel=r"G:\out.xlsx",
    )
    _assert(m.identity_key[1] == "dre ni5")


def _gate_p1_p_08_a_1() -> None:
    art = Stage2Artifacts(_FakeDf(_DRE_COLS), r"G:\calc.xlsx")
    meta = assemble_stage2_metadata(
        sample_name="s",
        identity_key=("d", "k"),
        saved_excel=r"G:\calc.xlsx",
    )
    p = build_payload_from_stage2(
        art,
        meta,
        opju_path=r"G:\t.opju",
        mode=WorkflowMode.OPJU_ONLY,
    )
    _assert(p.save_in_place is False)
    _assert(p.sample_name == "s")


_P1_GATES: list[tuple[str, object]] = [
    ("P1-P-01-a-1", _gate_p1_p_01_a_1),
    ("P1-P-02-a-1", _gate_p1_p_02_a_1),
    ("P1-P-03-a-1", _gate_p1_p_03_a_1),
    ("P1-P-04-a-1", _gate_p1_p_04_a_1),
    ("P1-P-05-a-1", _gate_p1_p_05_a_1),
    ("P1-P-06-a-1", _gate_p1_p_06_a_1),
    ("P1-P-07-a-1", _gate_p1_p_07_a_1),
    ("P1-P-08-a-1", _gate_p1_p_08_a_1),
]


def register_p1_gates() -> None:
    for gate_id, fn in _P1_GATES:
        register_gate(gate_id, fn, depends=P1_DEPS[gate_id], layer="P1")  # type: ignore[arg-type]
