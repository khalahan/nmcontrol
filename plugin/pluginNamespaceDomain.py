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
	filters = {'dns': '.bit$|.tor$'}
	handle  = ['dns']

	maxNestedCalls = 10
	supportedMethods = {
		'getIp4'	: 'ip',
		'getIp6'	: 'ip6',
		'getOnion'	: 'tor',
		'getI2p'	: 'i2p',
		'getFreenet'	: 'freenet',
		'getFingerprint': 'fingerprint',
		'getTls': 'tls',
		'getNS'		: 'ns',
		'getTranslate'		: 'translate',
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

		if recType == 'tls':
			if recType in data:
				result.add_raw(domain, recType, data[recType])
				return

		# record found in data
		if recType in data:
			result.add(domain, recType, data[recType])
			return True

		# legacy compatibility with ip not in an "ip" record
		if recType == 'ip' and ( type(data) == str or type(data) is unicode ):
			result.add(domain, recType, data)
			return True

		if recType == 'ns' and ( type(data) == str or type(data) is unicode ):
			result.add(domain, recType, data)
			return True

		# ns record in a dictionary, potentially with the translate option
		if recType == 'ip' and 'ns' in data:
			result.add(domain, recType, data)
			return True

		# legacy compatibility with "" in map instead of root
		if recType == 'ip' and 'map' in data and '' in data['map']:
			result.add(domain, recType, data['map'][''])
			return True

		if recType == 'ns' and 'map' in data and '' in data['map']:
			result.add(domain, recType, data['map']['']['ns'])
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

	def lookup(self, qdict) :
		if qdict["domain"].endswith(".bit"):
			return self._bitLookup(qdict)

		if qdict["domain"].endswith(".tor"):
			return self._torLookup(qdict)


	def _bitLookup(self,qdict):
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
		elif qtype == 52:
			reqtype = "TLSA"


		#try the new API first, then fall back to map if it fails
		if reqtype == "A":
			#new style A request
			answers = app['plugins']['dns'].getIp4(qdict["domain"])
			if answers != '[]':
				nameData = json.loads(answers)
				answers = str(nameData[0])
				#did we get an IP address or nothing?
				if answers:
					return answers
			return
		elif reqtype == "AAAA":
			#new style AAAA request
			answers = app['plugins']['dns'].getIp6(qdict["domain"])
			if answers != '[]':
				nameData = json.loads(answers)
				answers = str(nameData[0])
				#did we get an IP address or nothing?
				if answers:
					return answers
			return
		elif reqtype == "TLSA":
			port = qdict["domain"].split(".")[0][1:]
			protocol = qdict["domain"].split(".")[1][1:]
			answers = app['plugins']['dns'].getTlsFingerprint(qdict["domain"], protocol, port)
			answers = json.loads(answers)
			return {"type":52, "class":1, "ttl":300, "data":answers}
		return

	def _torLookup(self,qdict):

		answers = app['plugins']['dns'].getOnion(qdict["domain"])
		if answers != '[]':
			nameData = json.loads(answers)
			answers = str(nameData[0])
			#did we get an IP address or nothing?
			if answers:
				#if TXT record
				if qdict['qtype'] == 16:
					return {"type":16, "class":1, "ttl":300, "data":answers}
				#if A record return a CNAME
				elif qdict['qtype'] == 1:
					return {"type":5, "class":1, "ttl":300, "data":answers}
	
		return

