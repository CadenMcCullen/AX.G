provider "aws" {
  region = var.aws_region
}

# Secure VPC for Payment Rail settlement ledger nodes and enclaves
resource "aws_vpc" "payment_rail_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "payment-rail-secure-vpc"
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id     = aws_vpc.payment_rail_vpc.id
  cidr_block = "10.0.1.0/24"
  tags = {
    Name = "payment-rail-private-subnet"
  }
}

# EC2 Instance with secure Nitro Enclaves enabled
resource "aws_instance" "enclave_node" {
  ami           = var.enclave_ami_id
  instance_type = "c5.xlarge"
  subnet_id     = aws_subnet.private_subnet.id

  # Security parameter enabling AWS Nitro Enclaves
  enclave_options {
    enabled = true
  }

  tags = {
    Name = "payment-rail-enclave-settlement-node"
  }
}
