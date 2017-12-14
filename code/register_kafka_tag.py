import os

from register_ec2 import RegisterEC2
from register_file import RegisterFile
from register_util import RegisterUtil

my_basedir = os.path.dirname(os.path.realpath(__file__)).replace('/bin', '')
my_util = RegisterUtil("register_kafka", "{}/log".format(my_basedir))
my_hostname = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/local-ipv4")
my_region = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\\" '{{print $4}}'")
my_iid = my_util.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/instance-id")
my_file = RegisterFile(my_util, my_region, my_basedir)
params = my_file.process_conf("{}/etc/register_kafka.conf".format(my_basedir))
my_file.set_config_brok(params['cfg_broker'])
my_bid = my_file.get_broker_id()
my_ec2 = RegisterEC2(my_util, my_region)
result = my_ec2.add_tag(my_iid, 'ApacheId', my_bid)
if result == 200:
    for tag in my_ec2.describe_tags(my_iid):
        if tag['Key'] == 'ApacheId':
            my_util.log.info("register_kafka_tag: tag {}".format(tag))
