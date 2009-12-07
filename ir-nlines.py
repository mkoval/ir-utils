#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hey Michael I'm stealing your code!!

from __future__ import print_function, with_statement
from numpy import array, median
import os
import optparse
import re
import serial
import sys

parser = optparse.OptionParser(usage='usage: %prog [options] device nlines')
parser.add_option(
	'-b', '--baud', dest='baud',	default=115200, help='baud rate')
parser.add_option(
	'-t', '--timeout', dest='timeout', type='int', default=3,
	help='maximum timeout, in seconds')
parser.add_option(
	'-p', '--parity', dest='parity', choices=['none', 'even', 'odd'], 
	default='none', help='parity setting')
parser.add_option(
	'-s', '--stopbits', dest='stopbits', choices=['1', '1.5', '2'],
	default='1', help='stop bit setting')
parser.add_option(
	'-y', '--bytesize', dest='bytesize', choices=['5', '6', '7', '8'],
	default='8', help='number of bits per byte')
parser.add_option(
	'-e', '--endline', dest='endline', choices=['lf', 'cr', 'cr+lf'],
	default='cr', help='ASCII character sequence used to end a line '
	'where lf=\'\\n\' and cr=\'\\r\'')

opts, args = parser.parse_args()

# Convert command line parameters into the pySerial enums.
serialopts = { 
	'baudrate' : opts.baud,
	'timeout'  : opts.timeout,
	'parity'   : {
		'none' : serial.PARITY_NONE, 
		'even' : serial.PARITY_EVEN,
		'odd'  : serial.PARITY_ODD
	}[opts.parity],
	'stopbits' : {
		'1'    : serial.STOPBITS_ONE,
#		'1.5'  : serial.STOPBITS_ONE_POINT_FIVE,
		'2'    : serial.STOPBITS_TWO
	}[opts.stopbits],
	'bytesize' : {
		'5'    : serial.FIVEBITS,
		'6'    : serial.SIXBITS,
		'7'    : serial.SEVENBITS,
		'8'    : serial.EIGHTBITS
	}[opts.bytesize]
}

# Ensure that the TTY device was specified.
if len(args) != 2:
	parser.error('incorrect number of arguments')
	sys.exit(1)

device = args[0]
nlines = int(args[1])

# Attempt to open the specified serial port.
try:
	ser = serial.Serial(device, **serialopts)
except serial.SerialException as e:
	print('error: ' + e.__str__(), file=sys.stderr)
	sys.exit(1)

ser.open()
if not ser.isOpen():
	print("Failed to open serial port")
	sys.exit(1)

if nlines < 0:
	while 1:
		line = ser.readline()
		print("{0}".format(line), end='')
		sys.stdout.flush()

else:
	for i in range(nlines):
		line = ser.readline()
		print("{0}".format(line), end='')
		sys.stdout.flush()

ser.close()
