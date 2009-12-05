from __future__ import print_function, with_statement
from numpy import array, median
import os
import optparse
import re
import serial
import sys

#
# Parse command line parameters.
#
def main():
	parser = optparse.OptionParser(usage='usage: %prog [options] outfile min max '
	 'step samples')
	parser.add_option('-b', '--baud', dest='baud', default=115200, help='baud rate')
	parser.add_option('-t', '--timeout', dest='timeout', type='int', default=3,
	                  help='maximum timeout, in seconds')
	parser.add_option('-p', '--parity', dest='parity', choices=['none', 'even', 'odd'], 
	                  default='none', help='parity setting')
	parser.add_option('-s', '--stopbits', dest='stopbits', choices=['1', '1.5', '2'],
	                  default='1', help='stop bit setting')
	parser.add_option('-y', '--bytesize', dest='bytesize', choices=['5', '6', '7', '8'],
	                  default='8', help='number of bits per byte')
	parser.add_option('-e', '--endline', dest='endline', choices=['lf', 'cr', 'cr+lf'],
	                  default='cr', help='ASCII character sequence used to end a line '
	                  'where lf=\'\\n\' and cr=\'\\r\'')
	(opts, args) = parser.parse_args()
	
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
			'1.5'  : serial.STOPBITS_ONE_POINT_FIVE,
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
	if len(args) < 5:
		parser.error('incorrect number of arguments')
		return
	device = args[0]

	# Ensure the output file is writable.
	try:
		f = open(args[0], 'w')
	except IOError:
		parser.error('unable to write to \'{0}\'')
		f.close()
		return

	# Starting distance between the IR sensor and the obstruction.
	try:
		params = {
			'min'     : float(args[1]),
			'max'     : float(args[2]),
			'step'    : float(args[3]),
			'samples' : int(args[4])
		}
		
		# Ensure this selection of parameters will not cause an infinite loop (i.e. the
		# sign of the range must be the step size).
		if (params['max'] - params['min']) * params['step'] < 0:
			raise ValueError('minimum, maximum, and step-size parameter induce an infinite'
			                 ' loop')
		elif params['samples'] <= 0:
			raise ValueError('number of samples must be positive')
	except ValueError as err:
		parser.error(err)
		return

	# Attempt to open the specified serial port.
	try:
		ser = serial.Serial(device, **serialopts)
	except serial.SerialException as e:
		parser.error('error: ' + e.__str__())
		return

	ser.open();
	if not ser.isOpen():
		ser.close()
		parser.error('error: unable to open serial port')
		return
	ser.close()
	
	data = {}

	# Read the desired number of samples for each distance.
	for dist in range(params['min'], params['max'], params['step']):
		# Prompt the user to move the obstruction further from the sensor.
		# TODO: Enable endline type selection (i.e. with CR's).
		
		print('Place the obstruction {0} units from the sensor and press enter to continue. '
		      .format(dist), end='')
		sys.stdin.readline()

		data[dist] = []

		# Open the serial connection.
		ser.open()
		if not ser.isOpen():
			print('error: unable to open serial port')	
			return


		# Collect the desired number of samples before moving the object.
		while len(data[dist]) < params['samples']:
			line = ser.readline()

			print(line)
			# Parse sensor values from this line of serial output.
			res = re.match('^pot (\\d+) ir (\\d+)$', line)

			if res != None:
				reading = res.group(2)
				data[dist].append(int(reading))

		# Flush the buffer so we get up-to-date data (i.e. compensate for the
		# microcontroller potentially printing data at a rate that is faster
		# we're reading it.)
		ser.close()

	for dist, samples in data.iteritems():
		for sample in samples:
			print('{0} {1}'.format(dist, sample), file=f)

	print('Data written to {0}'.format(output))
	f.close()

if __name__ == '__main__':
	main()