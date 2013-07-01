from common import *
import plugin
import rpcClient
import socket, json, threading, StringIO, sys, time, traceback

class pluginRpc(plugin.PluginThread):
	name = 'rpc'
	options = {
		'start':	['Launch at startup', 1],
		'host':		['Listen on ip', '127.0.0.1', '<ip>'],
		'port':		['Listen on port', 9000, '<port>'],
	}

	def pStatus(self):
		if self.running:
			return "Plugin " + self.name + " running"

	def pStart(self):
		self.threads = []
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
		 	self.s.bind((self.conf['host'], int(self.conf['port'])))
			self.s.listen(1)
			while self.running:
				try:
					c = rpcClientThread(self.s.accept(), app)
					c.start()
					self.threads.append(c)
				except Exception as e:
					if app['debug']: print "except:", e
		except KeyboardInterrupt:
			pass
		except:
			print "nmc-manager: unable to listen on port"
			if app['debug']: traceback.print_exc()

		# close all threads
		if app['debug']: print "RPC stop listening"
		self.s.close()
		for c in self.threads:
			c.join()

	def pStop(self):
		if app['debug']: print "Plugin stop :", self.name
		self.pSend(['exit'])
		print "Plugin %s stopped" %(self.name)

	def pSend(self, args):
		if app['debug']: print "RPC - sending cmd :", args
		r = rpcClient.rpcClient(self.conf['host'], int(self.conf['port']))
		error, data = r.sendJson(args)
		return error, data


		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.connect((self.conf['host'], int(self.conf['port'])))
			s.sendall(json.dumps(args))
			data = s.recv(4096)
			s.close()
			if app['debug']: print 'RPC - received data : ', repr(data)
			data = json.loads(data)
			if app['debug'] and 'result' in data and 'prints' in data['result']:
				print data['result']['prints']

			if data['error'] is None:
				return data['result']['reply']
			else:
				return "ERROR: " + data['result']

		except Exception, e:
			print "ERROR: unable to send request. Is program started ?"
			print e
			s.close()
			return False


class rpcClientThread(threading.Thread):
	def __init__(self, (client, address), app):
		self.client = client
		self.client.settimeout(10)
		self.address = address
		self.size = 4096
		threading.Thread.__init__(self)

	def run(self):
		buff = ""
		start = time.time()
		while True:
			try:
				data = self.client.recv(self.size)
			except socket.timeout as e:
				break
			self.client.settimeout(time.time() - start + 1)
			if not data: break
			buff += data
			if len(data)%self.size != 0: break
		(error, result) = self.computeJsonData(buff)

		self.client.send('{"result":'+json.dumps(result)+',"error":'+json.dumps(error)+',"id":1}')
		self.client.close()

	def computeJsonData(self, data):
		if not data:
			return (True, 'no data')

		#print "computeJsonData:", data
		data = json.loads(data)
		
		if data['method'] == 'exit' or 'exit' in data['params']:
			return (True, 'exit')

		return self.computeData([data['method'], data['params']])

	def computeData(self, args):
		#if app['debug']: print "Received data :", args

		# check for default plugin
		if len(args[1]) == 0: args = ['main', [args[0]]]

		plugin = args[0]
		params = args[1]
		method = params.pop(0)
		#print "Plugin:", plugin
		#print "Method:", method
		#print "Params:", params

		if plugin not in app['plugins']:
			return (True, 'Plugin "' + plugin + '" not allowed')
		if not app['plugins'][plugin].running and params[0] != 'start':
			return (True, 'Plugin "' + plugin + '" not started')

		if method == 'start': method = 'start2'

		# reply before being blocked by non threaded start
		# TODO : recreate thread for the start command and delete when stop
		if not app['plugins'][plugin].running and method == 'start2':
			self.client.send('{"result":'+json.dumps({'reply':True, 'prints':'Restarting '+plugin+''})+',"error":'+json.dumps(None)+',"id":1}');

		# reply before closing connection
		if plugin == 'rpc' and method == 'restart':
			self.client.send('{"result":'+json.dumps({'reply':True, 'prints':'Restarting rpc'})+',"error":'+json.dumps(None)+',"id":1}');

		# can't call private/protected methods
		if method[0] == '_':
			if app['debug']: print "RPC - forbidden cmd :", args
			return (True, 'Method "' + params[0] + '" not allowed')

		# help asked on a method
		if 'help' in params:
			params.remove('help')
			params.insert(0, method)
			method = 'help'

		# help thrown due to incorrect use of method
		if method in app['plugins'][plugin].helps and len(params) not in range(app['plugins'][plugin].helps[method][0], app['plugins'][plugin].helps[method][1]+1):
			params.insert(0, method)
			method = 'help'

		if app['debug']: print "RPC - executing cmd :", plugin, method, params

		# capture stdout
		capture = StringIO.StringIO()
		#sys.stdout = capture

		try:
			methodRpc = getattr(app['plugins'][plugin], '_rpc')
			result = methodRpc(method, *params)
		except AttributeError, e:
			if app['debug']: traceback.print_exc()
			return (True, 'Method "' + method + '" not supported by plugin "' + plugin + '"')
		except Exception, e:
			if app['debug']: traceback.print_exc()
			return (True, 'Exception : ' + str(e))

		# restore stdout
		sys.stdout = sys.__stdout__
		prints = capture.getvalue()
		capture.close()

		#if result is None:
		#	result = 'No data'

		return (None, {'reply': result, 'prints': prints})


