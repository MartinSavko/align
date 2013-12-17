#!/usr/bin/python
# -*- coding: utf-8 -*-
'''testing grid collects on PX2'''

import Collect
import numpy

collect = Collect.collect(directory='/927bis/ccd/2013/Run4/2013-09-11/Commissioning/Grid',
                          prefix='grid',
                          template='grid_2_####.img',
                          nImages = 1,
                          #oscillation = 0.,
                          grid=True)
                          
start = collect.getMotorValues()

grid_start = [start['PhiY'], start['PhiZ']]
grid_nbsteps = [10, 8]
grid_lengths = [0.250, 0.200]

collect.nbFrames = int(numpy.array(grid_nbsteps).prod())

collect.setGridParameters(grid_start, grid_nbsteps, grid_lengths)

collect.collect()
