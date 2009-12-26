#!/Library/Frameworks/Python.framework/Versions/2.6/bin/python

from __future__ import print_function
import math

t = 0
while True:
	print('{0} {1}'.format(t, math.sin(t)))
	t += 2.0 * math.pi / 100.0