from common import *
import plugin
#import DNS
#import json, base64, types, random, traceback
import re, json
import random

class dnsResult(dict):

	def add(self, domain, recType, record):
		
		if type(record) == unicode or type(record) == str:
			record = [record]

		if not recType in self:
			self[recType] = []

		self[recType].extend(record)

	def add_raw(self, domain, recType, record):

		self[recType] = record

		#if type(record) == unicode or type(record) == str:
		#	record = [record]

		#print record

		#if not recType in self:
		#	self[recType] = []

		#self[recType].extend(dict(record))
		#print self

	def toJsonForRPC(self):

		result = []
		for key in self:
			result = self[key]
		
		return json.dumps(result)


class pluginDns(plugin.PluginThread):
	name = 'dns'
	options = {
		'start':	['Launch at startup', 1],
		'disable_ns_lookups':	['Disable remote lookups for NS records','0'],
		#'host':		['Listen on ip', '127.0.0.1'],
		#'port':		['Listen on port', 53],
		#'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	helps = {
		'getIp4':	[1, 1, '<domain>', 'Get a list of IPv4 for the domain'],
		'getIp6':	[1, 1, '<domain>', 'Get a list of IPv6 for the domain'],
		'getOnion':	[1, 1, '<domain>', 'Get the .onion for the domain'],
		'getI2p':	[1, 1, '<domain>', 'Get the i2p config for the domain'],
		'getFreenet':		[1, 1, '<domain>', 'Get the freenet config for the domain'],
		'getFingerprint':	[1, 1, '<domain>', 'Get the sha1 of the certificate for the domain (deprecated)'],
		'getTlsFingerprint': [1, 3, '<domain> <protocol> <port>', 'Get the TLS information for the domain'],
		'getNS':	[1, 1, '<domain>', 'Get a list of NS for the domain'],
	}
	handlers = []

	# process each sub dns plugin to see if one is interested by the request
	def _resolve(self, domain, recType, result):

		for handler in self.handlers:
			#if request['handler'] not in handler.handle:
			#	continue

			if recType not in handler.supportedMethods:
				continue

			if 'dns' in handler.filters:
				if not re.search(handler.filters['dns'], domain):
					continue

			if not handler._handle(domain, recType):
				continue

			handler._resolve(domain, recType, result)
			return result

		return False

	def _getRecordForRPC(self, domain, recType):
		result = dnsResult()
		self._resolve(domain, recType, result)
		return result.toJsonForRPC()

	def getIp4(self, domain):
		result = self._getRecordForRPC(domain, 'getIp4')
		# if we got an NS record because there is no IP we need to ask the NS server for the IP
		if self.conf['disable_ns_lookups'] != '1':
			if "ns" in result:
				result = '["'+self._getIPv4FromNS(domain)+'"]'

		return result

	def getIp6(self, domain):
		result = self._getRecordForRPC(domain, 'getIp6')
		# if we got an NS record because there is no IP we need to ask the NS server for the IP
		if self.conf['disable_ns_lookups'] != '1':
			if "ns" in result:
				result = '["'+self._getIPv6FromNS(domain)+'"]'

		return result

	def getOnion(self, domain):
		return self._getRecordForRPC(domain, 'getOnion')

	def getI2p(self, domain):
		return self._getRecordForRPC(domain, 'getI2p')

	def getFreenet(self, domain):
		return self._getRecordForRPC(domain, 'getFreenet')

	def getFingerprint(self, domain):
		return self._getRecordForRPC(domain, 'getFingerprint')

	def getTlsFingerprint(self, domain, protocol, port):
		#return tls data for the queried FQDN, or the first includeSubdomain tls record
		result = self._getTls(domain)

		try:	
			tls = json.loads(result)
		except:
			if app['debug']: traceback.print_exc()
			return

		try:
			answer = tls[protocol][port]
		except:
			try:
				answer = self._getSubDomainTlsFingerprint(domain, protocol, port)[protocol][port]
			except:
				return []

		result = dnsResult()
		result.add(domain, 'getTlsFingerprint' , answer)
		return result.toJsonForRPC()

	def getNS(self, domain):
		return self._getRecordForRPC(domain, 'getNS')

	def getTranslate(self, domain):
		return self._getRecordForRPC(domain, 'getTranslate')

	def _getTls(self, domain):
		return self._getRecordForRPC(domain, 'getTls')		

	def _getNSServer(self,domain):
		item = self.getNS(domain)

		try:	
			servers = json.loads(item)
		except:
			if app['debug']: traceback.print_exc()
			return

		server = servers[random.randrange(0, len(servers))]
		return server

	def _getIPv4FromNS(self,domain):
		#1 is the A record
		server = self._getNSServer(domain)
		
		translate = self.getTranslate(domain)
		
		if translate != '[]':
			try:	
				translate = json.loads(translate)
			except:
				if app['debug']: traceback.print_exc()
				return

			domain = translate[0].rstrip('.')

		return app['services']['dns']._lookup(domain, 1 , server)[0]['data']

	def _getIPv6FromNS(self,domain):
		#28 is the AAAA record
		server = self._getNSServer(domain)
		
		translate = self.getTranslate(domain)
		
		if translate != '[]':
			try:	
				translate = json.loads(translate)
			except:
				if app['debug']: traceback.print_exc()
				return

			domain = translate[0].rstrip('.')

		return app['services']['dns']._lookup(domain, 28 , server)[0]['data']

	def _getSubDomainTlsFingerprint(self,domain,protocol,port):
		#Get the first subdomain tls fingerprint that has the includeSubdomain flag turned on
		for i in xrange(0,domain.count('.')):

			sub_domain = domain.split(".",i)[i]
		
			result = self._getTls(sub_domain)

			try:	
				tls = json.loads(result)
			except:
				if app['debug']: traceback.print_exc()
				return

			try:
				if( tls[protocol][port][0][2] == 1):
					return tls
			except:
				continue
