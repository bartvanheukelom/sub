import curses
import sys
import subprocess

import svnwrap
import util

statusCodes = {
	'modified': 'M',
	'unversioned': '?',
	'added': 'A'
}

class icommit:
	
	def __init__(self, args):
		self.args = args
		curses.wrapper(self.loop)
		
	def moveSelection(self, direction):
		self.selectedChange = util.navigateList(self.changes, self.selectedChange, direction)
		self.renderAll()
		
	def renderAll(self):
		self.win.clear()
		height, width = self.win.getmaxyx()		
		
		changesStart = 0
		
		colType = 0
		colPath = 4
		
		for i, change in enumerate(self.changes):
			y = i + changesStart
			if y >= height-1:
				util.log('Too many changes')
				break
			
			attr = curses.A_REVERSE if change == self.selectedChange else 0
			
			self.win.addnstr(y, colType, statusCodes[change['status']], colPath - colType - 1, attr)
			self.win.addnstr(y, colPath, change['path'],                width - colPath,       attr)

		self.win.addnstr(height-1, 0, '[↑|↓] Select Change    [A] Add    [G] GDiff    [Q] Quit', width, curses.A_REVERSE)
		
	def launchGDiff(self):
		proc = ["svn","diff","--diff-cmd","meld","--git",self.selectedChange['path']]
		subprocess.run(proc)
		
	def add(self):
		proc = ["svn","add",self.selectedChange['path']]
		subprocess.run(proc)
		self.loadStatus()
	
	def loadStatus(self):
		self.changes = svnwrap.status()
		self.selectedChange = None
		self.renderAll()
		
	def loop(self, win):
		self.win = win

		self.loadStatus()
		win.refresh()
		
		# input loop
		while (True):
			ch = win.getch()
			if ch == 113: # Q
				break
			elif ch == curses.KEY_DOWN:
				self.moveSelection(1)
			elif ch == curses.KEY_UP:
				self.moveSelection(-1)
			elif ch == 103: # G
				self.launchGDiff()
			elif ch == 97: # A
				self.add()

			else:
				util.log('Unknown key', ch)
			win.refresh()

def start(args):
	icommit(args)