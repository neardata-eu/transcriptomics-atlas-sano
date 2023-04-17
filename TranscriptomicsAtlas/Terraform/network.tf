resource "aws_vpc" "neardata_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags  = {
    Name = "NearData_VPC"
    Project = "NearData"
  }

}

resource "aws_subnet" "subnet_1" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags = {
    Name = "NearData_SN_1"
    Project = "NearData"
  }
}

resource "aws_subnet" "subnet_2" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  tags = {
    Name = "NearData_SN_2"
    Project = "NearData"
  }
}

resource "aws_subnet" "subnet_3" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1c"
  tags = {
    Name = "NearData_SN_3"
    Project = "NearData"
  }
}

resource "aws_subnet" "subnet_4" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "us-east-1d"
  tags = {
    Name = "NearData_SN_4"
    Project = "NearData"
  }
}

resource "aws_internet_gateway" "neardata_ig" {
  vpc_id = aws_vpc.neardata_vpc.id

  tags  = {
    Name = "NearData_IGW"
    Project = "NearData"
  }
}

resource "aws_route_table" "neardata_rt" {
  vpc_id = aws_vpc.neardata_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.neardata_ig.id
  }

  tags  = {
    Name = "NearData_RT"
    Project = "NearData"
  }
}

resource "aws_main_route_table_association" "example" {
  route_table_id = aws_route_table.neardata_rt.id
  vpc_id         = aws_vpc.neardata_vpc.id
}