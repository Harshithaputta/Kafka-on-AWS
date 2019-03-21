# Project Overview
This repository contains code necessary for deploying a highly available and fault tolerant Apache Zookeeper ensemble and Apache Kafka cluster. The Cloudformation templates are as follows:


* templates/zookeeper_master.yaml
* templates/kafka_master.yaml

Each of those Cloudformation templates has an associated parameters configuration file.

* templates/zookeeper_config.json
* templates/kafka_config.json

## Zookeeper Deployment
The first thing we need to do is update the template/zookeeper_config.json file.

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
