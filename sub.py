#!/usr/bin/env python3

#
# Sub - utility commands for Subversion (SVN)
#
# https://github.com/bartvanheukelom/sub
#

import sys
if __name__ == '__main__': 
	SCRIPT_PYVER_REQUIRED = 3,5
	if sys.version_info < SCRIPT_PYVER_REQUIRED:
		print(SCRIPT_FILENAME, 'requires Python >=', SCRIPT_PYVER_REQUIRED, file=sys.stderr)
		sys.exit(64)

import svnwrap

# submodules
import ilog
import icommit
import browse
	
def main(argv):
	
	# check svn presence and version
	version = svnwrap.run('--version','--quiet', output=svnwrap.OUT_TXT).replace("\n","");
	if not version.startswith("1.9."):
		print("WARNING - svn version is " + version + ", but sub was tested with 1.9")
		
	# run the given command
	cmd(resolve_aliases((argv[1:]+['help'])[0]))(argv[2:])
	
def cmd(c):
	try:
		return getattr(commands, c)
	except AttributeError:
		print("Unknown command: " + c + ". Run `sub help` for help.")
		exit(1)

aliases = {}
aliases_reverse = {}
def alias(*alts):
	def aliased(f):
		aliases_reverse[f.__name__] = alts
		for a in alts:
			aliases[a] = f.__name__
		return f
	return aliased

def resolve_aliases(c):
	while c in aliases:
		c = aliases[c]
	return c

shorthelps = {}
def shorthelp(s):
	def ss(f):
		shorthelps[f.__name__] = s
		return f
	return ss

def fullshorthelp(c):
	h = c
	if c in aliases_reverse:
		h += ' (' + ','.join(aliases_reverse[c]) + ')'
	h += ': ' + shorthelps[c]
	return h

class commands:

	def help_help():
		print("usage:")
		print("  1. help")
		print("     Print the general help")
		print("  2. help COMMAND")
		print("     Print the help for the given COMMAND")
	@shorthelp('Get some help')
	def help(args):
		if args:
			c = resolve_aliases(args[0])
			print(fullshorthelp(c))
			cmd('help_' + c)()
		else:
			print("Sub - utility commands for Subversion")
			print("Commands:")
			print('   ', 'COMMAND'.ljust(8), 'ALTS'.ljust(16), 'INFO')
			for c in shorthelps:
				alts = ','.join(aliases_reverse.get(c, []))
				print('   ', c.ljust(8), alts.ljust(16), shorthelps[c])
			print("Run `help COMMAND` to get help for one of these.")
				

	def help_gdiff():
		print("usage:")
		print("  1. gdiff [OPTIONS...]")
		print("     Shorthand for `svn diff --diff-cmd meld --git $OPTIONS`")
	@alias('gd','d')
	@shorthelp('Graphical diff')
	def gdiff(args):
		svnwrap.run(*(['diff','--diff-cmd','meld','--git']+args))
		

	def help_up():
		pass
	@alias('u')
	@shorthelp('Update')
	def up(args):
		svnwrap.run(*(['up']+args))
			

	def help_ilog():
		pass
	@alias('l')
	@shorthelp('Interactive log')
	def ilog(args):
		ilog.start(args)
			

	def help_istatus():
		pass
	@alias('s', 's', 'ici', 'icommit')
	@shorthelp('Interactive wc status screen, with commit, revert and update actions')
	def istatus(args):
		icommit.start(args)


	def help_browse():
		pass
	@alias('ls', 'b')
	@shorthelp('Repo browser')
	def browse(args):
		browse.start(args)
			

if __name__ == '__main__': main(sys.argv)
