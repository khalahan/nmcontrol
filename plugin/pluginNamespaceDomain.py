from common import *
import plugin
import DNS
import json, base64, types, random, traceback
import re

class pluginNamespaceDomain(plugin.PluginThread):
	name = 'domain'
	options = {
		'start':	['Launch at startup', 1],
		#'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	depends = {'services': ['dns'], 'plugin': ['data']}
	services = {'dns':{'filter':'.bit$','cache':True}}
	namespaces = ['d']

	supportedMethods = {
		'getIp4'	: 'ip',
		'getIp6'	: 'ip6',
		'getOnion': 'tor',
		'getI2p'	: 'i2p',
		'getFreenet': 'freenet',
		'getFingerprint': 'fingerprint',
	}

	def pLoadconfig(self):
		app['plugins']['dns'].handlers.append(self)

	def _domainToName(self, domain):
		if domain.count(".") >= 2 :
			host = ".".join(domain.split(".")[-2:-1])
			subdomain = ".".join(domain.split(".")[:-2])
		else : 
			host = domain.split(".")[0]
			subdomain = ""
		return ['d/'+host, host, subdomain]

	def _formatRequest(self, request):
		return {
			'handler'	: request[0],
			'type'		: request[1][0],
			'domain'	: request[1][1],
		}

	def _handle(self, request):
		request = self._formatRequest(request)
		
		# requestHandler
		if request['handler'] != 'dns':
			return False

		# requestType
		if request['type'] not in self.supportedMethods:
			return False

		# requestDomain
		if re.search(self.services['dns']['filter'], request['domain']):
			return True

		return False

	def _process(self, request):
		request = self._formatRequest(request)
		params	= self._prepareParams(request)
		
		return params

	def _prepareParams(self, request):
		# get namecoin name from domain name
		name, host, subdomain = self._domainToName(request['domain'])

		# prepare list of subdomains until root
		subdomains = subdomain.split(".")
		subdomains.reverse()
		tmp = []
		flatDomains = [""]
		for sub in subdomains:
			tmp.append("*")
			flatDomains.insert(0, ".".join(tmp))
			tmp.remove("*")
			if sub != "":
				tmp.append(sub)
				flatDomains.insert(0, ".".join(tmp))

		# convert data to json
		nameKey = self.supportedMethods[request['type']]
		nameData = app['plugins']['data'].getValue(['data', ['getData', name]])
		try:	
			nameData = json.loads(nameData)
		except:
			if app['debug']: traceback.print_exc()
			return False

		return {
			'name': name,
			'host': host,
			'subdomain'		: subdomain,
			'flatDomains'	: flatDomains,
			'nameKey'	: nameKey,
			'nameData': nameData,
		}

	def _cleanBadRecords(self, data):
		pass

	def _getFlatZones(self, data):
		pass

	def _convertFlatToBind(self, data):
		pass













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
	
