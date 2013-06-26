from common import *
import plugin
#import DNS
#import json, base64, types, random, traceback

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
		for handler in self.handlers:
			if handler._handle(request):
				return handler._process(request)

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

