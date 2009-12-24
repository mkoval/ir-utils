#!/usr/bin/python

from __future__ import print_function

from collections import deque
from numpy import mean, median
from sys import argv, exit, stderr, stdin, stdout

def error(msg):
	print('{0}: error: {1}'.format(argv[0], msg), file=stderr)

def warning(msg):
	print('{0}: warning: {1}'.format(argv[0], msg), file=stderr)

def main():
	# Only command line argument should be the number of samples to median.
	if len(argv) != 5:
		print('Usage: {0} [mean | median] buf xcol ycol'.format(argv[0]),
		      file=stderr)
		error('incorrect number of arguments, expected {0} and received {1}'.
		      format(4, len(argv) - 1))
		exit(1)
	
	# User must select either median or mean. No other forms of averaging are
	# currently supported.
	if argv[1] not in [ 'mean', 'median' ]:
		error('averaging method must be either "mean" or "median"')
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
		xcol = int(argv[3])
		ycol = int(argv[4])
		
		if xcol < 1 or ycol < 1:
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
		
			# Parse the line into a space-delimited list of numbers.
			try:
				data = map(float, line.split(None))
			except ValueError:
				warning('received invalid data "{0}"'.format(line))
				continue
		
			if len(data) < max(xcol, ycol):
				warning('expected a minimum of {0} columns, received {1}'
				        .format(max(xcol, ycol), len(data)))
				continue
		
			buf.append(data[ycol - 1])
		
			print(data[xcol - 1], median(buf))
	# Cleanly handle a the user terminating the script with Ctrl+C.
	except KeyboardInterrupt:
		pass
		
if __name__ == '__main__':
	main()
