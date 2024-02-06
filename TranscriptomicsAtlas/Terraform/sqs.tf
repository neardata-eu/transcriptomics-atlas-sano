resource "aws_sqs_queue" "Salmon_queue" {
  name                       = "Salmon_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 18000

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.Salmon_deadletter_queue.arn
    maxReceiveCount     = 1
  })
}

resource "aws_sqs_queue" "Salmon_deadletter_queue" {
  name                       = "Salmon_deadletter_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 10800
}

resource "aws_sqs_queue" "Salmon_queue_hpc" {
  name                       = "Salmon_queue_hpc"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 18000

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.Salmon_deadletter_queue_hpc.arn
    maxReceiveCount     = 1
  })
}

resource "aws_sqs_queue" "Salmon_deadletter_queue_hpc" {
  name                       = "Salmon_deadletter_queue_hpc"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 10800
}

resource "aws_sqs_queue" "STAR_queue" {
  name                       = "STAR_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 36000

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.STAR_deadletter_queue.arn
    maxReceiveCount     = 1
  })
}

resource "aws_sqs_queue" "STAR_deadletter_queue" {
  name                       = "STAR_deadletter_queue"
  max_message_size           = 2048
  message_retention_seconds  = 604800
  receive_wait_time_seconds  = 5
  visibility_timeout_seconds = 36000
}