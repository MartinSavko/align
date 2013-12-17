#!/usr/bin/python

import optparse
import numpy
import pylab

usage = "Program will plot of the energy scan in the raw format -- and also any other format e.g. series of x, y values, one pair per line. Program will display the plot and also save the resulting graph in the .png format."

parser = optparse.OptionParser(usage=usage)

parser.add_option('-r', '--raw', help='raw data file')

options, args = parser.parse_args()

raw = open(options.raw).read().split('\n')

data = [numpy.array(map(float, line.split())) for line in raw if len(line.split()) == 2]

data = numpy.array(data)

pylab.plot(data[:,0], data[:,1])
pylab.title(raw[0])
pylab.xlabel('Energy [eV]')
pylab.ylabel('Normalized counts')

pylab.savefig((options.raw).replace('.raw', '.png'))

pylab.show()
