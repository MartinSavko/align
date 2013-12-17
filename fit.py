#!/usr/bin/python

'''Fitting the function y = c + r*sin(phi + alpha)'''
from math import sin, cos, pi
import scipy.optimize as op
import numpy as np
import pylab

#def f(als, c=1., r=1., phi=15*pi/180.):
    #return np.array([y(a, c, r, phi) for a in als])
    
def y(a,  c=1., r=1., phi=15*pi/180):
    return c + r * sin(phi + a)

#def y_grad(als, c, r, phi):
    #return np.array([y_prime(a, c, r, phi) for a in als])
    
def y_prime(a, c=1., r=1., phi=15.*pi/180):
    return -r * cos(phi + a[0])

def diffsquares(y_exp, y_fit):
    return (y_exp - y_fit)**2
    

step = 2*pi / 360.

xs = np.arange(0, 2*pi + step, step )
ys = [y(a) for a in xs]

pylab.plot(xs, ys)
pylab.show()
#result = op.check_grad(y, y_prime, np.array(np.arange(0, 2*pi + step, step )))

#print 'result', result