import curses
import util

def fill_line(win, y, x, width, attr=0, char=' '):
	fill_rect(win, y, x, 1, width, attr=attr, char=char)

def fill_rect(win, top, left, height, width, attr=0, char=' '):
	for x in range(left, left+width):
		for y in range(top, top+height):
			win.addch(y, x, char, attr)

def border(win, top, left, height, width, header='', attr=0, clear=False):
	
	if clear:
		fill_rect(win, top, left, height, width)
	
	# horizontal lines
	for x in range(left+1, left+width-1):
		win.addch(top, x, curses.ACS_HLINE, attr)
		win.addch(top+height-1, x, curses.ACS_HLINE, attr)
	# vertical lines
	for y in range(top+1, top+height-1):
		win.addch(y, left, curses.ACS_VLINE, attr)
		win.addch(y, left+width-1, curses.ACS_VLINE, attr)
	# corners
	win.addch(top, left, curses.ACS_ULCORNER, attr)
	win.addch(top, left+width-1, curses.ACS_URCORNER, attr)
	win.addch(top+height-1, left, curses.ACS_LLCORNER, attr)
	win.addch(top+height-1, left+width-1, curses.ACS_LRCORNER, attr)
	
	#header
	if header != '':
		hw = len(header)
		win.addnstr(top, left + int((width-hw)/2), header, width-2, attr)