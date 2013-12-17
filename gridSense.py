#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Making sense of grid scans'''

import commands
import optparse
import os 
import time
import re
import pickle 
import numpy
import scipy


def distl(filename):
    out = commands.getoutput('distl.signal_strength ' + filename)
    return out
    
def xdsme(filename):
    out = commands.getoutput('xdsme -1 ' + filename)
    return out
    
def assignPosition(filename):
    file_ordinal = int(filename.split('_')[-1][:-4])
    return file_ordinal
   
   
def getSpotTotal(distl_out):
    search = re.search(r'Spot Total : (.*)$', distl_out, re.M)
    return float(search.group(1))


def getGoodBraggCandidates(distl_out):
    search = re.search(r'Good Bragg Candidates : (.*)$', distl_out, re.M)
    return float(search.group(1))
        

def getMethod1Resolution(distl_out):
    search = re.search(r'Method 1 Resolution : (.*)$', distl_out, re.M)
    return float(search.group(1))

    
def getColspot(xdsme_out):
    return

def storeResults(results, filename):
    f = open(filename, 'w')
    pickle.dump(results, f)
    f.close()
    
def retrieveResults(filename):
    f = open(filename)
    results = pickle.load(f)
    f.close()
    return results

def getResults(template, directory):
    try:
        results = retrieveResults(os.path.join(directory, template) + '_results.pck')
        #results = retrieveResults('grid_2_results.pck')
    except IOError, EOFError:

        files = commands.getoutput('ls ' + os.path.join(options.directory, options.template + '*.img')).split()

        results = {'timestamp': time.asctime()}
        results['points'] = len(files)
        results['shape'] = eval(options.shape)
        #results[
        for f in files:
            n = assignPosition(f)
            results[n] = {}
            distl_out = distl(f)
            xdsme_out = xdsme(f)
            
            results[n]['distl_out'] = distl_out
            results[n]['xdsme_out'] = xdsme_out
            
            results[n]['goodBraggCandidates'] = getGoodBraggCandidates(distl_out)
            
            
        storeResults(results, os.path.join(directory, template) + '_results.pck')
    return results
    
def raster(grid, k=0):
    gs = grid.shape
    orderedGrid = []
    for i in range(gs[0]):
        line = grid[i, :]
        if (i + 1) % 2 == k:
            line = line[: : -1]
        orderedGrid.append(line)
    return numpy.array(orderedGrid)


def XYZ(results, shape=(8, 10), observable='goodBraggCandidates'):
    '''Go through the results and return X, Y, Z matrices for 3d plots'''
                  
    number_of_points = numpy.array(shape).prod()
    
    z = [results[n][observable] for n in range(1, number_of_points + 1)]
        
    X, Y = numpy.meshgrid(range(shape[0]), range(shape[1]))
    print 'X'
    print X
    print
    print 'Y'
    print Y
    
    Z = numpy.array(z)
    #print 'X.size', X.size
    #print 'Y.size', Y.size
    print 'Z.size', Z.size
    
    #X = numpy.reshape(X, shape)
    #Y = numpy.reshape(Y, shape)
    Z = numpy.reshape(Z, shape)
    
    X -= (shape[0] - 1)
    print 'X -' + str(shape[1] - 1)
    print X
    
    print 'X * -1, final X'
    X *= -1
    print X
    
    Y = numpy.transpose(Y)
    #Y = raster(Y, k=1)
    Y = numpy.transpose(Y)
    print 'final Y'
    print Y
    Z = raster(Z, k=1)
    Z = numpy.transpose(Z)
    print 'final Z'
    print Z #[:, 6:]
    print 'shapes', X.shape, Y.shape, Z.shape
    return X, Y, Z
    
   
def plot_surface(X, Y, Z):
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib import cm
    from matplotlib.ticker import LinearLocator, FormatStrFormatter
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
            linewidth=0, antialiased=False)
    #ax.zaxis.set_major_locator(LinearLocator(10))
    #ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show()

    
def plot_surface_wire(X, Y, Z, filename='resultFigure.png', stride=1):
    from mpl_toolkits.mplot3d import axes3d
    from matplotlib import cm
    import matplotlib.pyplot as plt

    fig = plt.figure(filename.replace('.png', ''), figsize=plt.figaspect(0.5))
    # surface
    
    ax = fig.add_subplot(1, 3, 1, projection='3d', title='Grey')
    surf = ax.plot_surface(X, Y, Z, rstride=stride, cstride=stride, cmap=cm.Greys, linewidth=0, antialiased=True)
    ax.view_init(elev=8., azim=-49.)
    fig.colorbar(surf, shrink=0.5, aspect=15)
    
    ax = fig.add_subplot(1, 3, 2, projection='3d', title='Bone')
    surf = ax.plot_surface(X, Y, Z, rstride=stride, cstride=stride, cmap=cm.bone, linewidth=0, antialiased=True)
    ax.view_init(elev=8., azim=-49.)
    fig.colorbar(surf, shrink=0.5, aspect=15)
    
    # wire
    ax = fig.add_subplot(1, 3, 3, projection='3d', title='Wireframe')
    wire = ax.plot_wireframe(X, Y, Z, rstride=stride, cstride=stride)
    ax.view_init(elev=8., azim=-49.)
    ## mesh
    #ax = fig.add_subplot(1, 4, 3, projection='3d', title='Wireframe')
    #wire = ax.mesh(X, Y, Z, rstride=stride, cstride=stride)

    # save and display
    plt.savefig(filename)
    plt.show()

def plot_wire_frame(X, Y, Z):
    from mpl_toolkits.mplot3d import axes3d
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1)

    plt.show()

parser = optparse.OptionParser()

parser.add_option('-t', '--template' , default='grid_2', type=str, help='Template of files with the scan results, (default: %default)')
parser.add_option('-d', '--directory', default='/927bis/ccd/2013/Run4/2013-09-11/Commissioning/Grid', type=str, help='Directory with the scan results, (default: %default)')
parser.add_option('-s', '--shape', default='(10, 8)', type=str, help='Shape of the grid')

options, args = parser.parse_args()

results = getResults(options.template, options.directory)

X, Y, Z = XYZ(results, shape=eval(options.shape))

#scipy.misc.imshow(Z)

scipy.misc.imsave(os.path.join(options.directory, options.template) + '_2d_scan.png', Z)

#plot_surface(X, Y, Z)

#plot_wire_frame(X, Y, Z)

plot_surface_wire(X, Y, Z)



    
    