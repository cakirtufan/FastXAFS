# -*- coding: utf-8 -*-
"""
Created on Tue Jul  5 11:43:07 2016

@author: martin
"""
#import readline

#from epics import PV
import epics
DCM_ENERGY=epics.Motor('Energ:25002000motor')
#DCM_OFFSET=epics.Motor('Energ:25002000z2.B')

DMM_ENERGY=epics.Motor('Energ:25000007motor')

S1_LEFT         =epics.Motor('OMS58:25000000')
S1_RIGHT        =epics.Motor('OMS58:25000001')
S1_TOP          =epics.Motor('OMS58:25000002')
S1_BOTTOM       =epics.Motor('OMS58:25000003')
FILTER1         =epics.Motor('OMS58:25000004')  
FILTER2         =epics.Motor('OMS58:25000005')
M1_VERTICAL     =epics.Motor('OMS58:25000006')
DMM_THETA1      =epics.Motor('OMS58:25000007')
DMM_Y1          =epics.Motor('OMS58:25001000')
DMM_ROLL1       =epics.Motor('OMS58:25001001')
DMM_Z2          =epics.Motor('OMS58:25001002')
DMM_THETA2      =epics.Motor('OMS58:25001003')
DMM_Y2          =epics.Motor('OMS58:25001004')
DMM_OFFSET=DMM_Y2
DMM_BENDER      =epics.Motor('OMS58:25001005')
DMM_X           =epics.Motor('OMS58:25003004')

M2_VERTICAL     =epics.Motor('OMS58:25001006')
DCM_Y           =epics.Motor('OMS58:25001007')
DCM_THETA       =epics.Motor('OMS58:25002000')
#DCM_MONOBR      =epics.Motor('DCM1OS2L:l0202000')
DCM_ROLL1       =epics.Motor('OMS58:25002001')
DCM_Z2          =epics.Motor('OMS58:25002002')
DCM_Y2          =epics.Motor('OMS58:25002003')
DCM_ROLL2       =epics.Motor('OMS58:25002004')
DCM_PITCH2      =epics.Motor('OMS58:25002005')
#DCM_CR2ROPI     =epics.Motor('DCM1OS2L:l0202003')
DCM_YAW2        =epics.Motor('OMS58:25002006')
DCM_B_RIGHT     =epics.Motor('OMS58:25002007') 
DCM_B_LEFT      =epics.Motor('OMS58:25003000')
BEAMSTOP        =epics.Motor('OMS58:25003001')
S2_LEFT         =epics.Motor('OMS58:25003002')
S2_RIGHT        =epics.Motor('OMS58:25003003')
S2_TOP          =epics.Motor('OMS58:25003006')    
S2_BOTTOM       =epics.Motor('OMS58:25003005')
M5_VERTICAL     =epics.Motor('OMS58:25003004')    
WINDOW          =epics.Motor('OMS58:25003007')
S0_1            =epics.Motor('OMS58:25004000')
S0_2            =epics.Motor('OMS58:25004001')
EXP_W           =epics.Motor('OMS58:25004002')
DET_Y           =epics.Motor('OMS58:25007003')
EXP_TISCH       =epics.Motor('OMS58:25004004')
EXP_X           =epics.Motor('OMS58:25004005')
EXP_Y           =epics.Motor('OMS58:25004006')
EXP_Z           =epics.Motor('OMS58:25004007')
S3_LEFT         =epics.Motor('OMS58:25005000')
S3_RIGHT        =epics.Motor('OMS58:25005001')
S3_TOP          =epics.Motor('OMS58:25005002')
S3_BOTTOM       =epics.Motor('OMS58:25005003')
Pinx           =epics.Motor('OMS58:25007002')
Piny           =epics.Motor('OMS58:25007003')
EULER_PITCH     =epics.Motor('OMS58:25007005')    
EULER_ROLL      =epics.Motor('OMS58:25007006')    
TOPO_YAW        =epics.Motor('OMS58:25007007')
TOPO_X          =epics.Motor('OMS58:25008000')
TOPO_Y          =epics.Motor('OMS58:25008001')
TOPO_Z          =epics.Motor('OMS58:25008002')
TOPO_W          =epics.Motor('OMS58:25008003')
TOPO_PITCH      =epics.Motor('OMS58:25008004')
TOPO_ROLL       =epics.Motor('OMS58:25008005')
S4_HORSIZE      =epics.Motor('OMS58:25008006')
S4_VERSIZE      =epics.Motor('OMS58:25008007')

XANES_X      =epics.Motor('OMS58:25004005')
XANES_Y      =epics.Motor('OMS58:25004006')
XANES_Reference      =epics.Motor('OMS58:25004002')



S1_HORPOS       =epics.Motor('Slot:25000000gapPos')
S1_VERPOS       =epics.Motor('Slot:25000002gapPos')
S1_HORSIZE       =epics.Motor('Slot:25000000gapSize')
S1_VERSIZE      =epics.Motor('Slot:25000002gapSize')


S2_HORPOS       =epics.Motor('Slot:25003002gapPos')
S2_VERPOS       =epics.Motor('Slot:25003006gapPos')
S2_HORSIZE       =epics.Motor('Slot:25003002gapSize')
S2_VERSIZE      =epics.Motor('Slot:25003006gapSize')
 
S3_HORPOS       =epics.Motor('Slot:25005000gapPos')
S3_VERPOS       =epics.Motor('Slot:25005002gapPos')
S3_HORSIZE       =epics.Motor('Slot:25005000gapSize')
S3_VERSIZE      =epics.Motor('Slot:25005002gapSize')


try:
    hexax=epics.Motor('PIF206:x')
    hexay=epics.Motor('PIF206:y')
    hexaz=epics.Motor('PIF206:z')
    hexarotx=epics.Motor('PIF206:rotx')
    hexaroty=epics.Motor('PIF206:roty')
    hexarotz=epics.Motor('PIF206:rotz')
except: print('No PI Hexapod')

try:
    DCM_PIEZO =epics.Motor('PI662:Piezo1')
except: print('No PIEZO')

try:
    Smaract =epics.Motor('MCS2Lin:RFAm1')
                   #      smarAct:m1')
except: print('No PIEZO')


try:
 EXP_MICOS_W     =epics.Motor('PEGAS:miocb0101000')
 EXP_MICOS_X     =epics.Motor('PEGAS:miocb0101002')
 EXP_MICOS_Y     =epics.Motor('PEGAS:miocb0101003')
 EXP_MICOS_Z     =epics.Motor('PEGAS:miocb0101001')
 EXP_MICOS_W.LLM =0
 EXP_MICOS_W.HLM=720
 EXP_MICOS_X.LLM =0
 EXP_MICOS_X.HLM=150

 EXP_MICOS_Y.LLM =0
 EXP_MICOS_Y.HLM=150
 
 EXP_MICOS_Z.LLM =0
 EXP_MICOS_Z.HLM=100

 
 
except: print('No MICOS')


ioni13=epics.Device('K6485:miocb0113.', attrs=('VAL',))
ioni14=epics.Device('K6485:miocb0114.', attrs=('VAL',))
ioni17=epics.Device('K6485:miocb0117.', attrs=('VAL',))
#ioni1_myspot=epics.Device('K64851MF102L:14.', attrs=('VAL',))

DCM_THETA_ENC=epics.Device('IK342:2500001.', attrs=('VAL'))