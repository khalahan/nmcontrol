import DNS
import json, base64, types, traceback
from common import *

def lookup(sp, qdict) :
	domain = qdict["domain"]
	if domain.count(".") >= 2 :
		host = ".".join(domain.split(".")[-2:-1])
		subdomain = ".".join(domain.split(".")[:-2])
	else :
		host = domain.split(".")[0]
		subdomain = ""
	#rawlist = json.dumps(rawjson)
	#error, item = sp.sendJson(['name_show', "d/"+host])
	item = sp.getData(['data', ['getData', 'd/'+host]])
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
								return dnslookup(value, key, qdict)
							return str(value[u"map"][u""])
						#else :
							#if type(value[u"map"][key]) == types.DictType :
								#return dnslookup(domain, qt)
							#return 1, str(value[u"map"][key])
					if hasdefault :
						if type(value[u"map"][u""]) == types.DictType :
							return dnslookup(value, u"", qdict)
						return str(value[u"map"][u""])
		except :
			return
			traceback.print_exc()
def dnslookup(value, key, qdict) :
	if value[u"map"][key].has_key(u"ns") :
		x = DnsClient.Request(server="8.8.8.8")
		if type(value[u"map"][key][u"ns"]) == types.UnicodeType :
			y = x.req(str(value[u"map"][key][u"ns"])).answers[0]["data"]
		else :
			y = x.req(str(value[u"map"][key][u"ns"][0])).answers[0]["data"]
		ns = DNS.Request(server=y)
		return ns.req(name=qdict["domain"], qtype=qdict["qtype"]).answers[0]
