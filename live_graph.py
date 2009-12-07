#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import optparse
import re
import sys

# This is a reallllllly simple live plotter for the terminal.
#
# It reads in lines of input, finds ONE number on the line, uses that to
# calculate a screen column, and prints out a line with one X on it.

parser = optparse.OptionParser(usage='%prog [OPTIONS]')
parser.add_option('--min', dest='min',
	type='float', default=0.0, help='left edge of the plotting window')
parser.add_option('--max', dest='max',
	type='float', default=1.0, help='right edge of the plotting window')
parser.add_option('--ncols', dest='ncols',
	type='int', default=80,
	help='number of columns wide the terminal window.')
parser.add_option('--step', dest='step',
	type='int', default=1,
	help='read every n lines (e.g. if step=2, skip every other line)')
parser.add_option('--pattern', dest='pattern',
	type='string', default='([\\d\\.\\-\\e]+)',
	help='pattern to extract one number from the line')

options, args = parser.parse_args()

if len(args) != 0:
	parser.error('Does not take any arguments')

w_min   = options.min
w_max   = options.max
w_ncols = options.ncols
step    = options.step
pattern = re.compile(options.pattern)

while 1:
	line = sys.stdin.readline()
	if len(line) == 0:
		break
	
	match = re.match(pattern, line)
	token = match.group(1)
	number = float(token)
	
	if number < w_min:
		print("<<<<<<< LOW <<<<<<<")
	
	elif number > w_max:
		print(">>>>>>> HI >>>>>>>")
	
	else:
		col = int(round( (number-w_min)/(w_max-w_min) * w_ncols ))
		for i in range(col-1):
			print(" ", end='')
		
		print('X')
	
	sys.stdout.flush()
	
	for i in range(step-1):
		sys.stdin.readline()
