from common import *
import plugin
import DNS
import dnsServer
import random, re

class serviceDNS(plugin.PluginThread):
	name = 'dns'
	options = {
		'start':	['Launch at startup', 1],
		'host':		['Listen on ip', '127.0.0.1'],
		'port':		['Listen on port', 53],
		'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	srv = None

	def pStart(self):
		self.servers = self.conf['resolver'].split(',')
		if self.srv is None:
			self.srv = dnsServer.DnsServer()
			self.srv.start()
		if app['debug']: print "Service %s started" %(self.name)
		return True
	
	def pStop(self):
		if self.srv is not None:
			self.srv.stop()
			self.srv = None
		if app['debug']: print "Service %s stopped" %(self.name)
		return True

	def lookup(self, qdict) :
		if app['debug']: print 'Lookup:', qdict
		for service, value in self.services.iteritems():
			if re.search(value['filter'], qdict["domain"]):
				return app['plugins'][service].lookup(qdict)

		return self._lookup(qdict)

	def _lookup(self, qdict, server = ''):
		if server == '':
			server = self.servers[random.randrange(0, len(self.servers)-1)]

		x = DNS.Request(server=server)
		return x.req(name=qdict["domain"], qtype=qdict["qtype"]).answers

