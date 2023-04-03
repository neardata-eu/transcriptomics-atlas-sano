resource "aws_vpc" "neardata_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

}

resource "aws_subnet" "subnet_1" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "subnet_2" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

resource "aws_subnet" "subnet_3" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1c"
}

resource "aws_subnet" "subnet_4" {
  vpc_id            = aws_vpc.neardata_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "us-east-1d"
}

resource "aws_internet_gateway" "neardata_ig" {
  vpc_id = aws_vpc.neardata_vpc.id
}

resource "aws_route_table" "neardata_rt" {
  vpc_id = aws_vpc.neardata_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.neardata_ig.id
  }
}

resource "aws_main_route_table_association" "example" {
  route_table_id = aws_route_table.neardata_rt.id
  vpc_id         = aws_vpc.neardata_vpc.id
}