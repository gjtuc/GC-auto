# -*- coding: utf-8 -*-
from data_pc_origin.gates.implementations.o0_gates import register_o0_gates
from data_pc_origin.gates.implementations.o1_gates import register_o1_gates
from data_pc_origin.gates.implementations.o2_gates import register_o2_gates
from data_pc_origin.gates.implementations.o3_gates import register_o3_gates
from data_pc_origin.gates.implementations.o4_gates import register_o4_gates
from data_pc_origin.gates.implementations.o5_gates import register_o5_gates
from data_pc_origin.gates.implementations.o5_t_gates import register_o5_t_gates
from data_pc_origin.gates.implementations.o5_m_gates import register_o5_m_gates
from data_pc_origin.gates.implementations.o5_debug_gates import register_o5_debug_gates
from data_pc_origin.gates.implementations.o5_meta_gates import register_o5_meta_gates
from data_pc_origin.gates.implementations.o6_gates import register_o6_gates
from data_pc_origin.gates.implementations.o6_f_gates import register_o6_f_gates
from data_pc_origin.gates.implementations.o6_p_gates import register_o6_p_gates
from data_pc_origin.gates.implementations.o6_i_gates import register_o6_i_gates
from data_pc_origin.gates.implementations.o6_r_gates import register_o6_r_gates
from data_pc_origin.gates.implementations.o7_p_gates import register_o7_p_gates
from data_pc_origin.gates.implementations.o7_w_gates import register_o7_w_gates
from data_pc_origin.gates.implementations.o7_g_gates import register_o7_g_gates
from data_pc_origin.gates.implementations.o8_c_gates import register_o8_c_gates
from data_pc_origin.gates.implementations.o8_j_gates import register_o8_j_gates
from data_pc_origin.gates.implementations.o9_f_gates import register_o9_f_gates
from data_pc_origin.gates.implementations.o9_e2e_gates import register_o9_e2e_gates
from data_pc_origin.gates.implementations.o9_l_gates import register_o9_l_gates
from data_pc_origin.gates.implementations.o9_p_gates import register_o9_p_gates

_GATES_LOADED = False


def ensure_gates_loaded() -> None:
    global _GATES_LOADED
    if not _GATES_LOADED:
        register_o0_gates()
        register_o1_gates()
        register_o2_gates()
        register_o3_gates()
        register_o4_gates()
        register_o5_gates()
        register_o5_t_gates()
        register_o5_m_gates()
        register_o5_debug_gates()
        register_o5_meta_gates()
        register_o6_gates()
        register_o6_f_gates()
        register_o6_p_gates()
        register_o6_i_gates()
        register_o6_r_gates()
        register_o7_p_gates()
        register_o7_w_gates()
        register_o7_g_gates()
        register_o8_c_gates()
        register_o8_j_gates()
        register_o9_f_gates()
        register_o9_e2e_gates()
        register_o9_p_gates()
        register_o9_l_gates()
        _GATES_LOADED = True
