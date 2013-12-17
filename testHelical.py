#!/usr/bin/python
# -*- coding: utf-8 -*-
'''testing helical collects on PX2'''

import Collect
import time
import pickle

dire = '/927bis/ccd/2013/Run4/2013-10-03/CEA/GG/Myb30'
pref = 'myb30_helical'
star = 5.
first = 1
temp =  pref + '_1_####.img'
rang = 180.
osci = 0.5
nImg = int(rang/abs(osci))

collect = Collect.collect(directory=dire,
                          prefix=pref,
                          start=star,
                          template=temp,
                          nImages=nImg,
                          firstImage = first,
                          #inverse=20,
                          test=False,
                          helical=True)
                          

print 'Starting helical collect ...'

#raw_input('Please center the starting point. Press enter when done.')
#collect.saveHelicalStart()
#print 'Motor positions for the starting position'
#print collect.helicalStart

#raw_input('Please center the final point. Press enter when done.')
#collect.saveHelicalFinal()
#print 'Motor positions for the final position'
#print collect.helicalFinal

collect.helicalStart = {'PhiX': -0.1229,
 'PhiY': 0.34489999999999998,
 'PhiZ': -0.1187,
 'SamX': -0.86739999999999995,
 'SamY': 0.30959999999999999}


collect.helicalFinal = {'PhiX': -0.1229,
 'PhiY': 0.1414,
 'PhiZ': -0.1186,
 'SamX': -0.80840000000000001,
 'SamY': 0.29399999999999998}



#{'PhiX': -0.1229,
 #'PhiY': 0.23760000000000001,
 #'PhiZ': -0.11849999999999999,
 #'SamX': -1.0268999999999999,
 #'SamY': 0.30599999999999999}
 
collect.moveToPosition(collect.helicalStart)

positions = collect.getCollectPositions(collect.nImages)

f = open('positions_' + pref + '_' + '_'.join(time.asctime().split())+ '.pck', 'w')
pickle.dump(positions, f)
f.close()
#pos = pickle.load(f)

collect.collect()

    
