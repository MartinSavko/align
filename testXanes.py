#!/usr/bin/python
# -*- coding: utf-8 -*-

import Xanes

scan = Xanes.xanes('Hg', 'L', nbSteps=300, beforeEdge=0.100, afterEdge=0.200, prefix='x5', directory='/927bis/ccd/2013/Run5/2013-11-29/CNB/ch286a/', bleSteps=7, test=False)

scan.scan()
