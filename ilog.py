import curses
import svn.local
import sys

import util
import svnwrap
import iutil

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

		def render_revision(y, entry, is_sel):
			data = entry.data
			attr = curses.A_REVERSE if is_sel else 0
			self.win.addnstr(y, colRevision, str(data.revision), colAuthor - colRevision - 1, attr)
			self.win.addnstr(y, colAuthor,   data.author, colMessage - colAuthor - 1, attr)
			self.win.addnstr(y, colMessage,  '' if data.msg == None else data.msg.replace('\n', ' ↵ '), width - colMessage, attr)
		iutil.render_list(self.win, self.log, self.selectedEntry, 0, self.logHeight, width, render_revision)		
		
		# --- changes --- #
		
		self.win.addnstr(self.logHeight, 0, '-------------------------------------', width)

		colType = 0
		colPath = 4
		
		def render_change(y, change, is_sel):
			attr = curses.A_REVERSE if is_sel else 0
			self.win.addnstr(y, colType, change[0], colPath - colType - 1, attr)
			self.win.addnstr(y, colPath, change[1], width - colPath,	   attr)
		iutil.render_list(self.win,
			self.selectedEntry.data.changelist, self.selectedEntry.selectedChange,
			self.logHeight+1, height - self.logHeight - 2, width, render_change)

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
		try:
			filter = self.args[1]
		except IndexError:
			filter = '.'
		svnClient = svn.local.LocalClient(filter)
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
