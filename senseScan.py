#!/usr/bin/python
# -*- coding: utf-8 -*-
'''Making sense of scan results (aperture, capillary beam stop, diffraction ...).'''

import pickle
import numpy
import gauss2d
import scipy.ndimage

def loadResults(fileName):
    f = open(fileName)
    results = pickle.load(f)
    f.close()
    return results
    
   
def raster(grid):
    gs = grid.shape
    orderedGrid = []
    for i in range(gs[0]):
        line = grid[i, :]
        if (i + 1) % 2 == 0:
            line = line[: : -1]
        orderedGrid.append(line)
    return numpy.array(orderedGrid)
    
def plot_wire_frame(X, Y, Z):
    from mpl_toolkits.mplot3d import axes3d
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1)

    plt.show()


def fitGauss(image):
    params  = gauss2d.fitgaussian(image)
    return params
    
    
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
    
def XYZ(xyz, shape=(20, 40), observable = ('self.imag', 'image'), what = 'capillary'):
    '''Go through the results and return X, Y, Z matrices for 3d plots'''
    motors = {'aperture': ['AprX', 'AprZ'],
              'capillary': ['CbsX', 'CbsZ']}
              
    x = []
    y = []
    z = []

    for item in xyz:
        x.append(item[motors[what][0]])
        y.append(item[motors[what][1]])
        z.append(item[observable])
        
    X = numpy.array(x)
    Y = numpy.array(y)
    Z = numpy.array(z)
    print 'X.size', X.size
    print 'Y.size', Y.size
    print 'Z.size', Z.size
    
    X = numpy.reshape(X, shape)
    Y = numpy.reshape(Y, shape)
    Z = numpy.reshape(Z, shape)
    
    Y = raster(Y)
    Z = raster(Z)
    
    return X, Y, Z
  
  

def main():
    import optparse
    
    usage = 'Program to analyze results of grid scan done on apertures and capillary beamstop of MD2. The only input is the filename of the file storing pickled dictionary of results. By default the program will try to find the center of the scanned object using maximum, gaussian fit and center of mass.'
    parser = optparse.OptionParser(usage = usage)

    parser.add_option('-f', '--filename', default='aperture_100um_Tue_Jul_23_18:42:40_2013.pck', type = str, help = 'File with the scan results, (default: %default)')
    
    (options, args) = parser.parse_args()
    print options
    print args
    
    results = loadResults(options.filename)
    #aperture_scan_shape = (20, 40)
    #cpbs_scan_shape = (80, 60)
    what = options.filename[:options.filename.index('_')]
    print 'what', what
    shape = results['shape']
    print 'shape', shape
    X, Y, Z = XYZ(results['xyz'], shape=shape, what=what)
    
    m = Z.max()
    print 'm', m
    i,j = numpy.unravel_index(Z.argmax(), Z.shape)
    print 'index of max point', i, j
    print 'X[i,j]', X[i][j]
    print 'Y[i,j]', Y[i][j]
    print 'Z[i,j]', Z[i][j]
    
    #Z = (Z > 0.8*m) * Z
    params = fitGauss(Z)
    print 'Gauss fit parameters', params
    ig = int(round(params[1]))
    jg = int(round(params[2]))
    print '\nindex of max point', ig, jg
    try:
        print 'X[i,j]',X[ig][jg]
        print 'Y[i,j]',Y[ig][jg]
        print 'Z[i,j]',Z[ig][jg]
    except:
        import traceback
        print traceback.print_exc()
    
    print '\nresults from center of mass calculation'
    com = scipy.ndimage.center_of_mass(Z)
    i, j = com
    i = int(round(i))
    j = int(round(j))
    print 'index of max point', i, j
    try:
        print 'X[i,j]',X[i][j]
        print 'Y[i,j]',Y[i][j]
        print 'Z[i,j]',Z[i][j]
    except:
        import traceback
        print traceback.print_exc()
    print com
    
    #Z = (Z > 0.8*m) * 1
    
    #x = Z * 
    print 
    plot_surface_wire(X, Y, Z, filename=options.filename.replace('pck', 'png'), stride=1)
    

if __name__ == '__main__':
    main()