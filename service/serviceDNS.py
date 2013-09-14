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
		'disable_standard_lookups': ['Disable lookups for standard domains','0']
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
		#for service, value in self.services.iteritems():
		#	if re.search(value['filter'], qdict["domain"]):
		#		return app['plugins'][service].lookup(qdict)
		if qdict["domain"].endswith(".bit") or qdict["domain"].endswith(".tor"):
			return app['plugins']['domain'].lookup(qdict)
		if self.conf['disable_standard_lookups'] == '1':
			return []
		return self._lookup(qdict["domain"],qdict["qtype"])

	def _lookup(self, domain, qtype=1, server = ''):
		#make sure the server string is a string and not unicode, otherwise the DNS library fails to resolve it
		server = str(server)

		if server == '':
			server = self.servers[random.randrange(0, len(self.servers)-1)]

		if app['debug']: print "Fetching IP Address for: ", domain, "with NS Server:", server

		x = DNS.Request(server=server)
		result = x.req(name=domain, qtype=qtype).answers

		if app['debug']: print "* result: ", result

		return result

