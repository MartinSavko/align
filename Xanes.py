#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xabs_lib import McMaster
import time
import threading
import logging
import matplotlib.pyplot as plt
import numpy
import commands
import pickle
import math

class xanes(object):
    cutoff = 5
    
    def __init__(self,
                 element,
                 edge,
                 nbSteps=80,
                 roiwidth=0.30,
                 beforeEdge=0.030,
                 afterEdge=0.050,
                 integrationTime=0.64,
                 peakingTime=2.5,
                 dynamicRange=20000, #47200
                 presettype=1,
                 bleSteps=1,
                 bleMode='c', # possibilities 'a' (ascending), 'd' (descending), 'c' (center)
                 undulatorOffset=0.,
                 filterNumber=7,
                 transmission=1.,
                 directory='/tmp/testXanes',
                 prefix='test',
                 testFile='/927bis/ccd/gitRepos/Scans/pychooch/examples/SeFoil.raw',
                 transmission_min=0.001,
                 transmission_max=0.05,
                 epsilon=1e-3,
                 session_id=None,
                 blsample_id=None,
                 channelToeV=10.,
                 test=True,
                 save=True,
                 plot=True,
                 expert=False):

        # initialize logging

        self.element = element
        self.edge = edge
        self.prefix = prefix
        self.nbSteps = nbSteps
        self.roiwidth = roiwidth
        self.beforeEdge = beforeEdge
        self.afterEdge = afterEdge
        self.integrationTime = integrationTime
        self.peakingTime = peakingTime
        self.dynamicRange = dynamicRange
        self.bleSteps = bleSteps
        self.bleMode = bleMode
        self.undulatorOffset = undulatorOffset
        self.presettype = presettype
        self.filterNumber = filterNumber
        self.transmissionValue = transmission
        self.directory = directory
        self.prefix = prefix
        self.session_id = session_id
        self.blsample_id = blsample_id
        self.getAbsEm()
        self.scanRange = float(afterEdge + beforeEdge)
        self.testFile = testFile
        self.epsilon = epsilon
        
        # conversion between energy and channel
        self.channelToeV = channelToeV

        # state variables
        self.stt = None
        self.test = test
        self.save = save
        self.plot = plot
        self.Stop = False
        self.Abort = False
        self.newPoint = False
        self.expert = expert
        
    def initializeDevices(self):
        # Initialize all the devices used throughout the collect
        from PyTango import DeviceProxy as dp
        self.stt = 'Init'
        if self.test: 
            return
        self.fluodet = dp('i11-ma-cx1/dt/dtc-mca_xmap.1')
        self.fluodet.presettype = self.presettype
        self.fluodet.peakingtime = self.peakingTime
        self.fluodet.presetvalue = self.integrationTime
        self.mono = dp('i11-ma-c03/op/mono1')
        self.monoFine = dp('i11-ma-c03/op/mono1-mt_rx_fine')
        self.undulator = dp('ans-c11/ei/m-u24_energy')
        self.ble = dp('i11-ma-c00/ex/beamlineenergy')
        self.safetyShutter = dp('i11-ma-c04/ex/obx.1')
        self.md2 = dp('i11-ma-cx1/ex/md2')
        self.diode1 = dp('i11-ma-c04/dt/xbpm_diode.1')
        self.diode3 = dp('i11-ma-c05/dt/xbpm_diode.3')
        self.diode5 = dp('i11-ma-c06/dt/xbpm_diode.5')
        self.cvd = dp('i11-ma-c05/dt/xbpm-cvd.1')
        self.counter = dp('i11-ma-c00/ca/cpt.2')
        self.pss = dp('i11-ma-ce/pss/db_data-parser')
        
    def getAbsEm(self):
        self.e_edge, self.roi_center = self.getEdgefromXabs(
            self.element, self.edge)

    def prepare(self):
        
        self.initializeDevices()
        
        if self.test: 
            pass
        else:
            self.transmission(self.transmissionValue)
            self.attenuation(self.filterNumber)
            self.monoFine.On()

        self.getAbsEm()
        self.setROI()
        
        self.MD2Phase(phase=4)
        self.insertFluoDet()
        
        self.results = {}
        self.results['timestamp'] = time.time()
        self.results['prefix'] = self.prefix
        self.results['element'] = self.element
        self.results['edge'] = self.edge
        self.results['peakingTime'] = self.peakingTime
        self.results['dynamicRange'] = self.dynamicRange
        self.results['integrationTime'] = self.integrationTime
        self.results['nbSteps'] = self.nbSteps
        self.results['roiwidth'] = self.roiwidth
        self.results['roi_center'] = self.roi_center
        self.results['roi_debut'] = self.roi_debut
        self.results['roi_fin'] = self.roi_fin

    def cleanUp(self):
        self.saveRaw()
        self.chooch()
        self.saveResults()
        if self.test: 
            return
        self.transmission(95)
        self.attenuation(0)
        self.ble.write_attribute('energy', self.pk/1000.)
        self.extractFluodet()
        self.safeTurnOff(self.monoFine)
        
    def closeSafetyShutter(self):
        logging.info('Closing the safety shutter')
        if self.test:
            return
        self.safetyShutter.Close()

    def safeOpenSafetyShutter(self):
        logging.info(
            'Opening the safety shutter -- checking the hutch PSS state')
        if self.test: return
        if int(self.pss.prmObt) == 1:
            self.safetyShutter.Open()
            while self.safetyShutter.State().name != 'OPEN' and self.stt not in ['STOP', 'ABORT']:
                time.sleep(0.1)
        logging.info(self.safetyShutter.State().name)

    def openSafetyShutter(self):
        logging.info('Opening the safety shutter')
        if self.test:
            return
        while self.safetyShutter.State().name != 'OPEN' and self.stt not in ['STOP', 'ABORT']:
            logging.info(self.safetyShutter.State().name)
            self.safeOpenSafetyShutter()
            time.sleep(0.1)

    def safeTurnOff(self, device):
        if self.test: return
        if device.state().name == 'STANDBY':
            device.Off()

    def wait(self, device):
        if self.test: return
        while device.state().name == 'MOVING':
            time.sleep(.1)

        while device.state().name == 'RUNNING':
            time.sleep(.1)

    def MD2Phase(self, phase=4):
        if self.test: return
        self.md2.write_attribute('PhasePosition', phase)  # Collect phase
        self.wait(self.md2)

    def insertFluoDet(self):
        if self.test: return
        self.md2.write_attribute('FluoDetectorBack', 0)  # Move detector In
        time.sleep(4)

    def extractFluodet(self):
        if self.test: return
        self.md2.write_attribute('FluoDetectorBack', 1)  # Move detector Out
        
    def setROI(self):
        roi_debut = 1000.0 * \
            (self.roi_center - self.roiwidth / 2.0)  # values set in eV
        roi_fin   = 1000.0 * \
            (self.roi_center + self.roiwidth / 2.0)  # values set in eV
        channel_debut = int(roi_debut / self.channelToeV)
        channel_fin = int(roi_fin / self.channelToeV)
        self.roi_debut = roi_debut
        self.roi_fin = roi_fin
        if self.test: return
        self.fluodet.setROIs(numpy.array((channel_debut, channel_fin)))

    def transmission(self, x=None):
        '''Get or set the transmission'''
        if self.test: return 0
        from PyTango import DeviceProxy
        Fp = DeviceProxy('i11-ma-c00/ex/fp_parser')
        if x == None:
            return Fp.TrueTrans_FP

        Ps_h = DeviceProxy('i11-ma-c02/ex/fent_h.1')
        Ps_v = DeviceProxy('i11-ma-c02/ex/fent_v.1')
        Const = DeviceProxy('i11-ma-c00/ex/fpconstparser')

        truevalue = (2.0 - math.sqrt(4 - 0.04 * x)) / 0.02

        newGapFP_H = math.sqrt(
            (truevalue / 100.0) * Const.FP_Area_FWHM / Const.Ratio_FP_Gap)
        newGapFP_V = newGapFP_H * Const.Ratio_FP_Gap

        Ps_h.gap = newGapFP_H
        Ps_v.gap = newGapFP_V

    def attenuation(self, x=None):
        '''Read or set the attenuation'''
        if self.test: return 0
        from PyTango import DeviceProxy
        Attenuator = DeviceProxy('i11-ma-c05/ex/att.1')
        labels = ['00 None',
                  '01 Carbon 200um',
                  '02 Carbon 250um',
                  '03 Carbon 300um',
                  '04 Carbon 500um',
                  '05 Carbon 1mm',
                  '06 Carbon 2mm',
                  '07 Carbon 3mm',
                  '10 Ref Fe 5um',
                  '11 Ref Pt 5um']
        if x == None:
            status = Attenuator.Status()
            print 'status', status
            status = status[:status.index(':')]
            value = status
            return value
        NumToLabel = dict([(int(l.split()[0]), l) for l in labels])
        Attenuator.write_attribute(NumToLabel[x], True)
        self.wait(Attenuator)

    def getEdgefromXabs(self, element, edge):
        edge = edge.upper()
        roi_center = McMaster[element]['edgeEnergies'][edge + '-alpha']
        if edge == 'L':
            edge = 'L3'
        e_edge = McMaster[element]['edgeEnergies'][edge]

        return e_edge, roi_center

    def getObservationPoints(self):
        if self.test:
            print 'getObservationPoints in test mode'
            self.getTestData()
            print "self.testData['ens']", self.testData['ens']
            return self.testData['ens']
        points = numpy.arange(
            0., 1. + 1. / (self.nbSteps), 1. / (self.nbSteps))
        points *= self.scanRange
        points -= self.beforeEdge
        points += self.e_edge
        points = numpy.array([round(en, self.cutoff) for en in points])
        return points

    def getBLEPoints(self):
        if self.bleSteps == 1:
            return [self.e_edge]
        if self.bleMode == 'c':
            points = numpy.arange(0., 1., 1. / (2*s))[1::2]
        elif self.bleMode == 'a':
            points = numpy.arange(0., 1. + 1./(2*s), 1./(2*s))[2::2]
        elif self.bleMode == 'd':
            points = numpy.arange(0., 1., 1. / (2*s))[0::2]
        points *= self.scanRange
        points -= self.beforeEdge
        points += self.e_edge
        return points

    def getBleVsEn(self, ens, bles):
        return dict([(round(en, self.cutoff), bles[list(abs(en - bles)).index(min(list(abs(en - bles))))]) for en in ens])

    def setMono(self, energy):
        logging.info('setMono: energy %s' % energy)
        if self.test: return
        self.mono.write_attribute('energy', energy)
        self.wait(self.mono)

    def setBLE(self, energy):
        logging.info('setBLE')
        if self.test: return
        energy = round(energy, self.cutoff)
        if abs(self.ble.read_attribute('energy').w_value - self.BleVsEn[energy]) > self.epsilon:
            print 'setting undulator energy', energy
            print 'self.BleVsEn[energy]', self.BleVsEn[energy]
            self.ble.write_attribute('energy', self.BleVsEn[energy])
            self.wait(self.ble)
            if self.undulatorOffset != 0:
                self.undulator.gap += self.undulatorOffset
                self.wait(self.undulator)
            
    def setObservationParameters(self, energy):
        logging.info('setObservationParameters: energy %s' % energy)
        self.setBLE(energy)
        self.setMono(energy)
        
    
    def stop(self):
        logging.info('Stopping the scan')
        self.Stop = True
        self.stt = 'Stop'
    
    def abort(self):
        logging.info('Aborting the scan')
        self.stop()
        self.Abort = True
        self.stt = 'Abort'
        if self.test: return
        self.md2.CloseFastShutter()
    
    def start(self):
        logging.info('scan thread')
        self.scanThread = threading.Thread(target=self.scan)
        #self.scanThread.daemon = True
        self.scanThread.start()

    def scan(self):
        logging.info('scan started')
        if self.plot:
            plt.ion()
            self.plotInit()
        self.stt = 'Scanning'
        self.prepare()

        ens = self.getObservationPoints()
        bles = self.getBLEPoints()
        print 'ens'
        print ens
        print 'bles'
        print bles
        
        self.BleVsEn = self.getBleVsEn(ens, bles)
        
        print 'ble vs en'
        print self.BleVsEn
        
        self.safeOpenSafetyShutter()
        self.optimizeTransmission()
        
        self.results['transmission'] = self.transmission()
        self.results['attenuation'] = self.attenuation() #filterNumber
        self.results['points'] = ens
        self.results['ens'] = ens
        self.results['bles'] = bles
        self.results['observations'] = {}
        self.runningScan = {'ens': [], 'points': []}
        self.results['raw'] = self.runningScan
        
        for en in ens:
            en = round(en, self.cutoff)
            #logging.info('measuring at energy %s (%s of %s)' % (en, x(en), len(ens)))
            if self.stt == 'Stop':
                break
            self.setObservationParameters(en)
            self.measure()
            self.takePoint(en)
            self.updateRunningScan(en)
            if self.plot:
                self.newPoint = True
                self.plotNewPoint()
            
        self.closeSafetyShutter()
        self.results['duration'] = time.time() - self.results['timestamp']
        self.cleanUp()
        if self.plot:
            plt.ioff()
        self.stt = 'Finished'
        
    def measure(self):
        # measurement
        if self.test:
            time.sleep(self.integrationTime/10.)
            return
        self.md2.OpenFastShutter()
        self.fluodet.Start()
        self.wait(self.fluodet)
        self.md2.CloseFastShutter()
        
    def takePoint(self, en):
        logging.info('takePoint')
        # readout
        print 'en', en
        en = round(en, self.cutoff)
        if self.test:
            print 'en', en
            self.results[en] = {'point': self.testData[en]}
            return
        # measurement
        self.results['observations'][en] = {'roiCounts': self.fluodet.roi00_01,
                                            'inputCountRate00': self.fluodet.inputCountRate00,
                                            'outputCountRate00': self.fluodet.outputCountRate00,
                                            'eventsInRun': self.fluodet.eventsInRun00,
                                            'spectrum': self.fluodet.channel00,
                                            'diode1': self.diode1.intensity,
                                            'diode3': self.diode3.intensity,
                                            'diode5': self.diode5.intensity,
                                            'cvd': self.cvd.intensity}
        self.results['observations'][en]['point'] = self.results[en]['roiCounts'] / self.results[en]['diode5']
            
    def updateRunningScan(self, en):
        self.runningScan['ens'].append(en)
        self.runningScan['points'].append(self.results[en]['point'])
        
    def checkTransmission(self, results):
        if 30000 > results['inputCountRate00'] > 10000:
            return 'OK'
        elif results['inputCountRate00'] <= 10000:
            return 'Hop'
        elif results['inputCountRate00'] >= 30000:
            return 'Trop'
        else:
            return None

    def setMiddleTransmission(self):
        self.transmission((self.transmission_max - self.transmission_min) / 2.)

    def optimizeTransmission(self):
        logging.info('optimizeTransmission')
        print 'trying to optimize transmission'
        if (not self.expert): return
        print 'optimizeTransmission, where only experts should tread'
        return
        self.setBLE(self.e_edge + 0.01)

        self.attenuation(7)
        time.sleep(10.) #putting filter in takes some time, there might be better -- to actually check if it is done
        
        self.setMiddleTransmission(
            self.transmission_min, self.transmission_max)

        results = self.takePoint()
        while self.checkTransmission(results) != 'OK':
            if self.checkTransmission(results) == 'Hop':
                self.transmission_min = self.transmission()
            elif self.checkTransmission(results) == 'Trop':
                self.transmission_max = self.transmission()
            else:
                break
            self.setMiddleTransmission()
            time.sleep(0.5)
            results = takePoint()

    def saveDat(self):
        logging.info('saveDat')
        f = open('{prefix}_{element}_{edge}.dat'.format(**self.results), 'w')
        f.write('# EScan {date}\n'.format(**{'date': time.ctime(self.results['timestamp'])}))
        f.write('# Energy Motor i11-ma-c03/op/mono1\n')
        f.write('# Normalized value\n')
        f.write('# roi counts\n')
        f.write('# i11-ma-c04/dt/xbpm_diode.1\n')
        f.write(
            '# Counts on the fluorescence detector: all channels\n')
        f.write(
            '# Counts on the fluorescence detector: channels up to end of ROI\n')
        for en in ens:
            en = round(en, self.cutoff)
            normalized_intensity=self.results[en][
                'roiCounts'] / self.results[en]['diode1']
            f.write(
                ' {en} {normalized_intensity} {roiCounts} {diode1} {eventsInRun}\n'.format(**{'en': en,
                                                                                              'normalized_intensity': normalized_intensity,
                                                                                              'roiCounts': self.results[en]['roiCounts'],
                                                                                              'diode1': self.results[en]['diode1'],
                                                                                              'eventsInRun': self.results[en]['eventsInRun']}))
        f.write('# Duration: {duration}\n'.format(**self.results))
        f.close()

    def saveRaw(self):
        logging.info('saveRaw')
        f = open('{prefix}_{element}_{edge}.raw'.format(**self.results), 'w')
        f.write('Proxima 2A, Escan, {date}\n'.format(**{'date': time.ctime(self.results['timestamp'])}))
        f.write('{nbPoints}\n'.format(**{'nbPoints': len(self.results['points'])}))
        for en in self.results['points']:
            x = en < 1e3 and en*1e3 or en
            en = round(en, self.cutoff)
            point = self.results[en]['point']
            f.write('{en} {point}\n'.format(**{'en': x, 'point': point}))
        f.close()

    def saveResults(self):
        logging.info('saveResults')
        f = open('{prefix}_{element}_{edge}.pck'.format(**self.results), 'w')
        pickle.dump(self.results, f)
        f.close()

    def parse_chooch_output(self, output):
        logging.info('parse_chooch_output')
        print 'Chooch output'
        print output
        
        table = output[output.find('Table of results'):]
        tabl = table.split('\n')
        tab = numpy.array([ line.split('|') for line in tabl if line and line[0] == '|'])
        self.pk = float(tab[1][2])
        self.fppPeak = float(tab[1][3])
        self.fpPeak = float(tab[1][4])
        self.ip = float(tab[2][2])
        self.fppInfl = float(tab[2][3])
        self.fpInfl = float(tab[2][4])
        self.efs = self.getEfs()
        return {'pk': self.pk, 'fppPeak': self.fppPeak, 'fpPeak': self.fpPeak, 'ip': self.ip, 'fppInfl': self.fppInfl, 'fpInfl': self.fpInfl, 'efs': self.efs}
    
    def chooch(self):
        logging.info('chooch')
        chooch_parameters = {'element': self.element, 
                             'edge': self.edge,
                             'raw_file': '{prefix}_{element}_{edge}.raw'.format(**self.results),
                             'output_ps': '{prefix}_{element}_{edge}.ps'.format(**self.results),
                             'output_efs': '{prefix}_{element}_{edge}.efs'.format(**self.results)}
                     
        chooch_output = commands.getoutput('chooch -p {output_ps} -o {output_efs} -e {element} -a {edge} {raw_file}'.format(**chooch_parameters))
        self.results['chooch_output'] = chooch_output
        chooch_results = self.parse_chooch_output(chooch_output)
        self.results['chooch_results'] = chooch_results
        
    def getEfs(self):
        filename = '{prefix}_{element}_{edge}.efs'.format(**self.results)
        f = open(filename)
        data = f.read().split('\n')
        efs = numpy.array([numpy.array(map(float, line.split())) for line in data if len(line.split()) == 3])
        return efs
        
    def suivi(self):
        self.plotThread = threading.Thread(target=self.plot)
        self.plotThread.daemon = True
        self.plotThread.start()
        
    def plotInit(self):
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_title('Energy scan {element}, {edge}'.format(**{'element': self.element, 'edge': self.edge}))
        self.ax.set_xlabel('Energy [eV]')
        self.ax.set_ylabel('Normalized counts [a.u.]')
    
    def plotNewPoint(self):
        self.ax.plot(self.runningScan['ens'], self.runningScan['points'], 'bo-')
        plt.draw()

    def getRunningScan(self):
        ens = []
        points = []
        for en in self.results['ens']:
            en = round(en, self.cutoff)
            if self.results.has_key(en):
                ens.append(en)
                normalized_intensity = self.results[en]['roiCounts'] / self.results[en]['diode1']
                points.append(normalized_intensity)
        return ens, points
    
    def getTestData(self):
        logging.info('getTestData')
        self.testData = {}
        logging.info('self.testFile %s' % self.testFile)
        f = open(self.testFile)
        fr = f.read()
        lines = fr.split('\n')
        print 'lines', lines
        try:
            nPoints = int(lines[1])
        except ValueError:
            nPoints = len(lines) - 2
        ens = []
        points = []
        for l in lines[2: nPoints + 2]:
            ls = l.split()
            if len(ls) == 2:
                en = float(ls[0]) #round(float(ls[0]), self.cutoff)
                point = float(ls[1])
                ens.append(en)
                self.testData[en] = point
        self.testData['ens'] = numpy.array(ens)
        print 'self.testData'
        print self.testData
        logging.info('self.testData %s' % self.testData)
        
if __name__ == "__main__":
    #scan = xanes('Se', 'K', prefix='SeMet', testFile='/927bis/ccd/gitRepos/Scans/pychooch/examples/SeMet.raw')
    #points = scan.getObservationPoints()
    #print 'len(points)', len(points)
    #print points

    #print scan.element
    #print scan.e_edge
    
    #scan.scan()
    
    usage = '''Program for energy scans
    
    ./Xanes.py -e <element> -s <edge> <options>
    
    '''
    
    import optparse
    
    parser = optparse.OptionParser(usage=usage)
        
    parser.add_option('-e', '--element', type=str, help='Specify the element')
    parser.add_option('-a', '--edge', type=str, help='Specify the edge')
    parser.add_option('-n', '--steps', type=int, default=80, help='number of scan points (default=%default)')
    parser.add_option('-u', '--undulator', type=int, default=1, help='Number of optimal undulator positions during the scan (default=%default)')
    parser.add_option('-b', '--bleMode', type=str, default='c', help='Set the beamline in the center of the scanned region (\'c\' - default), at the beginning ("d" - descending) or at the end ("a" - ascending), (default=%default)')
    parser.add_option('-o', '--undulatorOffset', type=float, default=0, help='Offset to the undulator gap (default=%default)')
    parser.add_option('-r', '--roiWidth', type=float, default=0.300, help='ROI width in keV (default=%default)')
    parser.add_option('-s', '--beforeEdge', type=float, default=0.030, help='Start scan this much (in keV) before the theoretical edge (default=%default)')
    parser.add_option('-f', '--afterEdge', type=float, default=0.050, help='Start scan this much (in keV) before the theoretical edge (default=%default)')
    parser.add_option('-g', '--dynamicRange', type=int, default=20000, help='Set the dynamic range (in eV) of the fluorescence detector (default=%default)')
    parser.add_option('-i', '--integrationTime', type=float, default=0.64, help='Set the integration time in seconds (default=%default)')
    parser.add_option('-p', '--peakingTime', type=float, default=2.5, help='Set the integration time in microseconds (default=%default)')
    parser.add_option('-P', '--presetType', type=int, default=1, help='Set the presetType attribute of the ketek detector, default is 1, which means that the data aquisition is timed by internal clocks of the detector')
    parser.add_option('-T', '--transmission', default=None, help='Set the transmission. If not set, the optimal transmission search routine will try to determine the optimal value (default=%default)')
    parser.add_option('-A', '--filterNumber', type=int, default=7, help='Set the attenuation filter (default=%default)')
    parser.add_option('-d', '--directory', type='str', default='/tmp/testXanes', help='Directory to store the results (default=%default)')
    parser.add_option('-x', '--prefix', type='str', default='prefix', help='Prefix of the result files (default=%default)')

    parser.add_option('-t', '--test', action='store_true', help='Run in test mode (default=%default)')
    parser.add_option('-E', '--expert', action='store_true', help='Run in expert mode - do not touch the transmission and attenuation (default=%default)')
    options, args = parser.parse_args()
    
    print 'options', options
    print 'args', args
    
    x = xanes(options.element,
              options.edge,
              undulatorOffset = options.undulatorOffset,
              bleSteps = options.undulator,
              test = options.test,
              nbSteps = options.steps,
              roiwidth = options.roiWidth,
              beforeEdge = options.beforeEdge,
              afterEdge = options.afterEdge,
              integrationTime = options.integrationTime,
              peakingTime = options.peakingTime,
              dynamicRange = options.dynamicRange, #47200
              presettype = options.presetType,
              bleMode = options.bleMode, # possibilities 'a' (ascending), 'd' (descending), 'c' (center)
              filterNumber = options.filterNumber,
              transmission = options.transmission,
              directory = options.directory,
              prefix = options.prefix,
              transmission_min=0.001,
              transmission_max=0.05,
              epsilon=1e-3,
              session_id=None,
              blsample_id=None,
              channelToeV=10.,
              save=True,
              plot=True,
              expert=False)

    # initialize logging
    x.scan()
    x.saveRaw()
    x.saveResults()