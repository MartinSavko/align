#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import time
import optparse
import time
import commands
import math
import re
from PyTango import *
import PyTango
import pickle
import numpy

usage = 'Program to perform collect on PX2 beamline.\n\n%prog -n <number_of_images>\n\nNumber of images to be collected has to be specified, others are optional.'
parser = optparse.OptionParser(usage = usage)

parser.add_option('-e', '--exposure', default = 1.0, type = float, help = 'exposure time (default: %default)')
parser.add_option('-o', '--oscillation', default = 1.0, type = float, help = 'oscillation range (default: %default)')
parser.add_option('-p', '--passes', default = 1, type = int, help = 'number of passes (default: %default)')
parser.add_option('-s', '--start', default = 0.0, type = float, help = 'collect start angle (default: %default)')
#parser.add_option('-e', '--end', default = 180.0, type = float, help = 'collect end angle')
parser.add_option('-n', '--nImages', default = 1, type = int, help = 'Number of images to collect (default = %default')
#parser.add_option('-f', '--frames', default = None, type = int, help = 'number of frames to collect')
parser.add_option('-r', '--range', default = None, type = float, help = 'collect range. This is alternative way to specify how much we want to explore (alternative to --nImages)')
parser.add_option('-a', '--anticipation', default = 1, type = int, help = 'scan anticipation (default: %default)')
parser.add_option('-l', '--overlap', default = 0.0, type = float, help = 'scanning overlap (default: %default)')
parser.add_option('-d', '--directory', default = '/tmp/test-data', type = str, help = 'where to store collected images (default: %default)')
parser.add_option('-u', '--run', default = 1, type = int, help = 'run number')
parser.add_option('-f', '--firstImage', default = 1, type = int, help = 'Image number to start with. Useful if some images were collected already and we do not want to overwrite them (default: %default)')
parser.add_option('-x', '--prefix', default = 'F6', type = str, help = 'prefix (default = %default)')
parser.add_option('-i', '--suffix', default = 'img', type = str, help = 'suffix (default = %default)')
parser.add_option('-t', '--template', default = 'prefix_1_####.img', type = str, help = 'teplate (default = %default)')
parser.add_option('-c', '--comment', default = '', type = str, help = 'Add your comment here ...')
parser.add_option('-I', '--inverse', default = None, help = 'Inverse collects, parameter is integer specifying reference interval i.e. number of images in the wedge (default = %default)')

(options, args) = parser.parse_args()
print options
print args
#sys.exit()

md2             =  DeviceProxy('i11-ma-cx1/ex/md2')
publisher       =  DeviceProxy('i11-ma-cx1/ex/md2-publisher')
phase           =  DeviceProxy('i11-ma-cx1/ex/md2-phase')
adsc            =  DeviceProxy('i11-ma-cx1/dt/adsc')
limaadsc        =  DeviceProxy('i11-ma-cx1/dt/limaadsc')
header          =  DeviceProxy('i11-ma-cx1/ex/header')
mono1           =  DeviceProxy('i11-ma-c03/op/mono1')
detector_mt_ts  =  DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_ts')
detector_mt_tx  =  DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_tx')
detector_mt_tz  =  DeviceProxy('i11-ma-cx1/dt/dtc_ccd.1-mt_tz')
obx             =  DeviceProxy('i11-ma-c04/ex/obx.1')
mono_mt_rx      =  DeviceProxy('i11-ma-c03/op/mono1-mt_rx')

#
#

#MD2 data
ScanAnticipation = options.anticipation # 1
ScanNumberOfPasses = options.passes # 1
ScanRange = options.oscillation # 10
ScanExposureTime = options.exposure # 1.0
ScanStartAngle = options.start #0.0


#
ScanOverlap = options.overlap #0.0 Not used for now

#ADSC data
imagePath = options.directory #'/tmp/test-data/' #'/927bis/ccd/2012/Run4/2012_07_09/'
if imagePath[-1] == '/':
    pass
else:
    imagePath += '/'

if options.nImages == None and options.range == None :
    #print 'You have to set either range or number of images to collect'
    #print commands.getoutput(sys.argv[0] + ' -h')
    print parser.usage
    sys.exit("Option nImages or option range have to be specified.")

if options.range != None:
    nbFrames = int( math.ceil( (options.range - options.start) / options.oscillation ) )
else:
    nbFrames = int(options.nImages)


print 'nbFrames', nbFrames

#Collect data
startAngle = options.start # 45.
#endAngle = options.start + options.range # 180.
#collectionRange = options.range #180.

#Image data
firstImage = options.firstImage
extension = '.' + options.suffix #S'.img'
#run = 'Run4'
run = str(options.run)  
#projectName = ''
projectName = options.prefix
template = options.template
if options.inverse:
    template_inv = template.replace(projectName + '_' + run, projectName + '_' + str(int(run) + 1))
#filenameTemplate = projectName #'F6_1_'

def wait_MD2(fileName):
    start = time.time()
    while md2.state() == PyTango._PyTango.DevState.MOVING:
        time.sleep(0.1)
        pass
    end = time.time()
    if collect_log[fileName].has_key('wait_MD2'):
        collect_log[fileName]['wait_MD2'].append(end - start)
    else:
        collect_log[fileName]['wait_MD2'] = [end - start]
        
def wait_ADSC(fileName):
    start = time.time()
    while adsc.state() == PyTango._PyTango.DevState.RUNNING:
        time.sleep(0.001)
        pass
    end = time.time()
    if collect_log[fileName].has_key('wait_ADSC'):
        collect_log[fileName]['wait_ADSC'].append(end - start)
    else:
        collect_log[fileName]['wait_ADSC'] = [end - start]
        
def wait_LIMAADSC(fileName):
    start = time.time()
    while limaadsc.state() == PyTango._PyTango.DevState.MOVING:
        time.sleep(0.01)
        pass
    end = time.time()
    if collect_log[fileName].has_key('wait_LIMAADSC'):
        collect_log[fileName]['wait_LIMAADSC'].append(end - start)
    else:
        collect_log[fileName]['wait_LIMAADSC'] = [end - start]
        
def get_MD2_ready_for_collect():
    '''Get MD2 ready for collect.'''
    #global collect_log
    md2.write_attribute('ScanAnticipation', ScanAnticipation)
    md2.write_attribute('ScanNumberOfPasses', ScanNumberOfPasses)
    md2.write_attribute('ScanRange', ScanRange)
    md2.write_attribute('ScanExposureTime', ScanExposureTime)
    md2.write_attribute('ScanStartAngle', ScanStartAngle)
    md2.write_attribute('PhasePosition', 4)
    
    
def get_ADSC_ready_for_collect():
    '''Get ADSC ready for collect.'''
    #global collect_log
    adscWriteAttribute('imagePath', imagePath)
    adscWriteAttribute('nbFrames', nbFrames)

def beamCenter(distance, wavelength):
    
    #Theta = numpy.matrix([[  1.53742614e+03,   1.51316832e+03], [ -7.71816355e-02,   1.28131955e-02], [ -6.56802346e+00,  -1.57707926e+01]])
    #Theta = numpy.matrix([[  1704.98,   1501.76], [ -7.42150181e-02,   2.93164082e-03], [ -5.53238312e+00,  -1.93360572e+01]])
    #Theta = numpy.matrix([[  1.70712903e+03,   1.49584863e+03], [ -5.21791360e-02,   4.08631901e-03], [  3.80811890e+00,   4.48254004e+00]])
    #Theta = numpy.matrix([[  1.72246336e+03,   1.49851542e+03], [ -8.60876670e-02,  -1.81071038e-03], [ -7.06449209e-02,   3.80798459e+00]])
    #Theta = numpy.matrix([[ 1.72224187e+03, 1.49827302e+03], [ -8.72504178e-02, -1.74089134e-03], [ 9.11421265e-02, 3.77119305e+00]]) #17.03.2013 i11-ma-cx1/dt/dtc_ccd.1-mt_tx: 25
    #Theta = numpy.matrix([[ 1.56765686e+03, 1.43451347e+03], [ -1.08989455e-01, 3.81221864e-03], [ -6.11315784e+00, 4.75723425e+00]]) #15.05.2013 tz = -6.5 mm; tx = -17.0 mm
    tz_ref = -6.5
    tx_ref = -17.0
    
    Theta = numpy.matrix([[ 1.55557116e+03, 1.43720063e+03], [ -8.51067454e-02, -1.84118001e-03], [ -1.99919592e-01, 3.57937064e+00]]) #16.05.2013
    q = 0.102592 #pixel size in milimeters
    X = numpy.matrix ([1., distance, wavelength])
    
    tx = detector_mt_tx.position
    tz = detector_mt_tz.position
    
    zcor = tz - tz_ref
    xcor = tx - tx_ref
    
    Origin = Theta.T * X.T
    Origin = Origin * q
    
    return Origin[1] + zcor, Origin[0] + xcor
    
def setup_header():
    wavelength = mono1.read_attribute('lambda').value
    distance = detector_mt_ts.read_attribute('position').value
    X, Y = beamCenter(distance, wavelength)
    BeamCenterX = str( round(X, 3) )
    BeamCenterY = str( round(Y, 3) )
    #header = '{\nWAVELENGTH = ' + str(wavelength) +'\n}\n'
    head = header.header
    head = re.sub('BEAM_CENTER_X=\d\d\d\.\d', 'BEAM_CENTER_X=' + BeamCenterX, head)
    head = re.sub('BEAM_CENTER_Y=\d\d\d\.\d', 'BEAM_CENTER_Y=' + BeamCenterY, head)
    #head = head.replace('BEAM_CENTER_X=161.3', 'BEAM_CENTER_X=' + BeamCenterX)
    #head = head.replace('BEAM_CENTER_Y=156.7', 'BEAM_CENTER_Y=' + BeamCenterY) #;BEAM_CENTER_Y=156.7'
    #head = head.replace('PROXIMA1', 'PROXIMA2A')
    return head

def EstimatedTime(nbFrames, ScanExposureTime, overhead = 0.5):
    return nbFrames * (ScanExposureTime + overhead)

def createFileName(imagePath = imagePath, projectName = projectName, template = template, imageNum = 1, extension = extension):
    #imagePath + projectName + 
    #return filenameTemplate + str(imageNum).zfill(4) + extension
    filename = template.replace('####', str(imageNum).zfill(4))
    return filename
    
def adscWriteAttribute(*args):
    try:
        adsc.write_attribute(*args)
    except:
        pass
    return 0

def adscCommand(fileName, *args):
    #global collect_log
    start = time.time()
    try:
        adsc.command_inout(*args)
    except:
        pass
    end = time.time()
    at = end - start
    collect_log[fileName]['adscCommand'] = at
    #print 'adscCommand took', at
    return 0
    
def headerCommand(*args):
    try:
        header.command_inout(*args)
    except:
        pass
    return 0

def limaadscCommand(fileName, *args):
    #global collect_log
    start = time.time()
    try:
        limaadsc.command_inout(*args)
    except:
        pass
    end = time.time()
    lat = end - start
    collect_log[fileName]['limaadscCommand' + str(args[0])] = lat
    #print 'limaadscCommand took', lat
    return 0

def md2Command(fileName, *args):
    #global collect_log
    start = time.time()
    md2.command_inout(*args)
    wait_MD2(fileName)
    end = time.time()
    mt = end - start
    collect_log[fileName]['md2Command'] = mt
    #print 'Move took', mt
    return 0

def md2WriteAttribute(*args):
    md2.write_attribute(*args)
    return 0

def publisherWriteAttribute(*args):
    publisher.write_attribute(*args)
    return 0

def lastImage(xformstatusfile = '/927bis/ccd/.lastImage', integer = 1, imagePath = '/927bis/ccd/test/', fileName = 'test.img'):
    os.system('echo "' + str(integer) + ' ' + imagePath + fileName + '" > ' + xformstatusfile)
    
def collectWedge(firstImage, nbFrames, ScanStartAngle, template = template):
    #global collect_log
    mono_mt_rx.Off()
    for imageNum in range(firstImage, nbFrames + firstImage):
        print imageNum
        s = time.time()
        fileName = createFileName(imageNum = imageNum, template = template)
        collect_log[fileName] = {}
        publisher.write_attribute('imageNum', imageNum)
        
        wait_ADSC(fileName)
        adscWriteAttribute('fileName', fileName) # adsc.write_attribute('fileName', fileName)
        wait_ADSC(fileName)
        wait_MD2(fileName)
        #headerCommand('SetExpression', setup_header()) #header.command_inout('SetExpression', setup_header())
        
        md2WriteAttribute('ScanStartAngle', ScanStartAngle)
        wait_ADSC(fileName)
        head = setup_header()
        print 'header', head
        adscCommand(fileName, 'SetHeaderParameters', head) #        adsc.command_inout('SetHeaderParameters', setup_header())
        wait_ADSC(fileName)
        limaadscCommand(fileName, 'Snap') #limadsc.command_inout('Snap')
        #wait_MD2()
        md2Command(fileName, 'StartScan')
        limaadscCommand(fileName, 'Stop') #limaadsc.command_inout('Stop')
        lastImage('/927bis/ccd/.lastImage', integer = imageNum, imagePath = imagePath, fileName = fileName) #for adxv autoload via -autoload
        ScanStartAngle += ScanRange - ScanOverlap
        
        #publisherWriteAttribute('EstimatedTime', EstimatedTime(nbFrames - imageNum, ScanExposureTime))
        tat = time.time() - s
        print 'this image took', tat, 'to collect'
        collect_log[fileName]['imageAcquisitionTime'] = tat
    mono_mt_rx.On()

def collect(firstImage = firstImage, nbFrames = nbFrames, ScanStartAngle = ScanStartAngle):
    '''Collect'''
    #global collect_log
    collect_log['firstImage'] = firstImage
    collect_log['nbFrames'] = nbFrames
    collect_log['ScanStartAngle'] = ScanStartAngle
    publisher.write_attribute('dataCollectionDone', False)
    get_MD2_ready_for_collect()
    get_ADSC_ready_for_collect()
    
    if options.inverse == 'None':
        collectWedge(firstImage, nbFrames, ScanStartAngle, template = template)
    else:
        wedgeSize = int(options.inverse)
        numberOfFullWedges, lastWedgeSize = divmod(nbFrames, wedgeSize)
        for k in range(0, numberOfFullWedges):
            _ScanStartAngle = ScanStartAngle + k * wedgeSize * ScanRange
            _firstImage = firstImage + k * wedgeSize
            collectWedge(_firstImage, wedgeSize, _ScanStartAngle, template = template)
            collectWedge(_firstImage, wedgeSize, _ScanStartAngle + 180., template = template_inv)
        
        _ScanStartAngle = ScanStartAngle + numberOfFullWedges * wedgeSize * ScanRange
        _firstImage = firstImage + numberOfFullWedges * wedgeSize
        collectWedge(_firstImage, lastWedgeSize, _ScanStartAngle, template = template)
        collectWedge(_firstImage, lastWedgeSize, _ScanStartAngle + 180., template = template_inv)
    
    publisher.write_attribute('dataCollectionDone', True)
    
collect_log = {}
start = time.time()
collect_log['start'] = start

collect_log['ScanAnticipation'] = ScanAnticipation
collect_log['ScanNumberOfPasses'] = ScanNumberOfPasses
collect_log['ScanRange'] = ScanRange
collect_log['ScanExposureTime'] = ScanExposureTime
collect_log['ScanStartAngle'] = ScanStartAngle
collect_log['ScanOverlap'] = ScanOverlap


collect_log['firstImage'] = firstImage
collect_log['extension'] = extension
collect_log['run'] = run
collect_log['projectName'] = projectName
collect_log['template'] = template
collect_log['inverse'] = options.inverse
#collect_log[''] = 

obx.Open()
collect(nbFrames = nbFrames, ScanStartAngle = ScanStartAngle)
obx.Close()


end = time.time()
collect_log['end'] = end
collect_log['collectAcquisitionTime'] = end - start

f = open('collect_log_' + '_'.join(time.ctime().split()) + template.replace('img', 'log').replace('_####',''), 'w')
pickle.dump(collect_log, f)
f.close()