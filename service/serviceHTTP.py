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
	srv = None

	def pStart(self):
		if self.srv is None:
			self.srv = BaseHTTPServer.HTTPServer((self.conf['host'], int(self.conf['port'])), MyHandler)
			self.srv.app = app
			self.srv.serve_forever()
		if app['debug']: print "Service %s started" %(self.name)
		return True
	
	def pStop(self):
		if self.srv is not None:
			self.srv.server_close()
			self.srv = None
		if app['debug']: print "Service %s stopped" %(self.name)
		return True

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_HEAD(s):
		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.end_headers()

	def do_GET(s):
		"""Respond to a GET request."""
		host = s.headers.get('Host');
		if host.endswith('.tor'):
			s.server.app['plugins']['tor'].httpHandle(s)
			return

		s.send_response(200)
		s.send_header("Content-type", "text/html")
		s.end_headers()
		s.wfile.write("<html><head><title>Title goes here.</title></head>")
		s.wfile.write("<body><p>This is a test.</p>")
		# If someone went to "http://something.somewhere.net/foo/bar/",
		# then s.path equals "/foo/bar/".
		s.wfile.write("<p>Domain is : %s</p>" % host)
		s.wfile.write("<p>You accessed path: %s</p>" % s.path)
		s.wfile.write("</body></html>")

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

