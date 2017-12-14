# (c) 2017 Amazon Web Services, Inc., its affiliates, or
# licensors. All Rights Reserved. This Content is provided subject to
# the terms of the AWS Customer Agreement available at
# http://aws.amazon.com/agreement or other written agreement between
# Customer and Amazon Web Services, Inc.
import boto3


################################################################################
# functions: ec2
################################################################################
class RegisterEC2:
    def __init__(self, ru, region):
        self.ru = ru
        self.region = region
        self.ec2_client = boto3.Session(region_name=region).client('ec2')

    def add_tag(self, instance, key, value):
        response = self.ec2_client.create_tags(
            Resources=[
                instance
            ],
            Tags=[
                {
                    'Key': key,
                    'Value': value
                }
            ]
        )
        return response['ResponseMetadata']['HTTPStatusCode']

    def describe_tags(self, instance):
        response = self.ec2_client.describe_tags(
            Filters=[
                {
                    'Name': 'resource-id',
                    'Values': [
                        instance
                    ]
                }
            ]
        )
        return response['Tags']
