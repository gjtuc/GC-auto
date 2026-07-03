# -*- coding: utf-8
"""O0 L4 gate bodies — register via register_o0_gates()."""

from __future__ import annotations

import math
import re

import pandas as pd

from data_pc_origin.gates.registry import register_gate
from data_pc_origin.o0_comments import (
    IdentityKey,
    comment_matches_identity,
    parse_comment_date,
    parse_equipment_suffix,
    sort_key_from_comment,
    strip_equipment_suffix,
)
from data_pc_origin.o0_identity import (
    identity_match_tokens,
    token_match_score,
    token_match_threshold,
)
from data_pc_origin.o0_keys import (
    keyword_in_normalized_text,
    keys_match,
    normalize_origin_key,
)
from data_pc_origin.o0_mapping import (
    DEFAULT_ORIGIN_MAPPING,
    MappingValidationError,
    mapping_for_df,
    validate_mapping,
)
from data_pc_origin.o0_series import GapPolicy, column_to_origin_list
from data_pc_origin.o0_types import OriginPath, ProbeResult, gap_policy_members

_IDENTITY_DRE: IdentityKey = ("20260620", "dre(1.5) 600c ni5_ce5_al2o3")
_SAMPLE_DRE = "dre(1.5) 600c ni5_ce5_al2o3"
_COMMENT_DRE = "20260620 DRE(1.5)@600°C 600CNi5_Ce5_Al2O3"
_COMMENT_DRE_SUFFIX = "20260620 DRE(1.5)@600°C Ni5_Ce5_Al2O3_DRM 장비"


def _gc3_gap_series(length: int = 107) -> list[float]:
    values = [1.0] * length
    values[99] = float("nan")
    values[100] = float("nan")
    return values


def register_o0_gates() -> None:
    # --- O0-K ---
    register_gate("O0-K-01-a-1", lambda: _assert(normalize_origin_key(None) == ""))
    register_gate("O0-K-01-b-1", lambda: _assert(normalize_origin_key("") == ""))
    register_gate("O0-K-01-c-1", lambda: _assert(normalize_origin_key("   \t  ") == ""))
    register_gate(
        "O0-K-01-d-1",
        lambda: _assert(normalize_origin_key("H2 yield") == "h2yield"),
    )
    register_gate(
        "O0-K-01-e-1",
        lambda: _assert(normalize_origin_key("  CO2 conversion ") == "co2conversion"),
    )
    register_gate(
        "O0-K-01-f-1",
        lambda: _assert(normalize_origin_key("DRM CH4") == "drmch4"),
    )
    register_gate(
        "O0-K-01-g-1",
        lambda: _assert(normalize_origin_key("H2\t\tYield") == "h2yield"),
    )
    register_gate(
        "O0-K-02-a-1",
        lambda: _assert(keys_match("H2 yield", "h2yield")),
    )
    register_gate("O0-K-02-b-1", _gate_o0_k_02_b_1)

    # --- O0-I ---
    register_gate("O0-I-01-a-1", lambda: _assert(identity_match_tokens("") == set()))
    register_gate(
        "O0-I-01-b-1",
        lambda: _assert("dre" in identity_match_tokens(_SAMPLE_DRE)),
    )
    register_gate(
        "O0-I-01-c-1",
        lambda: _assert("drme" in identity_match_tokens("20260620 DRME(0.5)@600°C")),
    )
    register_gate(
        "O0-I-01-d-1",
        lambda: _assert(any(t.startswith("@") for t in identity_match_tokens("dre @600"))),
    )
    register_gate(
        "O0-I-01-e-1",
        lambda: (
            _assert("ni5" in identity_match_tokens(_SAMPLE_DRE)),
            _assert("ce5" in identity_match_tokens("ni5_ce5_al2o3")),
        )[-1],
    )
    register_gate(
        "O0-I-01-f-1",
        lambda: _assert("a" not in identity_match_tokens("a dre test")),
    )
    register_gate(
        "O0-I-01-g-1",
        lambda: _assert("0.15g" in identity_match_tokens("0.15g dre")),
    )
    register_gate(
        "O0-I-02-a-1",
        lambda: _assert(
            token_match_score("dre ni5 x", {"dre", "@600", "ni5"}) >= 2 / 3
        ),
    )
    register_gate(
        "O0-I-02-b-1",
        lambda: (
            _assert(token_match_threshold(3) == 2),
            _assert(token_match_threshold(5) == 3),
        )[-1],
    )

    # --- O0-I-03 — Task C Comments 형식 (% / @ / 슬래시 촉매) ---
    _SAMPLE_TASK_C = "dre(1.5) 600c ni5_ce5_al2o3"
    _COMMENT_TASK_C = (
        "20260620 DRE(1.5%)@600°C Ni5/Ce5/Al2O3_OCM 장비"
    )

    register_gate(
        "O0-I-03-a-1",
        lambda: _assert("1.5" in identity_match_tokens(_SAMPLE_TASK_C)),
    )
    register_gate(
        "O0-I-03-b-1",
        lambda: _assert("@600" in identity_match_tokens(_SAMPLE_TASK_C)),
    )
    register_gate(
        "O0-I-03-c-1",
        lambda: (
            _assert("ni5" in identity_match_tokens("ni5/ce5/al2o3")),
            _assert("al2o3" in identity_match_tokens("ni5/ce5/al2o3")),
        )[-1],
    )
    register_gate(
        "O0-I-03-d-1",
        lambda: _assert(
            comment_matches_identity(_COMMENT_TASK_C, _IDENTITY_DRE)
        ),
    )
    register_gate(
        "O0-I-03-e-1",
        lambda: _assert(
            "장비" not in identity_match_tokens("dre ni5 _ocm 장비")
        ),
    )

    # --- O0-C ---
    register_gate("O0-C-01-a-1", lambda: _assert(parse_comment_date(None) is None))
    register_gate(
        "O0-C-01-b-1",
        lambda: _assert(parse_comment_date(_COMMENT_DRE) == "20260620"),
    )
    register_gate(
        "O0-C-01-c-1",
        lambda: _assert(parse_comment_date("prefix20260620suffix") is None),
    )
    register_gate(
        "O0-C-01-d-1",
        lambda: _assert(parse_comment_date("2026062 x") is None),
    )
    register_gate(
        "O0-C-01-e-1",
        lambda: _assert(parse_comment_date("  20260620 tail") == "20260620"),
    )
    register_gate(
        "O0-C-02-a-1",
        lambda: _assert(not comment_matches_identity(None, _IDENTITY_DRE)),
    )
    register_gate(
        "O0-C-02-b-1",
        lambda: _assert(not comment_matches_identity(_COMMENT_DRE, None)),
    )
    register_gate(
        "O0-C-02-c-1",
        lambda: _assert(not comment_matches_identity("20260619 other", _IDENTITY_DRE)),
    )
    register_gate(
        "O0-C-02-d-1",
        lambda: _assert(comment_matches_identity(_COMMENT_DRE, _IDENTITY_DRE)),
    )
    register_gate(
        "O0-C-02-e-1",
        lambda: _assert(
            comment_matches_identity(
                "20260620 DRe(1.5)@600°C Ni5_Ce5_Al2O3",
                _IDENTITY_DRE,
            )
        ),
    )
    register_gate(
        "O0-C-03-a-1",
        lambda: _assert(sort_key_from_comment("no date") > sort_key_from_comment("20260101 x")),
    )

    # --- O0-C-04 — 장비 접미사 (Task C: _DRM 장비 / _OCM 장비) ---
    register_gate(
        "O0-C-04-a-1",
        lambda: _assert(
            strip_equipment_suffix(_COMMENT_DRE_SUFFIX)
            == "20260620 DRE(1.5)@600°C Ni5_Ce5_Al2O3"
        ),
    )
    register_gate(
        "O0-C-04-b-1",
        lambda: _assert(
            strip_equipment_suffix(
                "20260620 DRME(1.5%)@600°C Ni5/Al2O3_OCM 장비"
            )
            == "20260620 DRME(1.5%)@600°C Ni5/Al2O3"
        ),
    )
    register_gate(
        "O0-C-04-c-1",
        lambda: _assert(parse_equipment_suffix(_COMMENT_DRE_SUFFIX) == "GC2"),
    )
    register_gate(
        "O0-C-04-d-1",
        lambda: _assert(
            parse_equipment_suffix("20260620 DRE(1.5%)@600°C x_OCM 장비") == "GC3"
        ),
    )
    register_gate(
        "O0-C-04-e-1",
        lambda: _assert(
            comment_matches_identity(_COMMENT_DRE_SUFFIX, _IDENTITY_DRE)
        ),
    )

    # --- O0-S ---
    register_gate(
        "O0-S-01-a-1",
        lambda: _assert(column_to_origin_list([None], gap_policy=GapPolicy.AS_EMPTY) == [""]),
    )
    register_gate(
        "O0-S-01-b-1",
        lambda: _assert(
            math.isnan(
                column_to_origin_list([float("nan")], gap_policy=GapPolicy.AS_NAN)[0]
            )
        ),
    )
    register_gate(
        "O0-S-01-c-1",
        lambda: _assert(column_to_origin_list([0.0], gap_policy=GapPolicy.AS_EMPTY) == [0.0]),
    )
    register_gate(
        "O0-S-01-d-1",
        lambda: _assert(column_to_origin_list([""], gap_policy=GapPolicy.AS_EMPTY) == [""]),
    )
    register_gate(
        "O0-S-02-a-1",
        lambda: _assert(
            len(column_to_origin_list([1.0, float("nan")], gap_policy=GapPolicy.AS_EMPTY)) == 2
        ),
    )
    register_gate(
        "O0-S-02-b-1",
        lambda: _assert(
            column_to_origin_list([1.0, float("nan"), float("nan"), 4.0], gap_policy=GapPolicy.AS_EMPTY)
            == [1.0, "", "", 4.0]
        ),
    )
    register_gate(
        "O0-S-02-c-1",
        lambda: _assert(
            column_to_origin_list([1.0, float("nan")], gap_policy=GapPolicy.AS_EMPTY)[0] == 1.0
        ),
    )
    register_gate(
        "O0-S-03-a-1",
        lambda: _assert(len(column_to_origin_list([1.0, float("nan")], gap_policy=GapPolicy.AS_NAN)) == 2),
    )
    register_gate(
        "O0-S-03-b-1",
        lambda: _assert(
            math.isnan(column_to_origin_list([float("nan")], gap_policy=GapPolicy.AS_NAN)[0])
        ),
    )
    register_gate(
        "O0-S-04-a-1",
        lambda: _assert(
            len(column_to_origin_list([1.0, float("nan"), 3.0], gap_policy=GapPolicy.SKIP_ROWS)) < 3
        ),
    )
    register_gate(
        "O0-S-04-b-1",
        lambda: _assert(
            column_to_origin_list([1.0, float("nan"), 3.0], gap_policy=GapPolicy.SKIP_ROWS)
            == [1.0, 3.0]
        ),
    )
    register_gate(
        "O0-S-05-a-1",
        lambda: _assert(column_to_origin_list([1.0, 2.0], gap_policy=GapPolicy.AS_EMPTY) == [1.0, 2.0]),
    )
    register_gate(
        "O0-S-05-b-1",
        lambda: _assert(
            column_to_origin_list(pd.Series([10.0, None]), gap_policy=GapPolicy.AS_EMPTY)
            == [10.0, ""]
        ),
    )
    register_gate(
        "O0-S-05-c-1",
        lambda: _assert(column_to_origin_list([], gap_policy=GapPolicy.AS_EMPTY) == []),
    )
    register_gate(
        "O0-S-06-a-1",
        lambda: _assert(len(column_to_origin_list(_gc3_gap_series(), gap_policy=GapPolicy.AS_EMPTY)) == 107),
    )
    register_gate(
        "O0-S-06-b-1",
        lambda: (
            out := column_to_origin_list(_gc3_gap_series(), gap_policy=GapPolicy.AS_EMPTY),
            _assert(out[99] == ""),
            _assert(out[100] == ""),
            _assert(out[99] != 0.0),
        )[-1],
    )

    # --- O0-M ---
    register_gate(
        "O0-M-01-a-1",
        lambda: _assert(len(DEFAULT_ORIGIN_MAPPING) == 8),
    )
    register_gate(
        "O0-M-01-b-1",
        lambda: _assert("H2 Yield (%)" in DEFAULT_ORIGIN_MAPPING),
    )
    register_gate(
        "O0-M-01-c-1",
        lambda: _assert("CH4 Conversion (%)" in DEFAULT_ORIGIN_MAPPING),
    )
    register_gate(
        "O0-M-02-a-1",
        lambda: _raises(MappingValidationError, lambda: validate_mapping({})),
    )
    register_gate(
        "O0-M-02-b-1",
        lambda: _raises(MappingValidationError, lambda: validate_mapping({"": "H2 yield"})),
    )
    register_gate(
        "O0-M-02-c-1",
        lambda: _raises(MappingValidationError, lambda: validate_mapping({"col": ""})),
    )
    register_gate(
        "O0-M-02-d-1",
        lambda: _raises(
            MappingValidationError,
            lambda: validate_mapping({"A": "H2 yield", "B": "H2  yield"}),
        ),
    )
    register_gate(
        "O0-M-02-e-1",
        lambda: _assert(validate_mapping() is not DEFAULT_ORIGIN_MAPPING),
    )
    register_gate("O0-M-03-a-1", _gate_o0_m_03_a_1)
    register_gate("O0-M-03-b-1", _gate_o0_m_03_b_1)

    # --- O0-T ---
    register_gate(
        "O0-T-01-a-1",
        lambda: _assert(isinstance(_IDENTITY_DRE, tuple) and len(_IDENTITY_DRE) == 2),
    )
    register_gate(
        "O0-T-01-b-1",
        lambda: _assert(re.fullmatch(r"\d{8}", _IDENTITY_DRE[0]) is not None),
    )
    register_gate(
        "O0-T-02-a-1",
        lambda: _assert(gap_policy_members() == {"AS_EMPTY", "AS_NAN", "SKIP_ROWS"}),
    )
    register_gate(
        "O0-T-02-b-1",
        lambda: _assert(issubclass(GapPolicy, str) and GapPolicy.AS_EMPTY == "empty"),
    )
    register_gate(
        "O0-T-03-a-1",
        lambda: (
            r := ProbeResult(ok=True, detail="x"),
            _assert(r.ok is True and r.detail == "x"),
        )[-1],
    )
    register_gate(
        "O0-T-04-a-1",
        lambda: _assert(isinstance(OriginPath("G:\\x.opju"), str)),
    )


def _gate_o0_k_02_b_1() -> None:
    _assert(keyword_in_normalized_text("H2 yield", "Book1 H2yield Sheet1"))
    _assert(not keyword_in_normalized_text("co2conversion", "Book1 H2yield"))


def _gate_o0_m_03_a_1() -> None:
    subset, skipped = mapping_for_df(frozenset({"H2 Yield (%)"}), DEFAULT_ORIGIN_MAPPING)
    _assert(len(skipped) == 7)
    _assert("H2 Yield (%)" in subset)


def _gate_o0_m_03_b_1() -> None:
    subset, _skipped = mapping_for_df(
        frozenset({"H2 Yield (%)", "missing"}), DEFAULT_ORIGIN_MAPPING
    )
    _assert(len(subset) == 1 and "H2 Yield (%)" in subset)


def _assert(condition: bool, msg: str = "") -> None:
    if not condition:
        raise AssertionError(msg or "assertion failed")


def _raises(exc_type: type[BaseException], fn) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")
