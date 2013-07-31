#!/usr/bin/python
# -*- coding: utf-8 -*-
'''testing CATS on Proxima2A'''

'''Part of SAT. We will cycle randomly each lid using three different samples mounted with three different pin types. '''


from catsapi import *
import itertools
import random
import time
import os
import pickle

motorsNames = ['PhiTableXAxisPosition', 
               'PhiTableYAxisPosition', 
               'PhiTableZAxisPosition',
               'CentringTableXAxisPosition', 
               'CentringTableYAxisPosition']
                   
motorShortNames = ['PhiX', 'PhiY', 'PhiZ', 'SamX', 'SamY']
 
shortFull = dict(zip(motorShortNames, motorsNames))

md2 = PyTango.DeviceProxy('i11-ma-cx1/ex/md2')

def wait(device):
    #self.logger.info('Waiting for ' + str(device))
    #self.logger.info(time.asctime(), str(__name__), 'INFO', 'waiting for device' + str(device))
    #print time.asctime(), str(__name__), 'INFO', 'waiting for device' + str(device)
    while device.state().name == 'MOVING':
        time.sleep(.1)
    
    while device.state().name == 'RUNNING':
        time.sleep(.1)


def moveToPosition(position={}):
    if position != {}:
        for motor in position:
            md2.write_attribute(shortFull[motor], position[motor])
    return
        

def getMotorValues():
    position = {}
    for motor in motorShortNames:
        position[motor] = md2.read_attribute(shortFull[motor]).value
        
    return position

    

cs8 = CS8Connection()
cs8.connect('172.19.10.116', 1000, 10000)


k = 0
d = 0

try:
    print 'cs8.state()', cs8.state()
except:
    print 'error in cs8.state()'
time.sleep(5)
try:
    print 'cs8.state()', cs8.state()
except:
    print 'error in cs8.state()'



lids = range(1, 4)
samples = range(1, 49)
energies = [6.86, 8.04, 9.16, 10.35, 11.46, 12.65, 13.77, 14.96] #, 16.08, 17.26]

centredPositions = dict(zip(samples, [None for k in range(len(samples))]))

if os.path.exists('sat3_centredPositions.log'):
    f = open('sat3_centredPositions.log')
    centredPositions = pickle.load(f)
    f.close()
else:
    pass

for lid in lids:
    log = {}
    proceed = raw_input('Can I proceed with testing the lid ' + str(lid) + '? [Y/n] ')
    if proceed in ['y', 'Y', '']:
        pass
    else:
        break
    print 'Testing lid', lid
    samples = range(1, 49)
    random.shuffle(samples)
    log['combinations'] = samples
    print 'Order of samples to be checked'
    print samples

    while samples:
        sample = samples.pop(0)
        print 'sample number', sample
        number_of_mounts = 0
        log[(lid, sample)] = {'number_of_mounts': 0}
        log[(lid, sample)][number_of_mounts] = {'OK': None,
                                                'comment': ''}
                                     
        answer = ''
        while answer == '' of answer[0] in ['y', 'Y']:
            print 'lid', lid +',', 'sample', sample
            print 'This sample has been mounted', number_of_mounts, 'times'
            answer = raw_input('Would you like me to mount this sample? [Y/n] ')
            if answer == '' or answer[0] in ['y', 'Y']:
                try:
                    number_of_mounts += 1
                    
                    print 'going getput_brcd'
                    try:
                        output = cs8.getput_brcd(1, lid, sample, 1, 0, 0, 0, 0)
                    except Exception, e:
                        output = e
                    print 'output', output
                    
                    try:
                        cs8state = cs8.state()
                    except Exception, e:
                        cs8state = e
                    print 'cs8 state', cs8state
                    log[(lid, sample)][number_of_mounts]['state'] = cs8state
                    
                    log[(lid, sample)]['number_of_mounts'] += 1
                    log[(lid, sample)][number_of_mounts] = {}
                    
                    ok = raw_input('Did robot do what it was supposed to do? [Y/n] ')
                    if ok == '' or ok[0] in ['y', 'Y']:
                        log[(lid, sample)][number_of_mounts]['OK'] = True
                    else:
                        log[(lid, sample)][number_of_mounts]['OK'] = False
                    
                    if centredPositions[sample] is None:
                        print 'Please center the sample'
                        center = raw_input('Do you want me to save the current centered position? [Y/n] ')
                        if center == '' or center[0] in ['y', 'Y']:
                            centredPositions[sample] = getMotorValues()
                            f = open('sat3_centredPositions.log', 'w')
                            pickle.dump(centredPositions, f)
                            f.close()
                    else:
                        print 'Moving to previously centered position for current sample'
                        print 'motor positions', centredPositions[sample]
                        moveToPosition(centredPositions[sample])
                    
                    diffraction = raw_input('Was diffraction OK? [Y/n] ')
                    if diffraction == '' or diffraction[0] in ['y', 'Y']:
                        log[(lid, sample)][number_of_mounts]['diffraction'] = True
                    else:
                        log[(lid, sample)][number_of_mounts]['diffraction'] = False
                    
                    comment = raw_input('Any comments? ')
                    log[(lid, sample)][number_of_mounts]['comment'] = comment
                            
                    
                except:
                    print 'I am deeply sorry master, but due to no fault on my part, the communication with my brother robot failed'
                    time.sleep(1.)
            else:
                break
                    
        os.system('./ftp_getlog.sh')
        timestamp = '_'.join(time.asctime().split())
        os.system('./ftp_getlog.sh')
        os.system('mv errors.log sat_' + str(lid) + '_' + timestamp + '.log')
    print 'Number of samples to go', len(samples)
    print 'detailed list of samples to go', samples
    print
            
    f = open('sat3_' + str(lid) + '.log', 'w')
    pickle.dump(log, f)
    f.close()
