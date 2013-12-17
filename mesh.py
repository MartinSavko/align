#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyTango
import math
import itertools

md2 = PyTango.DeviceProxy('i11-ma-cx1/ex/md2')

motorsNames = [ 
                'PhiTableXAxisPosition', 
                'PhiTableYAxisPosition', 
                'PhiTableZAxisPosition',
                'CentringTableXAxisPosition', 
                'CentringTableYAxisPosition'
              ]

motorShortNames = ['PhiX', 'PhiY', 'PhiZ', 'cX', 'cY']

shortFull = dict(zip(motorShortNames, motorsNames))


def getMotorValues():
    position = {}
    for motor in motorShortNames:
        position[motor] = md2.read_attribute(shortFull[motor]).value
        
    return position
    
def getAxis(n):
    length = .5
    pointsPerLine = 10
    return length, pointsPerLine
    
Center = getMotorValues()

Length1, ppl1 = getAxis(1)
Length2, ppl2 = getAxis(2)