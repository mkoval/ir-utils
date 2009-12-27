#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import time
import math

counter = 0

while 1:
	arg = counter / 100.0
	amp = int(100 * math.sin(arg)) + 110
	
	print("{0} {1}".format(counter, amp))
	
	counter += 1
	time.sleep(18.6 / 1000)
