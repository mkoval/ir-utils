from __future__ import print_function, with_statement
from numpy import array, median
import os
import optparse
import re
import serial
import sys

def calibrate_distance(ser, newline, args):
	# Log data to a file.
	if len(args) == 1:
		output = args[0]
	else:
		print('error: no output file specified', file=sys.stderr)
		return
	
	# Ensure the output file is writable.
	try:
		f = open(output, 'w')
	except IOError:
		print('error: unable to write to \'{0}\'', file=sys.stderr)
		f.close()
		return
	
	# Starting distance between the IR sensor and the obstruction.
	dist_min = input('Minimum Distance: ')
	if dist_min <= 0:
		print('error: minimum distance must be positive', file=sys.stder)
		return
	
	# Final distance between the IR sensor and the obstruction.
	dist_max = input('Maximum Distance: ')
	if dist_max <= dist_min:
		print('error: maximum distance must exceed minimum distance', file=sys.strerr)
		return
	
	# Increments in which the distance between the IR sensor and the obstruction is moved.
	dist_step = input('Step Distance: ')
	if dist_step < 0 or dist_step != int(dist_step) != 0:
		print('error: number of steps must be a positive integer', file=sys.stderr)
		return
	
	# Number of samples per data point.
	num_samples = input('Samples per Distance: ')
	if num_samples < 0 or num_samples != int(num_samples):
		print('error: number of samples must be a positive integer', file=sys.stderr)
	
	data = {}
	
	# Read the desired number of samples for each distance.
	for dist in range(dist_min, dist_max + dist_step, dist_step):
		# Prompt the user to move the obstruction further from the sensor.
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
		while len(data[dist]) < num_samples:
			line = ser.readline() # eol=newline
			
			print(line)
			# Parse sensor values from this line of serial output.
			res = re.match('^pot (\\d+) ir (\\d+)$', line)
			
			if res != None:
				reading = res.group(2)
				data[dist].append(int(reading))
		
		# Flush the buffer to ensure we're getting up-to-date data.
		ser.close()
	
	for dist, samples in data.iteritems():
		for sample in samples:
			print('{0} {1}'.format(dist, sample), file=f)
	
	print('Data written to {0}'.format(output))
	f.close()

#
# Parse command line parameters.
#
def main():
	parser = optparse.OptionParser(usage='usage: %prog [options] device [...]')
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
	if len(args) < 1:
		parser.error('error: incorrect number of arguments')
		return
	device = args[0]
	
	# Attempt to open the specified serial port.
	try:
		ser = serial.Serial(device, **serialopts)
	except serial.SerialException as e:
		print('error: ' + e.__str__(), file=sys.stderr)
		return
	
	# Ensure that we are able to open the serial port.
	ser.open();
	if not ser.isOpen():
		print('error: unable to open serial port')	
		return
	
	calibrate_distance(ser, opts.endline, args[1:])

if __name__ == '__main__':
	main()