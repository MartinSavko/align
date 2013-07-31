#!/usr/bin/python
# -*- coding: utf-8 -*-

import Collect

c = Collect.collect(nImages = 10, 
                    oscillation = 10,
                    directory = '/927bis/ccd/2013/Run3/2013-07-26/Commissioning/', 
                    template = 'linear_1_####.img',
                    linear = True)

raw_input('Please press enter when centred on the start position ')
c.saveLinearStart()
raw_input('Please press enter when centred on the final position ')
c.saveLinearFinal()
#c.linearStart = {'PhiX': -0.11890000000000001,
                 #'PhiY': 0.86970000000000003,
                 #'PhiZ': -0.053699999999999998,
                 #'SamX': -0.89159999999999995,
                 #'SamY': 0.39250000000000002,
                 #'Phi': 0.}

#c.linearFinal = {'PhiX': -0.11890000000000001,
                 #'PhiY': 0.43340000000000001,
                 #'PhiZ': -0.056000000000000001,
                 #'SamX': -0.90249999999999997,
                 #'SamY': 0.33329999999999999,
                 #'Phi': 90.}
                 
positions = c.getCollectPositions(range(c.nImages))
print 'positions'
print positions

for k, position in enumerate(positions):
    print k, position
    c.moveToPosition(position)