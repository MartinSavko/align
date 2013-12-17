#!/usr/bin/python
# -*- coding: utf-8 -*-
'''Perform chooch calculation on the .dat file with recorded energy scan data'''


import optparse
#import PyChooch
import commands
import pylab
import numpy
import os
#from matplotlib import rc

#rc('text', usetex=True)
#pylab.rc('text', usetex=True)

def getElementEdgeFromFilename(filename):
    fns = filename.split('_')
    return fns[-2], fns[-1][:-4]
    
def writeRAW(inFile, scanData, element='', edge='', qualifier=''):
    f = open(inFile.replace('.dat', qualifier + '.raw'), 'w')
    f.write('Proxima 2A, element: %s, edge: %s\n' % (element, edge))
    f.write(str(len(scanData)) + '\n')
    for line in scanData:
        f.write(str(line[0]) + '\t' + str(line[1]) + '\n')
    f.close()
   
def getScanData(data, y_index = 1):
    scanData = []
    for rec in data:
        if rec[0] != '#':
            rs = rec.split()
            x = float(rs[0])
            x = x < 1000 and x*1000.0 or x
            #if x > 7184.:
                #y = last_y
            #else:
            if y_index == 4:
                y = float(rs[2])/float(rs[3])
            elif y_index == 5:
                y = float(rs[2])/float(rs[4])
            else:
                y = float(rs[y_index])
            #last_y = y
            scanData.append((x, y))
    return scanData

def plotScanData(scanData, element, edge, number = 1):
    data = numpy.array(scanData)
    titles = {1: 'normalized by counts up to end of ROI', 2: 'Raw ROI counts', 4: 'normalized by xbpm intensity', 5: 'Normalized by total counts on ketek'}
    y = data[:, 1]
    x = data[:, 0]
    pylab.figure(number)
    pylab.title('Energy Scan ' + element + ' ' + edge + '\n' + titles[number])
    pylab.ylabel('Normalized counts')
    pylab.xlabel('Energy [eV]')
    pylab.plot(x, y)
    #pylab.show()

def plot_efs(efs_file):
    data =open(efs_file).readlines()
    matrix = numpy.array([numpy.array(map(float, line.split())) for line in data])
    print matrix
    pylab.figure('efs')
    pylab.plot(matrix[:,0], matrix[:,1:])
    pylab.legend((r"f''", r"f'"))
    pylab.ylabel('electrons')
    pylab.xlabel('Energy [eV]')
    #pylab.show()
   
def parse_chooch_output(output):
    table = output[output.find('Table of results'):]
    tabl = table.split('\n')
    tab = numpy.array([ line.split('|') for line in tabl if line and line[0] == '|'])
    pk = float(tab[1][2])
    fppPeak = float(tab[1][3])
    fpPeak = float(tab[1][4])
    ip = float(tab[2][2])
    fppInfl = float(tab[2][3])
    fpInfl = float(tab[2][4])
    
    return pk, fppPeak, fpPeak, ip, fppInfl, fpInfl

usage = 'Program to perform chooch calculation on the .dat file with recorded energy scan data'
parser = optparse.OptionParser(usage = usage)

parser.add_option('-i', '--inFile', type = str, help = 'data file')
parser.add_option('-o', '--outFile', default='choochOut.efs', type=str, help = 'output file')

options, args = parser.parse_args()

data = open(options.inFile).readlines()

element, edge = getElementEdgeFromFilename(options.inFile)

scanData = getScanData(data)

#print 'scanData', scanData

print 'element, edge'

element, edge = getElementEdgeFromFilename(options.inFile)

print element, edge

print 'outFile', options.outFile
  
scanData = tuple(scanData)

#plotScanData(scanData, element, edge, number = 1)

scanData2 = getScanData(data, y_index=2)

#plotScanData(scanData2, element, edge, number = 2 )

scanData4 = getScanData(data, y_index=4)

#plotScanData(scanData4, element, edge, number = 4 )

scanData5 = getScanData(data, y_index=5)

#plotScanData(scanData5, element, edge, number = 5 )

pylab.show()    

writeRAW(options.inFile, scanData4, element=element, edge=edge)
#writeRAW(options.inFile, scanData4, qualifier="_xbpm")
#writeRAW(options.inFile, scanData5, qualifier="_full_ketek")
#writeRAW(options.inFile, scanData, qualifier="_half_ketek")

#print 'scanData4'
#print scanData4
#pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, chooch_graph_data = PyChooch.calc(scanData4,
                                                                            #element, 
                                                                            #edge, 
                                                                            #options.outFile)
chooch_parameters = {'element': element, 
                     'edge': edge,
                     'raw_file': options.inFile.replace('.dat', '.raw'),
                     'output_ps': options.inFile.replace('dat', 'ps'),
                     'output_efs': options.inFile.replace('dat', 'efs')}
                     
chooch_output = commands.getoutput('chooch -p {output_ps} -o {output_efs} -e {element} -a {edge} {raw_file}'.format(**chooch_parameters))
print 'chooch -p {output_ps} -o {output_efs} -e {element} -a {edge} {raw_file}'.format(**chooch_parameters)
plot_efs(chooch_parameters['output_efs'])

print 'results'
print chooch_output
pk, fppPeak, fpPeak, ip, fppInfl, fpInfl = parse_chooch_output(chooch_output)
print 'pk, fppPeak, fpPeak, ip, fppInfl, fpInfl'
print pk, fppPeak, fpPeak, ip, fppInfl, fpInfl
#print pk, fppPeak, fpPeak, ip, fppInfl, fpInfl, chooch_graph_data
