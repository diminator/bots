import os, sys
import datetime
import logging

from slackclient import SlackClient

import configparser

from squid_py import Ocean, Config, ConfigProvider
from ocean_cli.ocean import (
    get_default_account
)
from chatbots.slack.parser import parse_bot_commands
from chatbots.slack.render import render_response

from .commands import (
    handle_command
)

if 'CONFIG_FILE' in os.environ and os.environ['CONFIG_FILE']:
    CONFIG = os.environ['CONFIG_FILE']
else:
    try:
        CONFIG = 'config.ini'
    except Exception as e:
        logging.error('A config file must be set in the environment '
                      'variable "CONFIG_FILE" or in config.ini')
        logging.error(e)
        sys.exit(1)

conf = configparser.ConfigParser()
conf.read(CONFIG)


class OceanSlackBot:

    version = 'v0.0.2.0'

    def __init__(self, name=None, store=None, options=None):
        self.name = name if name else conf['slack']['name']
        self.ocean = Ocean(Config(filename=conf['ocean']['config']))
        self.account = get_default_account(ConfigProvider.get_config())
        balance = self.ocean.accounts.balance(self.account)
        print(balance)

        self.store = store if store else {}
        self.options = options if options else \
            {
                'slack': {
                    'token': conf['slack']['token.bot'],
                    # bot's user ID in Slack:
                    # value is assigned after the bot starts up
                    'user_id': None,
                    # 1 second delay between reading from RTM
                    'rtm_read_delay': 1,
                },
            }

        self.connections = {
            'slack': SlackClient(self.options['slack']['token']),
        }

    def connect(self):
        is_connected = self.connections['slack']\
            .rtm_connect(with_team_state=False)
        if is_connected:
            self.options['slack']['user_id'] = self.connections['slack']\
                .api_call("auth.test")["user_id"]
            users = {}
            for member in \
                    self.connections['slack'].api_call('users.list')['members']:
                users[member['id']] = member
            self.store['users'] = users
        return is_connected

    def listen(self):
        slack_events = self.connections['slack'].rtm_read()
        return parse_bot_commands(slack_events=slack_events,
                                  bot_id=self.options['slack']['user_id'])

    def handle(self, command, event):
        success, response = handle_command(command=command,
                                           event=event,
                                           bot=self)
        channel = event['channel'] if 'channel' in event \
            else event['item']['channel'] if 'item' in event \
            else None
        return success, response, channel

    def respond(self, response, channel):
        if response:
            return render_response(response=response,
                                   channel=channel,
                                   connection=self.connections['slack'])
