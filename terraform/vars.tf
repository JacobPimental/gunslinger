#DigitalOcean Variables
variable "digitalocean_token" {}
variable "server_pub_key" {}
variable "server_priv_key" {}
variable "server_region" { default="nyc1" }

# Whether or not to use Amazon SQS Message Queue
variable "use_sqs" { 
	type=bool
	default=false 
}

# Launch Script variables
variable "rule_dir" { default="../gunslinger/rules/" }
variable "num_workers" { default="" }

# Miscellaneous
variable "aws_region" { default="us-east-1" }
