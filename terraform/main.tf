provider "aws" {
	region = var.aws_region
}
provider "digitalocean" {
	token = var.digitalocean_token
}

resource "aws_sqs_queue" "message_queue" {
	name = "gunslinger_queue.fifo"
  fifo_queue = true	
  content_based_deduplication = true
  count = var.use_sqs == false ? 0 : 1
}

output "sqs_id" {
	value = aws_sqs_queue.message_queue.*.id
}

output "sqs_arn" {
	value = aws_sqs_queue.message_queue.*.arn
}

resource "digitalocean_ssh_key" "key" {
	name = "Gunsinger Key"
	public_key = file(var.server_pub_key)
}

resource "digitalocean_droplet" "server" {
	image = "ubuntu-19-10-x64"
	name = "gunslinger"
	region = var.server_region
	size = "s-1vcpu-1gb"
	ssh_keys = [digitalocean_ssh_key.key.fingerprint]
	depends_on = [ aws_sqs_queue.message_queue ]
	user_data = templatefile("user-data.sh", {
		slack_token = format("-s %s ", var.slack_token),
		urlscan_api_key = format("-u %s ", var.urlscan_api_key),
		num_workers = var.num_workers != "" ? format("-t %s ", var.num_workers) : "",
		queue_channel = var.queue_channel != "" ? format("-c %s ", var.queue_channel) : "",
		urlscan_query = var.urlscan_query != "" ? format("-q %s ", var.urlscan_query) : "",
		num_results = var.num_results != "" ? format("-n %s ", var.num_results) : "",
		sqs_url = var.use_sqs == true ? format("-a %s ", aws_sqs_queue.message_queue.0.id) : ""})
	provisioner "remote-exec" {
		inline = ["sudo mkdir /opt/gunslinger_rules"]
		connection {
			user = "root"
			private_key = file(var.server_priv_key)
			host = digitalocean_droplet.server.ipv4_address
		}
	}
	provisioner "file" {
		source = substr(var.rule_dir, length(var.rule_dir)-1, 1) == "/" ? var.rule_dir : format("%s/", var.rule_dir)
		destination = "/opt/gunslinger_rules"
		connection {
			user = "root"
			private_key = file(var.server_priv_key)
			host = digitalocean_droplet.server.ipv4_address
		}
	}
}

output "ip" {
	value = digitalocean_droplet.server.ipv4_address
}
