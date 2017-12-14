# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import getopt
import logging
import subprocess
import sys
import time

from logging.handlers import TimedRotatingFileHandler
from logging.handlers import SysLogHandler


################################################################################
# functions: util
################################################################################
class RegisterUtil:
    # TODO: replace with configuration value
    cmd_restart_zook = "service zookeeper restart"
    cmd_restart_brok = "service broker restart"

    def __init__(self, name, logdir="/var/log"):
        self.name = name
        self.logdir = logdir
        self.log = self.get_logger()

    ################################################################################
    # functions: setters
    ################################################################################
    def set_cmd_restart_zook(self, cmd):
        self.cmd_restart_zook = cmd

    def set_cmd_restart_brok(self, cmd):
        self.cmd_restart_brok = cmd

    ################################################################################
    # functions: general
    ################################################################################
    def get_logger(self):
        """ Get a logging object

        :return: logging object
        """
        _log = logging.getLogger(self.name)
        log_formatter = logging.Formatter("%(asctime)s %(name)s: %(levelname)s '%(message)s'")
        syslog_formatter = logging.Formatter("%(name)s: %(levelname)s '%(message)s'")

        # regular log files
        log_path = "{}/{}.log".format(self.logdir, self.name)
        handler_file = logging.FileHandler(log_path)
        handler_file.setFormatter(log_formatter)

        # rotating log files
        # enable_compression = False
        # if enable_compression:
        #     log_path = "{}/{}.log.bz2".format(self.logdir, self.name)
        #     # handler_timed = TimedRotatingFileHandler(log_path, when="D", interval=1, backupCount=7, encoding="bz2")
        #     handler_timed = TimedRotatingFileHandler(log_path, when="midnight", backupCount=7, encoding="bz2")
        # else:
        #     log_path = "{}/{}.log".format(self.logdir, self.name)
        #     # handler_timed = TimedRotatingFileHandler(log_path, when="D", interval=1, backupCount=7)
        #     handler_timed = TimedRotatingFileHandler(log_path, when="midnight", backupCount=7)
        # handler_timed.setFormatter(log_formatter)

        # syslog files
        # note address=('localhost', 514) did not work, as syslog was not listening actively on 514
        handler_syslog = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_LOCAL0)
        handler_syslog.setFormatter(syslog_formatter)

        # log to console
        handler_console = logging.StreamHandler()
        handler_console.setFormatter(log_formatter)

        _log.setLevel(logging.INFO)
        if len(_log.handlers) == 0:
            _log.addHandler(handler_file)
            # _log.addHandler(handler_timed)
            _log.addHandler(handler_syslog)
            _log.addHandler(handler_console)

        return _log

    def usage(self):
        """ Print usage pattern

        :return:
        """
        self.log.error("register_*.py:")
        self.log.error("\t--hostname=[name]")
        self.log.error("\t--total=[count]")
        self.log.error("\t--region=[us-east-1]")
        self.log.error("\t--bucket=[name]")
        self.log.error("\t--zookeeper=[name]")
        self.log.error("\t--queue_host=[http://sqs.us-east-1.amazonaws.com/accountid/queuename]")
        self.log.error("\t--queue_replace=[http://sqs.us-east-1.amazonaws.com/accountid/queuename]")

    def process_opts(self, argv):
        """ Process command line arguments

        :param argv: list of arguments
        :return: dictionary of parameters
        """
        try:
            opts, args = getopt.getopt(argv[1:],
                                       '',
                                       ['hostname=',
                                        'total=',
                                        'region=',
                                        'bucket=',
                                        'zookeeper=',
                                        'queue_host=',
                                        'queue_replace='
                                        ])
        except getopt.GetoptError:
            self.usage()
            sys.exit(2)

        params = {}
        for opt, arg in opts:
            if opt == '--hostname':
                params['hostname'] = arg
            elif opt == '--total':
                params['total'] = int(arg)
            elif opt == '--region':
                params['region'] = arg
            elif opt == '--bucket':
                params['bucket'] = arg
            elif opt == '--zookeeper':
                params['zookeeper'] = arg
            elif opt == '--queue_host':
                params['queue_host'] = arg
            elif opt == '--queue_replace':
                params['queue_replace'] = arg

        for key in params:
            self.log.info("_process_opts(): param --{}={}".format(key, params[key]))

        return params

    ################################################################################
    # functions: execution
    ################################################################################
    def exec_shell_command(self, command, enable_logging=True):
        """ Execute a local shell command

        :param command: string of a command
        :return:
        """
        if enable_logging:
            self.log.info("_exec_shell_command(): running command: {}".format(command.strip()))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0]
        result = output.strip()
        if enable_logging:
            self.log.info("_exec_shell_command(): command output: {}".format(result))
        return result

    def exec_remote_command(self, command):
        self.log.info("_exec_remote_command(): running remote command: {}".format(command))

    def loop_sleep(self, seconds):
        """ Sleep function

        :param seconds:
        :return:
        """
        self.log.info("_loop_sleep(): sleeping for {} seconds".format(seconds))
        time.sleep(seconds)

    ################################################################################
    # functions: execution: zookeeper
    ################################################################################
    def restart_zookeeper(self):
        """ Restart the zookeeper service

        :return:
        """
        self.exec_shell_command(self.cmd_restart_zook)
        self.log.info("_restart_zookeeper(): restarted zookeeper")

    ################################################################################
    # functions: execution: broker
    ################################################################################
    def restart_broker(self):
        """ Restart the broker service

        :return:
        """
        self.exec_shell_command(self.cmd_restart_brok)
        self.log.info("_restart_broker(): restarted broker")

