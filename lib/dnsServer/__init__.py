#!/usr/bin/python

# Copyright (c) 2009 Tom Pinckney
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
#	 The above copyright notice and this permission notice shall be
#	 included in all copies or substantial portions of the Software.
#
#	 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#	 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#	 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#	 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#	 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#	 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#	 OTHER DEALINGS IN THE SOFTWARE.
#
# Modified by Khalahan in order to include it in nmcontrol
# Modified by sonicrules1234 (Westly Ward) in order to have it work as a dns server for all domains rather than just one
# File originally named pymds
import sys
import socket
import struct
import ConfigParser
import signal
import getopt
import traceback
import threading

from utils import *
from common import *

class DnsError(Exception):
	pass

class DnsServer(threading.Thread):
	daemon = True;
	running = True
	udps = None
	
	def run(self):
		self.serve()

	def serve(self):
		self.udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.udps.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		udps = self.udps
		listen_host = app['services']['dns'].conf['host']
		listen_port = int(app['services']['dns'].conf['port'])
		try:
			udps.bind((listen_host, listen_port))
		except socket.error as e:
			print "ERROR: Unable to start DNS server (%s)" % e
		#ns_resource_records, ar_resource_records = compute_name_server_resources(_name_servers)
		ns_resource_records = ar_resource_records = []
		while self.running:
			try:
				req_pkt, src_addr = udps.recvfrom(512)   # max UDP DNS pkt size
			except socket.error:
				continue
			qid = None
			try:
				exception_rcode = None
				try:
					qid, question, qtype, qclass = parse_request(req_pkt)
				except:
					exception_rcode = 1
					if not self.running:
						continue
					raise Exception("could not parse query")
				question = map(lambda x: x.lower(), question)
				found = False
				source_module = __import__("namecoindns", globals(), locals(), [])
				source_instance = source_module.Source()
				for config in [True]:
					#if question[1:] == config['domain']:
						#query = question[0]
					#elif question == config['domain']:
						#query = ''
					#else:
					#	continue
					#print question
					#if len(question) == 2 :
					query = ""   
					#query = question.split(".")
					rcode, an_resource_records = source_instance.get_response(query, ".".join(question), qtype, qclass, src_addr)
					#if rcode == 0 and 'filters' in config:
					#	for f in config['filters']:
					#		an_resource_records = f.filter(query, config['domain'], qtype, qclass, src_addr, an_resource_records)
					resp_pkt = format_response(qid, question, qtype, qclass, rcode, an_resource_records, ns_resource_records, ar_resource_records)
					found = True
					break
				if not found:
					exception_rcode = 3
					raise Exception("query is not for our domain: %s" % ".".join(question))
			except:
				if app['debug']: traceback.print_exc()
				if not self.running:
					continue
				if qid:
					if exception_rcode is None:
						exception_rcode = 2
					resp_pkt = format_response(qid, question, qtype, qclass, exception_rcode, [], [], [])
				else:
					continue
			udps.sendto(resp_pkt, src_addr)
	
	def stop(self):
		self.running = False
		try:
			self.udps.shutdown(socket.SHUT_RDWR)
			self.udps.close()
		except:
			pass

def compute_name_server_resources(name_servers):
	ns = []
	ar = []
	for name_server, ip, ttl in name_servers:
		ns.append({'qtype':2, 'qclass':1, 'ttl':ttl, 'rdata':labels2str(name_server)})
		ar.append({'qtype':1, 'qclass':1, 'ttl':ttl, 'rdata':struct.pack("!I", ip)})
	return ns, ar
		
def parse_request(packet):
	hdr_len = 12
	header = packet[:hdr_len]
	qid, flags, qdcount, _, _, _ = struct.unpack('!HHHHHH', header)
	qr = (flags >> 15) & 0x1
	opcode = (flags >> 11) & 0xf
	rd = (flags >> 8) & 0x1
	#print "qid", qid, "qdcount", qdcount, "qr", qr, "opcode", opcode, "rd", rd
	if qr != 0 or opcode != 0 or qdcount == 0:
		raise DnsError("Invalid query")
	body = packet[hdr_len:]
	labels = []
	offset = 0
	while True:
		label_len, = struct.unpack('!B', body[offset:offset+1])
		offset += 1
		if label_len & 0xc0:
			raise DnsError("Invalid label length %d" % label_len)
		if label_len == 0:
			break
		label = body[offset:offset+label_len]
		offset += label_len
		labels.append(label)
	qtype, qclass= struct.unpack("!HH", body[offset:offset+4])
	if qclass != 1:
		raise DnsError("Invalid class: " + qclass)
	return (qid, labels, qtype, qclass)

def format_response(qid, question, qtype, qclass, rcode, an_resource_records, ns_resource_records, ar_resource_records):
	resources = []
	resources.extend(an_resource_records)
	num_an_resources = len(an_resource_records)
	num_ns_resources = num_ar_resources = 0
	if rcode == 0:
		resources.extend(ns_resource_records)
		resources.extend(ar_resource_records)
		num_ns_resources = len(ns_resource_records)
		num_ar_resources = len(ar_resource_records)
	pkt = format_header(qid, rcode, num_an_resources, num_ns_resources, num_ar_resources)
	pkt += format_question(question, qtype, qclass)
	for resource in resources:
		pkt += format_resource(resource, question)
	return pkt

def format_header(qid, rcode, ancount, nscount, arcount):
	flags = 0
	flags |= (1 << 15)
	flags |= (1 << 10)
	flags |= (rcode & 0xf)
	hdr = struct.pack("!HHHHHH", qid, flags, 1, ancount, nscount, arcount)
	return hdr

def format_question(question, qtype, qclass):
	q = labels2str(question)
	q += struct.pack("!HH", qtype, qclass)
	return q

def format_resource(resource, question):
	r = ''
	r += labels2str(question)
	r += struct.pack("!HHIH", resource['qtype'], resource['qclass'], resource['ttl'], len(resource['rdata']))
	r += resource['rdata']
	return r

#def read_config():
#	for config_file in config_files:
#		config_files[config_file] = config = {}
#		config_parser = ConfigParser.SafeConfigParser()
#		try:
#			config_parser.read(config_file)
#			config_values = config_parser.items("default")	
#		except:
#			die("Error reading config file %s\n" % config_file)
#
#		for var, value in config_values:
#			if var == "domain":
#				config['domain'] = value.split(".")
#			elif var == "name servers":
#				config['name_servers'] = []
#				split_name_servers = value.split(":")
#				num_split_name_servers = len(split_name_servers)
#				for i in range(0,num_split_name_servers,3):
#					server = split_name_servers[i]
#					ip = split_name_servers[i+1]
#					ttl = int(split_name_servers[i+2])
#					config['name_servers'].append((server.split("."), ipstr2int(ip), ttl))
#			elif var == 'source':
#				module_and_args = value.split(":")
#				module = module_and_args[0]
#				args = module_and_args[1:]
#				source_module = __import__(module, {}, {}, [''])
#				source_instance = source_module.Source(*args)
#				config['source'] = source_instance
#			elif var == 'filters':
#				config['filters'] = []
#				for module_and_args_str in value.split():
#					module_and_args = module_and_args_str.split(":")
#					module = module_and_args[0]
#					args = module_and_args[1:]
#					filter_module = __import__(module, {}, {}, [''])			
#					filter_instance = filter_module.Filter(*args)
#					config['filters'].append(filter_instance)
#			else:
#				die("unrecognized paramter in conf file %s: %s\n" % (config_file, var))
#
#		if 'domain' not in config or 'source' not in config:
#			die("must specify domain name and source in conf file %s\n", config_file)
#		sys.stderr.write("read configuration from %s\n" % config_file)

#def reread(signum, frame):
#	read_config()
	
#def die(msg):
#	sys.stderr.write(msg)
#	sys.exit(-1)

#def usage(cmd):
#	die("Usage: %s\n" % (cmd))

#config_files = {}
#listen_port = 1053
#listen_host = ''

#try:
#	options, filenames = getopt.getopt(sys.argv[1:], "p:h:")
#except getopt.GetoptError:
#	usage(sys.argv[0])

#for option, value in options:
#	if option == "-p":
#		listen_port = int(value)
#	elif option == "-h":
#		listen_host = value
#if not filenames:
#	filenames = ['pymds.conf']
#for f in filenames:
#	if f in config_files:
#		raise Exception("repeated configuration")
#	config_files[f] = {}

#sys.stdout.write("Starting %s\n" % (sys.argv[0]))
#read_config()
#signal.signal(signal.SIGHUP, reread)
#for config in config_files.values():
#	sys.stdout.write("%s: serving for domain %s\n" % (sys.argv[0], ".".join(config['domain'])))
#sys.stdout.flush()
#sys.stderr.flush()
#serve()

