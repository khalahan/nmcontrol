import threading
import time
import os
from optparse import OptionGroup
from ConfigParser import SafeConfigParser
#import optparse
#import ConfigParser
import inspect
import json

class PluginThread(threading.Thread):
	app = None
	name = None
	desc = None
	running = False
	options = {}
	helps = {}
	depends = []
	#version = None

	def __init__(self, app):
		if self.name is None:
			raise Exception(str(self.__class__) + " : name not defined")
		self.app = app
		self.nameconf = 'plugin-' + self.name + '.conf'
		self.nameclass = 'plugin' + self.name.capitalize()
		self.parser = app['parser']
		self.conf = {}
		self._loadconfig()
		threading.Thread.__init__(self)

	def run(self):
		if self.running: return
		self.start2()

	def start2(self, arg = []):
		if self.app['debug']: print "Plugin %s parent starting" %(self.name)
		self.running = True
		# start depends
		if len(self.depends) > 0:
			for dep in self.depends:
				self.app['plugins'][dep].start()
		return self.pStart()

	def pStart(self, arg = []):
		if self.app['debug']: print "Plugin %s parent start" %(self.name)
		#time.sleep(1)
		return True

	def stop(self, arg = []):
		if self.app['debug']: print "Plugin %s parent stopping" %(self.name)
		self.running = False
		return self.pStop()

	def pStop(self, arg = []):
		if self.app['debug']: print "Plugin %s parent stop" %(self.name)
		time.sleep(0)
		return True

	def status(self, arg = []):
		return self.pStatus()

	def pStatus(self, arg = []):
		if self.running:
			return "Plugin " + self.name + " running"

	def reload(self, arg = []):
		if self.app['debug']: print "Plugin %s parent reloading" %(self.name)
		return self.pReload()
	
	def pReload(self, arg = []):
		if self.app['debug']: print "Plugin %s parent reload" %(self.name)
		self.loadconfig()
		return True

	def restart(self, arg = []):
		if self.app['debug']: print "Plugin %s parent restarting" %(self.name)
		return self.pRestart()

	def pRestart(self, arg = []):
		if self.app['debug']: print "Plugin %s parent restart" %(self.name)
		self.stop()
		self.start2()
		return True

	def help(self, arg = []):
		return self.pHelp(arg)

	def pHelp(self, arg = []):
		#if arg[0] == 'help':
		#	help = '* Available plugins :\n'
		#	for plugin in self.app['plugins']:
		#		if self.app['plugins'][plugin].running == True:
		#			help += '\n' + plugin + ' help'
		#	return help

		if len(arg[1]) > 1:
			if arg[1][1] in self.app['plugins'][arg[0]].helps:
				help = self.app['plugins'][arg[0]].helps[arg[1][1]][3]
				help += '\n' + arg[1][1] + ' ' + self.app['plugins'][arg[0]].helps[arg[1][1]][2]
				return help

		methods = self._getPluginMethods()
		help = '* Available commands for plugin ' + self.name + ' :'
		for method in methods:
			if method in self.helps:
				method = method + ' ' + self.helps[method][2]
			help += '\n' + method
		return help

	def _getPluginMethods(self):
		parents = []
		parentmethods = inspect.getmembers(threading.Thread)
		for (method, value) in parentmethods:
			parents.append(method)

		methods = []
		allmethods = inspect.getmembers(self, predicate=inspect.ismethod)
		for (method, value) in allmethods:
			if method[0] == '_':
				continue
			if method[0] == 'p' and method[1].upper() == method[1]:
				continue
			if method in parents:
				continue
			if method == 'start2': method = 'start'
			if method in self.helps:
				method = method + ' ' + self.helps[method][2]
			methods.append(method)
		methods.sort()
		return methods

	def _loadconfig(self, arg = []):
		# add command line args to the program options + build default configuration data
		defaultConf = '[' + self.name + ']\n'
		group = OptionGroup(self.app['parser'], self.name.capitalize() + " Options", self.desc)
		if self.options.__class__ is dict:	
			tmp = []
			for option, value in self.options.items():
				tmp.append({option: value})
			self.options = tmp
		#for option, value in self.options.items():
		for option in self.options:
			option, value = option.items()[0]
			if len(value) == 3:
				help = value[0] + " " + value[2] + ""
				defaultConf += '; ' + value[0] + ' - choices: ' + value[2] + '\n'
			else:
				help = value[0]
				defaultConf += '; ' + value[0] + '\n'
			defaultConf += ';' + option + '=' + str(value[1]) + '\n\n'
			if option != 'start':
				if self.name == 'main':
					group.add_option('--' + option, '--' + self.name + '.' + option, type='str', help=help, metavar=str(value[1]))
				else:
					group.add_option('--' + self.name + '.' + option, type='str', help=help, metavar=str(value[1]))
			self.conf[option] = value[1]
		self.app['parser'].add_option_group(group)
		
		# create default config if none
		userConfFile = self.app['path']['conf'] + self.nameconf
		if not os.path.exists(userConfFile):
			if not os.path.exists(self.app['path']['conf']):
				os.mkdir(self.app['path']['conf'])
			fp = open(userConfFile, 'w')
			fp.write(defaultConf)
			fp.close()

		# read user config
		fileconf = SafeConfigParser()
		fileconf.read(userConfFile)

		# set user config
		for option in fileconf.options(self.name):
			self.conf[option] = fileconf.get(self.name, option)

		self.pLoadconfig()

	def pLoadconfig(self, arg = []):
		pass

