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

    nmcontrol.py --help

Start in background :

	nmcontrol.py start

Start in terminal :

	nmcontrol.py --daemon=0 start

Start in debug mode:

	nmcontrol.py --daemon=0 --debug=1 start

View help and rpc commands :

	nmcontrol.py help
	nmcontrol.py data help
	nmcontrol.py data getValue help

Fecth data (from namecoin first, then data is cached) :

	nmcontrol.py data getValue d/dns


Import data from file
=====================

To generate the data file, do the following in the application folder (export is not implemented yet in nmcontrol) :

	mkdir data
	/path/to/namecoind name_filter > data/namecoin.dat

Configure conf/plugin-data.conf

	import.mode = all
	import.from = file
	import.file = data/namecoin.dat

