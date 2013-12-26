import socket
import json
import base64
import time

class rpcClient:
	s = None
	size = 4096
	conf = {}

	def __init__(self, host, port, user = None, password = None, timeout = 5):
		self.conf['host'] = host
		self.conf['port'] = port
		if user is not None:
			self.conf['user'] = user
		if password is not None:
			self.conf['password'] = password
		if timeout is not None:
			self.conf['timeout'] = timeout

	def send(self, data):
		start = time.time()
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.s.settimeout(self.conf['timeout'])
			self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.s.connect((self.conf['host'], int(self.conf['port'])))
			#print '* Sending :', '\n', data
			self.s.sendall(data)
			result = ''.decode('iso-8859-1')
			while True:
				try:
					tmp = self.s.recv(self.size).decode('iso-8859-1')
				except socket.timeout as e:
					break
				self.s.settimeout(time.time() - start + 2)
				if not tmp: break
				result += tmp
				if len(tmp)%self.size != 0: break

			#print '* Received :', '\n', result
			self.s.close()
			return (None, result)

		except socket.error as e:
			return (True, str(e) + ' - Unable to send command : ' + str(data))
		except Exception as e:
			return (True, 'Exception : ' + str(e))

	def sendJson(self, params):
		method = params[0]
		params.remove(method)
		body = json.dumps({'method': method, 'params': params, 'id':1})

		(error, result) = self.send(body)

		try:
			result2 = json.loads(result)

			return (error, result2)
		except Exception as e:
			if error and 'Connection refused' in result:
				return (True, "Can't contact server - command " + method)

			return (True, result)


class rpcClientNamecoin(rpcClient):
	def __init__(self, host, port, user = None, password = None, timeout = 60):
		rpcClient.__init__(self, host, port, user, password, timeout)

	def sendJson(self, params):
		method = params[0]
		params.remove(method)
		body = json.dumps({'method': method, 'params': params, 'id':1})

		header  = 'POST / HTTP/1.1\n'
		header += 'User-Agent: bitcoin-json-rpc/0.3.50' + '\n'
		header += 'Host: 127.0.0.1\n'
		header += 'Content-Type: application/json' + '\n'
		header += 'Content-Length: ' + str(len(body)) + '\n'
		header += 'Accept: application/json' + '\n'
		if  self.conf['user'] is not None and self.conf['password'] is not None:
			header += 'Authorization: Basic ' + base64.b64encode(self.conf['user'] + ':' + self.conf['password'], None) + '\n'
		
		(error, data) = self.send(header + '\n' + body)

		resp = None
		found = False
		data = data.split('\r\n')
		for line in data:
			if line == '':
				found = True
			elif found:
				resp = line

		try:
			resp = json.loads(resp)
			if resp is None or 'error' in resp and resp['error'] is not None:
				return (True, None)
			else:
				return (None, resp['result'])
		except Exception as e:
			return (True, e)


if __name__=='__main__':
	r = rpcClientNamecoin('127.0.0.1', 8337, 'namecoin', 'test165893741', 30)
	print "Sending", ['getinfo']
	print r.sendJson(['getinfo']), '\n'
	print "Sending", ['name_show','d/ns']
	print r.sendJson(['name_show','d/ns']), '\n'

	r = rpcClient('127.0.0.1', 9000)
	print "Sending", 'test'
	print r.send('test'), '\n'

	r = rpcClient('127.0.0.1', 9000)
	print "Sending", ['main', 'status']
	print r.sendJson(['main', 'status']), '\n'
	print "Sending", ['status']
	print r.sendJson(['status']), '\n'

