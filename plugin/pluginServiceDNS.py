import plugin
import dnsServer

class pluginServiceDNS(plugin.PluginThread):
	name = 'dns'
	options = {
		'start':	['Launch at startup', 1],
		'host':		['Listen on ip', '127.0.0.1'],
		'port':		['Listen on port', 53],
		'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	srv = None

	def pStart(self):
		if self.srv is None:
			self.srv = dnsServer.DnsServer(self.app)
			self.srv.start()
		if self.app['debug']: print "Plugin %s started" %(self.name)
		return True
	
	def pStop(self):
		if self.srv is not None:
			self.srv.stop()
			self.srv = None
		if self.app['debug']: print "Plugin %s stopped" %(self.name)
		return True

