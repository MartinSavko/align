#!/usr/bin/python

import pickle
import copy
import time

#filename = 'aperture_1_scan_measured_Tue_Jul_23_18:42:40_2013.pck'
#filename = 'aperture_2_scan_measured_[20, 40]_[0.20000000000000001, 0.40000000000000002]Tue_Jul_23_21:12:30_2013.pck'
#filename = 'aperture_3_scan_measured_[20, 40]_[0.20000000000000001, 0.40000000000000002]Tue_Jul_23_21:38:22_2013.pck'
filename = 'cbps_scan_measuredTue_Jul_23_20:02:41_2013.pck'

f = open(filename)
a1 = pickle.load(f)
f.close()

datetime = filename[filename.index('Tue'): filename.index('.pck')].replace('_', ' ')

results = {'time': time.time(),
           'datetime': datetime,
           'what': 'capillary',
           'shape': (80, 60),
           'lengths': (0.8, 0.6)}
           
apcap = {1: 'aperture_100um', 2: 'aperture_50um', 3: 'aperture_20um', 'capillary': 'capillary'}           

xyz = []
for k, position in enumerate(a1['positions']):
    if k % 25 == 0:
        print k, position
        print a1['measured'][k].mean()
        
    positionAndValue = copy.deepcopy(position)
    positionAndValue[('self.imag', 'image')] = a1['measured'][k].mean()
    xyz.append(positionAndValue)
    
results['xyz'] = xyz

filename = apcap[results['what']] + '_' + results['datetime'].replace(' ', '_') + '.pck'

a1ref = open(filename, 'w')
pickle.dump(results, a1ref)
a1ref.close()


    
    
