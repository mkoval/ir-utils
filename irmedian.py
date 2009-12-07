#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, with_statement
from numpy import array, median
from collections import deque
import csv
import os
import optparse
import numpy
import re
import serial
import sys

def main():
	parser = optparse.OptionParser(usage='usage: %prog [options] infile outfile pts')
	(opts, args) = parser.parse_args()
	
	if len(args) < 3:
		parser.error('incorrect number of arguments')
		return
	
	# Ensure that the number of points is a positive integer.
	try:
		size = int(args[2])
		if size <= 0:
			raise ValueError()
	except ValueError:
		parser.error('number of points must be a positive integer')
		return
	
	# Parse the results into a bunch of named dicts. Note that I am assuming
	# that the data is sorted by timestamp.
	try:
		fraw = open(args[0], 'r')
		raw  = csv.DictReader(fraw)
	except IOError:
		parser.error('unable to open "{0}" for reading'.format(args[0]))
		return
	
	fields = raw.fieldnames
	if 'ir_median' not in fields:
		fields.append('ir_median')

	# Open the output file for writing
	try:
		fparsed = open(args[1], 'w')
		parsed  = csv.DictWriter(fparsed, fields)
	except IOError:
		parser.error('unable to open "{0} for writing'.format(args[1]))
		return
	
	# Make sure the data file has all the columns we reference.
	if not set(['time', 'ir']).issubset(set(raw.fieldnames)):
		parser.error('data file must have "time", and "ir" columns')
		return

	size  = int(args[2])
	irbuf = deque()
	line  = 1 # Begin at line one to compensate for the header line.
	for sample in raw:
		line += 1
		
		# Skip invalid lines and print out a warning message
		try:
			irbuf.append(int(sample['ir']))
		except ValueError:
			print('warning: invalid ir value in {0} at line {1}'
			      .format(args[0], line), file=sys.stderr)
		
		# Don't preceed until the buffer is full. This will truncate the first
		# "size - 1" elements.
		if len(irbuf) < size:
			continue
		
		# Replace the current sample's IR reading with the running median.
		sample_med = sample
		sample_med['ir_median'] = median(irbuf)
		
		parsed.writerow(sample_med)
		
		# Remove the oldest sensor value from the buffer. This keeps the
		# total number of elements in it at a total of "size", excluding
		# the already-truncated leading elements.
		irbuf.popleft()
	
	fraw.close()
	fparsed.close()
	
if __name__ == '__main__':
	main()
