from common import *
import plugin
#import DNS
#import json, base64, types, random, traceback
import re

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
	def _handle(self, request):
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

			return handler._resolve(request['domain'], request['recType'])

		return False

	def getIp4(self, request):
		return self._handle(request)

	def getIp6(self, request):
		return self._handle(request)

	def getOnion(self, request):
		return self._handle(request)

	def getI2p(self, request):
		return self._handle(request)

	def getFreenet(self, request):
		return self._handle(request)

	def getFingerprint(self, request):
		return self._handle(request)

