import boto3

sqs = boto3.resource("sqs")
queue = sqs.get_queue_by_name(QueueName="neardata_queue")

queue.send_message(MessageBody="SRR11858779")
