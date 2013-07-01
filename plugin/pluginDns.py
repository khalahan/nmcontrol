from common import *
import plugin
#import DNS
#import json, base64, types, random, traceback
import re, json


class dnsResult(dict):

	def add(self, domain, recType, record):
		
		if type(record) == unicode or type(record) == str:
			record = [record]

		if not recType in self:
			self[recType] = []

		self[recType].extend(record)

	def toJsonForRPC(self):

		result = []
		for key in self:
			for value in self[key]:
				result.append(value)

		return json.dumps(result)


class pluginDns(plugin.PluginThread):
	name = 'dns'
	options = {
		'start':	['Launch at startup', 1],
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
		'getFingerprint':	[1, 1, '<domain>', 'Get the sha1 of the certificate for the domain'],
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
		return self._getRecordForRPC(domain, 'getIp4')

	def getIp6(self, domain):
		return self._getRecordForRPC(domain, 'getIp6')

	def getOnion(self, domain):
		return self._getRecordForRPC(domain, 'getOnion')

	def getI2p(self, domain):
		return self._getRecordForRPC(domain, 'getI2p')

	def getFreenet(self, domain):
		return self._getRecordForRPC(domain, 'getFreenet')

	def getFingerprint(self, domain):
		return self._getRecordForRPC(domain, 'getFingerprint')
