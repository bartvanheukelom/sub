import subprocess
import xml.etree.ElementTree as ET

import util

def status():
	proc = ['svn', 'status', '--xml']
	result = subprocess.run(proc, stdout=subprocess.PIPE)
	xml = result.stdout.decode('utf8')
	output = ET.fromstring(xml)
	
	ret = []
	for target in output.iter('target'):
		for entry in target.iter('entry'):
			ret.append({
				'path': entry.get('path'),
				'status': entry.find('wc-status').get('item')
			})
			
	return ret
	