resource "aws_sqs_queue" "NearData_queue" {
  name                       = "NearData_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 18000

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.NearData_deadletter_queue.arn
    maxReceiveCount     = 1
  })
}

resource "aws_sqs_queue" "NearData_deadletter_queue" {
  name                       = "NearData_deadletter_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 10800
}
