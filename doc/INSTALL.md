INSTALL
=======

Requires :

- python2.6 or above (maybe less too)

From sources
------------

    git clone https://github.com/khalahan/nmcontrol.git
    cd nmcontrol

RUN
===

Default config files will be generated on first execution in the 'conf' folder.

View all command line options (take precedence over the 'conf' folder) :

    nmcontrol --help

Start in background :

	nmcontrol start

Start in terminal :

	nmcontrol --daemon=0 start

Start in debug mode:

	nmcontrol --daemon=0 --debug=1 start

View help and rpc commands :

	nmcontrol help
	nmcontrol data help
	nmcontrol data getValue help

Fecth data (from namecoin first, then data is cached) :

	nmcontrol data getValue d/dns


Import data from file
=====================

To generate the data file, do the following in the application folder (export is not implemented yet in nmcontrol) :

	mkdir data
	/path/to/namecoind name_filter > data/namecoin.dat

Configure conf/plugin-data.conf

	import.mode = all
	import.from = file
	import.file = data/namecoin.dat

