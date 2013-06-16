#!/usr/bin/python

__version__ = '0.8'

import os
import sys
import inspect
import optparse
import ConfigParser

app = {}
def main():
	# init app config
	global app
	app['conf'] = ConfigParser.SafeConfigParser()
	app['path'] = {}
	app['path']['app'] = os.path.dirname(os.path.realpath(__file__)) + os.sep
	app['path']['conf'] = app['path']['app'] + os.sep + 'conf' + os.sep

	# add import path
	sys.path.append(app['path']['app'] + 'lib')
	sys.path.append(app['path']['app'] + 'plugin')
	sys.path.append(app['path']['app'] + 'service')

	import common
	common.app = app

	import console
	(cWidth, cHeight) = console.getTerminalSize()
	fmt=optparse.IndentedHelpFormatter(indent_increment=4, max_help_position=40, width=cWidth-3, short_first=1 )
	app['parser'] = optparse.OptionParser(formatter=fmt,description='nmcontrol %s' % __version__)
	app['debug'] = False

	# debug mode
	for argv in sys.argv:
		if argv in ['--debug=1','--main.debug=1']:
			app['debug'] = True

	# init modules
	import re
	import dircache

	# init vars and main plugin
	app['services'] = {}
	app['plugins'] = {}
	import pluginMain
	app['plugins']['main'] = pluginMain.pluginMain('plugin')

	# init service
	modules = dircache.listdir('service')
	for module in modules:
		if re.match("^service.*.py$", module):
			module = re.sub(r'\.py$', '', module)
			modulename = re.sub(r'^service', '', module).lower()
			exec("import " + module)
			try:
				exec("p = " + module + "." + module)
				app['services'][p.name] = p('service')
				p.app = app
			except Exception as e:
				print "Exception when loading service", module, ":", e

	# init plugins
	modules = dircache.listdir('plugin')
	modules.remove('pluginMain.py')
	#modules.insert(0, 'pluginMain.py')
	for module in modules: #dircache.listdir('module'):
		if re.match("^plugin.*.py$", module):
			module = re.sub(r'\.py$', '', module)
			modulename = re.sub(r'^plugin', '', module).lower()
			exec("import " + module)
			try:
				exec("p = " + module + "." + module)
				app['plugins'][p.name] = p('plugin')
				p.app = app
			except Exception as e:
				print "Exception when loading plugin", module, ":", e
	
	# parse command line options
	(options, app['args']) = app['parser'].parse_args()
	if app['debug']: print "Cmdline args:", app['args']
	if app['debug']: print "Cmdline options:", options
	for option, value in vars(options).items():
		if value is not None:
			tmp = option.split('.')
			if len(tmp) == 1:
				app['plugins']['main'].conf[tmp[0]] = value
			else:
				module = tmp[0]
				tmp.remove(module)
				if module in app['plugins']:
					app['plugins'][module].conf['.'.join(tmp)] = value
				elif module in app['services']:
					app['services'][module].conf['.'.join(tmp)] = value

	###### Act as client : send rpc request ######
	if len(app['args']) > 0 and app['args'][0] != 'start':
		error, data = app['plugins']['rpc'].pSend(app['args'][:])
		if error is True or data['error'] is True:
			print "ERROR:", data
		else:
			if data['result']['reply'] in [None, True]:
				print 'ok'
			else:
				print data['result']['reply']
			if app['debug'] and data['result']['prints']: print "LOG:", data['result']['prints']
		if app['args'][0] != 'restart':
			return

	# daemon mode
	if int(app['plugins']['main'].conf['daemon']) == 1:
		print "Entering background mode"
		import daemonize
		retCode = daemonize.createDaemon()

	###### Act as server : start plugins ######
	plugins_started = []
	for plugin in app['plugins']:
		if int(app['plugins'][plugin].conf['start']) == 1 and plugin not in ['rpc','main']:
			# exit immediatly when main is stopped, unless in debug mode
			app['plugins'][plugin].daemon=True
			if app['plugins'][plugin].running is False:
				app['plugins'][plugin].start()
				plugins_started.append(app['plugins'][plugin].name)
	print "Plugins started :", ', '.join(plugins_started)

	#services_started = []
	#for service in app['services']:
	#	if app['services'][service].running:
	#		services_started.append(app['services'][service].name)
	#print "Services started :", ', '.join(services_started)

	# stay there to catch CTRL + C and not exit when in daemon mode
	try:
		app['plugins']['main'].start2()
	except (KeyboardInterrupt, SystemExit):
		print '\n! Received keyboard interrupt, quitting threads.\n'

	# stop main program
	app['plugins']['main'].stop()


if __name__=='__main__':
    main()

