provider "aws" {
	region = "${var.aws_region}"
}

resource "aws_sqs_queue" "message_queue" {
	name = "gunslinger_queue.fifo"
  fifo_queue = true	
  content_based_deduplication = true
}

output "sqs_id" {
	value = "${aws_sqs_queue.message_queue.id}"
}

output "sqs_arn" {
	value = "${aws_sqs_queue.message_queue.arn}"
}
