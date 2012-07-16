import plugin
import dnsServer
import DNS
import json, base64, types, traceback

class pluginNamespaceDomain(plugin.PluginThread):
	name = 'domain'
	options = {
		'start':	['Launch at startup', 1],
		#'host':		['Listen on ip', '127.0.0.1'],
		#'port':		['Listen on port', 53],
		#'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	namespaces = ['d']

	def pStart(self):
		self.servers = self.app['plugins']['dns'].conf['resolver'].split(',')

	def lookup(self, qdict) :
		domain = qdict["domain"]
		if domain.count(".") >= 2 :
			host = ".".join(domain.split(".")[-2:-1])
			subdomain = ".".join(domain.split(".")[:-2])
		else : 
			host = domain.split(".")[0]
			subdomain = ""
		#rawlist = json.dumps(rawjson)
		item = self.app['plugins']['data'].getData(['data', ['getData', 'd/'+host]])
		try:	
			item = json.loads(item)
		except:
			if self.app['debug']: traceback.print_exc()
			return
			
		if str(item[u"name"]) == "d/" +  host :
			try :
				value = json.loads(item[u"value"])
				if value.has_key(u"map") :
					if type(value[u"map"]) is types.DictType :
						hasdefault = False
						for key in value[u"map"].keys()[:] :
							if key == u"" :
								hasdefault = True
							if str(key) == subdomain :
								if type(value[u"map"][key]) == types.DictType :
									return dnslookup(value, key, qdict)
								return str(value[u"map"][u""])
							#else :
								#if type(value[u"map"][key]) == types.DictType :
									#return dnslookup(domain, qt)
								#return 1, str(value[u"map"][key])
						if hasdefault :
							if type(value[u"map"][u""]) == types.DictType :
								return self.dnslookup(value, u"", qdict)
							return str(value[u"map"][u""])
			except :	
				if self.app['debug']: traceback.print_exc()
				return
	def dnslookup(self, value, key, qdict) :
		if value[u"map"][key].has_key(u"ns") : 
			server = self.servers[random.randrange(0, len(self.servers)-1)]
			self.reqobj = DNS.Request(server=server)

			x = DnsClient.Request(server="8.8.8.8")
			if type(value[u"map"][key][u"ns"]) == types.UnicodeType :
				y = x.req(str(value[u"map"][key][u"ns"])).answers[0]["data"]
			else : 
				y = x.req(str(value[u"map"][key][u"ns"][0])).answers[0]["data"]
			ns = DNS.Request(server=y)
			return ns.req(name=qdict["domain"], qtype=qdict["qtype"]).answers[0]
	
		
	#srv = None
	#
	#def pStart(self):
	#	if self.srv is None:
	#		self.srv = dnsServer.DnsServer()
	#		self.srv.start(self.app)
	#	return True
	#
	#def pStop(self):
	#	if self.srv is not None:
	#		self.srv.stop()
	#	print "Plugin %s stopped" %(self.name)
	#	return True


