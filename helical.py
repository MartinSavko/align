#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyTango

md2 = PyTango.DeviceProxy('i11-ma-cx1/ex/md2')

#helical motors are
#phiX
#phiY
#phiZ
#sampX
#sampY

centredPoints = []

motorsNames = [ 
                'PhiTableXAxisPosition', 
                'PhiTableYAxisPosition', 
                'PhiTableZAxisPosition',
                'CentringTableXAxisPosition', 
                'CentringTableYAxisPosition'
              ]

motorShortNames = ['PhiX', 'PhiY', 'PhiZ', 'SamX', 'SamY']

shortFull = dict(zip(motorShortNames, motorsNames))


def moveToCollectPoint(motorPositions={}):
    if grid and motorPositions != {}:
        md2.write_attribute('PhiTableXAxisPosition', motorPositions['PhiX'])
        md2.write_attribute('PhiTableYAxisPosition', motorPositions['PhiY'])
        md2.write_attribute('PhiTableZAxisPosition', motorPositions['PhiZ'])
        md2.write_attribute('CentringTableXAxisPosition', motorPositions['SamX'])
        md2.write_attribute('CentringTableYAxisPosition', motorPositions['SamY'])
    return
    

def getMotorValues():
    position = {}
    for motor in motorShortNames:
        position[motor] = md2.read_attribute(shortFull[motor]).value
        
    return position
   

def saveCentringPoint(motorPositions={}):
    if motorPositions != {}:
        centredPoints.append(motorPositions)
        

def getBeamSizeX():
    return 10.
    
    
def calculateHelicalOffset(start, final, nImages, Phi_start, oscillation, overlap):
    PhiY_range = start['PhiY'] - final['PhiY']
    bsx = getBeamSizeX()
    helical_start = {}
    helical_final = {}
    
    helical_start['SamX'] = (start['SamX'] - final['SamX']) / PhiY_range
    helical_start['SamY'] = (start['SamY'] - final['SamY']) / PhiY_range
    helical_start['PhiZ'] = (start['PhiZ'] - final['PhiZ']) / PhiY_range
    
    helical_final['SamX'] = (start['PhiY'] * final['SamX'] - final['PhiY'] * start['SamX']) / PhiY_range
    helical_final['SamY'] = (start['PhiY'] * final['SamY'] - final['PhiY'] * start['SamY']) / PhiY_range
    helical_final['PhiZ'] = (start['PhiY'] * final['PhiZ'] - final['PhiY'] * start['PhiZ']) / PhiY_range
    
    Phi_range = nImages * (oscillation - overlap)
    Phi_final = Phi_start + Phi_range
    
    helical_start['PhiY'] = PhiY_range / Phi_range
    helical_final['PhiY'] = (Phi_start * helical_final['PhiY'] - Phi_final * helical_start['PhiY']) / Phi_range
    
    return helical_start, helical_final
    

def calculateCollectPoint(n, nImages, Phi_start, oscillation, overlap, start, final):
    
    offset_start, offset_final =  calculateOffset(start, final, nImages, Phi_start, oscillation, overlap)
    
    motorPositions = {}
    
    Phi = Phi_start + n * (oscillation - overlap)
    #motorPositions['PhiX']
    motorPositions['PhiY'] = offset_start['PhiY'] * Phi + final['PhiY']
    motorPositions['PhiZ'] = offset_start['PhiZ'] * motorPositions['PhiY'] + offset_final['PhiZ']
    motorPositions['SamX'] = offset_start['SamX'] * motorPositions['PhiY'] + offset_final['SamX']
    motorPositions['SamY'] = offset_start['SamY'] * motorPositions['PhiY'] + offset_final['SamY']
    
    return motorPositions{}