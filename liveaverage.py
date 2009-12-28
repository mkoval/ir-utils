#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

from collections import deque
from numpy import mean, median
from sys import argv, exit, stderr, stdin, stdout, stderr

averages = {
	"mean"   : mean,
	"median" : median
}

def error(msg):
	print('{0}: error: {1}'.format(argv[0], msg), file=stderr)

def warning(msg):
	print('{0}: warning: {1}'.format(argv[0], msg), file=stderr)

def main():
	# Only command line argument should be the number of samples to median.
	if len(argv) != 4:
		print('Usage: {0} [mean | median] buf ycol'.format(argv[0]),
		      file=stderr)
		error('incorrect number of arguments, expected {0} and received {1}'.
		      format(4, len(argv) - 1))
		exit(1)
	
	# User must select either median or mean. No other forms of averaging are
	# currently supported.
	if averages.has_key(argv[1]):
		method = averages[argv[1]]
	else:
		error('averaging method must be one of ' + averages.keys().__str__())
		exit(1)
	
	# Size of the buffer from which the median is calculated. Larger buffers
	# give smoother data, but less responsiveness.
	try:
		n = int(argv[2])
		
		if n < 1:
			raise ValueError()
	except ValueError:
		error('buffer size must be a positive integer')
		exit(1)
	
	# We have no way of checking if the columns will be in stdin until we
	# receive it. Negative values are obviously invalid.
	try:
		ycol = int(argv[3])
		
		if ycol < 1:
			raise ValueError()
	except ValueError:
		error('x and y data columns must be positive integers')
		exit(1)
	
	# Deques with a non-default size will automatically discard old elements
	# to maintain the constant size.
	buf = deque([ ], n)
	
	try:
		while True:
			line = stdin.readline()
			line = line.replace('\n', '')
			
			# Waiting for some data to be written to stdin...
			if line == '':
				continue
		
			# Parse the line into a space-delimited list of numbers.
			try:
				data = map(float, line.split(None))
			except ValueError:
				warning('received invalid data "{0}"'.format(line))
				continue
		
			if len(data) < ycol:
				warning('expected a minimum of {0} columns, received {1}'
				        .format(ycol, len(data)))
				continue
		
			buf.append(data[ycol - 1])
			
			# Preserve the columns that we're not interested in. This allows
			# for the chaining of multiple averages via pipes.
			before   = ' '.join(map(str, data[0:(ycol - 1)]))
			after    = ' '.join(map(str, data[ycol:]))
			
			lineout = before + ' ' + method(buf).__str__() + ' ' + after + ' '
			
			print(lineout)
			stdout.flush()
			
			# If you want to know what's going on, these lines are very handy.
			#
			# instuff  = ' '.join(map(str, data))
			# outstuff = lineout
			# print('changed \'{0}\' into \'{1}\''.format(
			#    instuff, outstuff), file=stderr)
			
	# Cleanly handle a the user terminating the script with Ctrl+C.
	except KeyboardInterrupt:
		pass
		
if __name__ == '__main__':
	main()
