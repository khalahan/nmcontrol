from common import *
import os, json

class backendData():
	def __init__(self, filename):
		self.datafile = filename
		
	def getAllNames(self):
		if not os.path.exists(self.datafile):
			return True, 'Config file "' + self.datafile + '" doesn\'t exist.'

		data = open(app['path']['app'] + self.datafile).read()
		try:
			data = json.loads(data)
		except:
			return True, 'Data not in json in "' + self.datafile + '".'

		datas = {}
		for name in data:
			datas[name['name']] = name

		return None, datas

	def getName(self, name):
		return False

