import curses
import sys

import svnwrap
import util
import hexes

statusCodes = {
	'modified': 'M',
	'unversioned': '?',
	'added': 'A'
}

class change:
	
	def __init__(self, icommit, data):
		self.icommit = icommit
		self.data = data
		self.marked = data['status'] != 'unversioned'

	def toggleMarked(self):
		self.marked = not self.marked

class icommit:
	
	STATE_NORMAL = 'normal'
	STATE_REVERT_CONFIRM = 'revertConfirm'
	STATE_PRE_COMMIT = 'preCommit'
	STATE_COMMIT_MESSAGE = 'commitMessage'
	
	state = STATE_NORMAL
	tempStatusBar = None
	commitMessage = ''
	
	def __init__(self, args):
		self.args = args
		curses.wrapper(self.loop)
		
	def moveSelection(self, direction):
		self.selectedChange = util.navigateList(self.changes, self.selectedChange, direction)
		
	def renderAll(self):
		self.win.clear()
		height, width = self.win.getmaxyx()		
		
		cursorX = width-1
		cursorY = height-1
		
		# --- change list --- #
		
		changesStart = 0
		
		colMark = 0
		colType = colMark+3
		colPath = colType+3
		
		lst = self.changes
		sel = self.selectedChange
		curIndex = 0 if sel == None else lst.index(sel)
		
		for i, change in enumerate(lst):
			y = i + changesStart
			if y >= height-1:
				self.win.addnstr(height-2, 0, '        TOO MANY CHANGES                               ', width - 1, curses.A_REVERSE)
				break
			
			attr = curses.A_REVERSE if change == sel else 0
			
			self.win.addnstr(y, colMark, '✓' if change.marked else '',       colType - colMark - 1, attr)
			self.win.addnstr(y, colType, statusCodes[change.data['status']], colPath - colType - 1, attr)
			self.win.addnstr(y, colPath, change.data['path'],                width - colPath,       attr)
			
		if sel != None:
			self.win.addnstr(changesStart, width-5, '#' + str(curIndex), 4, curses.A_REVERSE)

		# --- commit message --- #
		if self.state == self.STATE_PRE_COMMIT or self.state == self.STATE_COMMIT_MESSAGE:
			hexes.border(self.win, 0, 0, height-1, width, header='Commit Message', clear=True)			
			for l, line in enumerate(self.commitMessage.split('\n')):
				self.win.addnstr(1+l, 1, line, width-2)
				cursorY = 1+l
				cursorX = 1 + len(line)


		# --- status bar --- #

		if self.tempStatusBar != None:
			statusBar = self.tempStatusBar + ' (press any key to dismiss...)'
		elif self.state == self.STATE_REVERT_CONFIRM:
			statusBar = '[Y] Confirm revert    [Other] Cancel    [Q] Quit'
		elif self.state == self.STATE_PRE_COMMIT:
			statusBar = '[Y] Commit    [N] Not yet    [E] Edit message    [Q] Quit'
		elif self.state == self.STATE_COMMIT_MESSAGE:
			statusBar = '[Ctrl+D] Stop editing'
		else:
			statusBar = '[↑|↓] Select  [Space] Mark  [C]ommit...  [A]dd  [R]evert  [G]Diff  [Q]uit'
		
		# width - 1 because writing the bottomrightmost character generates an error
		hexes.fill_line(self.win, height-1, 0, width-1, attr=curses.A_REVERSE)
		self.win.addnstr(height-1, 0, statusBar, width-1, curses.A_REVERSE)
		
		
		self.win.move(cursorY, cursorX)
		self.win.refresh()
		
	def launchGDiff(self):
		svnwrap.run('diff','--diff-cmd','meld','--git',self.selectedChange.data['path'], wait=False)
		
	def add(self):
		svnwrap.run('add',self.selectedChange.data['path'])
		self.loadStatus()
		
	def revert(self):
		svnwrap.run('revert',self.selectedChange.data['path'], output=svnwrap.OUT_TXT)
		self.loadStatus()
	
	def commit(self):
		cmd = ['commit']
		for c in self.changes:
			if c.marked:
				cmd.append(c.data['path'])
		cmd.extend(['--message', self.commitMessage])
		svnwrap.run(*cmd, output=svnwrap.OUT_TXT)
	
	def loadStatus(self):
		self.changes = list(map(lambda c: change(self, c), svnwrap.status()))
		self.selectedChange = None
		
	def loop(self, win):
		self.win = win

		self.loadStatus()
		
		# input loop
		while (True):
			
			self.renderAll()
			
			ch = win.getch()
			try:
				char = chr(ch)
			except ValueError:
				char = None
			
			self.tempStatusBar = None
			
			typing = self.state == self.STATE_COMMIT_MESSAGE
			
			if ch == 113 and not typing: # Q
				break
			elif ch == curses.KEY_RESIZE:
				pass
			else:
				
				if self.state == self.STATE_REVERT_CONFIRM:
					self.state = self.STATE_NORMAL
					if ch == 121: # Y
						self.revert()
				
				elif self.state == self.STATE_PRE_COMMIT:
					if ch == 121: # Y
						self.commit()
						self.state = self.STATE_NORMAL
					if ch == 110: # N
						self.state = self.STATE_NORMAL
					if ch == 101: # E
						self.state = self.STATE_COMMIT_MESSAGE
					
				elif self.state == self.STATE_COMMIT_MESSAGE:
					if ch == 4: # Ctrl-D
						self.state = self.STATE_PRE_COMMIT
					elif ch == curses.KEY_BACKSPACE:
						self.commitMessage = self.commitMessage[:-1]
					else:
						self.commitMessage += chr(ch)
				# normal state	
				else:
					if ch == curses.KEY_DOWN:
						self.moveSelection(1)
					elif ch == curses.KEY_UP:
						self.moveSelection(-1)
					elif ch == curses.KEY_NPAGE:
						self.moveSelection(10)
					elif ch == curses.KEY_PPAGE:
						self.moveSelection(-10)
					elif ch == 103: # G
						self.launchGDiff()
					elif ch == 97: # A
						self.add()
					elif ch == 114: # R
						self.state = self.STATE_REVERT_CONFIRM
					elif ch == curses.KEY_F5:
						self.loadStatus()
					elif ch == 32: # space
						self.selectedChange.toggleMarked()
					elif char == 'c':
						self.state = self.STATE_COMMIT_MESSAGE
					else:
						self.tempStatusBar = 'Unknown key ' + str(ch)
			
		# end while

def start(args):
	icommit(args)