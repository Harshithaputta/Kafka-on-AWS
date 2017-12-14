# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import boto3
import botocore
import copy


################################################################################
# functions: route 53
################################################################################
class RegisterRoute53:
    def __init__(self, ru, zoneid):
        self.ru = ru
        self.zoneid = zoneid
        self.client = boto3.client('route53')

    def update_route53(self, cname, hosts, action):
        """ Update Route 53 CNAMES for zookeeper instances

        :param cname: DNS hostname for CNAME record
        :param hosts: list of hosts that will be attached to that DNS hostname
        :param action: INSERT, DELETE, UPSERT
        :return:
        """
        changes = {
            "Comment": "Update DNS alias",
            "Changes": [
            ]
        }
        change = {
            "Action": action,
            "ResourceRecordSet": {
                "Name": "zookeeper.higlandia.com.",
                "Type": "CNAME",
                "SetIdentifier": "tbd",
                "Weight": 1,
                "TTL": 300,
                "ResourceRecords": [
                ]
            }
        }

        for host in hosts:
            change_i = copy.deepcopy(change)
            item = dict()
            item["Value"] = host
            change_i["ResourceRecordSet"]["Name"] = cname
            change_i["ResourceRecordSet"]["SetIdentifier"] = host
            change_i["ResourceRecordSet"]["ResourceRecords"].append(item)
            changes['Changes'].append(change_i)
            self.ru.log.info("_update_route53(): processing {} on {}".format(action, cname))

        try:
            if len(changes["Changes"]) > 0:
                response = self.client.change_resource_record_sets(
                    HostedZoneId=self.zoneid,
                    ChangeBatch=changes)
                change_id = response['ChangeInfo']['Id']
                self.ru.log.info("_update_route53(): update status: {}".format(response['ResponseMetadata']['HTTPStatusCode']))
                self.ru.log.info("_update_route53(): checking change id: {}".format(change_id))
                waiter = self.client.get_waiter('resource_record_sets_changed')
                self.ru.log.info("_update_route53(): waiting for update to complete")
                waiter.wait(Id=change_id)
            else:
                self.ru.log.info("_update_route53(): no changes needed")
        except botocore.exceptions.ClientError as e:
            self.ru.log.info("_update_route53(): {}".format(e))

