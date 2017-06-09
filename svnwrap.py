import subprocess
import xml.etree.ElementTree as ET

import util

OUT_XML = 1
OUT_STD = 2
OUT_TXT = 3

status_codes = {
	'none': ' ',
	'modified': 'M',
	'unversioned': '?',
	'added': 'A',
	'missing': '!',
	'deleted': 'D',
	'replaced': 'R',
	'conflicted': 'C',
	'external': 'X',
	'ignored': 'I',
	'merged': 'G'
}

def info():
	output = run('info', output=OUT_XML)
	return output

def status():
	output = run('status', output=OUT_XML)
	ret = []
	for target in output.iter('target'):
		for entry in target.iter('entry'):
			ret.append({
				'path': entry.get('path'),
				'status': entry.find('wc-status').get('item')
			})
			
	return ret

def ls(url):
	output = run('ls', url, output=OUT_XML)
	ret = []
	for file in output.find('list').iter('entry'):
		util.log(ET.tostring(file))
		ret.append({
			'name': file.find('name').text,
			'kind': file.get('kind'),
			'revision': file.find('commit').get('revision'),
			'author': file.find('commit').find('author').text,
			'date': file.find('commit').find('date').text
			# TODO file size
		})
	util.log('asdasdasd', ret)
	return ret
	
def run(*args, output=OUT_STD, wait=True):
	
	if not wait and output != OUT_STD:
		raise 'Can\'t not wait AND get output'
	
	cmd = ['svn', '--non-interactive']
	if output == OUT_XML:
		cmd.append('--xml')
	cmd.extend(args)
	cmd = list(map(str, cmd))
	util.log("svnwrap.run: ", cmd)
	
	if wait:
			
		process = subprocess.run(cmd, stdout=None if output == OUT_STD else subprocess.PIPE)
		if output == OUT_STD:
			return
			
		outTxt = process.stdout.decode('utf8')
		if output == OUT_TXT:
			return outTxt
			
		return ET.fromstring(outTxt)
		
	else:
		
		subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		