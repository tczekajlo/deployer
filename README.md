# deployer
Deployer is wrapper on MCollective which manages package deploy. 

# Requires
	* Python >=2.6<3.0
	* PLY module for Python
	* Pexpect module for Python
	* JIRA module for Python (http://jira-python.readthedocs.org/)
	* MCollective with puppet-agent, nrpe and service plugins

# Configuration
Configuration file is deployer.cfg. There you can also configure access to JIRA. 

	#project name
	[test-package]
	package.beta = test-package-beta
	package.prod = test-package

	#default version package to be installed
	package.beta.ensure = latest
	package.prod.ensure = latest

	#name of puppet classes which define nodes group
	class.beta = deploy::test_package::beta
	class.prod = deploy::test_package::prod

	#NRPE command uses to service check
	nrpe.prod.command = check_test_procs
	nrpe.beta.command = check_test_procs_beta

# Usage
	-h, --help            show this help message and exit
	-v, --version         show program's version number and exit
	-p PROJECT, --project PROJECT
                        project name
	-i JIRA_ISSUE, --jira-issue JIRA_ISSUE
                        JIRA update issue
	-d DEPLOY_TYPE, --deploy-type DEPLOY_TYPE
                        Type of deploy process, ex. beta or prod

### Available commands

	deploy     : Install package on all nodes 
	help       : Print this help 
	nodes      : Display list of all nodes for which wll be done deploy 
	puppet     : Re-run puppet agent 
	quit       : Kill 'Em All. 
	service    : Manages system services 
	set        : Show/set variables (set PARAMETER VALUE) 
	status     : Check status of package, service or nrpe

### Command usage

#### deploy
	deploy [hosts_group]

for example:

	deploy (deploy::test_package::beta::cluster_a and virtual=physical)

If you don't specify a hosts group, package will be installed on nodes included class from class.* option in configuration file.
You can type *set* command to display current settings for deploy.

#### service
	service start|stop|restart|status [hosts_group]

#### status
	status package|service|nrpe [hosts_group] [add_comment]

for example, display version of current installed package and add output as JIRA comment.
	
	status package add_comment

# Examples of use
### Check list of nodes
	deployer> nodes
	test-nodex.domain.name

	deployer> nodes (virtual=physical and processorcount=8)
	test-nodex.domain.name

You can use filter for each command. Syntax is the same like in MCollective for "-S" argument. 

### Deploy package
	~ # deployer --project test-package --jira-issue UPD-1 --deploy-type beta
  	   _            _                      
	  __| | ___ _ __ | | ___  _   _  ___ _ __
	 / _` |/ _ \ '_ \| |/ _ \| | | |/ _ \ '__|
	| (_| |  __/ |_) | | (_) | |_| |  __/ |  
	 \__,_|\___| .__/|_|\___/ \__, |\___|_|v0.1.0... shit happens :)  
	          |_|            |___/
	 I'm ready!
	
	deployer> deploy
 	I'll install package with following parameters:
 	Project            		 : test-package
 	Deploy type            : beta
 	Package ensure         : latest
 	Package name           : test-package-beta
 	Puppet class           : deploy::test_package::beta
	JIRA update issue      : UPD-1
	JIRA add comment       : true

	 Are you sure? (y/N):
	> y
		* [ ============================================================> ] 1 / 1

	test-nodex.domain.name               
			Changed: true
    	Result: ensure changed 'purged' to 'latest'

	Summary of Changed:
			Changed = 1

	Finished processing 1 / 1 hosts in 4843.59 ms
	Adding JIRA comment...
	Done.
	deployer>

## Service status in Nagios
	deployer> status nrpe
		* [ ============================================================> ] 1 / 1
	Summary of Exit Code:
	OK : 1
    	CRITICAL : 0
      	WARNING : 0
      	UNKNOWN : 0

	Finished processing 1 / 1 hosts in 44.72 ms

