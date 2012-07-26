from common import *
import plugin
import DNS
import json, base64, types, random, traceback

class pluginNamespaceDomain(plugin.PluginThread):
	name = 'domain'
	options = {
		'start':	['Launch at startup', 1],
		#'host':		['Listen on ip', '127.0.0.1'],
		#'port':		['Listen on port', 53],
		#'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	depends = {'services': ['dns']}
	services = {'dns':{'filter':'.bit$','cache':True}}
	namespaces = ['d']

	def domainToNamespace(self, domain):
		if domain.count(".") >= 2 :
			host = ".".join(domain.split(".")[-2:-1])
			subdomain = ".".join(domain.split(".")[:-2])
		else : 
			host = domain.split(".")[0]
			subdomain = ""
		return 'd/'+host, host, subdomain
	
	def namespaceToDomain(self, name):
		pass

	def lookup(self, qdict) :
		#dns = app['services']['dns'].lookup()
		# 
		name, host, subdomain = self.domainToNamespace(qdict["domain"])
		item = app['plugins']['data'].getData(['data', ['getData', name]])
		#rawlist = json.dumps(rawjson)
		try:	
			item = json.loads(item)
		except:
			if app['debug']: traceback.print_exc()
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
									#return dnslookup(value, key, qdict)
									if value[u"map"][key].has_key(u"ns") :
										server = value[u"map"][key][u"ns"][random.randrange(0, len(value[u"map"][key][u"ns"])-1)]
										#return app['services']['dns']._lookup(qdict, server)
										return app['services']['dns']._lookup(qdict, server)[0]['data']
										#return [{"qtype":1, "qclass":qclass, "ttl":300, "rdata":struct.pack("!I", ipstr2int(response))}]
										#return [{'name': 'ssl.bit', 'data': '178.32.31.42', 'typename': 'A', 'classstr': 'IN', 'ttl': 86400, 'type': 1, 'class': 1, 'rdlength': 4}]
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
				if app['debug']: traceback.print_exc()
				return

		#app['services']['dns'].lookup()

	def dnslookup(self, value, key, qdict) :
		print 'dnslookup:', value, key, qdict
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
	
