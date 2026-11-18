# -*- coding: utf-8 -*-
"""O8-C — sample job context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from data_pc_origin.o0_mapping import mapping_for_df, validate_mapping

IdentityKey = Tuple[str, str]


@dataclass(frozen=True)
class SampleContext:
    opju_path: str
    df: Any
    sample_name: str
    identity_key: IdentityKey | None
    mapping: Dict[str, str]
    save_in_place: bool = True
    pe_folder: str = ""
    reaction_type: str = ""
    equipment: str = ""


def build_context(
    opju_path: str,
    df: Any,
    sample_name: str,
    *,
    identity_key: IdentityKey | None = None,
    mapping: Optional[Dict[str, str]] = None,
    save_in_place: bool = True,
    pe_folder: str | None = None,
    reaction_type: str | None = None,
    equipment: str | None = None,
) -> SampleContext:
    """validate_mapping + df subset (O8-C-02)."""
    from data_pc_origin.o0_pe_folder import resolve_pe_folder

    validated = validate_mapping(mapping)
    cols = set(getattr(df, "columns", []))
    subset, _skipped = mapping_for_df(cols, validated)
    reaction = (reaction_type or "").strip()
    equip = (equipment or "").strip()
    folder = resolve_pe_folder(
        pe_folder=pe_folder,
        reaction_type=reaction,
        equipment=equip,
        sample_name=sample_name,
    )
    return SampleContext(
        opju_path=opju_path,
        df=df,
        sample_name=sample_name,
        identity_key=identity_key,
        mapping=subset,
        save_in_place=save_in_place,
        pe_folder=folder,
        reaction_type=reaction,
        equipment=equip,
    )


def dataframe_row_count(df: Any) -> int:
    if hasattr(df, "__len__"):
        try:
            return int(len(df))
        except TypeError:
            pass
    cols = getattr(df, "columns", None)
    if cols is not None and len(cols) > 0:
        series = df[cols[0]]
        if hasattr(series, "__len__"):
            return int(len(series))
    return 0
