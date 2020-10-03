import boto3
import logging

class AWS_SQS():

    def __init__(self, **kwargs):
        logging.getLogger(__name__)
        self.sqs = boto3.client('sqs')
        self.url = kwargs.get('url', '')


    def post_message(self, text, **kwargs):
        """Posts message to SQS.

        Arguments:
            text (str): Text to send to SQS

        Returns:
            dict: Response object from SQS
        """
        while True:
            try:
                response = self.sqs.send_message(QueueUrl=self.url,
                                                 MessageBody=text,
                                                 MessageGroupId='gunslinger_group')
                break
            except Exception as e:
                logging.error(e)
                continue
        return response


    def get_next_message(self, **kwargs):
        """Gets next message from the queue and deletes it.

        Returns:
            list: list of results from SQS
            int: numeric 0 to comply with Gunslinger logic
        """
        while True:
            try:
                response = self.sqs.receive_message(QueueUrl=self.url,
                                                    MaxNumberOfMessages=1)
                break
            except Exception as e:
                logging.error(e)
                continue

        messages = response.get('Messages', [])
        if len(messages) == 0:
            return [], 0
        message = messages[0]
        self.sqs.delete_message(QueueUrl=self.url,
                                ReceiptHandle=message['ReceiptHandle'])
        message_body = message['Body']
        if 'gunslinger' in message_body:
            return [], 0
        dat = message_body.strip().split('\n')[1:]
        return dat, 0
