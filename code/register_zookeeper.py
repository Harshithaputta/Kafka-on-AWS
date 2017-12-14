# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import os

from register_asg import RegisterASG
from register_ec2 import RegisterEC2
from register_file import RegisterFile
from register_queue import RegisterQueue
from register_util import RegisterUtil


################################################################################
# functions: main
################################################################################
def main():
    my_basedir = os.path.dirname(os.path.realpath(__file__)).replace('/bin', '')
    my_util = RegisterUtil("register_zookeeper", "{}/log".format(my_basedir))
    my_util.log.info("register_zookeeper: beginning registration process")
    my_util.log.info("register_zookeeper: using basedir={}".format(my_basedir))

    # my_hostname = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/hostname")
    my_hostname = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/local-ipv4")
    my_region = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\\" '{{print $4}}'")
    my_util.log.info("register_zookeeper: hostname {}".format(my_hostname))
    my_util.log.info("register_zookeeper: region {}".format(my_region))
    my_asg = RegisterASG(my_util, my_region)
    asg_name = my_asg.get_asg_name()
    asg_desired_cap = my_asg.get_desired_capacity(asg_name)
    asg_elb = my_asg.get_asg_elbs(asg_name)
    my_util.log.info("register_zookeeper: instance is part of asg {}".format(asg_name))
    my_util.log.info("register_zookeeper: asg desired capacity is currently {}".format(asg_desired_cap))
    my_util.log.info("register_zookeeper: asg is behind elb {}".format(asg_elb))

    my_file = RegisterFile(my_util, my_region, my_basedir)
    params = my_file.process_conf("{}/etc/register_zookeeper.conf".format(my_basedir))
    my_file.set_bucket_name(params['s3_bucket'])
    my_file.set_config_zook(params['cfg_zookeeper'])

    my_queue_zook = RegisterQueue(my_util, my_region, params['sqs_url_zook'])
    my_queue_replace = RegisterQueue(my_util, my_region, params['sqs_url_replace'])

    firstrun = my_file.get_zookeeper_firstrun()
    my_util.log.info("register_zookeeper: firstrun: {}".format(firstrun))

    # get register_zookeeper.connection file
    hosts_s3 = my_file.get_connection_file()

    # if connection file exists, ensemble has already been stood up, thus this launch is a replacement
    # therefore, this instance must initialize but also tell other instances to perform replacement
    # achieved by setting state flag to 1, service_register_zookeeper.py listens for this state change
    # state = 0, brand new cluster build
    # state = 1, existing cluster, failure replacement
    my_util.log.info("register_zookeeper: remote execution check: {}, {}".format(firstrun, len(hosts_s3)))
    if firstrun == '1' and len(hosts_s3) > 0:
        my_file.write_zookeeper_state('1')

    # send my hostname to the queue
    my_queue_zook.send_hostname(my_hostname)

    # get online instances that registered to the sqs queue, will wait until param_total hosts are in the queue
    hosts_queue = my_queue_zook.get_hostnames(asg_desired_cap)

    # determine proper server list identities
    hosts_final, hosts_replaced, hosts_existing, hosts_new = my_queue_zook.process_hosts(hosts_s3, hosts_queue)
    my_util.log.info("register_zookeeper: master list: {}".format(hosts_final))
    my_util.log.info("register_zookeeper: existing hosts: {}".format(hosts_existing))
    my_util.log.info("register_zookeeper: replaced hosts: {}".format(hosts_replaced))
    my_util.log.info("register_zookeeper: new hosts: {}".format(hosts_new))

    if firstrun == '1':
        # scenario: brand new instantiation
        # set firstrun to '0'
        my_file.write_zookeeper_firstrun('0')

        # write new entries to zookeeper properties
        my_file.write_zookeeper_properties(hosts_final)

        # get myid from the final list and write myid file
        my_file.write_zookeeper_id(hosts_final.index(my_hostname)+1)

        # need to wait for other replacement hosts to complete their replace process
        # the following statement sets a condition to wait for the _replace_zookeeper_property() function to complete
        if len(hosts_replaced) > 0:
            hosts_completed = my_queue_replace.get_hostnames(len(hosts_s3)-len(hosts_replaced))
            my_util.log.info("register_zookeeper: hosts that completed replacement: {}".format(len(hosts_completed)))

        # write a connection string to a temp file and upload to S3
        my_file.write_connection_file(hosts_final)

        # set state to 0 now that all hosts are configured
        # state = 0, cluster is healthy
        # state = 1, cluster requires replacement
        my_file.write_zookeeper_state('0')
    else:
        # replace failed entries in zookeeper properties
        for host in hosts_replaced:
            my_file.replace_zookeeper_property(host, hosts_new[hosts_replaced.index(host)])
            my_queue_replace.send_hostname(my_hostname)

        my_util.set_cmd_restart_zook(params['cmd_restart_zook'])
        my_util.restart_zookeeper()

    my_iid = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/instance-id")
    my_zid = my_file.get_zookeeper_id()
    my_ec2 = RegisterEC2(my_util, my_region)
    result = my_ec2.add_tag(my_iid, 'KafkaId', my_zid)
    if result == 200:
        for tag in my_ec2.describe_tags(my_iid):
            if tag['Key'] == 'KafkaId':
                my_util.log.info("register_zookeeper: tag {}".format(tag))


if __name__ == "__main__":
    main()
