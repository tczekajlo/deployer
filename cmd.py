import time
import readline
import logging
import sys
import pexpect

import ply.yacc as yacc

from parser import *
from utils import params, l
from jira.client import JIRA


parse_arg = None

def p_expression_cli(p):
	'''expression : NAME
			| NAME SELECT
			| NAME NAME
			| NAME NAME SELECT
			| NAME NAME NAME
			| NAME NAME NAME SELECT
			| NAME NAME SELECT NAME
			| NAME NAME NAME NAME
			| NAME SELECT NAME'''
	global parse_arg
	parse_arg = p


class cmd_runner:
	def __init__(self, ui):
		self.ui = ui
		self.commands = {
			'help':	[self.cmd_help, "Print this help"],
			'quit': [self.cmd_quit, "Kill 'Em All."],
			'nodes': [self.cmd_nodes, "Display list of all nodes for which wll be done deploy"],
			'deploy': [self.cmd_deploy, "Install package on all nodes"],
			'status': [self.cmd_status, "Check status of package, service or nrpe"],
			'service': [self.cmd_service, "Manages system services"],
			'set': [self.cmd_set, "Show/set variables (set PARAMETER VALUE)"],
			'puppet': [self.cmd_puppet, "Re-run puppet agent"]
		}

	#--------------------------------------------------------------------------

	def cmd_help(self, args):
		self.ui.write(" Available commands:")
		for c in sorted(self.commands.keys()):
			self.ui.write("   %-10s : %s " % (c, self.commands[c][1]))

	#--------------------------------------------------------------------------	

	def cmd_nodes(self, args):
		self.__run_mco(["find", "-C", params.class_name, "-S", self.__hosts_select(args, 0)])

	#--------------------------------------------------------------------------

	def cmd_puppet(self, args):
		if not len(args):
			self.ui.write("Use: puppet runonce [hosts_group] [add_comment]")
			return

		if args[0] == "runonce":
			cmd_result=self.__run_mco(["puppet", "runonce", "-C", params.class_name, "-S", self.__hosts_select(args, 1)])
		else:
			self.ui.write("Unknown argument")
			self.ui.write("Use: puppet runonce [hosts_group] [add_comment]")
			return
		
		#Adds JIRA comment
		self.__add_jira_comment_prepare(args, 'puppet', cmd_result)

	#--------------------------------------------------------------------------
	def cmd_service(self, args):
		action = None

		if not len(args):
			self.ui.write("Use: service start|stop|restart|status [hosts_group]")
			return

		if args[0] == "start":
			action = args[0]
		elif args[0] == "stop":
			action = args[0]
		elif args[0] == "status":
			action = args[0]
		elif args[0] == "restart":
			action = args[0]
		else:
			self.ui.write("Unknown action")
			self.ui.write("Use: service start|stop|restart|status [hosts_group]")
			return

		self.ui.write(" Are you sure? (y/N): ")
		line = raw_input("> ")

		if line == "y" or line == "Y" or line == "Yes" or line == "YES":
			cmd_result=self.__run_mco(["service", params.package_name, action, "-C", params.class_name, "-S", self.__hosts_select(args, 1)])
		else:
			self.ui.write(" Aborted.")		

	#--------------------------------------------------------------------------
	def cmd_status(self, args):
		if not len(args):
			self.ui.write("Use: status package|service|nrpe [hosts_group] [add_comment]")
			return

		if args[0] == "package":
			cmd_result=self.__run_mco(["package", params.package_name, "status", "-C", params.class_name, "-S", self.__hosts_select(args, 1)])
		elif args[0] == "service":
			cmd_result=self.__run_mco(["service", params.package_name, "status", "-C", params.class_name, "-S", self.__hosts_select(args, 1)])
		elif args[0] == "nrpe":
			if params.nrpe_command == "None":
				self.ui.write("NRPE commands is not set")
				l.debug("NRPE command is not set.")
				return

			cmd_result=self.__run_mco(["nrpe", params.nrpe_command, "-C", params.class_name, "-S", self.__hosts_select(args, 1)])
		else:
			self.ui.write("Unknown argument")
			self.ui.write("Use: status package|service|nrpe [hosts_group] [add_comment]")

		#Adds JIRA comment
		self.__add_jira_comment_prepare(args, 'status', cmd_result)
	
	#--------------------------------------------------------------------------
	def cmd_deploy(self, args):
		self.ui.write(" I'll install package with following parameters: ")
		self.ui.write("")
		self.print_cfg()
		self.ui.write("")
		self.ui.write(" Are you sure? (y/N): ")
		line = raw_input("> ")
		
		if line == 'yes' or line == "y" or line == "Y" or line == "Yes":
			deploy_result = self.__run_mco(["puppet", "resource", "package", params.package_name,
				"ensure=" + params.package_ensure, "-C", params.class_name, "-S", self.__hosts_select(args, 0)])
			
			jira= JIRA(basic_auth=(params.jira_user, params.jira_password), 
				options={'server': params.jira_server})
			issue= jira.issue(params.jira_issue)

			#Update jira status
			for k in params.jira_transitions:
				if k['name'] == params.jira_success_transitions[params.deploy_type]:
					l.info("JIRA transition: %s" % (k['name']))
					jira.transition_issue(issue, k['id'])
					break

			#Add jira comment
			self.__add_jira_comment(jira,
				"{code:title=" + params.project + " deploy result}" + deploy_result + "{code}")
		else:
			self.ui.write(" Aborted.")

	#--------------------------------------------------------------------------

	def __add_jira_comment(self, jira, comment):
		issue= jira.issue(params.jira_issue)
		try:
			if not params.jira_add_comment:
				self.ui.write("Adding comments is disabled.")
				l.info("Adding comments is disabled. You can enable it in configuration file.")
				return
			l.info("Adding JIRA comment. Issue %s" % (params.jira_issue))
			self.ui.write("Adding JIRA comment...")
			jira.add_comment(issue, comment)
		except Exception as e:
			print e
		finally:
			self.ui.write("Done.")

	def __add_jira_comment_prepare(self, args, cmd_name, cmd_result):
		if args.index('add_comment') != 0:
			jira= JIRA(basic_auth=(params.jira_user, params.jira_password),
				options={'server': params.jira_server})

			self.__add_jira_comment(jira, "{code:title=" + params.project +
				" - '" + cmd_name +" " + args[0] + "' command result}" + cmd_result + "{code}")

	#--------------------------------------------------------------------------

	def __hosts_select(self, select_filter, arg_pos):
		group = None
		if (len(select_filter) < arg_pos+1 or
				select_filter[arg_pos] == 'add_comment'):
			group = params.class_name
		else:
			group = select_filter[arg_pos]

		l.debug("Hosts group: %s" % (group))

		return group

	#--------------------------------------------------------------------------

	def cmd_quit(self, args):
		self.ui.write(" Exiting...")
		sys.exit(0)

	#--------------------------------------------------------------------------

	def __run_mco(self, mco_args):
		result = ""
		p = pexpect.spawn("mco",mco_args,timeout=None,logfile=sys.stdout)
		line = p.readline()
		result = line
		while line:
			line = p.readline()
			result+=line

		return result

	#--------------------------------------------------------------------------

	def print_cfg(self):
		self.ui.write(" Project			: %s" % params.project)
		self.ui.write(" Deploy type			: %s" % params.deploy_type)
		self.ui.write(" Package ensure			: %s" % params.package_ensure)
		self.ui.write(" Package name			: %s" % params.package_name)
		self.ui.write(" Puppet class			: %s" % params.class_name)
		self.ui.write(" JIRA update issue		: %s" % params.jira_issue)
		self.ui.write(" JIRA add comment		: %s" % params.jira_add_comment)
		self.ui.write("")

	#--------------------------------------------------------------------------

	def cmd_set(self, args):
		if not len(args):
			self.print_cfg()
			return

		if len(args) != 2:
			self.ui.write("Use: 'set PARAMETER VALUE' to change setting")
			self.ui.write("Use: You can set following parameters:")
			for k,v in params.settable.items():
				self.ui.write("parameter:	%s, %s" % (k, v))
			return

		if not hasattr(params, args[0]):
			self.ui.write(" No such parameter: %s" % args[0])
			return

		if args[0] not in params.settable:
			self.ui.write(" Paremeter is not settable: %s" % args[0])
			return

		if args[1] == '':
			self.ui.write(" VALUE for '%s' can't be empty" % args[0])
			return

		try:
			v_test = params.settable[args[0]][0] (args[1])
		except:
			self.ui.write(" VALUE for '%s' must be of %s" % (args[0], params.settable[args[0]][0]))
			return

		l.debug("Setting '%s' to '%s'" % (args[0], args[1]))
		try:
			params.__dict__[args[0]] = args[1]
		except Exception, e:
			self.ui.write(" Could not set parameter '%s' to '%s', error: %s" % (args[0], args[1], str(e)))
			l.warning("Could not set parameter '%s' to '%s', error: %s" % (args[0], args[1], str(e)))
			return
		
		self.ui.write(" Parameter '%s' set to '%s' " % (args[0], params.__dict__[args[0]]))

	#--------------------------------------------------------------------------

	def process_command(self):
		try:
			line = self.ui.read()
			if not line:
				return
			yacc.parse(line)
			l.info("Got command: '%s'" % line)
			l_cmd = parse_arg[1]
			l_args = parse_arg[2:]
			if l_cmd and (l_cmd not in self.commands.keys()):
				self.ui.write(" Unknown command: '%s'" % l_cmd)
				self.ui.finish()
			else:
				res = self.commands[l_cmd][0](l_args)
				self.ui.finish()
				return res
		except KeyboardInterrupt:
			l.debug("Got KeyboardInterrupt, ignoring")
			self.ui.write("")
		except EOFError:
			self.ui.write("Bye.")
			sys.exit(0)
		except Exception, e:
			l.warning("Exception %s: %s" % (type(e), str(e)))
		return

	#--------------------------------------------------------------------------

	def run(self):
		yacc.yacc(debug=0, write_tables=0)
		while True:
			if self.process_command():
				break
		self.ui.shutdown()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
