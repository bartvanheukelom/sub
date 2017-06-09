#!/usr/bin/env python3

#
# Sub - utility commands for Subversion (SVN)
#
# https://github.com/bartvanheukelom/sub
#

import sys
import svnwrap

# submodules
import ilog
import icommit
import browse

if sys.version_info < (3,5):
	print('Python >= 3.5 required')
	exit(1)
	
def main():
	
	# check svn presence and version
	version = svnwrap.run('--version','--quiet', output=svnwrap.OUT_TXT).replace("\n","");
	if not version.startswith("1.9."):
		print("WARNING - svn version is " + version + ", but sub was tested with 1.9")
		
	# run the given command
	cmd(sys.argv[1] if len(sys.argv) >= 2 else "help", False, sys.argv[2:])
	
# command shorthands
def normalizeCmd(c):
	if c == "gd":
		return "gdiff"
	elif (c == "ici"
		or c == "ist" 
		or c == "istatus"):
		return "icommit"
	elif (c == "ls"):
		return "browse"
	return c
	
def cmd(c, help, args):
	
	# resolve command name
	try:
		fun = getattr(sys.modules[__name__], "cmd_" + normalizeCmd(c))
	except AttributeError:
		print("Unknown command: " + c + ". Run `sub help` for help.")
		exit(1)
	
	# invoke it
	fun(help, args)

# ------------ COMMANDS ------------ #
	
def cmd_help(help, args):
	if help:
		print("help:")
		print("usage:")
		print("  1. help")
		print("     Print the general help")
		print("  2. help COMMAND")
		print("     Print the help for the given COMMAND")
	else:
		if len(args) == 0:
			print("Sub - utility commands for Subversion")
			print("Commands: help, gdiff (gd), up, ilog, icommit (ici, istatus, ist), browse (ls)")
			print("Run `help COMMAND` to get help for one of these.")
		else:
			cmd(args[0], True, None)
			
def cmd_gdiff(help, args):
	if help:
		print("gdiff (gd): Graphical diff")
		print("usage:")
		print("  1. gdiff [OPTIONS...]")
		print("     Shorthand for `svn diff --diff-cmd meld --git $OPTIONS`")
	else:
		cmd = ['diff','--diff-cmd','meld','--git']
		cmd.extend(args)
		svnwrap.run(*cmd)
	
def cmd_up(help, args):
	if help:
		print("TODO HELP")
	else:
		cmd = ['up']
		cmd.extend(args)
		svnwrap.run(*cmd)
		
def cmd_ilog(help, args):
	if help:
		print("ilog: Interactive log")
	else:
		ilog.start(args)
		
def cmd_icommit(help, args):
	if help:
		print("icommit (ici): Interactive commit dialog")
	else:
		icommit.start(args)

def cmd_browse(help, args):
	if help:
		print("browse: Repo browser")
	else:
		browse.start(args)
		
# ---- END OF COMMANDS ---- #

main()
