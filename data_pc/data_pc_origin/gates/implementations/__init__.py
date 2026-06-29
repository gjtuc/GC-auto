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
from data_pc_origin.gates.implementations.p20_gates import register_p20_gates
from data_pc_origin.gates.implementations.p21_gates import register_p21_gates
from data_pc_origin.gates.implementations.p22_gates import register_p22_gates
from data_pc_origin.gates.implementations.p23_gates import register_p23_gates
from data_pc_origin.gates.implementations.p24_gates import register_p24_gates
from data_pc_origin.gates.implementations.p25_gates import register_p25_gates
from data_pc_origin.gates.implementations.p26_gates import register_p26_gates
from data_pc_origin.gates.implementations.p27_gates import register_p27_gates
from data_pc_origin.gates.implementations.p19_gates import register_p19_gates
from data_pc_origin.gates.implementations.p18_gates import register_p18_gates
from data_pc_origin.gates.implementations.p17_gates import register_p17_gates
from data_pc_origin.gates.implementations.p16_gates import register_p16_gates
from data_pc_origin.gates.implementations.p15_gates import register_p15_gates
from data_pc_origin.gates.implementations.p14_gates import register_p14_gates
from data_pc_origin.gates.implementations.p13_gates import register_p13_gates
from data_pc_origin.gates.implementations.p12_gates import register_p12_gates
from data_pc_origin.gates.implementations.p11_gates import register_p11_gates
from data_pc_origin.gates.implementations.p10_gates import register_p10_gates
from data_pc_origin.gates.implementations.p9_l_gates import register_p9_l_gates
from data_pc_origin.gates.implementations.p8_gates import register_p8_gates
from data_pc_origin.gates.implementations.p7_gates import register_p7_gates
from data_pc_origin.gates.implementations.p6_gates import register_p6_gates
from data_pc_origin.gates.implementations.p5_gates import register_p5_gates
from data_pc_origin.gates.implementations.p4_gates import register_p4_gates
from data_pc_origin.gates.implementations.p3_gates import register_p3_gates
from data_pc_origin.gates.implementations.p2_gates import register_p2_gates
from data_pc_origin.gates.implementations.p1_gates import register_p1_gates
from data_pc_origin.gates.implementations.p0_gates import register_p0_gates
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
        register_p0_gates()
        register_p1_gates()
        register_p2_gates()
        register_p3_gates()
        register_p4_gates()
        register_p5_gates()
        register_p6_gates()
        register_p7_gates()
        register_p8_gates()
        register_p9_l_gates()
        register_p10_gates()
        register_p11_gates()
        register_p12_gates()
        register_p13_gates()
        register_p14_gates()
        register_p15_gates()
        register_p16_gates()
        register_p17_gates()
        register_p18_gates()
        register_p19_gates()
        register_p20_gates()
        register_p21_gates()
        register_p22_gates()
        register_p23_gates()
        register_p24_gates()
        register_p25_gates()
        register_p26_gates()
        register_p27_gates()
        _GATES_LOADED = True
