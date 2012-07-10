import json, StringIO, os, sys, time
import plugin
import rpcClient
import platformDep
import backendDataFile
import backendDataNamecoin

class pluginData(plugin.PluginThread):
	name = 'data'
	#depends = ['datanamecoin']
	options = [
		{'start':			['launch at startup', 1]},
		{'import.mode':		['Import data at launch', 'none', '<none|all>']},
		{'import.from':		['Import data from', 'namecoin', '<namecoin|file>']},
		{'import.file':		['Import data from file ', 'data' + os.sep + 'namecoin.dat']},
		{'import.namecoin':	['Path of namecoin.conf', platformDep.getNamecoinDir() + os.sep + 'namecoin.conf']},

		{'update.mode':		['Update mode', 'ondemand', '<none|all|ondemand>']},
		{'update.from':		['Update data from', 'namecoin', '<namecoin|url|file>']},
		{'update.freq':		['Update data if older than', '30m', '<number>[h|m|s]']},
		{'update.file':		['Update data from file ', 'data' + os.sep + 'namecoin.dat']},
		{'update.namecoin':	['Path of namecoin.conf', platformDep.getNamecoinDir() + os.sep + 'namecoin.conf']},

		{'export.mode':		['Export mode', 'none', '<none|all>']},
		{'export.to':		['Export data to', 'file']},
		{'export.freq':		['Export data frequency', '1h', '<number>[h|m|s]']},
		{'export.file':		['Export data to file ', 'data' + os.sep + 'namecoin.dat']},
	]
	helps = {
		'getData':	[1, 1, '<name>', 'Get raw data of a name'],
		'getValue':	[1, 1, '<name>', 'Get raw value of a name'],
	}

	data = {}
	update = None
	export = None

	def pLoadconfig(self):
		for key, value in self.conf.items():
			if '.freq' in key:
				if value[-1] == 's':
					self.conf[key] = int(value[0:-1])
				elif value[-1] == 'm':
					self.conf[key] = int(value[0:-1]) * 60
				elif value[-1] == 'h':
					self.conf[key] = int(value[0:-1]) * 60 * 60
				else:
					self.conf[key] = int(value)

	def pStatus(self):
		if self.running:
			return "Plugin " + self.name + " running (" + str(len(self.data)) + " names)"

	def pStart(self):
		# load import backend
		if self.conf['import.mode'] == 'all':
			if self.app['debug']: print "Plugin Data : loading...",
			sys.stdout.flush()
			exec('backend = backendData' + self.conf['import.from'].capitalize() + '.backendData');
			backend = backend(self.app, self.conf['import.' + self.conf['import.from']])
			error, data = backend.getAllNames()
			if error is None:
				self.data = data
			# set expire time if not set
			for name in self.data:
				if 'expires_at' not in self.data[name]:
					self.data[name]['expires_at'] = int(time.time() + self.conf['update.freq'])
			if self.app['debug']: print len(self.data), "names loaded"

		# load update backend
		if self.conf['update.mode'] != 'none':
			exec('backend = backendData' + self.conf['update.from'].capitalize() + '.backendData');
			self.update = backend(self.app, self.conf['update.' + self.conf['update.from']])

		# load export backend
		if self.conf['export.mode'] != 'none':
			exec('backend = backendData' + self.conf['export.to'].capitalize() + '.backendData');
			self.export = backend(self.app, self.conf['export.' + self.conf['export.to']])

	def getData(self, cmd):
		if cmd[1][1] not in self.data or self.data[cmd[1][1]]['expires_at'] < time.time():
			error, data = self.update.getName(cmd[1][1])
			if error is None:
				data['expires_at'] = int(time.time() + self.conf['update.freq'])
				self.data[cmd[1][1]] = data
		
		if cmd[1][1] in self.data:
			return json.dumps(self.data[cmd[1][1]])
		else:
			return False
	
	def getValue(self, cmd):
		data = self.getData(cmd)

		if not data:
			return False

		data = json.loads(data)
		if 'value' in data:
			return data['value']

		return False

