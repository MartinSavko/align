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
    
    
    def __init__(self, save=True):
        self.md2 = PyTango.DeviceProxy('i11-ma-cx1/ex/md2')
        self.imag = PyTango.DeviceProxy('i11-ma-cx1/ex/imag.1')
        self.ia = PyTango.DeviceProxy('i11-ma-cx1/ex/limaprosilica-analyzer')
        self.save = save


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
    
    
    def scan(self, center, nbsteps, lengths, attributes):
        '''2D scan on an md2 attribute'''
        
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
        print 'points'
        print points
        print
        points = numpy.dot(self.shift(- nbsteps / 2.), points.T).T
        points = numpy.dot(self.scale(stepsizes), points.T).T
        points = numpy.dot(self.shift(center), points.T).T
        
        grid = numpy.reshape(points, numpy.hstack((nbsteps, 3)))
        
        rasteredGrid = self.raster(grid)
        
        orderedPositions = rasteredGrid.reshape((grid.size/3, 3))
        
        
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
        print 'points'
        print points
        print
        points = numpy.dot(self.shift(- nbsteps / 2.), points.T).T
        points = numpy.dot(self.scale(stepsizes), points.T).T
        points = numpy.dot(self.shift(center), points.T).T
        
        self.points = points
        
        grid = numpy.reshape(points, numpy.hstack((nbsteps, 3)))
        
        rasteredGrid = self.raster(grid)
        
        orderedPositions = rasteredGrid.reshape((grid.size/3, 3))
        
        dictionariesOfOrderedPositions = [{motors[0]: position[0], motors[1]: position[1]} for position in orderedPositions]
        
        return dictionariesOfOrderedPositions
        
    #def tupleOutOfPosition
    def linearizedScan(self, positions, dependent, mode='economic'):
        measured = []
        xyz = []
        k = 0
        for position in positions:
            positionAndValue = copy.deepcopy(position)
            positionAndValue['values'] = {}
            values = []
            if k % 20 == 0:
                print k
                print 'moving to position', position
            k += 1
            self.moveToPosition(position)
            #print 'self.md2.state().name', self.md2.state().name
            #print 'AprX', self.md2.read_attribute(self.shortFull['AprX']).value
            #print 'AprZ', self.md2.read_attribute(self.shortFull['AprZ']).value
            #print 'ApertureVerticalPosition', self.md2.read_attribute('ApertureVerticalPosition').value
            #self.md2.CapillaryBSSaveInPosition()
            #self.md2.ApertureSaveInPosition()
            for observable in dependent:
                if observable == 'diffraction':
                    self.collectObject.nbFrames = 4
                    self.collectObject.template =  self.template.replace('CbsX', str(position['CbsX'])).replace('CbsZ', str(position['CbsZ']))
                    print 'template', self.collectObject.template
                    self.collectObject.collect()
                else:
                    if observable[1] == 'image' and mode == 'economic':
                        value = observable[0].read_attribute(observable[1]).value.mean()
                    else:
                        value = observable[0].read_attribute(observable[1]).value
                    
                    if k % 20 == 0:
                        print 'measured value', value
                    measured.append(value)
                    positionAndValue[(observable[0],observable[1])] = value
            xyz.append(positionAndValue)
            
        return measured, xyz
        

    def scanCBPS(self, nbsteps, lengths):
        print 'Starting capillary beam stop scan'
        #self.directory = '/927bis/ccd/2013/Run3/2013-07-21/Commissioning/CBPS/Scan25'
        #self.template = 'CBS_CbsX_CbsZ_1_####.img'
        #self.collectObject = Collect.collect(directory = self.directory,
                                             #template = self.template,
                                             #nImages = 4,
                                             #test = False)
        
        cHor = self.md2.CapillaryBSHorizontalPosition
        cVer = self.md2.CapillaryBSVerticalPosition
        center = [self.md2.CapillaryBSHorizontalPosition, self.md2.CapillaryBSVerticalPosition]
        motors = ['CbsX', 'CbsZ']
        positions = self.calculatePositions(center, nbsteps, lengths, motors)
        
        print positions
        print 'len(positions)', len(positions)
        
        measured, xyz = a.linearizedScan(positions, [(self.imag, 'image')]) # ['diffraction'])
        results = {'positions': positions, 'measured': measured}
        
        self.moveToPosition({'CbsX': cHor, 'CbsZ': cVer})
        self.md2.CapillaryBSSaveInPosition()
        
        f = open('cbps_scan_measured' + str(nbsteps) + '_' + str(lengths) + '_'.join(time.asctime().split()) + '.pck', 'w')
        pickle.dump(results, f)
        f.close()
        
        g = open('cbps_scan_xyz_' + str(nbsteps) + '_' + str(lengths) + '_'.join(time.asctime().split()) + '.pck', 'w')
        pickle.dump(results, g)
        g.close()


    def scanAperture(self, nbsteps, lengths):
        center = [self.md2.ApertureHorizontalPosition, self.md2.ApertureVerticalPosition]
        motors = ['AprX', 'AprZ']
        positions = self.calculatePositions(center, nbsteps, lengths, motors)
        
        print positions
        print 'len(positions)', len(positions)

        measured, xyz = self.linearizedScan(positions, [(self.imag, 'image')]) #(a.md2, 'image'), (a.ia, 'inputImage'),
        results = {'positions': positions, 'measured': measured}

        f = open('aperture_' + str(self.md2.CurrentApertureDiameterIndex) + '_scan_measured_' + str(nbsteps) + '_' + str(lengths) + '_'.join(time.asctime().split()) + '.pck', 'w')
        g = open('aperture_' + str(self.md2.CurrentApertureDiameterIndex) + '_scan_xyz_' + str(nbsteps) + '_' + str(lengths) + '_'.join(time.asctime().split()) + '.pck', 'w')
        pickle.dump(results, f)
        pickle.dump(xyz, g)
        f.close()
        g.close()
    
    
if __name__ == '__main__':
    start = time.time()
    a = align()
    
    fullsteps_aperture = [20, 40]
    fullsteps_cpbs = [80, 60]
    teststeps = [5, 10]
    nbsteps = fullsteps_aperture
    lengths_cpbs = [0.8, 0.6]
    lengths_aperture = [0.2, 0.4]
    lengths = lengths_aperture
    #a.scanCBPS(nbsteps, lengths)
    a.scanAperture(nbsteps, lengths)
    end = time.time()
    print 'The scan took', end - start, 'seconds'
    
    #import pylab
    #f = open('aperture_scan_Thu_Jul_11_02:28:21_2013.pck')
    #measured = pickle.load(f)
    #f.close()
    #a.scan([95.3, 0.6], [15, 10], [1.5, 1.], 'ach')
        
    