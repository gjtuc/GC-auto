# -*- coding: utf-8 -*-
"""Gate package."""

from data_pc_origin.gates.registry import register_gate, rollup_gate_ids
from data_pc_origin.gates.runner import run_gate, run_rollup

__all__ = ["register_gate", "rollup_gate_ids", "run_gate", "run_rollup"]
