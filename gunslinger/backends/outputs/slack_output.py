import logging
import slack
import yaml

class SlackHandler():

    def __init__(self, **kwargs):
        logging.getLogger(__name__)
        channel = kwargs.get('channel', 'mq')
        slack_token = kwargs.get('slack_token', '')
        self.client = slack.WebClient(token=slack_token)
        logging.info(f'Channel is {channel}')
        self.channel = self.get_channel(channel)


    def get_channel(self, channel):
        """Gets ID of Slack channel.

        Arguments:
            channel (str): channel to get ID of

        Returns:
            str: Channel ID
        """
        logging.info(f'Getting channel {channel}')
        channels = self.client.conversations_list()
        for slack_channel in channels['channels']:
            if slack_channel['name'] == channel:
                return slack_channel['id']
        raise Exception('Channel does not exist')


    def post_message(self, text, **kwargs):
        """Posts message to Slack

        Arguments:
            text (str): message to send
            channel (str, optional): channel to send the message to

        Returns:
            (dict): Message response object from Slack API
        """
        channel = kwargs.get('channel', self.channel)
        message_response = self.client.chat_postMessage(channel=channel,
                                                        text=text)
        return message_response


def run(output_data, config_data):
    slack_handler = SlackHandler(**config_data)
    try:
        output_str = 'Hit!:gun:\n'+yaml.dump(output_data)
        slack_handler.post_message(output_str)
    except Exception as e:
        logging.error(e)
