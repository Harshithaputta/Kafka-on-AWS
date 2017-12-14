# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import boto3


################################################################################
# functions: sqs
################################################################################
class RegisterQueue:
    def __init__(self, ru, region, url):
        self.ru = ru
        self.region = region
        self.url = url
        self.sqs_resource = boto3.Session(region_name=region).resource('sqs')
        self.sqs_queue = self.sqs_resource.Queue(url)

    def get_hostnames(self, total):
        """ Get hostnames from SQS queue

        :param total: total expected hostnames in the queue
        :return: sorted list of hostnames
        """
        hosts_online = set()

        while len(hosts_online) < total:
            messages = self.sqs_queue.receive_messages(
                AttributeNames=['All'],
                MaxNumberOfMessages=5,
                VisibilityTimeout=1,
                WaitTimeSeconds=5
            )
            for message in messages:
                hosts_online.add(message.body)
            self.ru.log.info("_get_hostnames(): total for {}:{} {}".format(self.sqs_queue.url.split('/')[-1], len(hosts_online), hosts_online))
            self.ru.loop_sleep(3)

        return sorted(hosts_online)

    def send_hostname(self, hostname):
        """ Send hostname to SQS queue for registration

        :param sqs_queue: SQS queue object
        :param hostname: hostname to be sent
        :return:
        """
        response = self.sqs_queue.send_message(
            MessageBody=hostname,
            DelaySeconds=0
        )
        self.ru.log.info("_send_hostname(): sending hostname {} to {}: {}".format(hostname, self.sqs_queue.url.split('/')[-1], response['ResponseMetadata']['HTTPStatusCode']))
        return response

    def process_hosts(self, hosts_s3, hosts_queue):
        """ Perform logic to discern the state of hosts in the zookeeper ensemble

        :param hosts_s3: list of hosts in the S3 connection file
        :param hosts_queue: list of hosts in the SQS queue
        :return: different lists of hosts, based on status
        """
        self.ru.log.info("_process_hosts(): s3 list: {}".format(hosts_s3))
        self.ru.log.info("_process_hosts(): sqs list: {}".format(hosts_queue))
        if len(hosts_s3) == 0:
            hosts_existing = sorted(hosts_queue)
            hosts_replaced = []
            hosts_new = hosts_existing
            hosts_final = hosts_existing
        else:
            hosts_existing = sorted(list(set(hosts_s3).intersection(set(hosts_queue))))
            hosts_replaced = sorted(list(set(hosts_s3).difference(set(hosts_queue))))
            hosts_new = sorted(list(set(hosts_queue).difference(set(hosts_s3))))
            hosts_final = list(hosts_s3)
        for host in hosts_replaced:
            index_s3 = hosts_s3.index(host)
            index_replaced = hosts_replaced.index(host)
            replacement = hosts_new[index_replaced]
            self.ru.log.info("_process_hosts(): replacing {} at index {} with {}".format(host, index_s3, replacement))
            hosts_final[index_s3] = replacement
        return hosts_final, hosts_replaced, hosts_existing, hosts_new

