#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''This is a program beamline'''

from PyTango import DeviceProxy
import math

class Beamline(object):
    '''I'am the beamline'''

class Goniometer(object):
    '''Everything about the goniometer'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
class Detector(object):
    '''Everything about the detector'''
    adsc            =  DeviceProxy('i11-ma-cx1/dt/adsc')
    limaadsc        =  DeviceProxy('i11-ma-cx1/dt/limaadsc')
    
    
class Memory(object):
    '''Memory of the beamline, we'll try to remember everything'''
    

class Future(object):
    '''All prediction, machine learning algorithms should go here'''

#class FocusingMirrors(object):
    

#class Table(object):


class Slits(object):
    '''General slits'''

class PrimarySlits(Slits):
    '''Everything about the primary slits'''

class SecondarySlits(Slits):
    '''Everything about the secondary slits'''
    
class ExperimentalSlits(Slits):
    '''Everything about the experimental slits'''

class FluorescenceDetector():
    '''Everything about the fluorescence detector'''

class Mono(object):
    '''Everything about the mono'''

class Undulator(object):
    '''Everything about the undulator'''


def beamlineSnapshot(x = None):
    '''Will save the state of the beamline. Everything that can be stored, should be stored.'''
    
    
def OAVBeamCenterCalibration():
    '''Will determine beam center on the OAV'''

def moveToReferenceState():
    '''Will move the beamline to the reference state'''

def diffractionExperiment():
    '''Will perform a diffraction experiment'''

def energyScan():
    '''Will perform an energy scan'''

def XfeSpectrum():
    '''Will measure a X-ray fluorescence spectrum'''
    
def centerSample():
    '''Will center a sample in the beam'''

def beamShape():
    '''Set or get the beam shape'''
    
def transmission(x = None):
    '''Get or set the transmission'''
    Fp   = DeviceProxy('i11-ma-c00/ex/fp_parser')
    if x == None:
        return Fp.TrueTrans_FP
        
    Ps_h         = DeviceProxy('i11-ma-c02/ex/fent_h.1')
    Ps_v         = DeviceProxy('i11-ma-c02/ex/fent_v.1')
    Const        = DeviceProxy('i11-ma-c00/ex/fpconstparser')
    
    truevalue = (2.0 - math.sqrt(4 - 0.04 * x)) / 0.02

    newGapFP_H = math.sqrt( (truevalue / 100.0) * Const.FP_Area_FWHM / Const.Ratio_FP_Gap )
    newGapFP_V = newGapFP_H * Const.Ratio_FP_Gap
    
    Ps_h.gap = newGapFP_H
    Ps_v.gap = newGapFP_V
    
def attenuation(x = None):
    '''Read or set the attenuation'''
    Attenuator = DeviceProxy('i11-ma-c05/ex/att.1')
    labels = [  
                '00 Extract', 
                '01 Carbon 200um', 
                '02 Carbon 250um', 
                '03 Carbon 300um', 
                '04 Carbon 500um', 
                '05 Carbon 1mm', 
                '06 Carbon 2mm', 
                '07 Carbon 3mm', 
                '10 Ref Fe 5um', 
                '11 Ref Pt 5um'
             ]

    if x == None:
        status = Attenuator.Status()
        status = status[:status.index(':')]
        value = status
        return value
        
    NumToLabel = dict([(int(l.split()[0]), l) for l in labels])
    Attenuator.write_attribute(NumToLabel[x], True)
    
def energy(x = None):
    '''Read or set the energy of the beamline'''
    ble  = DeviceProxy('i11-ma-c00/ex/beamlineenergy')
    
    if x == None:
        return ble.energy
    
    ble.energy = x

def wavelength(x = None):
    mono = DeviceProxy('i11-ma-c03/op/mono1')
    
    if x == None:
        return mono.Lambda
        
    mono.Lambda = x
    
def distance(x = None):
    '''Read or set the detector distance'''
    ts = DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_ts')
    
    if x == None:
        return ts.position
    
    ts.position = x
       
    
def resolution(x = None):
    '''Read or set the resolution'''
    
    ts = DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_ts')
    
    diameter = 315. # detector diameter in mm
    radius = diameter / 2.
    distance = ts.position
    wavelen = wavelength()
    
    if x == None:
        theta = math.atan(radius / distance)
        resolution = 0.5 * wavelen / math.sin(theta / 2.)
        return resolution
    
    theta = math.asin(wavelen / 2. / x)
    distance = radius / math.tan(2. * theta)
    ts.position = distance
    

def detectorPosition(x = None):
    '''Read or set the detector position'''
    ts = DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_ts')
    tx = DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_tx')
    tz = DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_tz')
    
    if x == None:
        return ts.position, tx.position, tz.position
        
    ts.position, tx.position, tz.position = x
    
def beamCenterOnDetector():
    '''Return beam center on the detector'''
    d = distance()
    w = wavelength()
    Theta = numpy.matrix([[ 1.55557116e+03, 1.43720063e+03], [ -8.51067454e-02, -1.84118001e-03], [ -1.99919592e-01, 3.57937064e+00]]) #16.05.2013
    q = 0.102592 #pixel size in milimeters
    X = numpy.matrix ([1., d, w])
    
    Origin = Theta.T * X.T
    Origin = Origin * q
    
    return Origin[1], Origin[0]
    
def backLight():
    '''Read or set the sample back light value'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def frontLight():
    '''Read or set the sample front light value'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def zoom():
    '''Read or set the OAV zoom'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def focus():
    '''Read or set the OAV focus'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def horizontalMotor():
    '''Read or set the goniometer horizontal motor'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def verticalMotor():
    '''Read or set the goniometer vertical motor'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def phiMotor():
    '''Read or set the goniometer phi motor'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def frontendShutter(x = None):
    '''Read the state, close or open the frontend shutter'''
    tdl = DeviceProxy('tdl-i11-ma/vi/tdl.1')
    
    if x == None:
        return tdl.State()
    elif x == 0:
        tdl.Close()
    elif x == 1:
        tdl.Open()
    else:
        print 'Only possible arguments are None, 0 and 1'
    
def safetyShutter(x = None):
    '''Read the state, close or open the safety shutter'''
    obx = DeviceProxy('i11-ma-c04/ex/obx.1')
    
    if x == None:
        return obx.State()
    elif x == 0:
        obx.Close()
    elif x == 1:
        obx.Open()
    elif x == -1:
        obx.FaultAck()
    else:
        print 'Only possible arguments are None, 0 (close), 1 (open) and -1 (fault acknowledge)'
        
def fastShutter():
    '''Read the state, close or open the fast shutter'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
    if x == None:
        return md2.FastShutterIsOpen
    elif x == 0:
        md2.CloseFastShutter()
    elif x == 1:
        md2.OpenFastShutter()
    else:
        print 'Only possible arguments are None, 0 and 1'
        
def fluodetectorPosition():
    '''Read the state, set-in or set-out the fluorescence detector'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def cryoInOut():
    '''Read the state, set-in or set-out of the cryo'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def apertureCalibration():
    '''Calibrate the aperture positions'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def apertureOnOffCover():
    '''Read the state of the aperture, set it in the beam, set it off the beam or send it under cover'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def capillaryBeamstopCalibration():
    '''Calibrate the capillary beam stop'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
def capillaryBeamstopOnOffCover():
    '''Read the state of capillary beam stop, set it in the beam, set it off, or send it under cover'''
    md2 = DeviceProxy('i11-ma-cx1/ex/md2')
    
