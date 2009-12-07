#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import optparse
import re
import sys

parser = optparse.OptionParser(usage='%prog [OPTIONS] [COEFF] ...')
parser.add_option('--pattern', dest='pattern',
type='string', default='([\\d\\.\\-\\e]+)',
	help='pattern to extract one number from the line')

options, args = parser.parse_args()
coeffs = [ None ] * len(args)
N = len(coeffs)

for i in range(N):
	try:
		coeffs[i] = float(args[i])
	except ValueError:
		print("{0} is not a floating-point number".format(args[i]))
		sys.exit(1)

pattern = re.compile(options.pattern)

buff = [ 0 ] * N
index = 0

while 1:
	line = sys.stdin.readline()
	if len(line) == 0:
		break
	
	match = re.match(pattern, line)
	token = match.group(1)
	number = float(token)
	
	buff[index%N] = number
	total = sum([coeffs[i]*buff[i] for i in range(N)])
	
	print("{0}".format(total))
	sys.stdout.flush()
	
	index += 1


