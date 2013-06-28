from common import *
import plugin
import DNS
import json, base64, types, random, traceback

class pluginNamespaceDomain(plugin.PluginThread):
	name = 'domain'
	options = {
		'start':	['Launch at startup', 1],
		#'resolver':	['Forward standard requests to', '8.8.8.8,8.8.4.4'],
	}
	depends = {'plugins': ['data', 'dns']}
	filters = {'dns': '.bit$'}
	handle  = ['dns']

	maxNestedCalls = 10
	supportedMethods = {
		'getIp4'	: 'ip',
		'getIp6'	: 'ip6',
		'getOnion'	: 'tor',
		'getI2p'	: 'i2p',
		'getFreenet': 'freenet',
		'getFingerprint': 'fingerprint',
	}

	def pLoadconfig(self):
		app['plugins']['dns'].handlers.append(self)

	# specific handler filter
	def _handle(self, request):
		return True

	def _prepareDomain(self, domain):
		subdoms = domain.split(".")
		gTLD = subdoms.pop()
		gSLD = subdoms.pop()

		return (gTLD, gSLD, subdoms, "d/" + gSLD)

	def _resolve(self, domain, recType, limit = maxNestedCalls):
		if app['debug']: print "Resolving :", domain, recType

		if recType in self.supportedMethods:
			recType = self.supportedMethods[recType]

		gTLD, gSLD, subdoms, name = self._prepareDomain(domain)

		# convert name value to json
		nameData = app['plugins']['data'].getValue(['data', ['getData', name]])
		try:	
			nameData = json.loads(nameData)
		except:
			if app['debug']: traceback.print_exc()
			return False

		
		# prepare list of subdomains up to root in which data will be searched
		flatDomains = []
		subdomains = subdoms[:]
		subdomains.reverse()
		tmp = []

		# add root zone for some record types or if no subdomains
		if recType in ['fingerprint'] or len(subdomains) == 0:
			flatDomains.insert(0, [""])

		# add each subdomain + "*"
		for sub in subdomains:
			tmp.append("*")
			#flatDomains.insert(0, ".".join(tmp))
			flatDomains.insert(0, tmp[:])
			tmp.remove("*")
			if sub != "":
				tmp.append(sub)
				#flatDomains.insert(0, ".".join(tmp))
				flatDomains.insert(0, tmp[:])

		if app['debug']: print "Possible domains :", flatDomains

		# for each possible sub-domain, search for data
		results = []
		for subs in flatDomains:
			subExists = True
			subData = nameData
			for sub in subs:
				if sub == '' and len(sub) == 0:
					pass
				elif 'map' in subData and sub in subData['map']:
					subData = subData['map'][sub]
				else:
					subExists = False
			if subExists:
				result = self._fetchData(domain, recType, subs, subData)
				if result is not False:
					if app['debug']: print "* result: ", json.dumps(result)
					if type(result) == unicode:
						result = [result]
					return json.dumps(result)

		if app['debug']: print "* result: ", json.dumps(results)
		return json.dumps(results)
	
	def _fetchData(self, domain, recType, subdoms, data):
		if app['debug']: print "Fetching", recType, "for", domain, "in sub-domain", subdoms

		# record found in data
		if recType in data:
			return data[recType]

		# legacy compatibility with ip not in an "ip" record
		if recType == 'ip' and ( type(data) == str or type(data) is unicode ):
			return data

		return False

	# remove incompatible records (ns with ip, etc)
	#def _cleanBadRecords(self, data):
	#	pass

	# complete 'import', etc
	#def _expandRecords(self, data):
	#	pass






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
	
