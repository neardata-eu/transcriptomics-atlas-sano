import os
import boto3
import botocore
import requests

if "RUN_IN_CONTAINER" not in os.environ:
    metadata_url = 'http://169.254.169.254/latest/meta-data/'
    os.environ['AWS_DEFAULT_REGION'] = requests.get(metadata_url + 'placement/region').text

from logger import logger  # NOQA

ssm = boto3.client("ssm")
sqs = boto3.resource("sqs")
s3 = boto3.resource('s3')


def check_file_exists(s3_bucket_name, path_to_file):
    try:
        s3.Object(s3_bucket_name, path_to_file).load()
        # return True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != "404":
            logger.warning(e)

    return False


def get_instance_id():
    if "RUN_IN_CONTAINER" not in os.environ:
        instance_id = requests.get(metadata_url + 'instance-id').text
    else:
        instance_id = os.environ["HOSTNAME"]

    return instance_id


def get_ssm_parameter(param_name):
    ssm_param = ssm.get_parameter(Name=param_name, WithDecryption=True)
    param_value = ssm_param['Parameter']['Value']
    return param_value


def get_sqs_queue():
    queue_name = get_ssm_parameter("/neardata/queue_name")
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return queue
