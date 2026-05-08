"""Beamline constants and PV names extracted from the production scripts."""

from __future__ import annotations


D_SPACING = 0.31355

FILTER_POSITIONS = {
    "V K": 11,
    "V_K": 11,
    "Cr K": 14,
    "Cr_K": 14,
    "Mn K": 20,
    "Mn_K": 20,
    "Fe K": 7,
    "Fe_K": 7,
    "Co K": 2,
    "Co_K": 2,
    "Ni K": 9,
    "Ni_K": 9,
    "Cu K": 5,
    "Cu_K": 5,
    "Zn K": 18,
    "Zn_K": 18,
    "Se K": 8,
    "Se_K": 8,
}

ZEBRA_PVS = {
    "pc_dir": "BAMZEBRA:PC_DIR",
    "gate_start": "BAMZEBRA:PC_GATE_START",
    "gate_width": "BAMZEBRA:PC_GATE_WID",
    "gate_step": "BAMZEBRA:PC_GATE_STEP",
    "gate_ngate": "BAMZEBRA:PC_GATE_NGATE",
    "pulse_start": "BAMZEBRA:PC_PULSE_START",
    "pulse_step": "BAMZEBRA:PC_PULSE_STEP",
    "pulse_width": "BAMZEBRA:PC_PULSE_WID",
    "pulse_max": "BAMZEBRA:PC_PULSE_MAX",
    "sys_reset": "BAMZEBRA:SYS_RESET.PROC",
    "pc_arm": "BAMZEBRA:PC_ARM",
    "pc_disarm": "BAMZEBRA:PC_DISARM",
    "num_captured": "BAMZEBRA:PC_NUM_CAP",
    "div1": "BAMZEBRA:PC_DIV1",
    "div2": "BAMZEBRA:PC_DIV2",
    "div3": "BAMZEBRA:PC_DIV3",
    "encoder": "BAMZEBRA:PC_ENC2",
    "div_max": "BAMZEBRA:DIV2_DIV",
    "m2_eres": "BAMZEBRA:M2:ERES",
    "pos2_set": "BAMZEBRA:POS2_SET",
}

XSPRESS3_PVS = {
    "file_path": "XSP3_4Chan:HDF1:FilePath",
    "capture": "XSP3_4Chan:HDF1:Capture",
    "acquire": "XSP3_4Chan:det1:Acquire",
    "num_images": "XSP3_4Chan:det1:NumImages",
    "erase": "XSP3_4Chan:det1:ERASE",
    "update": "XSP3_4Chan:det1:UPDATE",
    "file_name": "XSP3_4Chan:HDF1:FileName",
    "trigger_mode": "XSP3_4Chan:det1:TriggerMode",
}

MOTOR_NAMES = {
    "dcm_energy": "DCM_ENERGY",
    "dcm_theta": "DCM_THETA",
    "sample_x": "XANES_X",
    "sample_y": "XANES_Y",
    "reference": "XANES_Reference",
}
