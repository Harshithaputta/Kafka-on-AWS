# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import boto3
import botocore
import os.path
import time


################################################################################
# functions: file
################################################################################
class RegisterFile:
    base_conn_zook = "register_zookeeper.connection"
    s3key_conn_zook = "state/{}".format(base_conn_zook)
    base_ids_brok = "register_broker.ids"
    s3key_ids_brok = "state/{}".format(base_ids_brok)
    base_state_zook = "register_zookeeper.state"
    base_state_brok = "register_broker.state"
    s3key_state_zook = "state/{}".format(base_state_zook)
    s3key_state_brok = "state/{}".format(base_state_brok)

    # these default values will be overwritten by conf file values
    config_zook = "/opt/kafka_2.11-0.11.0.2/config/zookeeper.properties"
    config_brok = "/opt/kafka_2.11-0.11.0.2/config/server.properties"
    bucket_name = "kafka-configurations-1"

    def __init__(self, ru, region, basedir):
        self.ru = ru
        self.region = region
        self.basedir = basedir
        self.local_conn_zook = "{}/tmp/{}".format(self.basedir, self.base_conn_zook)
        self.local_ids_brok = "{}/tmp/{}".format(self.basedir, self.base_ids_brok)
        self.local_state_zook = "{}/tmp/{}".format(self.basedir, self.base_state_zook)
        self.local_state_brok = "{}/tmp/{}".format(self.basedir, self.base_state_brok)
        self.local_firstrun_zook = "{}/tmp/register_zookeeper.firstrun".format(self.basedir)
        self.local_firstrun_brok = "{}/tmp/register_broker.firstrun".format(self.basedir)
        self.s3_client = boto3.Session(region_name=region).client('s3')
        self.s3_resource = boto3.Session(region_name=region).resource('s3')
        self.s3_bucket = self.s3_resource.Bucket(self.bucket_name)


    ################################################################################
    # functions: setters
    ################################################################################
    def set_basedir(self, config):
        self.basedir = config

    def set_config_zook(self, config):
        self.config_zook = config

    def set_config_brok(self, config):
        self.config_brok = config

    def set_config_brok_puppet(self, config):
        self.config_brok_puppet = config

    def set_bucket_name(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3_resource = boto3.Session(region_name=self.region).resource('s3')
        self.s3_bucket = self.s3_resource.Bucket(self.bucket_name)

    ################################################################################
    # functions: general local filesystem functions
    ################################################################################
    def read_file(self, local_file):
        """ Generic function to read data from a file

        :param local_file: local file
        :return:
        """
        with open(local_file, "r") as f:
            self.ru.log.info("_read_file(): reading from {}".format(local_file))
            data = f.read().strip()
        f.close()
        return data

    def write_file(self, local_file, data):
        """ Generic function to write data to a file

        :param local_file: local file
        :param data: data to be written
        :return:
        """
        f = open(local_file, "w+")
        self.ru.log.info("_write_file(): writing to {}: {}".format(local_file, data))
        f.write("{}".format(data))
        f.close()

    def append_file(self, local_file, data):
        """ Generic function to append data to a file

        :param local_file: local file
        :param data: data to be written
        :return:
        """
        f = open(local_file, "a")
        self.ru.log.info("_write_file(): appending to {}: {}".format(local_file, data))
        f.write("\n\n# Broker Identification\n\n{}".format(data))
        f.close()

    def process_conf(self, local_file):
        if os.path.isfile(local_file):
            with open(local_file, "r") as f:
                self.ru.log.info("process_conf: reading from {}".format(local_file))
                data = f.readlines()
            f.close()

            params = dict()
            for line in data:
                if line.startswith('#'):
                    continue
                self.ru.log.info("process_conf: processing {}".format(line.strip()))
                (key, value) = line.strip().split("=")
                params[key] = value

            return params
        else:
            self.ru.log.error("process_conf: error reading from {}".format(local_file))

    ################################################################################
    # functions: general s3 functions
    ################################################################################
    def download_file(self, local_file, key):
        """ Download a file from S3

        :param local_file: target local file location
        :param key: S3 key from which to download
        :return:
        """
        try:
            self.s3_bucket.download_file(key, local_file)
        except botocore.exceptions.ClientError as e:
            self.ru.log.info("_download_file(): {} not found: {}".format(key, e.response['Error']['Code']))

    def upload_file(self, local_file, key):
        """ Upload a file to S3

        :param local_file: target local file location
        :param key: S3 key to which to download
        :return:
        """
        self.ru.log.info("_upload_file(): uploading {} to {}".format(local_file, self.s3_bucket.name))
        self.s3_bucket.upload_file(local_file, key, ExtraArgs={'ServerSideEncryption': 'AES256'})

    ################################################################################
    # functions: zookeeper functions: local filesystem
    ################################################################################
    def get_zookeeper_id(self):
        """ Get the Zookeeper ID from the /dataDir/myid file

        :return: zook_id
        """
        logdir_zook = self.ru.exec_shell_command("grep dataDir {} | awk -F= '{{print $2}}'".format(self.config_zook))
        file_zid = "{}/myid".format(logdir_zook)
        if os.path.isfile(file_zid):
            return self.read_file(file_zid)
        else:
            return "0"

    def write_zookeeper_id(self, zook_id):
        """ Write the Zookeeper ID to the /dataDir/myid file

        :param zook_id: Zookeeper ID for this instance
        :return:
        """
        logdir_zook = self.ru.exec_shell_command("grep dataDir {} | awk -F= '{{print $2}}'".format(self.config_zook))
        self.write_file("{}/myid".format(logdir_zook), zook_id)

    def exists_zookeeper_properties(self, config):
        """ Check if server.X entry already exists
        
        :param config: config to be checked
        :return: True|False
        """
        count = self.ru.exec_shell_command("grep {} {} | wc -l".format(config, self.config_zook))
        if int(count) > 0:
            return True
        else:
            return False

    def write_zookeeper_properties(self, hosts):
        """ Add server.X entries for all the Zookeeper instances

        :param hosts: list of hostnames in the ensemble
        :return:
        """
        f = open(self.config_zook, "a+")
        for host in hosts:
            config = "server.{}={}:2888:3888".format(hosts.index(host) + 1, host)
            if self.exists_zookeeper_properties(config):
                self.ru.log.info("_write_zookeeper_properties(): skipping zookeeper config: {}".format(config))
            else:
                self.ru.log.info("_write_zookeeper_properties(): writing zookeeper config: {}".format(config))
                f.write("{}\n".format(config))
        f.close()

    def replace_zookeeper_property(self, hostname_old, hostname_new):
        """ Replace a server.X entry for a failed Zookeeper instance

        :param hostname_old: old hostname
        :param hostname_new: new hostname
        :return:
        """
        command_replace = "sed -i 's/{}/{}/' {}".format(hostname_old, hostname_new, self.config_zook)
        self.ru.exec_shell_command(command_replace)
        self.ru.log.info("_replace_zookeeper_property(): replaced {} with {}".format(hostname_old, hostname_new))

    ################################################################################
    # functions: zookeeper functions: s3
    ################################################################################
    def get_connection_file(self):
        """ Get connection file from S3 for zookeeper

        :return: list of hosts in the connection file
        """
        hosts = []
        self.download_file(self.local_conn_zook, self.s3key_conn_zook)
        if os.path.isfile(self.local_conn_zook):
            with open(self.local_conn_zook, "r") as f:
                temps = f.read().strip().split(',')
            for temp in temps:
                hosts.append(temp.split(':')[0])
            f.close()
            self.ru.log.info("_get_connection_file(): register_zookeeper.connection hosts in s3: {}".format(hosts))
        return hosts

    def write_connection_file(self, hosts):
        """ Write connection file to be used by the Kafka

        :param hosts: list of hostnames in the ensemble
        :return:
        """
        conn_string = ""
        for host in hosts:
            conn_string += "{}:2181,".format(host)
        conn_string = conn_string[:-1]
        self.write_file(self.local_conn_zook, conn_string)
        self.upload_file(self.local_conn_zook, self.s3key_conn_zook)

    def get_ids_file(self):
        """ Get ids file from S3 for Kafka

        :return: list of ids in the Kafka cluster
        """
        ids = []
        self.download_file(self.local_ids_brok, self.s3key_ids_brok)
        if os.path.isfile(self.local_ids_brok):
            with open(self.local_ids_brok, "r") as f:
                temps = f.read().strip().split(',')
            for temp in temps:
                ids.append(temp.split(':')[0])
            f.close()
            self.ru.log.info("_get_ids_file(): register_broker.ids in s3: {}".format(ids))
        return ids

    def write_ids_file(self, ids):
        """ Write ids file to S3 for Kafka

        :param ids: list of ids in the Kafka cluster
        :return:
        """
        id_string = ""
        for ident in ids:
            id_string += "{},".format(ident)
        id_string = id_string[:-1]
        self.write_file(self.local_ids_brok, id_string)
        self.upload_file(self.local_ids_brok, self.s3key_ids_brok)

    def get_zookeeper_state(self):
        """ Get register_zookeeper.state file

        :return: state in state file
        """
        self.download_file(self.local_state_zook, self.s3key_state_zook)
        if os.path.isfile(self.local_state_zook):
            return self.read_file(self.local_state_zook)
        else:
            return "0"

    def write_zookeeper_state(self, flag):
        """ Write register_zookeeper.state file

        :param flag: 0|1
        :return:
        """
        self.write_file(self.local_state_zook, flag)
        self.upload_file(self.local_state_zook, self.s3key_state_zook)

    def get_zookeeper_firstrun(self):
        """ Get register_zookeeper.firstrun file

        :return: state in firstrun file
        """
        if os.path.isfile(self.local_firstrun_zook):
            return self.read_file(self.local_firstrun_zook)
        else:
            return "1"

    def write_zookeeper_firstrun(self, flag):
        """ Write register_zookeeper.firstrun file

        :param flag: 0|1
        :return:
        """
        self.write_file(self.local_firstrun_zook, flag)

    ################################################################################
    # functions: broker functions: local filesystem
    ################################################################################
    def get_broker_id(self):
        """ Get the broker.id from the /dataDir/myid file

        :return: zook_id
        """
        logdir_brok = self.ru.exec_shell_command("grep log.dirs {} | awk -F= '{{print $2}}'".format(self.config_brok))
        file_bid = "{}/meta.properties".format(logdir_brok)
        in_loop = True
        attempt = 0
        max_retries = 12
        while in_loop:
            if os.path.isfile(file_bid):
                return self.ru.exec_shell_command("grep broker.id {} | awk -F= '{{print $2}}'".format(file_bid))
            else:
                attempt += 1
                if attempt <= max_retries:
                    self.ru.log.info("get_broker_id(): meta.properties does not yet exist, attempt {}, sleeping 5".format(attempt))
                    time.sleep(5)
                else:
                    in_loop = False
                    self.ru.log.info("get_broker_id(): meta.properties does not yet exist, max retries exceeded, failing".format(attempt))
        return "0"

    def fix_broker_id(self, broker_id):
        """ Fix a broker.id entry in a new instance that is replacing a failed instance

        :param broker_id: broker.id
        :return:
        """
        # no longer replacing #broker.id=0, as it doesn't exist in the puppet managed file
        # logdir_brok = self.ru.exec_shell_command("grep log.dirs {} | awk -F= '{{print $2}}'".format(self.config_brok))
        # cmd_replace = "sed -i 's/#broker.id=0/broker.id={}/' {}".format(broker_id, self.config_brok)
        # self.ru.exec_shell_command(cmd_replace)
        # self.ru.log.info("_replace_broker_id(): replaced broker.id with {}".format(broker_id))

        # appending broker.id=[#] to the server.properties file
        new_line = "broker.id={}".format(broker_id)
        self.append_file(self.config_brok, new_line)

        # disable broker.id.generation
        cmd_disable = "sed -i 's/broker.id.generation.enable=true/broker.id.generation.enable=false/' {}".format(self.config_brok)
        self.ru.exec_shell_command(cmd_disable)
        self.ru.log.info("fix_broker_id(): disabled broker.id.generation")


    ################################################################################
    # functions: broker functions: s3
    ################################################################################
    def get_broker_state(self):
        """ Get register_broker.state file

        :return: state in state file
        """
        self.download_file(self.local_state_brok, self.s3key_state_brok)
        if os.path.isfile(self.local_state_brok):
            return self.read_file(self.local_state_brok)
        else:
            return "0"

    def write_broker_state(self, flag):
        """ Write register_broker.state file

        :param flag: 0|1
        :return:
        """
        self.write_file(self.local_state_brok, flag)
        self.upload_file(self.local_state_brok, self.s3key_state_brok)

    def get_broker_firstrun(self):
        """ Get register_broker.firstrun file

        :return: state in firstrun file
        """
        if os.path.isfile(self.local_firstrun_zook):
            return self.read_file(self.local_firstrun_brok)
        else:
            return "1"

    def write_broker_firstrun(self, flag):
        """ Write register_broker.firstrun file

        :param flag: 0|1
        :return:
        """
        self.write_file(self.local_firstrun_brok, flag)