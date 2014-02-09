#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Aligning procedures for Proxima 2A beamline'''

import sys
import itertools
import pylab
import numpy
import math
import PyTango
import time
import pickle
import Collect
import copy
import optparse

class align(object):
    motorsNames = ['PhiTableXAxisPosition', 
                   'PhiTableYAxisPosition', 
                   'PhiTableZAxisPosition',
                   'CentringTableXAxisPosition', 
                   'CentringTableYAxisPosition',
                   'ApertureHorizontalPosition',
                   'ApertureVerticalPosition',
                   'CapillaryBSHorizontalPosition',
                   'CapillaryBSVerticalPosition']
                   
    motorShortNames = ['PhiX', 'PhiY', 'PhiZ', 'SamX', 'SamY', 'AprX', 'AprZ', 'CbsX', 'CbsZ']
    
    shortFull = dict(zip(motorShortNames, motorsNames))
    
    motors = {'aperture': ['AprX', 'AprZ'],
              'capillary': ['CbsX', 'CbsZ']}
    
    def __init__(self, motor_device='i11-ma-cx1/ex/md2'):
        self.motor_device = PyTango.DeviceProxy(motor_device)
        self.results = {'time': time.time(),
                        'datetime': time.asctime()}
                        
        
    def wait(self, device):
        while device.state().name == 'MOVING':
            time.sleep(.1)
        
        while device.state().name == 'RUNNING':
            time.sleep(.1)
            

    def moveToPosition(self, position={}, epsilon=0.0005):
        if position != {}:
            for motor in position:
                while abs(self.motor_device.read_attribute(self.shortFull[motor]).value - position[motor]) > epsilon:
                    self.wait(self.motor_device)
                    self.motor_device.write_attribute(self.shortFull[motor], position[motor])
            self.wait(self.motor_device)
        return
        

    def rotate(self, angle, unit='radians'):
        if unit != 'radians':
            angle = math.radians(angle)
            
        r = numpy.array([[ math.cos(angle),  math.sin(angle), 0.], 
                         [-math.sin(angle),  math.cos(angle), 0.], 
                         [              0.,               0., 1.]])
        return r
        

    def shift(self, displacement):
        s = numpy.array([[1., 0., displacement[0]], 
                         [0., 1., displacement[1]], 
                         [0., 0.,              1.]])
        return s


    def scale(self, factor):
        s = numpy.diag([factor[0], factor[1], 1.])
        return s
        

    def raster(self, grid):
        gs = grid.shape
        orderedGrid = []
        for i in range(gs[0]):
            line = grid[i, :]
            if (i + 1) % 2 == 0:
                line = line[: : -1]
            orderedGrid.append(line)
        return numpy.array(orderedGrid)
    
    
    def calculatePositions(self, center, nbsteps, lengths, motors):
        '''Calculate positions at which we will measure. 2D for now i.e. two motors only.'''
        center = numpy.array(center)
        nbsteps = numpy.array(nbsteps)
        lengths = numpy.array(lengths)
        
        stepsizes = lengths / nbsteps
        
        print 'center', center
        print 'nbsteps', nbsteps
        print 'lengths', lengths
        print 'stepsizes', stepsizes
        
        # adding [1] so that we can use homogeneous coordinates
        positions = list(itertools.product(range(nbsteps[0]), range(nbsteps[1]), [1])) 
        
        points = [numpy.array(position) for position in positions]
        points = numpy.array(points)
        points = numpy.dot(self.shift(- nbsteps / 2.), points.T).T
        points = numpy.dot(self.scale(stepsizes), points.T).T
        points = numpy.dot(self.shift(center), points.T).T
        grid = numpy.reshape(points, numpy.hstack((nbsteps, 3)))
        rasteredGrid = self.raster(grid)
        orderedPositions = rasteredGrid.reshape((grid.size/3, 3))
        dictionariesOfOrderedPositions = [{motors[0]: position[0], motors[1]: position[1]} for position in orderedPositions]
        
        self.results['points'] = points
        self.results['grid'] = grid
        self.results['rasteredGrid'] = rasteredGrid
        self.results['orderedPositions'] = orderedPositions
        self.results['dictionariesOfOrderedPositions'] = dictionariesOfOrderedPositions
        
        return dictionariesOfOrderedPositions
        

    def linearizedScan(self, positions, observable):
        xyz = []
        lp = len(positions)
        for k, position in enumerate(positions):
            if k % 5 == 0:
                print k
                print 'moving to position %s (%d of %d)' % (str(position), k, lp)
            self.positionAndValues = copy.deepcopy(position)
            self.moveToPosition(position)
            
            #for o in observable:
            self.observe(observable)
            
            xyz.append(self.positionAndValues)

        self.results['xyz'] = copy.deepcopy(xyz)


    def observe(self, observable):
        if observable != 'diffraction' and observable['attribute'].find('image') != -1:
            if observable['economy'] == 'mean':
                self.positionAndValues[(observable['device'], observable['attribute'])] = self.sensor_device.read_attribute(observable['attribute']).value.mean()
            else:
                self.positionAndValues[(observable['device'], observable['attribute'])] = self.sensor_device.read_attribute(observable['attribute']).value
        else:
            self.collectObject.nbFrames = 4
            self.collectObject.template =  self.template.replace('CbsX', str(position['CbsX'])).replace('CbsZ', str(position['CbsZ']))
            print 'template', self.collectObject.template
            self.collectObject.collect()
            value = self.collectObject.imagePath + self.collectObject.template
            self.positionAndValues['diffraction'] = value
        

    def scan(self, nbsteps, lengths, observable={'device': 'i11-ma-cx1/ex/imag.1', 'attribute': 'image', 'economy': 'mean'}): #self.imag
        # observable is dictionary which contains three entries: the 'device' refers to the device through which we access sensors, 'attribute' referring list of attributes to record and 'economy' that is intended for multidimensional measurements to indicate whether full measurement or just some global value (like e.g. mean) should be stored. 
        start = time.time()
        self.sensor_device = PyTango.DeviceProxy(observable['device'])
        self.results['nbsteps'] = nbsteps
        self.results['lengths'] = lengths
        
        self.putScannedObjectInBeam()
        
        self.observable = observable
        self.results['observable'] = self.observable
        if observable.has_key('device'):
            self.sensor_device = PyTango.DeviceProxy(observable['device'])
        else:
            self.sensor_device = observable
            
        motors = self.motors[self.what]
        self.results['motors'] = motors
        
        # center will contain current values of the scanned object
        center = [self.motor_device.read_attribute(self.shortFull[motor]).value for motor in motors]
        print 'center', center

        # precalculating all the measurement positions
        positions = self.calculatePositions(center, nbsteps, lengths, motors)
        self.results['positions'] = positions
        
        print positions
        print 'len(positions)', len(positions)
        
        self.linearizedScan(positions, observable)
        
        end = time.time()
        self.duration = end - start
        self.results['duration'] = self.duration
        self.putScannedObjectInBeam()
        
    def setAperture(self, index=1):
        self.motor_device.write_attribute('CurrentApertureDiameterIndex', index)
        self.wait(self.motor_device)


    def setWhatToScan(self, what):
        self.what = what
        self.results['what'] = self.what

    
    def putScannedObjectInBeam(self):
        positionAttributeOfScannedObject = {'capillary': 'CapillaryBSPosition', 
                                            'aperture': 'AperturePredefinedPosition'}
        # Put scanned object (capillary beamstop or an aperture into beam
        self.motor_device.write_attribute(positionAttributeOfScannedObject[self.what], 1)
        self.wait(self.motor_device)

        
    def saveScan(self):
        apcap = {1: 'aperture_100um', 2: 'aperture_50um', 3: 'aperture_20um', 4: 'aperture_10um', 5: 'aperture_05um', 'aperture': 'aperture', 'capillary': 'capillary'}
        if self.what != 'aperture':
            what = self.what
        else:
            what = apcap[self.motor_device.read_attribute('CurrentApertureDiameterIndex').value]
        filename = what + '_' + '_'.join(self.results['datetime'].split()) + '.pck'

        f = open(filename, 'w')
        pickle.dump(self.results, f)
        f.close()
    
    
def main():
    import optparse
    
    usage = 'Program to perform grid scan of apertures and capillary beamstop of MD2, and find it\'s center with respect to the beam. The program will do the scan of 100um aperture by default.'
    parser = optparse.OptionParser(usage = usage)

    parser.add_option('-a', '--aperture', default=1, type = int, help = 'scan selected aperture (1 for 100um, 2 for 50um, 3 for 20um) (default: %default)')
    parser.add_option('-c', '--capillary', action='store_true', help = 'scan capillary')
    parser.add_option('-x', '--nxsteps', default=4, type=int, help='number of steps in x direction (default: %default)')
    parser.add_option('-y', '--nysteps', default=8, type=int, help='number of steps in y direction (default: %default)')
    parser.add_option('-H', '--hlength', default=.3, type=float, help='length of scan in x direction (mm) (default: %default)')
    parser.add_option('-V', '--vlength', default=.6, type=float, help='length of scan in y direction (mm) (default: %default)')
    
    (options, args) = parser.parse_args()
    print options
    print args
    
    nbsteps = (options.nxsteps, options.nysteps)
    lengths = (options.hlength, options.vlength)
    
    print 'nbsteps', nbsteps
    print 'lengths', lengths
    
    a = align()
    
    if options.capillary:
        a.setWhatToScan('capillary')
        
    else:
        a.setWhatToScan('aperture')
        a.setAperture(options.aperture)
    
    print 'scanning', a.what
    print 'a.scan(nbsteps, lengths)', nbsteps, lengths
    #sys.exit()
    a.scan(nbsteps, lengths)
    print 'The scan took', a.results['duration'], 'seconds'
    
    a.saveScan()
    
if __name__ == '__main__':
    main()
    

        
    