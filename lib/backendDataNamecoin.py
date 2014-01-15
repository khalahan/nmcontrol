from common import *
import rpcClient
import ConfigParser, StringIO

class backendData():
	def __init__(self, conf):
		self.conf = conf

	rpc = None

	def _loadRPCConfig(self):
		conf = ConfigParser.SafeConfigParser()
		ini_str = '[r]\n' + open(self.conf).read()
		ini_fp = StringIO.StringIO(ini_str)
		conf.readfp(ini_fp)

		host = '127.0.0.1'
		port = 8336
		user = ''
		password = ''

		if conf.has_option('r', 'rpcconnect'):
			host = conf.get('r', 'rpcconnect')
		if conf.has_option('r', 'rpcport'):
			port = conf.get('r', 'rpcport')
		if conf.has_option('r', 'rpcuser'):
			user = conf.get('r', 'rpcuser')
		if conf.has_option('r', 'rpcpassword'):
			password = conf.get('r', 'rpcpassword')
		
		self.rpc = rpcClient.rpcClientNamecoin(host, port, user, password)

	def getAllNames(self):
		datas = {}
		error, data = self._rpcSend(["name_filter", app['plugins']['data'].conf['name_filter']])
		for name in data:
			datas[name['name']] = name
		return error, datas

	def getName(self, name):
		return self._rpcSend(["name_show", name])
	
	def _rpcSend(self, rpcCmd):
		if app['debug']: print "BackendDataNamecoin:", rpcCmd
		if self.rpc is None:
			self._loadRPCConfig()
		return self.rpc.sendJson(rpcCmd)
	
