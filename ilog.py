import curses
import svn.local
import svn.remote
import sys

import util
import svnwrap
import iutil
import hexes

class revision:
	
	def __init__(self, ilog, data):
		self.ilog = ilog
		self.data = data
		self.selectedChange = None
					
	def moveSelection(self, direction):
		self.selectedChange = util.navigateList(self.data.changelist, self.selectedChange, direction)
		
	def launchGDiff(self):
		svnwrap.run('diff','--diff-cmd','meld','--git','--change',self.data.revision,'^' + self.selectedChange[1], wait=False)

class ilog:

	def __init__(self, args):
		self.args = args
		self.markedRevisions = set()
		self.logHeight = 10
		self.filter = hexes.TextBox()
		
	def moveSelection(self, direction):
		self.selectedEntry = util.navigateList(self.filtered_log(), self.selectedEntry, direction)
		
	def renderAll(self):
		self.win.clear()
		height, width = self.win.getmaxyx()
		
		# --- log --- #
		
		colMark = 0
		colRevision = 2
		colAuthor = 10
		colMessage = 26

		filteredLog = self.filtered_log()
		if self.selectedEntry not in filteredLog:
			self.selectedEntry = filteredLog[0] if filteredLog else None
		def render_revision(y, entry, is_sel):
			data = entry.data
			attr = curses.A_REVERSE if is_sel else 0
			if is_sel:
				hexes.fill_line(self.win, y, 0, width, curses.A_REVERSE)
			self.win.addnstr(y, colMark, '✓' if data.revision in self.markedRevisions else '', colRevision - colMark, attr)
			self.win.addnstr(y, colRevision, str(data.revision), colAuthor - colRevision - 1, attr)
			self.win.addnstr(y, colAuthor,   data.author, colMessage - colAuthor - 1, attr)
			self.win.addnstr(y, colMessage,  '' if data.msg == None else data.msg.replace('\n', ' ↵ '), width - colMessage, attr)
		iutil.render_list(self.win, filteredLog, self.selectedEntry, 1, self.logHeight, width, render_revision)		
		
		# --- changes --- #
		
		if self.markedRevisions:
			sepStr = ','.join(str(r) for r in sorted(self.markedRevisions))
		else:
			sepStr = ' [I/K] Move separator'
			sepStr = '═' * (width - len(sepStr)) + sepStr
		self.win.addnstr(self.logHeight+1, 0, sepStr, width)

		colType = 0
		colPath = 4
		
		if self.selectedEntry:
			def render_change(y, change, is_sel):
				attr = curses.A_REVERSE if is_sel else 0
				self.win.addnstr(y, colType, change[0], colPath - colType - 1, attr)
				self.win.addnstr(y, colPath, change[1], width - colPath,	   attr)
			iutil.render_list(self.win,
				self.selectedEntry.data.changelist, self.selectedEntry.selectedChange,
				2+self.logHeight, height - self.logHeight - 3, width, render_change)

		# --- legend --- #

		# width - 1 because writing the bottomrightmost character generates an error
		if self.filter.focused:
			statusBar = 'Type to edit filter  [Enter] Return'
		else:
			statusBar = '[↑|↓] Select Revision  [O|L] Select Change  [Space] Mark Rev  [G] GDiff  [P] Limit ' + str(self.limit + 50) + '  [F]ilter  [Q] Quit'
		hexes.fill_line(self.win, height-1, 0, width-1, attr=curses.A_REVERSE)
		self.win.addnstr(height-1, 0, statusBar, width-1, curses.A_REVERSE)

		# --- filter --- #
		# last because of cursor
		filterLabel = '[F]ilter: '
		self.win.addstr(0, 0, filterLabel, curses.A_NORMAL if self.filter.focused else curses.A_DIM)
		self.filter.render(self.win, 0, len(filterLabel), width - len(filterLabel))

		if not self.filter.focused:
			self.win.move(height-1, width-1)

		self.win.refresh()

	def filtered_log(self):
		return [l for l in self.log if self.rev_in_filter(l)]

	def rev_in_filter(self, l):
		f = self.filter.text.lower()
		d = l.data
		if f in str(d.revision) or f in d.author.lower() or f in str(d.msg).lower(): return True
		for c in d.changelist:
			if f in c[1].lower(): return True
		return False

	def load(self):
		self.log = [revision(self, d) for d in self.svnClient.log_default(limit=self.limit, changelist=True)]
		if len(self.log) == 0:
			raise 'No log!'
		self.selectedEntry = self.log[0]

	def loop(self, win):
				
		self.win = win
		
		self.win.clear()
		util.log('This will be log ' + str(self.args) + '\n')
		self.win.addstr('This will be log ' + str(self.args) + '\n')
		self.win.addstr('Loading...\n')
		self.win.refresh()
		
		# load the log
		try:
			self.limit = int(self.args[1])
		except IndexError:
			self.limit = 50
		try:
			filter = self.args[0]
		except IndexError:
			filter = '.'
		self.svnClient = svn.remote.RemoteClient(filter) if filter.startswith('svn://') else svn.local.LocalClient(filter)

		self.load()
		
		# input loop
		while (True):

			self.renderAll()

			ch = win.getch()
			try:
				char = chr(ch)
			except ValueError:
				char = None
			
			if self.filter.focused:
				if self.filter.input(ch):
					self.filter.focused = False
			else:

				if char == 'q':
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
				elif ch == 112: # P
					self.limit += 50
					self.load()
				elif ch == 32: # space
					self.markedRevisions ^= {self.selectedEntry.data.revision}
				elif ch == 105: # I
					self.logHeight -= 1
				elif ch == 107: # K
					self.logHeight += 1
				elif char == 'f':
					self.filter.focused = True

				else:
					util.log('Unknown key', ch)

def start(args):
	i = ilog(args)
	curses.wrapper(i.loop)
