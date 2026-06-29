# mock 촉매 모듈 — P6 importlib 게이트·unittest 전용 (live GC 금지)

from __future__ import annotations

from data_pc_origin.o7_fixtures import _FakeDf, gc3_gap_series


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
    return _FakeDf(cols), r"G:\mock\calc.xlsx", ["warn"], "feed desc"


def generate_sample_name(filename: str) -> str:
    return "20250601 DRE(1.5) 600C mock"


def _experiment_identity_key(source: str):
    return ("20250601", "mock")


def reaction_type_from_output_file(saved_excel: str) -> str:
    return "DRE"


def setup_experiment_folder(source_excel, calculated_excel, reaction_type):
    return None, r"G:\mock\run.opju", r"G:\mock\run.xlsx"
