import sys

def navigateList(lst, cur, direction):
	if cur == None: return None if len(lst) == 0 else lst[0]
	curIndex = lst.index(cur)
	return lst[(curIndex + direction) % len(lst)]

def log(*str):
	print(*str, file=sys.stderr)
	sys.stderr.flush()
	