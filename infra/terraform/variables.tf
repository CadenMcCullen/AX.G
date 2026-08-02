variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target secure AWS region for infrastructure deployment."
}

variable "enclave_ami_id" {
  type        = string
  default     = "ami-0c55b159cbfafe1f0"
  description = "Hardened Linux AMI with native Nitro Enclaves CLI tools."
}
