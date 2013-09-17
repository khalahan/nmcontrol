#name_scan "d/yourdomain" 1
import sys, os
#sys.path.append('/home/khal/sources/nmcontrol/lib/')
import DNS
import rpcClient
import struct, listdns, base64, types, json, random
#from jsonrpc import ServiceProxy
from utils import *
from common import *

class Source(object):
	#def __init__(self):
		#self.servers = app['services']['dns'].conf['resolver'].split(',')
		#self.reqobj = DNS.Request()
		#jsonfile = open("config.json", "r")
		#data = json.loads(jsonfile.read())
		#jsonfile.close()
		#username = str(data[u"username"])
		#port = data[u"port"]
		#password = str(data[u"password"])
		#self.sp = ServiceProxy("http://%(user)s:%(passwd)s@127.0.0.1:%(port)d" % dict(user=username, passwd=password, port=port))
		#elf.sp = rpcClient.rpcClientNamecoin('127.0.0.1', port, username, password)
		#self.sp = app['plugins']['domain']

#	def _parse_file(self):
#		f = open(self._filename, "r")
#		for line in f.readlines():
#			line = line.strip()		
#			if line and line[0] != '#':
#				question, type, value = line.split()
#				question = question.lower()
#				type = type.upper()
#				if question == '@':
#					question = ''
#				if type == 'A':
#					answer = struct.pack("!I", ipstr2int(value))
#					qtype = 1
#				if type == 'NS':
#					answer = labels2str(value.split("."))
#					qtype = 2
#				elif type == 'CNAME':
#					answer = labels2str(value.split("."))
#					qtype = 5
#				elif type == 'TXT':
#					answer = label2str(value)
#					qtype = 16
#				elif type == 'MX':
#					preference, domain = value.split(":")
#					answer = struct.pack("!H", int(preference))
#					answer += labels2str(domain.split("."))
#					qtype = 15
#				self._answers.setdefault(question, {}).setdefault(qtype, []).append(answer)
#		f.close()

	def isIP(self, host) :
		parts = host.split(".")
		if len(parts) != 4:
			return False
		try :
			valid = False
			for part in parts :
				intpart = int(part)
				if intpart <= 255 and intpart >= 0 :
					valid = True
				else : return False
			if valid :
				return True
			return False
		except : return False
	def get_response(self, query, domain, qtype, qclass, src_addr):
		#print query
		#print domain
		#print qtype
		#print qclass
		#print src_addr
		if qtype == 1:
			#answer = struct.pack("!I", ipstr2int(value))
			reqtype = "A"
		if qtype == 2:
			#answer = labels2str(value.split("."))
			reqtype = "NS"
		elif qtype == 5:
			#answer = labels2str(value.split("."))
			reqtype = "CNAME"
		elif qtype == 16:
			#answer = label2str(value)
			reqtype = "TXT"
		elif qtype == 15:
			#preference, domain = value.split(":")
			#nswer = struct.pack("!H", int(preference))
			#answer += labels2str(domain.split("."))
			reqtype = "MX"
		elif qtype == 28:
			#answer = struct.pack("!I", ipstr2int(value))
			reqtype = "AAAA"
		elif qtype == 52:
			reqtype = "TLSA"
		else : reqtype = None
		answers = app['services']['dns'].lookup({"query":query, "domain":domain, "qtype":qtype, "qclass":qclass, "src_addr":src_addr})
		#print 'domain:', domain
		#print 'answers:', answers
		if domain.endswith(".bit") or domain.endswith(".tor") :
			#response = listdns.lookup(self.sp, {"query":query, "domain":domain, "qtype":qtype, "qclass":qclass, "src_addr":src_addr})
			#response = self.sp.lookup({"query":query, "domain":domain, "qtype":qtype, "qclass":qclass, "src_addr":src_addr})
			response = answers
			results = []
			if type(response) == types.DictType :
				tempresults = {"qtype":response["type"], "qclass":response["class"], "ttl":response["ttl"]}
				if response["type"] == 1 :
					#if answers == [] :
					#	return self.get_response(query, domain, 5, qclass, src_addr)
					tempresults["rdata"] = struct.pack("!I", ipstr2int(response["data"]))
				elif response["type"] == 2 or response["type"] == 5:
					tempresults["rdata"] = labels2str(response["data"].split("."))
				elif response["type"] == 16 :
					tempresults["rdata"] = labels2str(response["data"])
				elif response["type"] == 15 :
					tempresult = struct.pack("!H", response["data"][0])
					tempresult += labels2str(response["data"][1].split("."))
					tempresults["rdata"] = tempresult
				elif response["type"] == 28 :
					tempresults["rdata"] = response["data"]
				elif response["type"] == 52 :
					tempresult = '\x03\x00'
					tempresult += chr(int(response["data"][0][0]))
					tempresult += bytearray.fromhex(response["data"][0][1])
					tempresults["rdata"] = tempresult
				#else : return 3, []
				results.append(tempresults)
				return 0, results
			if type(response) == types.StringType :
				if self.isIP(response) :
					return 0, [{"qtype":1, "qclass":qclass, "ttl":300, "rdata":struct.pack("!I", ipstr2int(response))}]
			return 3, []
			#if query not in self._answers:
				#return 3, []
			#if qtype in self._answers[query]:
			#if domain == "sonicrules.bit":
			#	results = [{'qtype': 1, 'qclass':qclass, 'ttl': 300, 'rdata': struct.pack("!I", ipstr2int(self.reqobj.req("sonicrules.org", qtype=1).answers[0]["data"]))}]
			#	return 0, results
			#elif qtype == 1:
				# if they asked for an A record and we didn't find one, check for a CNAME
				#return self.get_response(query, domain, 5, qclass, src_addr)
		else:
			#server = self.servers[random.randrange(0, len(self.servers)-1)]
			#answers = self.reqobj.req(name=domain, qtype=qtype, server=server).answers
			results = []
			for response in answers :
				tempresults = {"qtype":response["type"], "qclass":response["class"], "ttl":response["ttl"]}
				if response["type"] == 1 :
					if answers == [] :
						return self.get_response(query, domain, 5, qclass, src_addr)
					tempresults["rdata"] = struct.pack("!I", ipstr2int(response["data"]))
				elif response["type"] == 2 or response["type"] == 5:
					tempresults["rdata"] = labels2str(response["data"].split("."))
				elif response["type"] == 16 :
					tempresults["rdata"] = labels2str(response["data"])
				elif response["type"] == 15 :
					tempresult = struct.pack("!H", response["data"][0])
					tempresult += labels2str(response["data"][1].split("."))
					tempresults["rdata"] = tempresult
				elif response["type"] == 28 :
					if answers == [] :
						return self.get_response(query, domain, 5, qclass, src_addr)
					#tempresults["rdata"] = struct.pack("!I", ipstr2int(response["data"]))
					tempresults["rdata"] = response["data"]
				elif response["type"] == 52 :
					tempresults["rdata"] = response["data"]
				#else : return 3, []
				results.append(tempresults)
			return 0, results
		return 3, []
