from common import *
import plugin
#import DNS
#import json, base64, types, random, traceback

class pluginGuiHttpConfig(plugin.PluginThread):
	name = 'guiHttpConfig'
	options = {
		'start':	['Launch at startup', 1],
	}
	depends = {'services': ['http']}

	def pLoadconfig(self):
		app['plugins']['guiHttp'].handlers.append(self)
	
	def handle(self, request):
		if request.path[0:7] == '/config':
			return True

		return False
	
	def do_GET(self, req):
		#print "GET:", req.headers.get('Host'), req.path

		req.send_response(200)
		req.send_header("Content-type", "text/html")
		req.end_headers()
		req.wfile.write("<html><head><title>Nmcontrol configuration</title></head>")
		req.wfile.write("<body><p>This is the configuration plugin.</p>")
		# If someone went to "http://something.somewhere.net/foo/bar/",
		# then req.path equals "/foo/bar/".
		req.wfile.write("<p>Domain is : %s</p>" % req.headers.get('Host'))
		req.wfile.write("<p>You accessed path: %s</p>" % req.path)
		req.wfile.write("</body></html>")

		return True

