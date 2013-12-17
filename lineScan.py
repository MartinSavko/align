#!/usr/bin/env python
'''Testing fast scans over the MD2 motors.'''

def lineScan(start, end, device, motor, observable):
    move(device, motor, start)
    move(device, motor, end)
    line = []
    while device.motor != end:
        line.append(device.motor, observable)
        
    return line
    
    
