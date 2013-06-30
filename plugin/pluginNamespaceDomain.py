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

	# specific filter for this handler
	def _handle(self, domain, recType):
		return True

	def _prepareDomain(self, domain):
		subdoms = domain.split(".")
		gTLD = subdoms.pop()
		gSLD = subdoms.pop()

		return (gTLD, gSLD, subdoms, "d/" + gSLD)

	def _resolve(self, domain, recType, result):
		if app['debug']: print "Resolving :", domain, recType

		if recType in self.supportedMethods:
			recType = self.supportedMethods[recType]

		gTLD, gSLD, subdoms, name = self._prepareDomain(domain)

		# convert name value to json
		nameData = app['plugins']['data'].getValue(name)
		try:	
			nameData = json.loads(nameData)
		except:
			if app['debug']: traceback.print_exc()
			return False


		# prepare list of subdomains up to root in which data will be searched
		flatDomains = []
		subdomains = subdoms[:]
		subdomains.reverse()

		# add root zone for some record types or if no subdomains
		if recType in ['fingerprint'] or len(subdomains) == 0:
			flatDomains.append([""])

		# add each subdomain + "*"
		tmp = []
		for sub in subdomains:
			tmp.append("*")
			flatDomains.append(tmp[:])
			tmp.remove("*")
			if sub != "":
				tmp.append(sub)
				flatDomains.append(tmp[:])

		# complete imports, alias, translate, etc
		for subs in flatDomains:
			nameData = self._expandSelectedRecord(nameData, subs)

		# for each possible sub-domain, search for data
		flatDomains.reverse()
		if app['debug']: print "Possible domains :", flatDomains
		for subs in flatDomains:
			subData = self._fetchSubTree(nameData, subs)
			if subData is not False:
				if self._fetchNamecoinData(domain, recType, subs, subData, result):
					if app['debug']: print "* result: ", json.dumps(result)
					return result

		if app['debug']: print "* result: ", json.dumps(result)
		return result


	def _fetchNamecoinData(self, domain, recType, subdoms, data, result):
		if app['debug']: print "Fetching", recType, "for", domain, "in sub-domain", subdoms

		# record found in data
		if recType in data:
			result.add(domain, recType, data[recType])
			return True

		# legacy compatibility with ip not in an "ip" record
		if recType == 'ip' and ( type(data) == str or type(data) is unicode ):
			result.add(domain, recType, data)
			return True

		# legacy compatibility with "" in map instead of root
		if recType == 'ip' and 'map' in data and '' in data['map']:
			result.add(domain, recType, data['map'][''])
			return True

		return False

	# remove incompatible records (ns with ip, etc)
	#def _cleanBadRecords(self, data):
	#	pass

	def _fetchSubTree(self, subData, subKeys):

		for sub in subKeys:
			if sub == '' and len(sub) == 0:
				return subData
			elif 'map' in subData and sub in subData['map']:
				subData = subData['map'][sub]
			else:
				return False

		return subData

	# complete imports, alias, translate, etc
	def _expandSelectedRecord(self, nameData, subDoms, limit = maxNestedCalls):
		#print "Selected subs :", subDoms, nameData

		limit -= 1
		if limit < 0:
			print "Too much recursive calls (%s+)" %(maxNestedCalls)
			return nameData

		subData = self._fetchSubTree(nameData, subDoms)

		# sub-domain not found, nothing to do
		if subData is False:
			return nameData

		# alias
		if 'alias' in subData:
			alias = subData['alias']
			del subData['alias']

			# resolve dependency
			subAlias = alias.split(".")
			nameData = self._expandSelectedRecord(nameData, subAlias, limit)

			#print "Expanding '%s' alias to '%s' record" %(".".join(subDoms), alias)
			aliasData = self._fetchSubTree(nameData, subAlias)
			if aliasData is not False:
				subData.update(aliasData)

		#print "* nameData:", nameData
		return nameData









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
	
