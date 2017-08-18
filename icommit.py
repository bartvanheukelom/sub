import curses
import curses.ascii
import sys
import os
from os import path

import svnwrap
import util
import hexes
import iutil

class change:
	
	def __init__(self, icommit, path, isdir, status):
		self.icommit = icommit
		self.path = path
		self.isdir = isdir
		self.fullPath = ('/'.join(path) if path else '.') + ('/' if isdir else '')
		self.status = status

	def toggleMarked(self):
		if self.status == 'none': return
		self.icommit.markedChanges ^= {self.fullPath}

	def marked(self):
		return self.fullPath in self.icommit.markedChanges

	def lastDir(self):
		return self.path if self.isdir else self.path[:-1]

class icommit:
	
	STATE_NORMAL = 'normal'
	STATE_CONFIRM = 'confirm'
	STATE_PRE_COMMIT = 'preCommit'
	STATE_COMMIT_MESSAGE = 'commitMessage'
	
	state = STATE_NORMAL
	tempStatusBar = None
	tempMessage = None
	confirmQuestion = None
	confirmAction = None
	commitMessage = hexes.TextArea()
	
	def __init__(self, args):
		self.args = args
		self.path = os.getcwd()
		self.changes = []
		self.selectedChange = None
		self.markedChanges = set()
		self.info = None
		self.onlyMarked = False
		while True:
			intermezzo = curses.wrapper(self.loop)
			if not intermezzo: break
			intermezzo()
			print('Press enter to return to main interface...')
			input()
		
	def moveSelection(self, direction):
		self.selectedChange = util.navigateList(self.visibleChanges(), self.selectedChange, direction)
		
	def render(self):
		self.win.clear()
		height, width = self.win.getmaxyx()		
		
		cursorX = width-1
		cursorY = height-1
		
		hexes.fill_line(self.win, 0, 0, width, curses.A_REVERSE)
		self.win.addnstr(0, 0, self.path, width, curses.A_REVERSE)
		if self.info:
			info = self.info.find('entry')
			root = info.find('repository').find('root').text
			relative = info.find('relative-url').text
			rev = info.find('commit').get('revision')
			hexes.fill_line(self.win, 1, 0, width, curses.A_REVERSE)
			self.win.addnstr(1, 0, root + '/' + '/'.join(relative.split('/')[1:]) + ' @ ' + rev, width, curses.A_REVERSE)
		

		# --- change list --- #
		
		colMark = 0
		colType = colMark+3
		colPath = colType+3
		

		changes = self.visibleChanges()

		def render_change(y, change, is_sel):
			attr = curses.A_DIM if self.state != self.STATE_NORMAL or self.tempMessage else (curses.A_REVERSE if is_sel else 0)
			if is_sel:
				hexes.fill_line(self.win, y, 0, width, attr)

			p = change.path;
			# dimPart = ('/'.join(p[:-1]) + '/') if len(p) > 1 else ''
			dimPart = ''.rjust(len(p)*4)
			visPart = p[-1] if p else '.'
			if change.isdir: visPart += '/'

			colWidth = width - colPath
			dimWidth = min(colWidth, len(dimPart))
			visWidth = colWidth - dimWidth
			
			self.win.addnstr(y, colMark, '✓' if change.marked() else '', colType - colMark, attr)
			self.win.addnstr(y, colType, svnwrap.status_codes.get(change.status, '#'), colPath - colType - 1, attr)
			self.win.addnstr(y, colPath, dimPart, dimWidth, attr | curses.A_DIM)
			self.win.addnstr(y, colPath+dimWidth, visPart, visWidth, attr)
		iutil.render_list(self.win, changes, self.selectedChange, 2, height-3, width, render_change)

		# --- status bar --- #

		if self.tempStatusBar != None:
			statusBar = self.tempStatusBar + ' (press any key to dismiss...)'
		elif self.state == self.STATE_CONFIRM:
			statusBar = '[Y]es  [N]o  [Q]uit  '
		elif self.state == self.STATE_PRE_COMMIT:
			statusBar = '[Y] Commit    [N] Not yet    [E] Edit message    [Q] Quit'
		elif self.state == self.STATE_COMMIT_MESSAGE:
			statusBar = '[Ctrl+D] Stop editing'
		else:
			statusBar = '[↑|↓] Select  [C]ommit...  [F5] Refresh  [U]pdate  '
			if self.selectedChange:
				statusBar += '[Space] Unmark  ' if self.selectedChange.marked() else '[Space] Mark  '
				if self.selectedChange.status == 'unversioned': statusBar += '[A]dd  '
				if self.selectedChange.status != 'unversioned': statusBar += '[R]evert  '
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
			hexes.border(self.win, top, left, 4, w+2, 'Confirm', clear=True)
			self.win.addnstr(top+1, 1+left, self.confirmQuestion, w)
			buttons = '[Y]es   [N]o'
			self.win.addnstr(top+2, 1+center-int(len(buttons)/2), buttons, w, curses.A_REVERSE)
		
		# --- commit message --- #
		if self.state == self.STATE_PRE_COMMIT or self.state == self.STATE_COMMIT_MESSAGE:
			padx = 6
			pady = 4
			padx2 = 2*padx
			pady2 = 2*pady
			hexes.border(self.win, pady, padx, height-pady2, width-padx2, header='Commit Message', clear=True)			
			self.commitMessage.render(self.win, pady+1, padx+1, width-padx2-2, height-pady2-2, self.state == self.STATE_COMMIT_MESSAGE)

		if self.tempMessage != None:
			pad = 5
			top = int(height/2) - 2
			w = min(len(self.tempMessage), width-2-(2*pad))
			center = int(width/2)
			left = center - int(w/2)
			hexes.border(self.win, top, left, 3, w+2, 'Please wait...', clear=True)
			self.win.addnstr(top+1, 1+left, self.tempMessage, w)

		if self.state != self.STATE_COMMIT_MESSAGE:
			self.win.move(cursorY, cursorX)

		self.win.refresh()

	def launchGDiff(self):
		svnwrap.run('diff','--diff-cmd','meld','--git',self.selectedChange.fullPath, wait=False)
		
	def add(self):
		svnwrap.run('add',self.selectedChange.fullPath)
		self.loadStatus()
		
	def revert(self):
		cmd = ['revert'] + \
		      [c.fullPath for c in self.changes if c.marked()] + \
		      ['--depth', 'files']
		print('Reverting...')
		svnwrap.run(*cmd)
	
	def commit(self):
		cmd = ['commit']
		for c in self.changes:
			if c.marked():
				cmd.append(c.fullPath)
		cmd.extend([
			'--depth', 'files',
			'--message', self.commitMessage.get_text()
		])
		print('Committing...')
		svnwrap.run(*cmd)

	def visibleChanges(self):
		return [c for c in self.changes if not self.onlyMarked or c.marked()]
	
	def loadStatus(self):

		self.tempMessage = 'Loading status'
		self.render()

		self.info = svnwrap.info()
		# TODO update instead of replace
		self.changes = []
		for s in svnwrap.status():
			isdir = path.isdir(s['path'])
			pp = s['path'].split('/')
			if pp == ['.']: pp = []			
			c = change(self, pp, isdir, s['status'])
			util.log(repr(pp))

			ld = c.lastDir()

			if not pp: follows = True
			elif not self.changes: follows = False
			elif ld == self.changes[-1].lastDir(): follows = True
			elif isdir and ld[0:-1] == self.changes[-1].lastDir(): follows = True
			else: follows = False

			if not follows:
				
				prevDir = [] if not self.changes else self.changes[-1].lastDir()
				common = []
				for i in range(0, min(len(prevDir), len(c.lastDir()))):
					if prevDir[i] != ld[i]:
						break
					common.append(prevDir[i])

				for i in range(len(common)+1, len(ld)+1):
					self.changes.append(change(self, ld[0:i], True, 'none'))
			self.changes.append(c)
		self.selectedChange = None

		self.tempMessage = None

	def confirm(self, question, action):
		self.state = self.STATE_CONFIRM
		self.confirmQuestion = question
		self.confirmAction = action
		
	def loop(self, win):
		self.win = win

		self.render()
		self.loadStatus()
		
		# input loop
		while (True):
			
			self.render()
			
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
					
					intermezzo = None
					if char == 'y':
						intermezzo = self.confirmAction()

					if char in 'yn':
						self.state = self.STATE_NORMAL
						self.confirmQuestion = None
						self.confirmAction = None

					if intermezzo: return intermezzo
				
				elif self.state == self.STATE_PRE_COMMIT:
					if char == 'y':
						self.state = self.STATE_NORMAL
						return self.commit
					if char == 'n':
						self.state = self.STATE_NORMAL
					if char == 'e':
						self.state = self.STATE_COMMIT_MESSAGE
					
				elif self.state == self.STATE_COMMIT_MESSAGE:
					if ch == curses.ascii.EOT: # Ctrl-D
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
					elif char == 'g':
						self.launchGDiff()
					elif char == 'a':
						self.add()
					elif char == 'r':
						self.confirm("Revert marked changes?", lambda: lambda: self.revert())
					elif ch == curses.KEY_F5:
						self.loadStatus()
					elif ch == curses.KEY_F4:
						sys.exit(200) # TODO via return
					elif char == ' ':
						self.selectedChange.toggleMarked()
						if self.onlyMarked:
							vc = self.visibleChanges()
							if not self.selectedChange in vc:
								self.selectedChange = vc[0] if vc else None
					elif char == 'c':
						self.state = self.STATE_COMMIT_MESSAGE
					elif char == 'u':
						def up():
							print('Updating...')
							svnwrap.run('update')
						self.confirm('Are you sure you want to update?', lambda: up)
					elif char == 'x':
						self.onlyMarked = not self.onlyMarked
						vc = self.visibleChanges()
						if not self.selectedChange in vc:
							self.selectedChange = vc[0] if vc else None
					else:
						self.tempStatusBar = 'Unknown key ' + str(ch) + ' (' + char + ')'
			
		# end while

def start(args):
	icommit(args)