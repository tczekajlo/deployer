#!/usr/bin/python

import argparse
import logging
import ConfigParser
import sys
from jira.client import JIRA

l = logging.getLogger()
config = ConfigParser.ConfigParser()
config.read("deployer.cfg")
__version__ = "0.1.0"

class my_params:
	try:
		settable = {'package_ensure': [str], 'jira_add_comment': [bool]}		

		#History
		history_file = ".deployer_history"

		#Project
		deploy_project = config.get('deploy', 'project')

		project = None
		deploy_type = None
		class_name = None
		jira_issue = None
		deploy_type_allowed = ['beta', 'prod']

		#Package
		package_name = None
		package_ensure = None

		#JIRA
		jira_server=config.get('jira', 'server')
		jira_user=config.get('jira', 'user')
		jira_password=config.get('jira', 'password')
		jira_add_comment=config.getboolean('jira', 'add_comment')
		jira_expected_status=config.get('jira', 'expected_status')
		jira_transitions = []

		jira_success_transitions = {
			'prod': config.get('jira', 'success.prod.deploy.transitions'),
			'beta':	config.get('jira', 'success.beta.deploy.transitions')
		}

		#Logging
		log_level = ['INFO', config.get('global', 'log.level')][config.get('global', 'log.level') != '']
		log_file = ['deployer.log', config.get('global', 'log.file')][config.get('global', 'log.file') != '']
		log_format = '%(asctime)-15s %(levelname)-7s [%(threadName)-10s] (%(module)s::%(funcName)s) [L:%(lineno)d] %(message)s'
		log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
	except ConfigParser.NoOptionError as e:
		print e
		sys.exit(1)
	except Exception as e:
		print e
		sys.exit(1)

params = my_params()

def parse_args():
	parser = argparse.ArgumentParser(description="deployer " + __version__ + "", version="%(prog)s " + __version__)
	parser.add_argument('-p', '--project', help='project name', required=True)	
	parser.add_argument('-i', '--jira-issue', help='JIRA update issue', required=True)
	parser.add_argument('-d', '--deploy-type', help='Type of deploy process, ex. beta or prod', required=True)

	args = parser.parse_args()

	# check for required parameters
	if args.project not in params.deploy_project:
		raise SyntaxError("Given project name is not in configuration file.")
	else:
		params.project = args.project

	if args.deploy_type not in params.deploy_type_allowed:
		raise SyntaxError("Given deploy type doesn't match. You type 'beta' or 'prod'")
	else:
		params.deploy_type = args.deploy_type

	params.jira_issue=args.jira_issue

	jira= JIRA(basic_auth=(params.jira_user, params.jira_password), options={'server': params.jira_server})
	issue= jira.issue(params.jira_issue)

	if str(issue.fields.status) !=  params.jira_expected_status:
		raise SyntaxError("Issue %s has not '%s' status. Current status is '%s'" % 
			(params.jira_issue, params.jira_expected_status, issue.fields.status))
	else:
		transitions = jira.transitions(params.jira_issue)
		params.jira_transitions=transitions


	#Set params
	try: 
		params.package_name = config.get(params.project, 'package.%s' % params.deploy_type)
		params.package_ensure = config.get(params.project, 'package.%s.ensure' % params.deploy_type)
		params.class_name = config.get(params.project, 'class.%s' % params.deploy_type)
		params.nrpe_command = config.get(params.project, 'nrpe.%s.command' % params.deploy_type)
	except Exception as e:
		print "Error parsing configuration file: %s" % (e)
		sys.exit(1)
	
	

def setup_logging():
	logging.basicConfig(format=params.log_format, filename=params.log_file)
	l.setLevel(logging.__dict__["_levelNames"][params.log_level])
