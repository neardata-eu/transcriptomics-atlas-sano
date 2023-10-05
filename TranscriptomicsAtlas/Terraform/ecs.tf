resource "aws_ecs_cluster" "NearData_cluster" {
  name = "NearData_cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_ecs_task_definition" "NearData_task_definition" {
  container_definitions = jsonencode([
    {
      essential : true,
      image : "542811361644.dkr.ecr.us-east-1.amazonaws.com/neardata_registry:salmon_pipeline",
      environment : [
        { "name" : "execution_mode", "value" : "Fargate" }
      ]
      name : "SalmonPipeline_container",
      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-create-group" : "true",
          "awslogs-group" : "/ecs/NearData_SalmonPipeline",
          "awslogs-region" : "us-east-1",
          "awslogs-stream-prefix" : "ecs"
        },
        "secretOptions" : []
      },
      healthCheck : {
        "command" : [
          "CMD-SHELL",
          "pgrep -f 'python3 /opt/TAtlas/container_start.py' || exit 1"
        ],
        "interval" : 15,
        "retries" : 3,
        "timeout" : 5
      }
    }
  ])
  cpu = "2048"

  ephemeral_storage {
    size_in_gib = "200"
  }

  execution_role_arn       = "arn:aws:iam::542811361644:role/ecsTaskExecutionRole"
  family                   = "NearData_SalmonPipeline"
  memory                   = "8192"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  task_role_arn            = "arn:aws:iam::542811361644:role/neardata-ec2-role"
}

#resource "aws_ecs_service" "SalmonPipeline_service" {
#  name                               = "SalmonPipeline"
#  cluster                            = aws_ecs_cluster.NearData_cluster.id
#  task_definition                    = aws_ecs_task_definition.NearData_task_definition.family
#  desired_count                      = 2
#  deployment_minimum_healthy_percent = "0"
#  deployment_maximum_percent         = "100"
#  enable_ecs_managed_tags            = "true"
#  enable_execute_command             = true
#
#  capacity_provider_strategy {
#    capacity_provider = "FARGATE_SPOT"
#    weight = 1
#  }
#
#  network_configuration {
#    subnets          = values(aws_subnet.NearData_Subnets)[*].id
#    security_groups  = [aws_security_group.NearData_sg.id]
#    assign_public_ip = true
#  }
#  deployment_circuit_breaker {
#    enable   = "true"
#    rollback = "true"
#  }
#  platform_version = "LATEST"
#}
