#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

from csv import DictReader
from numpy import array, interp, lexsort
from sys import argv, exit, stderr, stdin, stdout, stderr

def usage():
	print('usage: {0} file col'.format(argv[0]), file=stderr)

def error(msg):
	print('{0}: error: {1}'.format(argv[0], msg), file=stderr)

def warning(msg):
	print('{0}: warning: {1}'.format(argv[0], msg), file=stderr)

def main():
	if len(argv) != 3:
		usage()
		error('expected 2 argument, received {0}'.format(len(argv) - 1))
		return 1
	
	# Validate the column number (this is the column that is interpolated).
	try:
		col = int(argv[2])
		if col < 1:
			raise ValueError()
	except ValueError:
		error('column number must be a positive integer, received "{0}"'.
		      format(argv[2]))
		return 1
	
	# Make sure the file is readable since DictReader seems to silently fail
	# if the file does not exist.
	try:
		f = open(argv[1], 'r')
	except IOError:
		error('unable to read "{0}"'.format(argv[1]))
		return 1	
	
	reader = DictReader(f, fieldnames=['distance', 'reading'])
	reads  = []
	dists  = []
	
	# Generate an interpolation based upon the data file.
	try:
		for row in reader:
			reads.append(float(row['reading']))
			dists.append(float(row['distance']))
	except ValueError:
		error('invalid data on line {0}'.format(reader.line_num))
		return 1
	finally:
		f.close()
	
	# Sort the readings to make sure their x-coordinates are monotonic
	# increasing. Non-monotonic increasing x-coordinates will produce garbage
	# output from interp(x, y).
	order = lexsort((dists, reads))
	reads = array(reads)[order]
	dists = array(dists)[order]
	
	# Hack around NumPy's Matlab-clone interpolation function. It would be
	# much more usable if it returned a function.
	f = lambda reading: interp([reading], reads, dists)[0]
	
	# Convert input from stdin from analog voltages to distances using the
	# interpolation function.
	try:
		while True:
			line = stdin.readline()
			line = line.replace('\n', '')
			
			if line == '':
				continue
			
			# Convert the data to a list of floats; a much more usable format.
			try:
				data = map(float, line.split(None))
			except ValueError:
				warning('invalid data "{0}"'.format(line))
				continue
			
			if len(data) < col:
				warning('expected at least {0} columns, received {1}'.
				        format(col, len(data)))
				continue
			
			# Preserve the columns that we're not interested in. This allows
			# for the chaining of multiple averages via pipes.
			before  = ' '.join(map(str, data[0:(col - 1)]))
			after   = ' '.join(map(str, data[col:]))
			modded  = str(f(data[col - 1]))
			lineout = before + ' ' + modded + ' ' + after
			
			print(lineout)
			stdout.flush()
			
	except KeyboardInterrupt:
		pass
	
	return 0

if __name__ == '__main__':
	exit(main())
