import curses
import sys

import svnwrap
import util
import hexes
import iutil

class change:
	
	def __init__(self, icommit, data):
		self.icommit = icommit
		self.data = data
		self.marked = False #data['status'] != 'unversioned'

	def toggleMarked(self):
		self.marked = not self.marked

class icommit:
	
	STATE_NORMAL = 'normal'
	STATE_CONFIRM = 'confirm'
	STATE_PRE_COMMIT = 'preCommit'
	STATE_COMMIT_MESSAGE = 'commitMessage'
	
	state = STATE_NORMAL
	tempStatusBar = None
	confirmQuestion = None
	confirmAction = None
	commitMessage = hexes.TextArea()
	
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
		
		colMark = 0
		colType = colMark+3
		colPath = colType+3
		
		def render_change(y, change, is_sel):
			attr = curses.A_REVERSE if is_sel else 0
			if is_sel:
				hexes.fill_line(self.win, y, 0, width, curses.A_REVERSE)
			
			self.win.addnstr(y, colMark, '✓' if change.marked else '', colType - colMark, attr)
			self.win.addnstr(y, colType, svnwrap.status_codes.get(change.data['status'], '#'), colPath - colType - 1, attr)
			self.win.addnstr(y, colPath, change.data['path'], width - colPath, attr)
		iutil.render_list(self.win, self.changes, self.selectedChange, 0, height-1, width, render_change)

		# --- status bar --- #

		if self.tempStatusBar != None:
			statusBar = self.tempStatusBar + ' (press any key to dismiss...)'
		elif self.state == self.STATE_CONFIRM:
			statusBar = '[Q]uit'
		elif self.state == self.STATE_PRE_COMMIT:
			statusBar = '[Y] Commit    [N] Not yet    [E] Edit message    [Q] Quit'
		elif self.state == self.STATE_COMMIT_MESSAGE:
			statusBar = '[Ctrl+D] Stop editing'
		else:
			statusBar = '[↑|↓] Select  [Space] Mark  [C]ommit...  '
			if self.selectedChange:
				if self.selectedChange.data['status'] == 'unversioned': statusBar += '[A]dd  '
				if self.selectedChange.data['status'] != 'unversioned': statusBar += '[R]evert  '
				statusBar += '[G]Diff  '
			statusBar += '[Q]uit'
		
		# width - 1 because writing the bottomrightmost character generates an error
		hexes.fill_line(self.win, height-1, 0, width-1, attr=curses.A_REVERSE)
		self.win.addnstr(height-1, 0, statusBar, width-1, curses.A_REVERSE)

		# --- confirm dialog --- #
		if self.state == self.STATE_CONFIRM:
			pad = 5
			top = int(height/2) - 2
			w = min(len(self.confirmQuestion), width-2-(2*pad))
			center = int(width/2)
			left = center - int(w/2)
			hexes.border(self.win, top, left, 4, w+2, 'Revert', clear=True)
			self.win.addnstr(top+1, 1+left, self.confirmQuestion, w)
			buttons = '[Y]es   [N]o'
			self.win.addnstr(top+2, 1+center-int(len(buttons)/2), buttons, w, curses.A_REVERSE)
		
		# --- commit message --- #
		if self.state == self.STATE_PRE_COMMIT or self.state == self.STATE_COMMIT_MESSAGE:
			hexes.border(self.win, 0, 0, height-1, width, header='Commit Message', clear=True)			
			self.commitMessage.render(self.win, 1, 1, width-2, height-3)

		if self.state != self.STATE_COMMIT_MESSAGE:
			self.win.move(cursorY, cursorX)

		self.win.refresh()

	def launchGDiff(self):
		svnwrap.run('diff','--diff-cmd','meld','--git',self.selectedChange.data['path'], wait=False)
		
	def add(self):
		svnwrap.run('add',self.selectedChange.data['path'])
		self.loadStatus()
		
	def revert(self, path):
		svnwrap.run('revert', path, output=svnwrap.OUT_TXT)
		self.loadStatus()
	
	def commit(self):
		cmd = ['commit']
		for c in self.changes:
			if c.marked:
				cmd.append(c.data['path'])
		cmd.extend(['--message', self.commitMessage.get_text()])
		svnwrap.run(*cmd, output=svnwrap.OUT_TXT)
		#util.log('COMMIT NOT', cmd)
		self.loadStatus()
	
	def loadStatus(self):
		# TODO update instead of replace (preserve marked)
		self.changes = list(map(lambda c: change(self, c), svnwrap.status()))
		self.selectedChange = None

	def confirm(self, question, action):
		self.state = self.STATE_CONFIRM
		self.confirmQuestion = question
		self.confirmAction = action
		
	def loop(self, win):
		self.win = win

		self.loadStatus()
		
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
			
			typing = self.state == self.STATE_COMMIT_MESSAGE
			
			if ch == 113 and not typing: # Q
				break
			elif ch == curses.KEY_RESIZE:
				pass
			else:
				
				if self.state == self.STATE_CONFIRM:
					
					if ch == 121: # Y
						self.confirmAction()

					if ch == 121 or ch == 110: # Y or N
						self.state = self.STATE_NORMAL
						self.confirmQuestion = None
						self.confirmAction = None
				
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
					else:
						self.commitMessage.input(ch)
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
						revertFile = self.selectedChange.data['path']
						self.confirm("Revert '" + revertFile + "'?", lambda: self.revert(revertFile))
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