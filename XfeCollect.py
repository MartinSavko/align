#!/usr/bin/env python
# -*- coding: utf-8 -*-

import optparse
import time
import PyTango
import pylab
import numpy
import os
import pickle

class XfeCollect(object):
    def __init__(self, integrationTime = 1., directory = '/tmp', prefix = 'test', sessionId = None, sampleId = None):
        self.integrationTime = integrationTime
        self.directory = directory
        self.prefix = prefix
        self.sessionId = sessionId
        self.sampleId = sampleId
        self.filename = os.path.join(self.directory, self.prefix + '_fxe.png') #filename
        
        self.md2     = PyTango.DeviceProxy('i11-ma-cx1/ex/md2')
        self.ketek   = PyTango.DeviceProxy('i11-ma-cx1/dt/dtc-mca_xmap.1')
        #self.counter = PyTango.DeviceProxy('i11-ma-c00/ca/cpt.2')
        self.obx     = PyTango.DeviceProxy('i11-ma-c04/ex/obx.1')
        
        self.ketek.presettype = 1
        self.ketek.peakingtime = 2.5
        self.channelToeV = 10. #self.ketek.dynamicRange / len(self.ketek.channel00)
        
        try:
            os.mkdir(directory)
        except OSError, e:
            print e
        
    def canSpectrum(self):
        return True
        
    def setIntegrationTime(self, integrationTime = 1.):
        #self.counter.integrationTime = integrationTime
        self.ketek.presetvalue = int(integrationTime)
        
    def setROI(self, roi_debut = 0., roi_fin = 2048.):
        self.ketek.SetROIs(numpy.array((roi_debut, roi_fin)))
        #pass
    
    def insertDetector(self):
        self.md2.write_attribute('FluoDetectorBack', 0)
        time.sleep(5)
    
    def extractDetector(self):
        self.md2.write_attribute('FluoDetectorBack', 1)
        time.sleep(5)
    
    def startXfeSpectrum(self):
        self.measureSpectrum()
        return 
        
    def cancelXfeSpectrum(self):
        self.md2.CloseFastShutter()
        self.ketek.Abort()
        self.obx.Close()
        self.extractDetector()
        
    def isConnected(self):
        return True
        
    def measureSpectrum(self):
        self.setIntegrationTime(self.integrationTime)
        self.insertDetector()
        self.obx.Open()
        self.md2.OpenFastShutter()
        self.ketek.Start()
        #self.counter.Start()
        time.sleep(int(self.integrationTime))
        #while self.counter.State().name != 'STANDBY':
            #pass
        #self.ketek.Abort()
        self.md2.CloseFastShutter()
        self.obx.Close()
        self.extractDetector()
        
    def getSpectrum(self):
        return self.ketek.channel00
        
    def getMcaCalib(self):
        return None
        
    def getMcaConfig(self):
        return {'att': '7', 'energy': 12.65, 'bsX': 1, 'bsY': 2 }
    
    def getXvals(self):
        start, end   = 0, 2048 #self.ketek.roisStartsEnds
        #energy_start = start * self.channelToeV
        #energy_end   = end   * self.channelToeV
        #step = (energy_end - energy_start) / len(ketek.channel00)
        step = 1 #(end - start) / len(self.ketek.channel00)
        return numpy.arange(start, end, step)
        
    def getValue(self):
        return self.getXvals(), self.getSpectrum()
        
    def saveData(self):
        f = open(self.filename[:-4]  + '.pck', 'w')
        x = self.getXvals()
        y = self.getSpectrum()
        pickle.dump({'x': x, 'y': y}, f)
        f.close()
        
    def plotSpectrum(self):
        x = self.getXvals()
        y = self.getSpectrum()
        self.saveData(x, y)
        
        pylab.figure()
        pylab.plot(x, y)
        pylab.xlim(x[0], x[-1])
        pylab.title('X-ray fluorescence emission spectrum')
        pylab.xlabel('Channels')
        pylab.ylabel('Intensity [Counts]')
        pylab.savefig(self.filename)
        
        pylab.show()
        
if __name__ == '__main__':
    usage = 'Program to perform collect on PX2 beamline.\n\n%prog -n <number_of_images>\n\nNumber of images to be collected has to be specified, others are optional.'
    parser = optparse.OptionParser(usage = usage)

    parser.add_option('-e', '--exposure', default = 2.0, type = float, help = 'integration time (default: %default)')
    parser.add_option('-x', '--prefix', default = 'test', type = str, help = 'prefix (default = %default)')
    parser.add_option('-d', '--directory', default = '/tmp/fxetests2', type = str, help = 'where to store spectrum collected (default: %default)')

    (options, args) = parser.parse_args()
    print options
    print args
    
    doCollect = XfeCollect(options.exposure, options.directory, options.prefix)
    doCollect.setROI(1, 2048)
    time.sleep(0.5)
    #doCollect.setIntegrationTime()
    doCollect.measureSpectrum()
    doCollect.plotSpectrum()
    