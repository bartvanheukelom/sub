import curses
import svn.local
import sys

import util
import svnwrap
	
class revision:
	
	def __init__(self, ilog, data):
		self.ilog = ilog
		self.data = data
		self.selectedChange = None # if len(data.changelist) == 0 else data.changelist[0]
					
	def moveSelection(self, direction):
		self.selectedChange = util.navigateList(self.data.changelist, self.selectedChange, direction)
		self.ilog.renderAll()
		
	def launchGDiff(self):
		svnwrap.run('diff','--diff-cmd','meld','--git','--change',self.data.revision,'^' + self.selectedChange[1], wait=False)

class ilog:
	
	logHeight = 10

	def __init__(self, args):
		self.args = args
		curses.wrapper(self.loop)
		
	def moveSelection(self, direction):
		self.selectedEntry = util.navigateList(self.log, self.selectedEntry, direction)
		self.renderAll()
		
	def renderAll(self):
		self.win.clear()
		height, width = self.win.getmaxyx()
		

		# --- log --- #
		
		colRevision = 0
		colAuthor = 10
		colMessage = 26
		
		lst = self.log
		sel = self.selectedEntry
		curIndex = lst.index(sel)
		offset = curIndex - int(self.logHeight / 2)
		if offset < 0: offset = 0
		if offset > len(self.log) - self.logHeight: offset = len(lst) - self.logHeight
		
		for i in range(0, self.logHeight):
			
			io = i + offset
			if io < 0 or io >= len(self.log):
				continue
			entry = self.log[io]
			data = entry.data
			
			y = i
			
			attr = curses.A_REVERSE if entry == sel else 0
			
			#util.log(str(entry))
			
			self.win.addnstr(y, colRevision, str(data.revision),										colAuthor - colRevision - 1, attr)
			self.win.addnstr(y, colAuthor,   data.author,											   colMessage - colAuthor - 1,  attr)
			self.win.addnstr(y, colMessage,  '' if data.msg == None else data.msg.replace('\n', ' ↵ '), width - colMessage,		 attr)
			
		if sel != None:
			self.win.addnstr(0, width-5, '#' + str(curIndex), 4, curses.A_REVERSE)
		
		
		# --- changes --- #
		
		self.win.addnstr(self.logHeight, 0, '-------------------------------------', width)
		changesStart = self.logHeight + 1
		
		colType = 0
		colPath = 4
		
		lst = self.selectedEntry.data.changelist
		sel = self.selectedEntry.selectedChange
		curIndex = 0 if sel == None else lst.index(sel)
		changesHeight = height - changesStart - 1
		offset = curIndex - int(changesHeight / 2)
		if offset < 0: offset = 0
		if offset > len(lst) - changesHeight: offset = len(lst) - changesHeight
		
		for i in range(0, changesHeight):
			
			io = i + offset
			if io < 0 or io >= len(lst):
				continue
			change = lst[io]
			
			y = i + changesStart
			if y >= height-1:
				util.log('Too many changes')
				break
			
			attr = curses.A_REVERSE if change == sel else 0
			
			self.win.addnstr(y, colType, change[0], colPath - colType - 1, attr)
			self.win.addnstr(y, colPath, change[1], width - colPath,	   attr)
			
		if sel != None:
			self.win.addnstr(changesStart, width-5, '#' + str(curIndex), 4, curses.A_REVERSE)
		
		# --- legend --- #

		# width - 1 because writing the bottomrightmost character generates an error
		self.win.addnstr(height-1, 0, '[↑|↓] Select Revision    [O|L] Select Change    [G] GDiff    [Q] Quit', width-1, curses.A_REVERSE)

	def loop(self, win):
				
		self.win = win
		
		win.addstr('This will be log ' + str(self.args) + '\n')
		win.addstr('Loading...\n')
		win.refresh()
		
		# load the log
		try:
			limit = int(self.args[0])
		except IndexError:
			limit = 32
		svnClient = svn.local.LocalClient('.')
		self.log = list(map(lambda d: revision(self, d), svnClient.log_default(limit=limit, changelist=True)))
		
		if len(self.log) == 0:
			raise 'No log!'
		
		self.selectedEntry = self.log[0]
		
		self.renderAll()
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
			elif ch == curses.KEY_NPAGE:
				self.moveSelection(self.logHeight)
			elif ch == curses.KEY_PPAGE:
				self.moveSelection(-self.logHeight)
			elif ch == 108: # L
				self.selectedEntry.moveSelection(1)
			elif ch == 111:  # O
				self.selectedEntry.moveSelection(-1)
			elif ch == 103: # G
				self.selectedEntry.launchGDiff()

			else:
				util.log('Unknown key', ch)
			win.refresh()

def start(args):
	ilog(args)
