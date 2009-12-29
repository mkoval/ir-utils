#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
import sys

try:
	for line in sys.stdin:
		print(line, end='')
		sys.stdout.flush()
	
		time.sleep(18.6 / 1000)
except KeyboardInterrupt:
	pass