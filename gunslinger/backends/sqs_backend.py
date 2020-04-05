import boto3

class AWS_SQS():

    def __init__(self, url):
        self.sqs = boto3.client('sqs')
        self.url = url


    def post_message(self, text, **kwargs):
        """Posts message to SQS.

        Arguments:
            text (str): Text to send to SQS

        Returns:
            dict: Response object from SQS
        """
        response = self.sqs.send_message(QueueUrl=self.url,
                                         MessageBody=text,
                                         MessageGroupId='gunslinger_group')
        return response


    def get_next_message(self, **kwargs):
        """Gets next message from the queue and deletes it.

        Returns:
            list: list of results from SQS
            int: numeric 0 to comply with Gunslinger logic
        """
        response = self.sqs.receive_message(QueueUrl=self.url,
                                            MaxNumberOfMessages=1)
        messages = response.get('Messages', [])
        if len(messages) == 0:
            return [], 0
        message = messages[0]
        self.sqs.delete_message(QueueUrl=self.url,
                                ReceiptHandle=message['ReceiptHandle'])
        message_body = message['Body']
        if not 'New batch' in message_body:
            return [], 0
        dat = message_body.strip().split('\n')[1:]
        return dat, 0
