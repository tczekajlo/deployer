#!/usr/bin/python
import readline
import logging
import sys

from utils import params, l, __version__

COMMANDS = ["status", "deploy", "help", "set", "quit", "nodes", "puppet", "service"]

class ui:
	def __init__(self):
		l.debug("Starting readline user interface")
		self.__print_logo()
		try:
			readline.read_history_file(params.history_file)
		except IOError:
			file(params.history_file, "w")
		print " I'm ready!"

	def __complete(self, text, state):
		for cmd in COMMANDS:
			if cmd.startswith(text):
				if not state:
					return cmd
				else:
					state -= 1

	def __print_logo(self):
		print """
     _            _                       
  __| | ___ _ __ | | ___  _   _  ___ _ __ 
 / _` |/ _ \ '_ \| |/ _ \| | | |/ _ \ '__|
| (_| |  __/ |_) | | (_) | |_| |  __/ |   
 \__,_|\___| .__/|_|\___/ \__, |\___|_|v%s... shit happens :)   
           |_|            |___/ 
""" % (__version__)

	def read(self):
		readline.parse_and_bind("tab: complete")
		readline.set_completer(self.__complete)
		line = raw_input("deployer> ")
		try:
			readline.write_history_file(params.history_file)
		except Exception as e:
			print e
		return line

	def write(self, text):
		print text

	def finish(self):
		pass
	
	def shutdown(self):
		print "Bye"


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
