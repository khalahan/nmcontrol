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
	handlers = []

	# process each sub dns plugin to see if one is interested by the request
	def _resolve(self, request, result):
		request = {
			'handler'   : request[0],
			'recType'   : request[1][0],
			'domain'    : request[1][1],
		}

		for handler in self.handlers:
			if request['handler'] not in handler.handle:
				continue

			if request['recType'] not in handler.supportedMethods:
				continue

			if 'dns' in handler.filters:
				if not re.search(handler.filters['dns'], request['domain']):
					continue

			if not handler._handle(request):
				continue

			handler._resolve(request['domain'], request['recType'], result)
			return result

		return False

	def _getRecordForRPC(self, request):
		result = dnsResult()
		self._resolve(request, result)
		return result.toJsonForRPC()
		
	def getIp4(self, request):
		return self._getRecordForRPC(request)

	def getIp6(self, request):
		return self._getRecordForRPC(request)

	def getOnion(self, request):
		return self._getRecordForRPC(request)

	def getI2p(self, request):
		return self._getRecordForRPC(request)

	def getFreenet(self, request):
		return self._getRecordForRPC(request)

	def getFingerprint(self, request):
		return self._getRecordForRPC(request)
