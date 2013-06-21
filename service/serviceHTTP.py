from common import *
import plugin, time, BaseHTTPServer

class serviceHTTP(plugin.PluginThread):
#class pluginServiceHTTP(plugin.PluginThread):
	name = 'http'
	options = {
		'start':	['Launch at startup', 1],
		'host':		['Listen on ip', '127.0.0.2'],
		'port':		['Listen on port', 80],
	}
	handlers = []
	srv = None

	def pStart(self):
		if self.srv is None:
			try:
				self.srv = BaseHTTPServer.HTTPServer((self.conf['host'], int(self.conf['port'])), MyHandler)
				self.srv.app = app
				self.srv.serve_forever()
			except Exception as e:
				print "ERROR: Unable to start HTTP server (%s)" % e
		if app['debug']: print "Service %s started" %(self.name)
		return True
	
	def pStop(self):
		if self.srv is not None:
			self.srv.server_close()
			self.srv = None
		if app['debug']: print "Service %s stopped" %(self.name)
		return True

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_HEAD(req):
		req.send_response(200)
		req.send_header("Content-type", "text/html")
		req.end_headers()

	def do_GET(req):
		self = req.server.app['services']['http']

		isHandled = False
		for handler in self.handlers:
			httpHandler = handler.handle(req)
			if httpHandler is not False:
				isHandled = httpHandler.do_GET(req)
				if isHandled:
					return

		MyHandler.default_GET(req)
	
	def default_GET(req):
		"""Respond to a GET request."""
		#if req.headers.get('Host').endswith('.tor'):
		#	req.server.app['plugins']['tor'].httpHandle(s)
		#	return

		req.send_response(200)
		req.send_header("Content-type", "text/html")
		req.end_headers()
		req.wfile.write("<html><head><title>Nmcontrol</title></head>")
		req.wfile.write("<body><p>This is the default page of nmcontrol.</p>")
		# If someone went to "http://something.somewhere.net/foo/bar/",
		# then req.path equals "/foo/bar/".
		req.wfile.write("<p>Domain is : %s</p>" % req.headers.get('Host'))
		req.wfile.write("<p>You accessed path: %s</p>" % req.path)
		req.wfile.write("</body></html>")



if __name__ == '__main__':
	server_class = BaseHTTPServer.HTTPServer
	httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
	print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

