import time
import slack
import logging

class Slack_MQ():

    def __init__(self, **kwargs):
        logging.getLogger(__name__)
        queue_channel = kwargs.get('channel', 'mq')
        slack_token = kwargs.get('slack_token', '')
        self.client = slack.WebClient(token=slack_token)
        logging.info(f'Channel is {queue_channel}')
        self.channel = self.get_channel(queue_channel)


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
            reaction (str, optional): Slack reaction code to add to message

        Returns:
            (dict): Message response object from Slack API
        """
        channel = kwargs.get('channel', self.channel)
        reaction = kwargs.get('reaction', '')
        message_response = self.client.chat_postMessage(channel=channel,
                                                        text=text)
        if reaction:
            self.react_message(message_response['ts'],
                               reaction,
                               channel)
        return message_response


    def react_message(self, ts, reaction, channel=''):
        """Reacts to a Slack message

        Arguments:
            ts (str): timestamp of message to react to
            reaction (str): Slack reaction code
            channel (str, optional): channel that message is in

        Returns:
            (dict): Reaction response object from Slack API
        """
        if channel == '':
            channel = self.channel
        reaction_response = self.client.reactions_add(channel=channel,
                                                      name=reaction,
                                                      timestamp=ts)
        return reaction_response


    def get_next_message(self, **kwargs):
        """Gets next message in queue and reacts to it to mark it as taken

        Arguments:
            oldest (str, optional): timestamp of oldest message to check
            latest (str, optional): timestamp of latest message to check
            cursor (str, optional): cursor code used for pagination

        Returns:
            (str, str): message text and timestamp of message
        """
        oldest = kwargs.get('oldest', 0)
        latest = kwargs.get('latest', '')
        cursor = kwargs.get('cursor', '')
        try:
            r = self.client.conversations_history(channel=self.channel,
                                                  limit=999,
                                                  oldest=str(oldest),
                                                  latest=str(latest),
                                                  inclusive=1,
                                                  cursor=cursor)
            data = r.data
            messages = data['messages']
            i = 0
            for i in range(len(messages)-1):
                m = messages[i]
                if 'reactions' in messages[i+1] and m['text'][0] == '{' \
                   and not 'reactions' in m.keys():
                    ts = m['ts']
                    self.client.reactions_add(channel=self.channel,
                                              name='+1',
                                              timestamp=ts)
                    oldest = ts
                    dat = m['text'].strip()
                    return dat, oldest
                if 'reactions' in m.keys():
                    return [], 0
            if 'reactions' in messages[i] and \
               messages[i]['text'][0] == '{':
                ts = messages[i]['ts']
                self.client.reactions_add(channel=self.channel,
                                          name='+1',
                                          timestamp=ts)
                oldest = ts
                dat = m['text'].strip()
                return dat, oldest
            if 'response_metadata' in data.keys() and \
               'next_cursor' in data['response_metadata'].keys():
                logging.info('Getting next cursor')
                cursor = data['response_metadata']['next_cursor']
                return self.get_next_message(oldest=oldest,
                                             latest=latest,
                                             cursor=cursor)
            return [], latest
        except Exception as e:
            logging.error(e)
            if 'response' in dir(e):
                r = e.response
                logging.error(r)
                time.sleep(60)
                if r['error'] == 'ratelimited':
                    return self.get_next_message(oldest=oldest,
                                                 latest=latest,
                                                 cursor=cursor)
                return [], 0
            return [], oldest
