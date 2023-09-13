import os
import boto3
import requests

if "RUN_IN_CONTAINER" not in os.environ:
    metadata_url = 'http://169.254.169.254/latest/meta-data/'
    os.environ['AWS_DEFAULT_REGION'] = requests.get(metadata_url + 'placement/region').text

from logger import logger  # NOQA


def srr_id_in_metadata_table(table, SRR_id):
    if "Item" in table.get_item(Key={"SRR_id": SRR_id}):
        return True
    return False


def get_instance_id():
    if "RUN_IN_CONTAINER" not in os.environ:
        instance_id = requests.get(metadata_url + 'instance-id').text
    else:
        instance_id = os.environ["HOSTNAME"]

    return instance_id


def get_ssm_parameter(param_name):
    ssm = boto3.client("ssm")
    ssm_param = ssm.get_parameter(Name=param_name, WithDecryption=True)
    param_value = ssm_param['Parameter']['Value']
    return param_value


def get_sqs_queue():
    sqs = boto3.resource("sqs")
    if "RUN_IN_CONTAINER" not in os.environ:
        queue_name = get_ssm_parameter("/neardata/queue_name")
    else:
        queue_name = get_ssm_parameter("/neardata/queue_name_container")
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    return queue
