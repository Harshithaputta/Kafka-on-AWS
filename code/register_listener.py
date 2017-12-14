# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import os
import os.path

from register_file import RegisterFile
from register_util import RegisterUtil


################################################################################
# functions: main
################################################################################
def main():
    my_basedir = os.path.dirname(os.path.realpath(__file__)).replace('/bin', '')
    my_util = RegisterUtil("register_zookeeper", "{}/log".format(my_basedir))
    my_util.log.info("service_register_zookeeper: starting registration service")

    my_region = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\\" '{print $4}'")
    my_file = RegisterFile(my_util, my_region, my_basedir)
    params = my_file.process_conf("{}/etc/register_zookeeper.conf".format(my_basedir))
    my_file.set_bucket_name(params['s3_bucket'])

    while 1:
        state = my_file.get_zookeeper_state()
        my_util.log.info("service_register_zookeeper: state {}".format(state))
        if state == "1":
            command_shell = "python {}/bin/register_zookeeper.py".format(my_basedir)
            my_util.exec_shell_command(command_shell)
        my_util.loop_sleep(120)


if __name__ == "__main__":
    main()
