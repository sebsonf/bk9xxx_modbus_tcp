# -*- coding: utf-8 -*-

# RTD Element:         NTC1K8
# Measurement Range:   -40°C - 130°C
# Resistance at 25°C:  1.8 kOhm

ADR_SENSOR_TYPE_RW  = 39
REG_ACCESS       = 0x80
REG_ACCESS_READ  = 0
REG_ACCESS_WRITE = 0x40
CODE_DISABLE_WRITE_PROTECTION = 0x1235
CODE_ENABLE_WRITE_PROTECTION = 0

ADR_AD_RAW_VALUE_R = 0
ADR_AD_LINE_RES_RAW_VALUE_R = 1
ADR_DIAGNOSE_REGISTER_R = 6
ADR_BUS_TERMINAL_TYPE_R = 8
ADR_FIRMWARE_VERSION_R = 9

ADR_HARDWARE_VERSION_R = 16
ADR_MANUFACTURER_ADJUSTMENT_OFFSET_RW = 17
ADR_MANUFACTURER_ADJUSTMENT_GAIN_RW = 18
ADR_MANUFACTURER_SCALING_OFFSET_RW = 19
ADR_MANUFACTURER_SCALING_GAIN_RW = 20
ADR_MANUFACTURER_CALIB_OFFSET_RW = 23
ADR_MANUFACTURER_CALIB_GAIN_RW = 24
ADR_BUS_TERMINAL_TYPE_EXTENSION_R = 29
ADR_CODEWORD_REG_RW = 31

RTD_NTC1K8       = 0x0032
RTD_NTC1K8_TK    = 0x0033
RTD_NTC2K2       = 0x0034
RTD_NTC3K        = 0x0035
RTD_NTC5K        = 0x0036
RTD_NTC10K       = 0x0037
RTD_NTC10KPRE    = 0x0038
RTD_TC10K_3204   = 0x0039
RTD_NTC10KTYP2   = 0x003A
RTD_NTC10KTYP3   = 0x003B
RTD_NTC10KDALE   = 0x003C
RTD_NTC10K3A221  = 0x003D
RTD_NTC20K       = 0x003E
POTI_0_1R        = 0x0064
POTI_1R          = 0x0065
RTD_NTC100K      = 0x00C8
RTD_NTC_CUSTOM   = 0x00FF
RTD_DEFAULT_NONE = 0x0000

A1 = 1.12119e-3
B1 = 2.35346e-4
C1 = 0
D1 = 8.34620e-8

def sensor_type_string(sensor_type_num):
    return {
        RTD_NTC1K8:         'RTD_NTC1K8',
        RTD_NTC1K8_TK:      'RTD_NTC1K8_TK',
        RTD_NTC2K2:         'RTD_NTC2K2',
        RTD_NTC3K:          'RTD_NTC3K',
        RTD_NTC5K:          'RTD_NTC5K',
        RTD_NTC10K:         'RTD_NTC10K',
        RTD_NTC10KPRE:      'RTD_NTC10KPRE',
        RTD_TC10K_3204:     'RTD_TC10K_3204',
        RTD_NTC10KTYP2:     'RTD_NTC10KTYP2',
        RTD_NTC10KTYP3:     'RTD_NTC10KTYP3',
        RTD_NTC10KDALE:     'RTD_NTC10KDALE',
        RTD_NTC10K3A221:    'RTD_NTC10K3A221',
        RTD_NTC20K:         'RTD_NTC20K',
        POTI_0_1R:          'POTI_0_1R',
        POTI_1R:            'POTI_1R',
        RTD_NTC100K:        'RTD_NTC100K',
        RTD_NTC_CUSTOM:     'RTD_NTC_CUSTOM',
        RTD_DEFAULT_NONE:   'RTD_DEFAULT_NONE'
    }.get(sensor_type_num)
