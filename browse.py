import curses
import sys

import svnwrap
import util
import hexes
import iutil
import ilog

class browse:

	tempStatusBar = None
	
	def __init__(self, args):
		self.args = args
		curses.wrapper(self.loop)

	def selectedUrl(self):
		path = self.root + '/' + '/'.join(self.path)
		if self.selectedFile and self.selectedFile['name'] != '.':
			path += '/' + self.selectedFile['name']
		return path

	def moveSelection(self, direction):
		self.selectedFile = util.navigateList(self.files, self.selectedFile, direction)
		pass

	def renderAll(self):
		self.win.clear()
		height, width = self.win.getmaxyx()		
		
		cursorX = width-1
		cursorY = height-1
		
		self.win.addnstr(0, 0, self.selectedUrl(), width, curses.A_REVERSE)
	
		colKind = 0
		colName = colKind + 2
		colDate = width - 19
		colAuth = colDate - 12
		colRev = colAuth - 8

		def render_file(y, file, is_sel):
			attr = curses.A_REVERSE if is_sel else 0
			if is_sel:
				hexes.fill_line(self.win, y, 0, width, curses.A_REVERSE)
			self.win.addnstr(y, colKind, '📂' if file['kind'] == 'dir' else '', colName - colKind, attr)
			self.win.addnstr(y, colName, file['name'], colRev - colName, attr)
			self.win.addnstr(y, colRev, file['revision'], colAuth - colRev, attr)
			self.win.addnstr(y, colAuth, file['author'], colDate - colAuth, attr)
			self.win.addnstr(y, colDate, file['date'], width - colDate, attr)
		iutil.render_list(self.win, self.files, self.selectedFile, 1, height-2, width, render_file)

		# --- status bar --- #

		if self.tempStatusBar != None:
			statusBar = self.tempStatusBar + ' (press any key to dismiss...)'
		else:
			statusBar = '[↑|↓] Select  '
			if self.selectedFile and self.selectedFile['kind'] == 'dir' and self.selectedFile['name'] != '.':
				statusBar += '[→] Enter  '
			if len(self.path) != 0:
				statusBar += '[←] Up  '
			if self.selectedFile:
				statusBar += '[L]og  '
			statusBar += '[Q]uit'
		
		# width - 1 because writing the bottomrightmost character generates an error
		hexes.fill_line(self.win, height-1, 0, width-1, attr=curses.A_REVERSE)
		self.win.addnstr(height-1, 0, statusBar, width-1, curses.A_REVERSE)

		self.win.move(cursorY, cursorX)

		self.win.refresh()
	
	def navigate(self, path):
		self.path = path
		self.files = svnwrap.ls(self.root + '/' + '/'.join(self.path))
		self.files.insert(0, {
			'name': '.',
			'kind': 'dir',
			'revision': '?',
			'author': '?',
			'date': '?'
		})
		self.selectedFile = None
		
	def loop(self, win):
		self.win = win

		info = svnwrap.info().find('entry')
		self.root = info.find('repository').find('root').text
		self.navigate(info.find('relative-url').text.split('/')[1:])
		
		# input loop
		while (True):
			
			self.renderAll()
			
			# wait for input
			ch = win.getch()
			try:
				char = chr(ch)
			except ValueError:
				char = None
		
			self.tempStatusBar = None

			if ch == 113: # Q
				break
			elif ch == curses.KEY_RESIZE:
				pass
			else:
				if ch == curses.KEY_DOWN:
					self.moveSelection(1)
				elif ch == curses.KEY_UP:
					self.moveSelection(-1)
				elif ch == curses.KEY_NPAGE:
					self.moveSelection(10)
				elif ch == curses.KEY_PPAGE:
					self.moveSelection(-10)
				elif ch == curses.KEY_RIGHT:
					if self.selectedFile and self.selectedFile['kind'] == 'dir' and self.selectedFile['name'] != '.':
						self.navigate(self.path + [self.selectedFile['name']])
				elif ch == curses.KEY_LEFT:
					if len(self.path) != 0:
						self.navigate(self.path[:len(self.path)-1])
				elif ch == 108: # L
					if self.selectedFile:
						log = ilog.ilog([self.selectedUrl()])
						log.loop(self.win)
				else:
					self.tempStatusBar = 'Unknown key ' + str(ch)
			
		# end while

def start(args):
	browse(args)