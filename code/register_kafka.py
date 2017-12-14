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
    my_util = RegisterUtil("register_kafka", "{}/log".format(my_basedir))
    my_util.log.info("register_kafka: beginning registration process")
    my_util.log.info("register_kafka: using basedir={}".format(my_basedir))

    # my_hostname = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/hostname")
    my_hostname = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/local-ipv4")
    my_region = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\\" '{{print $4}}'")
    my_util.log.info("register_zookeeper: hostname {}".format(my_hostname))
    my_util.log.info("register_zookeeper: region {}".format(my_region))
    my_asg = RegisterASG(my_util, my_region)
    asg_name = my_asg.get_asg_name()
    asg_desired_cap = my_asg.get_desired_capacity(asg_name)
    asg_elb = my_asg.get_asg_elbs(asg_name)
    my_util.log.info("register_kafka: instance is part of asg {}".format(asg_name))
    my_util.log.info("register_kafka: asg desired capacity is currently {}".format(asg_desired_cap))
    my_util.log.info("register_kafka: asg is behind elb {}".format(asg_elb))

    my_file = RegisterFile(my_util, my_region, my_basedir)
    params = my_file.process_conf("{}/etc/register_kafka.conf".format(my_basedir))
    my_file.set_bucket_name(params['s3_bucket'])
    my_file.set_config_brok(params['cfg_broker'])

    my_queue_brok = RegisterQueue(my_util, my_region, params['sqs_url_brok'])

    my_util.set_cmd_restart_brok(params['cmd_restart_brok'])
    cmd_brokids = '{} {}:2181 <<< "ls /brokers/ids" | grep "\["'.format(params['zookshell'], params['zookeeper'])

    # state = 0, brand new cluster build
    # state = 1, existing cluster or failure replacement
    state = my_file.get_broker_state()
    firstrun = my_file.get_broker_firstrun()
    my_util.log.info("register_kafka: firstrun: {}".format(firstrun))
    my_util.log.info("register_kafka: state: {}".format(state))
    if firstrun == '1' and state == '0':
        # scenario: brand new instantiation
        # need to send to broker queue
        my_queue_brok.send_hostname(my_hostname)

        # need to wait on broker queue
        hosts_queue = my_queue_brok.get_hostnames(asg_desired_cap)
        my_util.log.info("register_kafka: got {} hosts from queue".format(len(hosts_queue)))

        # write a ids string to a temp file and upload to S3
        # note: setting first = 1001 is the default value for reserved.broker.id.max+1
        first = int(params['broker_start'])
        ids_init = range(first, first + int(asg_desired_cap))
        my_file.write_ids_file(ids_init)

        # write not first run locally
        my_file.write_broker_firstrun('0')

        # write not first run s3/globally
        my_file.write_broker_state('1')
    elif firstrun == '1' and state == '1':
        # scenario: replacement
        # need to first get active broker.ids
        result = my_util.exec_shell_command(cmd_brokids).translate(None, '[]').translate(None, ' ')
        my_util.log.info("register_kafka: result: {}".format(result))
        ids_active = sorted(result.split(","))
        ids_active = [int(ident) for ident in ids_active]
        my_util.log.info("register_kafka: active ids: {}".format(ids_active))

        # need to discover bad.broker.id
        # no longer programmatically generating ids_all but getting it from s3 now
        # ids_all = range(ids_active[0], ids_active[0] + int(asg_desired_cap))
        ids_all = my_file.get_ids_file()
        ids_all = [int(ident) for ident in ids_all]
        # need to handle failure + change in asg_desired_cap
        if len(ids_all) != int(asg_desired_cap):
            for add_id in range(1, int(asg_desired_cap) - len(ids_all)):
                ids_all.append(ids_active[-1] + add_id)
        my_util.log.info("register_kafka: all ids: {}".format(ids_all))
        ids_missing = sorted(list(set(ids_all).difference(set(ids_active))))
        my_util.log.info("register_kafka: missing ids: {}".format(ids_missing))

        # setup puppet managed config file
        my_file.init_broker_config()

        # need to append the appropriate broker.id
        # need to disable auto gen id
        if len(ids_missing) > 0:
            my_file.fix_broker_id(ids_missing[0])

    # this code needs to be executed after kafka starts, hence needs to be a separate python script
    # my_iid = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/instance-id")
    # my_bid = my_file.get_broker_id()
    # my_ec2 = RegisterEC2(my_util, my_region)
    # result = my_ec2.add_tag(my_iid, 'KafkaId', my_bid)
    # if result == 200:
    #     for tag in my_ec2.describe_tags(my_iid):
    #         if tag['Key'] == 'KafkaId':
    #             my_util.log.info("register_kafka: tag {}".format(tag))


if __name__ == "__main__":
    main()
