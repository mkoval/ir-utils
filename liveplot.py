from __future__ import print_function
import optparse
import os
import sys
import subprocess
import tempfile

def main():
	parser = optparse.OptionParser(usage='usage: %prog [options] file xcol ycol')
	parser.add_option('-f', '--file', dest='infile', default=None, help='file from which to read the data (defaults to stdin)')
	parser.add_option('-o', '--output', dest='outfile', default=None, help='temporary file used to buffer stdin (applies only if -f is omitted)')
	(opts, args) = parser.parse_args()
	
	if len(args) != 2:
		parser.error('incorrect number of arguments')
		return
	elif opts.infile != None and opts.outfile != None:
		parser.error('--file and --output flags are mutually exclusive')
		return
	
	# Insure the parameters are valid.
	try:
		xcol = int(args[0])
		ycol = int(args[1])
		
		if xcol <= 0 or ycol <= 0:
			raise ValueError()
	except ValueError:
		parser.error('x and y column numbers must be positive')
		return
	
	# Create a temporary file to alias stdin.
	infile = opts.infile
	try:
		if opts.infile == None and opts.outfile == None:
			tmpfile = tempfile.NamedTemporaryFile('w')
			infile  = tmpfile.name
		# Use the user-defined temporary file.
		elif opts.infile == None and opts.outfile != None:
			tmpfile = open(opts.outfile, 'w')
			infile  = opts.outfile
	except IOError:
		parser.error('unable to write to \'{0}\''.format(opts.outfile))
	
	# Read the input file or the temporary alias for stdin
	try:
		stream = open(infile, 'r')
	except IOError:
		parser.error('unable to read \'{0}\''.format(infile))
		return
	
	# Open a connection to gnuplot via pipes.
	gnuplot = subprocess.Popen(['gnuplot', '-persist'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
	
	try:
		while True:
			# Redirect stdin to a temporary file.
			if opts.infile == None:
				print(sys.stdin.readline(), file=tmpfile, end='')
				tmpfile.flush()
			
			line = stream.readline()
		
			# Force GNUPlot to re-render the graph.
			if line != '':
				print('plot "{0}" using {1}:{2} with lines'.format(infile, xcol, ycol),
				      file=gnuplot.stdin)
	# Clean up our resources in the finally clause (see below).
	except KeyboardInterrupt:
		pass
	finally:
		gnuplot.kill()
		stream.close()
		
		# Also close the temporary alias for stdin, if applicable.
		if opts.infile == None:
			tmpfile.close()

if __name__ == '__main__':
	main()