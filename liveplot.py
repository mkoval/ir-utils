#!/Library/Frameworks/Python.framework/Versions/2.6/bin/python

# cat noisy.txt | ./slow 100 | ./liveplot.py -pl -cb -f60 -w1000 -s1 --min 50 --max 150 1 4

from __future__ import print_function
from datetime import datetime, timedelta
import collections
import optparse
import os
import sys
import subprocess
import tempfile

# Plot type options (i.e. line vs point).
plots = {
	'p' : 'points',
	'l' : 'lines'
}

colors = {
	'r' : 'red',
	'g' : 'green',
	'b' : 'blue',
	'y' : 'yellow',
	'c' : 'cyan',
	'm' : 'magenta'
}

def get_first(str):
	return str.split(' ', 1)[0]

# Refresh the graphical representation of the plot.
def refresh(gnuplot, settings, buf):
	# Force gnuplot to re-render the graph.
	cmd = [ ]
	for i in range(0, len(settings['ycols'])):
		cmd.append("'-' using {xcol}:{ycol} w {type} lw {weight} lt 6 lc rgb \"{color}\""\
		      .format(**{
				'xcol'   : settings['xcol'],
				'ycol'   : settings['ycols'][i],
				'color'  : settings['colors'][i],
				'type'   : settings['type'][i],
				'weight' : settings['size']
		}))
	
	print('set xrange [{xmin}:{xmax}]\n'\
	      'set yrange [{ymin}:{ymax}]'.format(**{
		'xmin'   : settings['minX'],
		'xmax'   : settings['maxX'],
		'ymin'   : settings['minY'],
		'ymax'   : settings['maxY']
	}), file=gnuplot.stdin)
	
	print('plot ' + ', '.join(cmd), file=gnuplot.stdin)
		
	# Pipe the buffer of data into gnuplot. This needs to be repeated for each
	# column of y-data; each terminated by a single 'e' character.
	for i in range(0, len(settings['ycols'])):
		print('\n'.join(buf), file=gnuplot.stdin)
		print('e', file=gnuplot.stdin)
	
	gnuplot.stdin.flush()

def main():
	parser = optparse.OptionParser(usage='usage: %prog [options] xcol ycol1 [ycol2 [ycol3 ...]]')
	parser.add_option('-f', '--freq', dest='freq', type="int", default=60,
	                  help='number of redraws per second (in Hz)')
	parser.add_option('-p', '--plot', dest='plot', default=None,
	                  help='list of plot styles, in order of ycol (\'p\' for points, \'l\' for lines)')
	parser.add_option('-c', '--color', dest='color', default=None,
	                  help='list of colors, in order of ycol (blacK, Red, Green, Blue, Yellow, Cyan, and Magenta)')
	parser.add_option('-s', '--size', dest='size', default=3, type="int",
	                  help='thickness (i.e. weight) of lines and size of points')
	parser.add_option('-w', '--width', dest='width', default=100, type="float")
	parser.add_option('--min', dest='ymin', default=-10, type="float")
	parser.add_option('--max', dest='ymax', default=+10, type="float")
	(opts, args) = parser.parse_args()
	
	if len(args) < 2:
		parser.error('too few arguments')
		return
	
	# Validate the required parameters (i.e. x and y column numbers).
	try:
		# For simplicity, all y-coordinates are assumed to share the same x-coordinate.
		xcol  = int(args[0])
		ycols = []
		
		if xcol <= 0:
			raise ValueError()
		
		# With gnuplot's flexibility, it is very easy to support multiple y-coordinates.		
		for ycol in args[1:]:
			ycols.append(int(ycol))
			
			if ycol <= 0:
				raise ValueError()
	except ValueError:
		parser.error('x and y column numbers must be positive')
		return
	
	if opts.width != None and opts.width <= 0:
		parser.error('width must be a positive real number')
		return
	elif opts.size <= 0:
		parser.error('line size must be a positive integer')
		return
	elif opts.freq <= 0:
		parser.error('frequency must be a positive integer')
		return
	elif opts.ymax < opts.ymin:
		parser.error('maximum y value must exceed minimum y value')
	
	# Populate the graphical plot options.
	settings = {}
	if opts.plot == None:
		settings['type'] = [ 'lines' for ycol in ycols ]
	else:
		settings['type'] = [ ]
		
		for ch in opts.plot:
			try:
				value = plots[ch]
				settings['type'].append(value)
			except KeyError:
				parser.error("unknown plot type '{0}'".format(ch))
				return
		
		# Enforce a one-to-one mapping between plot types and y columns.
		if len(settings['type']) != len(ycols):
			parser.error('expected {0} plot setting(s), received {1}'\
			             .format(len(ycols), len(settings['type'])))
			return
	
	# ...
	settings['minY']  = opts.ymin
	settings['maxY']  = opts.ymax
	settings['ycols'] = ycols
	settings['xcol']  = xcol
	settings['size']  = opts.size
	
	settings['colors'] = [ ]
	if opts.color == None:
		done = lambda: len(settings['colors']) >= len(ycols)
		
		# Cycle through the list of colors.
		while not done():
			for color_short, color_long in colors.items():
				if done():
					break
				else:
					settings['colors'].append(color_long)
	else:
		try:
			# Read the user's color choices.
			for ch in opts.color:
				settings['colors'].append(colors[ch])
		except KeyError:
			parser.error("unknown color symbol '{0}'".format(ch))
			return
		
		if len(settings['colors']) != len(ycols):
			parser.error('expected {0} colors, received {1}'
			             .format(len(settings['colors']), len(ycols)))
			return
	
	stream = sys.stdin
	
	# Open a connection to gnuplot via pipes.
	gnuplot = subprocess.Popen(['gnuplot', '-persist'], stdout=sys.stdout, stdin=subprocess.PIPE)
	
	# Keep a buffer of relevent data points. Only points in the buffer will be plotted.
	buf  = collections.deque()
	minX = 0.0
	maxX = opts.width
	
	# Throttle the refresh rate of the graph.
	lastRedraw = datetime.now()
	
	try:
		while True:
			updated = stream.readline().replace('\n', '').replace('\r', '')
			
			# HACK
			updated = updated.replace(',', ' ')
			
			if updated == '':
				continue
			buf.append(updated)
			
			if len(buf) > opts.width:
				buf.popleft()
			
			# Remove the oldest point to keep the size constant.
			try:
				curX   = float(get_first(updated))
				firstX = float(get_first(buf[0]))
			except ValueError:
				print('warning: received invalid data "{0}"'.format(updated), file=sys.stderr)
				continue
				
			settings['minX'] = firstX
			settings['maxX'] = curX
			
			# Throttle the redraw rate to the specified frequency.
			curTime = datetime.now()
			if curTime - lastRedraw >= timedelta(0, 0, 0, 100.0 / opts.freq) and len(buf) > 1:
				refresh(gnuplot, settings, buf)
				lastRedraw = curTime
					
	# Clean up our resources in the finally clause (see below).
	except KeyboardInterrupt:
		pass
	finally:
		gnuplot.kill()
		stream.close()

if __name__ == '__main__':
	main()