#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Aligning procedures for Proxima 2A beamline'''

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

class scan(object):
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
    
    def __init__(self):
        self.md2 = PyTango.DeviceProxy('i11-ma-cx1/ex/md2')
        self.imag = PyTango.DeviceProxy('i11-ma-cx1/ex/imag.1')
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
                while abs(self.md2.read_attribute(self.shortFull[motor]).value - position[motor]) > epsilon:
                    self.wait(self.md2)
                    self.md2.write_attribute(self.shortFull[motor], position[motor])
            self.wait(self.md2)
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
        self.results['nbsteps'] = nbsteps
        self.results['lengths'] = lengths
        self.results['motors'] = motors
        
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
        

    def linearizedScan(self, positions, dependent):
        xyz = []

        for self.enumeratedPosition, position in enumerate(positions):
            self.positionAndValue = copy.deepcopy(position)
            self.moveToPosition(position)
            
            for observable in dependent:
                self.observe(observable)
                
            xyz.append(self.positionAndValue)

        self.results['xyz'] = copy.deepcopy(xyz)


    def observe(self, observable):
        if observable != 'diffraction' and observable[1].find('image') != -1:
            if observable[-1] == 'mean':
                self.positionAndValue[(observable[0], observable[1])] = observable[0].read_attribute(observable[1]).value.mean()
            else:
                self.positionAndValue[(observable[0], observable[1])] = observable[0].read_attribute(observable[1]).value
        else:
            self.collectObject.nbFrames = 4
            self.collectObject.template =  self.template.replace('CbsX', str(position['CbsX'])).replace('CbsZ', str(position['CbsZ']))
            print 'template', self.collectObject.template
            self.collectObject.collect()
            value = self.collectObject.imagePath + self.collectObject.template
            self.positionAndValue['diffraction'] = value
        

    def scan(self, nbsteps, lengths, dependent=[(self.imag, 'image', 'mean')]):
        
        start = time.time()
        
        self.putScannedObjectInBeam()
        
        self.dependent = dependent
        self.results['dependent'] = self.dependent
        
        motors = self.motors[self.what]        
        center = [self.md2.read_attribute(self.shortFull(attribute)).value for attribute in motors]
        
        positions = self.calculatePositions(center, nbsteps, lengths, motors)
        
        print positions
        print 'len(positions)', len(positions)
        
        self.linearizedScan(positions, dependent)
        
        end = time.time()
        self.duration = end - start
        self.results['duration'] = self.duration
        
        
    def setAperture(self, index=1):
        self.md2.write_attribute('CurrentApertureDiameterIndex', index)
        self.wait(self.md2)


    def setWhatToScan(self, what):
        self.what = what
        self.results['what'] = self.what

    
    def putScannedObjectInBeam(self):
        positionAttributeOfScannedObject = {'capillary': 'CapillaryBSPosition', 
                                            1: 'AperturePosition', 
                                            2: 'AperturePosition', 
                                            3: 'AperturePosition'}
                                            
        self.md2.write_attribute(positionAttributeOfScannedObject[self.what], 1)
        self.wait(self.md2)

        
    def saveScan(self):
        apcap = {1: 'aperture_100um', 2: 'aperture_50um', 3: 'aperture_20um', 'capillary': 'capillary'}
        filename = apcap[self.results['what']] + '_' + self.results['datetime'].replace(' ', '_') + '.pck'

        f = open(filename, 'w')
        pickle.dump(self.results, f)
        f.close()
    
    
def main():
    import optparse
    
    usage = 'Program to perform grid scan of apertures and capillary beamstop of MD2, and find it\'s center with respect to the beam. The program will do the scan of 100um aperture by default.'
    parser = optparse.OptionParser(usage = usage)

    parser.add_option('-a', '--aperture', default=1, type = int, help = 'scan selected aperture (1 for 100um, 2 for 50um, 3 for 20um) (default: %default)')
    parser.add_option('-c', '--capillary', action='store_true', help = 'scan capillary')
    parser.add_option('-x', '--nxsteps', default=5, type=int, help='number of steps in x direction (default: %default)')
    parser.add_option('-y', '--nysteps', default=10, type=int, help='number of steps in y direction (default: %default)')
    parser.add_option('-H', '--hlength', default=.5, type=float, help='length of scan in x direction (mm) (default: %default)')
    parser.add_option('-V', '--vlength', default=1., type=float, help='length of scan in y direction (mm) (default: %default)')
    
    (options, args) = parser.parse_args()
    print options
    print args
    
    nbsteps = (options.nxsteps, options.nysteps)
    lengths = (options.hlength, options.vlength)
    
    print 'nbsteps', nbsteps
    print 'lengths', lengths
    
    s = scan()
    
    if options.capillary:
        s.setWhatToScan('capillary')
        
    else:
        s.setWhatToScan(options.aperture)
        s.setAperture(options.aperture)
    
    print 'scanning', s.what
    print 'a.scan(nbsteps, lengths)', nbsteps, lengths
    s.scan(nbsteps, lengths)
    print 'The scan took', s.results['duration'], 'seconds'
    
    s.saveScan()
    
if __name__ == '__main__':
    main()
    

        
    