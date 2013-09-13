#!/usr/bin/python
# -*- coding: utf-8 -*-
'''testing helical collects on PX2'''

import Collect

collect = collect = Collect.collect(directory='/927bis/ccd/2013/Run3/2013-07-14/Commissioning/Helical',
                                    prefix='helical',
                                    template='helical_1_####.img',
                                    nImages=100,
                                    helical=True)

collect.helicalStart = {'PhiX': -0.10970000000000001,
                        'PhiY': 0.15579999999999999,
                        'PhiZ': -0.023599999999999999,
                        'SamX': -0.0147,
                        'SamY': -0.014999999999999999}

                        
collect.helicalFinal = {'PhiX': -0.10970000000000001,
                        'PhiY': -0.3498,
                        'PhiZ': -0.041700000000000001,
                        'SamX': 0.42670000000000002,
                        'SamY': -0.0023}

hs, hf = collect.calculateHelicalOffset()

positions = []
collect.moveToPosition(collect.helicalStart)

for n in range(1, collect.nImages + 1):
    p = collect.calculateLinearCollectPosition(n, collect.helicalStart, collect.helicalFinal)
    positions.append(p)
    
for k, position in enumerate(positions):
    print 'position', k
    print position
    collect.moveToPosition(position)

#for n in range(collect.nImages):
    #p = collect.calculateHelicalCollectPosition(n, hs, hf)
    #positions.append(p)
    ##print 'position', n
    ##print p
    ##print


#for k, position in enumerate(positions):
    #print 'position', k
    #print position
    #collect.moveToPosition(position)
    
    
