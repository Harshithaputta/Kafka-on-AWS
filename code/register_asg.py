# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import boto3


################################################################################
# functions: asg
################################################################################
class RegisterASG:
    def __init__(self, ru, region):
        self.ru = ru
        self.region = region
        self.asg_client = boto3.Session(region_name=region).client('autoscaling')
        self.elb_client = boto3.Session(region_name=region).client('elb')

    def get_asg_name(self):
        instance_id = self.ru.exec_shell_command("curl -s http://169.254.169.254/latest/meta-data/instance-id")
        response = self.asg_client.describe_auto_scaling_groups()
        for record in response['AutoScalingGroups']:
            instances = record['Instances']
            for instance in instances:
                # print "{}: {}".format(record['AutoScalingGroupName'], instance['InstanceId'])
                if instance_id == instance['InstanceId']:
                    return record['AutoScalingGroupName']
        return "n/a"

    def get_desired_capacity(self, asg_name):
        response = self.asg_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[
                asg_name
            ]
        )
        if len(response['AutoScalingGroups']) == 1:
            return response['AutoScalingGroups'][0]['DesiredCapacity']
        else:
            return -1

    def get_asg_elbs(self, asg_name):
        elbs = list()
        response = self.asg_client.describe_auto_scaling_groups()
        for record in response['AutoScalingGroups']:
            if asg_name == record['AutoScalingGroupName']:
                response2 = self.elb_client.describe_load_balancers(
                    LoadBalancerNames=record['LoadBalancerNames']
                )
                for record2 in response2['LoadBalancerDescriptions']:
                    elbs.append(record2['DNSName'])
        return elbs
