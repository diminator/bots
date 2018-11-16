#!/usr/bin/python
import time
import os
import logging
import sys

from chatbots.slack.bot import SlackBot

if 'CONFIG_FILE' in os.environ and os.environ['CONFIG_FILE']:
    CONFIG = os.environ['CONFIG_FILE']
else:
    try:
        CONFIG = 'config.ini'
    except Exception as e:
        logging.error('A config file must be set in the environment variable "CONFIG_FILE" or in config.ini')
        logging.error(e)
        sys.exit(1)


if __name__ == "__main__":
    bot = SlackBot()

    if bot.connect():
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        while True:
            response, channel = None, None
            commands, events = bot.listen()

            for index, command in enumerate(commands):
                try:
                    success, response, channel = bot.handle(command=command, event=events[index])
                    bot.respond(response, channel)
                except Exception as e:
                    print(e)

            time.sleep(bot.options['slack']['rtm_read_delay'])
    else:
        print("Connection failed. Exception traceback printed above.")
