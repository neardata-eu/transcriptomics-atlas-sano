resource "aws_vpc" "NearData_VPC" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {
    Name = "NearData_VPC"
  }

}

variable "subnets" {
  default = {
    "Subnet_1" = {
      "cidr_block"        = "10.0.1.0/24"
      "availability_zone" = "us-east-1a"
    }
    "Subnet_2" = {
      "cidr_block"        = "10.0.2.0/24"
      "availability_zone" = "us-east-1b"
    }
    "Subnet_3" = {
      "cidr_block"        = "10.0.3.0/24"
      "availability_zone" = "us-east-1c"
    }
    "Subnet_4" = {
      "cidr_block"        = "10.0.4.0/24"
      "availability_zone" = "us-east-1d"
    }
  }
}

resource "aws_subnet" "NearData_Subnets" {
  for_each          = var.subnets
  vpc_id            = aws_vpc.NearData_VPC.id
  cidr_block        = each.value["cidr_block"]
  availability_zone = each.value["availability_zone"]

  tags = {
    Name = "NearData_${each.key}"
  }
}

resource "aws_internet_gateway" "NearData_IG" {
  vpc_id = aws_vpc.NearData_VPC.id

  tags = {
    Name = "NearData_IGW"
  }
}

resource "aws_route_table" "NearData_RT" {
  vpc_id = aws_vpc.NearData_VPC.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.NearData_IG.id
  }

  tags = {
    Name = "NearData_RT"
  }
}

resource "aws_main_route_table_association" "NearData_RT" {
  route_table_id = aws_route_table.NearData_RT.id
  vpc_id         = aws_vpc.NearData_VPC.id
}