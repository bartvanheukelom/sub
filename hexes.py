import curses
import util

class textarea:
	
	text = ['']
	
	def __init__(self):
		pass
		
	def render(self, win, y, x, width, height):
		yy = y
		for l, line in enumerate(self.text):
			util.log('line', line)
			ll = line
			first = True
			while True:
				
				if yy >= y + height:
					win.addnstr(y+height-1, x, 'Too long text!!', width, curses.A_REVERSE)
					break
				
				if first:
					pref = str(l)
					first = False
				else:
					pref = ''
				win.addnstr(yy, x, pref.rjust(3), 3, curses.A_REVERSE)
				
				util.log('ll', len(ll), ll)
				theresMore = len(ll) > width-4
				if theresMore:
					rl = ll[:width-4]
					ll = ll[width-4:]
				else:
					rl = ll
				util.log('rl', rl)
				win.addnstr(yy, x+4, rl, width-4)
				yy += 1
				if not theresMore: break
				
			if yy >= y + height:
				break
		
	def get_text(self):
		return '\n'.join(self.text)
		
	def input(self, ch):
		if ch == curses.KEY_BACKSPACE:
			if self.text[-1] == '':
				if len(self.text) != 1:
					self.text = self.text[:-1]
			else:
				self.text[-1] = self.text[-1][:-1]
		elif ch == ord('\n'):
			self.text.append('')
		else:
			self.text[-1] += chr(ch)
		

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