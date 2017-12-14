# Project Overview
This repository contains code necessary for deploying a highly available and fault tolerant Apache Zookeeper ensemble and Apache Kafka cluster. The Cloudformation templates are as follows:

* templates/base_master.yaml
* templates/zookeeper_master.yaml
* templates/kafka_master.yaml

Each of those Cloudformation templates has an associated parameters configuration file.

* templates/base_config.json
* templates/zookeeper_config.json
* templates/kafka_config.json

## Zookeeper Deployment
The first thing we will need to do is setup our template/base_config.json file. The parameters in that file are as follows. Feel free to update these setting as is appropriate.

```
[
  {
    "ParameterKey": "VpcCidrBlock",
    "ParameterValue": "10.20.0.0/16"
  },
  {
    "ParameterKey": "CidrPublic1",
    "ParameterValue": "10.20.10.0/24"
  },
  {
    "ParameterKey": "CidrPublic2",
    "ParameterValue": "10.20.20.0/24"
  },
  {
    "ParameterKey": "CidrPrivate1",
    "ParameterValue": "10.20.30.0/24"
  },
  {
    "ParameterKey": "CidrPrivate2",
    "ParameterValue": "10.20.40.0/24"
  },
  {
    "ParameterKey": "BastInstanceType",
    "ParameterValue": "t2.micro"
  },
  {
    "ParameterKey": "BastKeyName",
    "ParameterValue": "ec2-key-1"
  },
  {
    "ParameterKey": "BastAllowedRangeSSH",
    "ParameterValue": "0.0.0.0/0"
  }
]
```

And now from here, we will execute our first Cloudformation template:

```
aws cloudformation create-stack \
--stack-name zookeeper-on-aws-1 \
--template-body file://templates/base_master.yaml \
--parameters file://templates/base_config.json \
--capabilities CAPABILITY_IAM
```

And you can monitor the status of the stack creation either in the GUI or via the following CLI command. The stack creation should complete roughly in 6-8 minutes.

```
aws cloudformation describe-stacks --stack-name zookeeper-on-aws-1
```

One thing to note from the describe-stacks command is the set of values in the Outputs array. In my case, it looked something like this. We are going to use the following values in the next stack: CoreVpcId="vpc-fab6f182", CoreSubnetPrivate1Id="subnet-a2d078ff", CoreSubnetPrivate2Id="subnet-ab3f40cf".

```
"Outputs": [
    {
        "Description": "Private IP address for Bastion",
        "OutputKey": "BastPrivateIp",
        "OutputValue": "10.20.10.169"
    },
    {
        "Description": "Id of public subnet 2",
        "OutputKey": "CoreSubnetPublic2Id",
        "OutputValue": "subnet-f3394697"
    },
    {
        "Description": "Id of private subnet 2",
        "OutputKey": "CoreSubnetPrivate2Id",
        "OutputValue": "subnet-ab3f40cf"
    },
    {
        "Description": "Id of private subnet 1",
        "OutputKey": "CoreSubnetPrivate1Id",
        "OutputValue": "subnet-a2d078ff"
    },
    {
        "Description": "Public IP address for Bastion",
        "OutputKey": "BastPublicIp",
        "OutputValue": "54.209.68.224"
    },
    {
        "Description": "Public DNS for Bastion",
        "OutputKey": "BastPublicDnsName",
        "OutputValue": "ec2-54-209-68-224.compute-1.amazonaws.com"
    },
    {
        "Description": "Id of the VPC",
        "OutputKey": "CoreVpcId",
        "OutputValue": "vpc-fab6f182"
    },
    {
        "Description": "Id of public subnet 1",
        "OutputKey": "CoreSubnetPublic1Id",
        "OutputValue": "subnet-76ab032b"
    }
]
```

Note that we could have exported these values and then imported them into the next stack, but we did this intentionally to make sure that we are aware of the VPC and private subnets into which we are doing these deployments.

Now that we have the core infrastructure up, we can go ahead and deploy Zookeeper. The first thing we need to do is update the template/zookeeper_config.json file.

```
[
  {
    "ParameterKey": "ZookInstanceType",
    "ParameterValue": "t2.small"
  },
  {
    "ParameterKey": "ZookKeyName",
    "ParameterValue": "enter-your-keyname-here"
  },
  {
    "ParameterKey": "ZookVpcId",
    "ParameterValue": "vpc-fab6f182"
  },
  {
    "ParameterKey": "ZookSubnetIds",
    "ParameterValue": "subnet-a2d078ff, subnet-ab3f40cf"
  },
  {
    "ParameterKey": "ZookDesiredCapacity",
    "ParameterValue": "3"
  },
  {
    "ParameterKey": "ZookDownloadUrl",
    "ParameterValue": "http://apache.osuosl.org/zookeeper/zookeeper-3.4.10/zookeeper-3.4.10.tar.gz"
  },
  {
    "ParameterKey": "ZookAllowedRangeApp",
    "ParameterValue": "0.0.0.0/0"
  },
  {
    "ParameterKey": "ZookAllowedRangeSSH",
    "ParameterValue": "0.0.0.0/0"
  },
  {
    "ParameterKey": "ZookBucketName",
    "ParameterValue": "zookeeper-configurations-1"
  }
]
```

We need to make a few updates to the parameters:

* Update ZookKeyName to the name of your key pair
* Set ZookVpcId to the CoreVpcId value above
* Set ZookSubnetIds to the values of CoreSubnetPrivate1Id and CoreSubnetPrivate2Id above
* Update ZookAllowedRangeApp to an appropriate subnet for applications that will connect to Zookeeper
* Update ZookAllowedRangeSSH to an appropriate subnet for users/admins that need to SSH to Zookeeper instances
* Set ZookBucketName to the name of a bucket that will be created for holding metadata

Once the file is updated, we can execute the template for Zookeeper.

```
aws cloudformation create-stack \
--stack-name zookeeper-on-aws-2 \
--template-body file://templates/zookeeper_master.yaml \
--parameters file://templates/zookeeper_config.json \
--capabilities CAPABILITY_IAM
```

And you can monitor the status of the stack creation either in the GUI or via the following CLI command. The stack creation should complete roughly in 6-8 minutes.

```
aws cloudformation describe-stacks --stack-name zookeeper-on-aws-2
```

At this point, we now have deployed a highly available, fault tolerant Zookeeper ensemble in AWS. For additional information on how to use Zookeeper, see their getting started guide at: https://zookeeper.apache.org/doc/r3.3.3/zookeeperStarted.html.

## Kafka Deployment
The first thing we will need to do is setup our template/base_config.json file. The parameters in that file are as follows. Feel free to update these setting as is appropriate.

```
[
  {
    "ParameterKey": "KafkaInstanceType",
    "ParameterValue": "t2.medium"
  },
  {
    "ParameterKey": "KafkaKeyName",
    "ParameterValue": "enter-your-keyname-here"
  },
  {
    "ParameterKey": "KafkaVpcId",
    "ParameterValue": "vpc-fab6f182"
  },
  {
    "ParameterKey": "KafkaSubnetIds",
    "ParameterValue": "subnet-a2d078ff, subnet-ab3f40cf"
  },
  {
    "ParameterKey": "KafkaDesiredCapacity",
    "ParameterValue": "3"
  },
  {
    "ParameterKey": "KafkaEbsCapacity",
    "ParameterValue": "50"
  },
  {
    "ParameterKey": "KafkaMessageRetention",
    "ParameterValue": "24"
  },
  {
    "ParameterKey": "KafkaBucketName",
    "ParameterValue": "kafka-configurations-1"
  },
  {
    "ParameterKey": "ZookLoadBalancerName",
    "ParameterValue": "internal-zookeeper-ZookLoad-15FAHFOSVU67U-1827209741.us-east-1.elb.amazonaws.com"
  },
  {
    "ParameterKey": "KafkaDownloadUrl",
    "ParameterValue": "http://apache.osuosl.org/zookeeper/zookeeper-3.4.10/zookeeper-3.4.10.tar.gz"
  },
  {
    "ParameterKey": "KafkaAllowedRangeApp",
    "ParameterValue": "0.0.0.0/0"
  },
  {
    "ParameterKey": "KafkaAllowedRangeSSH",
    "ParameterValue": "0.0.0.0/0"
  }
]
```

We need to make a few updates to the parameters:

* Update KafkaKeyName to the name of your key pair
* Set KafkaVpcId to the CoreVpcId value from the previous article in the VPC Cloudformation stack
* Set KafkaSubnetIds to the values of CoreSubnetPrivate1Id and CoreSubnetPrivate2Id from the previous article in the VPC Cloudformation stack
* Set KafkaBucketName to the name of a bucket that will be created for holding metadata
* Set KafkaEbsCapacity to the amount of usable capacity on each instance (depend on message rates, size, and retention)
* Set KafkaMessageRetention to the number of hours to retain message (default is 7 days, we are changing it to 1 day)
* Set ZookLoadBalancerName to the DNS name of the Zookeeper load balancer that we created in the previous article in the Zookeeper Cloudformation stack 
* Update KafkaAllowedRangeApp to an appropriate subnet for applications that will connect to Kafka
* Update KafkaAllowedRangeSSH to an appropriate subnet for users/admins that need to SSH to Kafka instances

Once the file is updated, we can execute the template for Zookeeper.

```
aws cloudformation create-stack \
--stack-name kafka-on-aws-1 \
--template-body file://templates/kafka_master.yaml \
--parameters file://templates/kafka_config.json \
--capabilities CAPABILITY_IAM
```

And you can monitor the status of the stack creation either in the GUI or via the following CLI command. The stack creation should complete roughly in 6-8 minutes.

```
aws cloudformation describe-stacks --stack-name kafka-on-aws-1
```

At this point, we now have deployed a highly available, fault tolerant Kafka cluster in AWS.
