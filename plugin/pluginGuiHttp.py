from common import *
import plugin
#import DNS
#import json, base64, types, random, traceback

class pluginGuiHttp(plugin.PluginThread):
	name = 'http'
	options = {
		'start':	['Launch at startup', 1],
		#'host':		['Listen on ip', '127.0.0.1'],
		#'port':		['Listen on port', 53],
		#'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	depends = {'services': ['http']}
	#services = {'dns':{'filter':'.bit$','cache':True}}
	#namespaces = ['d']

	#def pStart(self):
	#	print "pstart"
