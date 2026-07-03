# mock 촉매 모듈 — P6 importlib 게이트·unittest 전용 (live GC 금지)
#
# 실제 `촉매 반응 계산.py` 와 동일한 표면 API 를 흉내 냅니다.
#   · process_excel → saved_excel 경로에 _GC2_/_GC3_ 포함 (equipment_from_output_file 용)
#   · generate_sample_name(filename, equipment=None) → 4-tuple
# live GC·IMAP 경로에서는 절대 import 하지 말 것.

from __future__ import annotations

from data_pc_origin.o7_fixtures import _FakeDf, gc3_gap_series

# P6 게이트·workflow_bridge smoke — GC2 DRE 계산완료 파일명 규칙
_MOCK_SAVED = r"G:\mock\in_GC2_DRE_계산완료.xlsx"


def process_excel(input_file: str):
    if input_file.endswith("_fail.xlsx"):
        return None, None, [], ""
    cols = {
        "C2H6 Conversion (%)": gc3_gap_series(),
        "CH4 Conversion (%)": gc3_gap_series(),
        "CO2 Conversion (%)": gc3_gap_series(),
        "H2 Yield (%)": gc3_gap_series(),
        "CO Yield (%)": gc3_gap_series(),
        "CH4 (%)": gc3_gap_series(),
        "C2H4 (%)": gc3_gap_series(),
        "C2H6 (%)": gc3_gap_series(),
    }
    return _FakeDf(cols), _MOCK_SAVED, ["warn"], "feed desc"


def equipment_from_output_file(saved_excel: str) -> str | None:
    """계산 완료 파일명 접미사로 장비 판별 — P6 adapter 가 generate_sample_name 에 전달."""
    base = (saved_excel or "").replace("\\", "/")
    if "_GC3_" in base:
        return "GC3"
    if "_GC2_" in base:
        return "GC2"
    if "_GC1_" in base:
        return "GC1"
    return None


def generate_sample_name(filename: str, equipment=None):
    """
    Origin Comments mock — Task C 4-tuple 계약.

    Returns:
        (sample_name, warnings, needs_user_input, question)
    """
    eq = equipment or equipment_from_output_file(_MOCK_SAVED) or "GC2"
    suffix = "_OCM 장비" if eq == "GC3" else "_DRM 장비"
    name = f"20250601 DRE(1.5%)@600°C mock{suffix}"
    return name, [], False, ""


def _experiment_identity_key(source: str):
    return ("20250601", "mock")


def reaction_type_from_output_file(saved_excel: str) -> str:
    return "DRE"


def setup_experiment_folder(source_excel, calculated_excel, reaction_type):
    return None, r"G:\mock\run.opju", r"G:\mock\run.xlsx"
