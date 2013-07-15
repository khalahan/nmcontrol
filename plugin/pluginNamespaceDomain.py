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
	depends = {'plugins': ['data', 'dns'],'services': ['dns']}
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

		# init
		flatDomains = []
		subdomains = subdoms[:]
		subdomains.reverse()
		# fingerprint and xxx records are valid for all sub-domains
		parentIsValid = False
		if recType in ['fingerprint']:
			parentIsValid = True

		# add asked domain first (ex: www.fr.dot-bit.bit)
		flatDomains.append(subdomains[:])
		# add each parent domain until root (ex: *.fr.dot-bit.bit, *.dot-bit.bit)
		for sub in subdoms:
			subdomains.pop()
			subdomains.append("*")
			flatDomains.append(subdomains[:])
			subdomains.remove("*")
			if parentIsValid: # (ex, if fingerprint: fr.dot-bit.bit, dot-bit.bit)
				flatDomains.append(subdomains[:])

		# complete imports, alias, translate, etc
		# starting from root domain to domain which has most sub-domains
		flatDomains.reverse()
		for subs in flatDomains:
			nameData = self._expandSelectedRecord(nameData, subs)

		# for each possible sub-domain, search for data
		# starting at domain which has most sub-domains up to root domain
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
		item = app['plugins']['data'].getData(name)
		#rawlist = json.dumps(rawjson)
		try:	
			item = json.loads(item)
		except:
			if app['debug']: traceback.print_exc()
			return
		
		qtype = qdict['qtype']
		if qtype == 1:
			reqtype = "A"
		if qtype == 2:
			reqtype = "NS"
		elif qtype == 5:
			reqtype = "CNAME"
		elif qtype == 16:
			reqtype = "TXT"
		elif qtype == 15:
			reqtype = "MX"
		elif qtype == 28:
			reqtype = "AAAA"


		#try the new API first, then fall back to map if it fails
		if reqtype == "A":
			#new style A request
			answers = app['plugins']['dns'].getIp4(qdict["domain"])
                        if answers != '[]':
                                nameData = json.loads(answers)
                                answers = str(nameData[0])
				#did we get an IP address or nothing?
				if answers.lower() == 'ns':
					server = self._getNSServer(qdict["domain"])
					answers = self._getIPFromNS(qdict,server)
				if answers:
					return answers
		elif reqtype == "AAAA":
			#new style AAAA request
			answers = app['plugins']['dns'].getIp6(qdict["domain"])
                        if answers != '[]':
                                nameData = json.loads(answers)
                                answers = str(nameData[0])
				#this probably doesnt work for ipv6...
				if answers.lower() == 'ns':
					server = self._getNSServer(qdict["domain"])
					answers = self._getIPFromNS(qdict,server)
				#did we get an IP address or nothing?
				if answers:
					return answers

		print item

		#Try old style map resolution and recursive lookup when using a NS record
		if str(item[u"name"]) == "d/" +  host :
			try :

				try:
					value = json.loads(item[u"value"])
				except:
					if app['debug']: print "Value Result Is Not Valid JSON"
					return

				#old style resolution
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

	def _getNSServer(self,domain):
		name, host, subdomain = self.domainToNamespace(domain)
		item = app['plugins']['data'].getData(name)

		try:	
			item = json.loads(item)
		except:
			if app['debug']: traceback.print_exc()
			return

		try:
			value = json.loads(item[u"value"])
		except:
			if app['debug']: print "Value Result Is Not Valid JSON"
			return

		server = value[u"ns"][random.randrange(0, len(value[u"ns"]))]
		return server

	def _getIPFromNS(self,qdict,server):
		return app['services']['dns']._lookup(qdict, server)[0]['data']

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
	
