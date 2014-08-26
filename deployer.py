#!/usr/bin/python

from utils import params, l
from cmd import cmd_runner
from ui import *
from utils import l, parse_args, setup_logging
import sys

class deployer:
		def __init__(self):
			self.cmd = cmd_runner(ui())

try:
	parse_args() # provides global configuration repository 'params'
except Exception, e:
    print "Error parsing command line: " + str(e)
    sys.exit(1)

# setup logging
try:
    setup_logging()
except Exception, e:
    print "Error starting logger: %s" % str(e)
    sys.exit(1)

d = deployer()
d.cmd.run()
