#!/usr/bin/python

from __future__ import print_function

from collections import deque
from datetime import datetime, timedelta
from optparse import OptionParser
from sys import stderr, stdin, stdout

import csv
import os
import re
import sys
import subprocess
import tempfile

# General plotting style (i.e. how/if to render individual data points and the
# lines between data points). These options represent only the small set of
# gnuplot styles that would be of interest in a live plot. The short single-
# character options can be chained together to style a number of columns in a
# single parameter (e.g. "plb" would plot y1 as points, y2 as lines, and y2 as
# both points and lines).
types = {
	'p' : 'points',
	'l' : 'lines',
	'b' : 'linespoints'
}

# Small subset of color keywords aliased to single character options. These
# options can be chained together in the manner described above.
colors = {
	'r' : 'red',
	'g' : 'green',
	'b' : 'blue',
	'y' : 'yellow',
	'c' : 'cyan',
	'm' : 'magenta',
	'k' : 'black'
}

# Refresh the graphical representation of the plot.
def refresh(gnuplot, xcol, ycol, settings, buf):
	# Force gnuplot to re-render the graph.
	cmd = [ ]
	for i in range(0, len(ycol)):
		cmd.append("'-' using 1:2 notitle w {type} lw {weight} lt 6 lc rgb \"{color}\""\
		      .format(**{
				'type'   : settings['type'][i],
				'color'  : settings['color'][i],
				'weight' : settings['size']
		}))
	
	print('set xrange [{minx}:{maxx}]\n'\
	      'set xlabel "{labelx}"\n'\
	      'set ylabel "{labely}"\n'\
	      'set yrange [{miny}:{maxy}]'.format(**settings), file=gnuplot.stdin)
	
	print('plot ' + ', '.join(cmd), file=gnuplot.stdin)
		
	# Pipe the buffer of data into gnuplot. This needs to be repeated for each
	# column of y-data; each terminated by a single 'e' character.
	for col in ycol:
		format_row = lambda val: '{0} {1}'.format(val[xcol - 1], val[col - 1])
		print('\n'.join(map(format_row, buf)), file=gnuplot.stdin)
		print('e', file=gnuplot.stdin)
	
	gnuplot.stdin.flush()

def main():
	parser = OptionParser(usage='usage: %prog [options] xcol ycol1 [ycol2 ...]')
	parser.add_option('-f', '--freq', dest='freq', type="int", default=60,
		help='number of redraws per second (in Hz)')
	parser.add_option('-n', '--nsamples', dest='nsamples', type='int',
		default=100, help='number of samples to display at once')
	parser.add_option('--xlabel', dest='labelx', default='x',
	    help='descriptive label for the x-axis')
	parser.add_option('--ylabel', dest='labely', default='y',
	    help='descriptive label for the y-axis')
	parser.add_option('--min', dest='ymin', type='float', default=-10.0,
	    help='minimum y-coordinate in the range of y values')
	parser.add_option('--max', dest='ymax', type='float', default=10.0,
	    help='maximum y-coordinate in the range of y values')
	parser.add_option('-p', '--plot', dest='type', default=None,
		help="list of plot styles, in order of ycol ('p' for points, 'l' for"
		     "lines, or 'b' for both)")
	parser.add_option('-c', '--color', dest='color', default=None,
		help='list of colors, in order of ycol (blacK, Red, Green, Blue,'
		     'Yellow, Cyan, and Magenta)')
	parser.add_option('-s', '--size', dest='size', default=3, type='int',
		help='thickness (i.e. weight) of lines and size of points')
	(opts, args) = parser.parse_args()
	
	if len(args) < 2:
		parser.error('too few arguments')
		return
	
	# Validate the required x and y column numbers.
	try:
		xcol = int(args[0])
		ycol = [ ]
		ncol = len(args) - 1
	
		for col in args[1:]:
			ycol.append(int(col))
		
		# gnuplot uses one-indexed data columns.
		if min(xcol, min(ycol)) <= 0:
			raise ValueError()
	except ValueError:
		parser.error('x and y column numbers must be positive integers')
		return
	
	# Initialize sensible default plot settings that can be overriden using
	# optional commandline flags.
	settings = {
		'labelx' : opts.labelx,
		'labely' : opts.labely,
		# The x-range will be almost immediately modified by gnuplot.
		'minx'  : 0.0,
		'maxx'  : 1.0,
		# Very domain-specific. Most likely will be overridden with parameters.
		'miny'  : opts.ymin,
		'maxy'  : opts.ymax,
		# Type of plot (i.e. lines, points, )
		'type'  : [ 'lines' ] * len(ycol),
		# Repeat the available colors as required to assign one to each ycol.
		'color' : (colors.values() * (len(ycol) / len(colors) + 1))[0:len(ycol)],
		# Set both line thickness and point size.
		'size'  : opts.size
	}
	
	# Validate the y-range to which the window is restricted.
	if opts.ymin == opts.ymax:
		parser.error('y range must be non-empty')
		return
	elif opts.ymin > opts.ymax:
		print('warning: negative y-range specified; results will be reflected' +
		      ' across the x-axis', file=stderr)
	
	# Validate the frequency (must be a positive integer).
	if opts.freq <= 0:
		parser.error('redraw frequency must be a positive integer (in Hz)')
		return
	
	# Validate the number of samples (must be a positive integer).
	if opts.nsamples <= 0:
		parser.error('sample buffer size must be a positive integer')
		return
	
	# Validate the point size and line width (must be a positive integer)
	if opts.size <= 0:
		parser.error('point size and line width must be a positive integer')
		return
	
	# Parse the list of user-specified plot styles (i.e. line vs points).
	if opts.type != None:
		if len(opts.type) != len(ycol):
			parser.error('expected {0} styles, received {1}'.format(len(ycol),
			             len(opts.type)))
			return
		
		settings['type'] = [ ]
		
		for ch in opts.plot:
			if types.has_key(ch):
				settings['type'].append(types[ch])
			else:
				parser.error("'{0}' is not a valid plot style".format(ch))
				return
	
	# Parse the user-specified list of colors.
	if opts.color != None:
		if len(opts.color) != len(ycol):
			parser.error('expected {0} colors, received {1}'.format(len(ycol),
			             len(opts.color)))
			return
		
		settings['color'] = [ ]
		
		for ch in opts.plot:
			if colors.has_key(ch):
				settings['color'].append(colors[ch])
			else:
				parser.error("'{0}' is not a valid color".format(ch))
				return
	
	# Open a connection to gnuplot via pipes.
	gnuplot = subprocess.Popen('gnuplot', stdout=stdout,
	                           stdin=subprocess.PIPE)
	
	# Keep a buffer of relevent data points. Only points in the buffer will be
	# plotted. This makes plotting an O(m) operation, as opposed to a horrid
	# O(m*n) operation (where m = number of lines and n = number of data points
	# piped to this script).
	buf = deque()
	
	# Throttle the refresh rate of the graph.
	lastTime = datetime.now()
	thresh   = timedelta(0, 0, 0, 100.0 / opts.freq)
	
	# Highest column number required to plot the requested data.
	maxCol = max(xcol, max(ycol))
	
	try:
		while True:
			line = stdin.readline()
			
			# TODO: Check if any errors have occurred in gnuplot.
			
			# Convert the raw line of data into a list of floats using the
			# str.split function's default behavior: any amount of continuous
			# whitespace serves as a delimiter.
			try:
				cur = map(float, line.split(None))
			except ValueError:
				print('warning: received invalid data "{0}"'.format(line),
				      file=stderr)
				continue
			
			# Make sure we have enough floats to plot the requested data (i.e.
			# if the user wishes to plot column 4, there must be at least four
			# columns of data).
			if len(cur) < maxCol:
				print('warning: received only {0} of {1} columns of'.format(
				      len(cur), maxCol), file=stderr)
				continue
			
			# Keep a constant-sized buffer to speed up plotting.
			buf.append(cur)
			
			if len(buf) > opts.nsamples:
				buf.popleft()
			
			# Manually update the x-range of the window to avoid gnuplot's
			# rounding algorithm. Note that the data is internally zero-indexed,
			# but is one-indexed in gnuplot.
			settings['minx'] = buf[0][xcol - 1]
			settings['maxx'] = cur[xcol - 1]
			
			# Throttle the redraw rate to the specified frequency.
			curTime = datetime.now()
			if curTime - lastTime >= thresh and len(buf) > 1:
				refresh(gnuplot, xcol, ycol, settings, buf)
				lastTime = curTime
	
	# Cleanly handle Ctrl+C termination by the user as it is the most common
	# method of exiting this script. See the finally clause for cleanup code.
	except KeyboardInterrupt:
		pass
	finally:
		gnuplot.kill()

if __name__ == '__main__':
	main()