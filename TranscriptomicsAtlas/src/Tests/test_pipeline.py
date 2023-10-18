import boto3
from moto import mock_sqs, mock_dynamodb, mock_s3, mock_logs

from consumer import start_pipeline


@mock_s3
@mock_sqs
@mock_logs
@mock_dynamodb
def test_pipeline():
    ## CREATE BUCKETS
    s3 = boto3.resource("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="neardata-salmon-ec2-results")
    s3.create_bucket(Bucket="neardata-salmon-ec2-results-low-mr")

    ## CREATE SQS QUEUE
    queue_name = "NearData_queue"
    sqs = boto3.resource("sqs", region_name="us-east-1")
    sqs.create_queue(QueueName=queue_name)
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    tissue_name = "kidney_cells"
    srr_id = "SRR13210228"
    ## SEND MESSAGES
    messages = [f"{tissue_name}-{srr_id}"]
    entries = [{"Id": srr_id, "MessageBody": srr_id} for srr_id in messages]
    queue.send_messages(Entries=entries)

    ## CREATE DYNAMODB TABLE
    dynamodb_resource = boto3.resource('dynamodb', region_name="us-east-1")
    table_name = "neardata-test-table"
    table = dynamodb_resource.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'SRR_id',
                'KeyType': 'HASH'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'SRR_id',
                'AttributeType': 'S'
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    ## START PIPELINE
    start_pipeline(mode="job")

    ## CHECK S3 AND DYNAMODB
    s3.Object("neardata-salmon-ec2-results-low-mr", f"{tissue_name}/{srr_id}_normalized_counts.txt").load()
    assert "Item" in table.get_item(Key={"SRR_id": srr_id})
    print(table.get_item(Key={"SRR_id": srr_id}))


test_pipeline()
