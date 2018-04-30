import os
import datetime

from slackclient import SlackClient

from bigchaindb_driver import BigchainDB

from chatbots.slack.parser import parse_bot_commands
from chatbots.slack.commands import handle_command
from chatbots.slack.render import render_response

from chatbots.backends.bdb.utils import generate_key_pair
from chatbots.backends.bdb import backend
from chatbots.slack.topic import Topic


class SlackBot:

    version = 'v0.0.3a'

    def __init__(self, name=None, store=None, options=None):
        self.name = name if name else os.environ.get('SLACK_BOT_NAME', 'alice')
        secret = os.environ.get('SLACK_BOT_TOKEN_{}'.format(self.name), '')
        self.store = store if store else {
            'active': -1,
            'topics': {},
            'users': {}
        }
        self.options = options if options else \
            {
                'slack': {
                    'token': secret,
                    # bot's user ID in Slack: value is assigned after the bot starts up
                    'user_id': None,
                    # 1 second delay between reading from RTM
                    'rtm_read_delay': 1,
                },
                'bdb': {
                    'uri': 'http://localhost:9984/',
                    'key_pair': generate_key_pair(secret),
                    'token': {
                        'app_id': os.environ.get('BDB_APP_ID', ''),
                        'app_key': os.environ.get('BDB_APP_KEY', '')
                    }
                }
            }

        self.connections = {
            'slack': SlackClient(self.options['slack']['token']),
            'bdb': BigchainDB(
                self.options['bdb']['uri'],
                headers=self.options['bdb']['token']
            )
        }

    @property
    def namespace(self):
        return 'agents.ocean.bots.slack.{}.{}'.format(self.version, self.name)

    @property
    def active_topic(self):
        sorted_topics = self.sorted_topics
        if len(sorted_topics) > 0:
            return sorted_topics[self.store['active']]
        return None

    def balance(self, topics=None):
        accounts = {}
        if not topics:
            topics = self.sorted_topics
        for topic in topics:
            for account, value in topic.balance().items():
                if account in accounts.keys():
                    accounts[account] += value
                else:
                    accounts[account] = value

        return accounts

    @property
    def sorted_topics(self):
        return sorted(self.store['topics'].values(), key=lambda k: k.recent['data']['event']['ts'])

    def connect(self):
        is_connected = self.connections['slack'].rtm_connect(with_team_state=False)
        if is_connected:
            self.options['slack']['user_id'] = self.connections['slack'].api_call("auth.test")["user_id"]
            users = {}
            for member in self.connections['slack'].api_call('users.list')['members']:
                users[member['id']] = member
            self.store['users'] = users
        return is_connected

    def pull(self, query=None):
        assets = backend.get(query=self.namespace + (query or ""),
                             connection=self.connections['bdb'])
        topics = {}
        for asset in assets:
            topic = Topic(asset)
            topic.load(self.connections['bdb'])
            topics[asset['id']] = topic

        self.store.update({
            'topics': topics
        })
        return topics

    def put(self, message, event, unspent=None):
        payload = {
            'namespace': '{}.{}'.format(self.namespace, message.split(" ")[0]),
            'timestamp': str(datetime.datetime.now()),
            'message': message,
            'event': event,
        }

        return backend.put(
            asset=payload,
            metadata=payload,
            connection=self.connections['bdb'],
            key_pair=self.options['bdb']['key_pair'],
            unspent=unspent
        )

    def listen(self):
        slack_events = self.connections['slack'].rtm_read()
        return parse_bot_commands(slack_events=slack_events,
                                  bot_id=self.options['slack']['user_id'])

    def handle(self, command, event):
        success, response = handle_command(command=command, event=event, bot=self)
        channel = event['channel'] if 'channel' in event \
            else event['item']['channel'] if 'item' in event \
            else None
        return success, response, channel

    def respond(self, response, channel):
        return render_response(response=response,
                               channel=channel,
                               connection=self.connections['slack'])
