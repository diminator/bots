#!/usr/bin/python
import time

from chatbots.slack.bot import SlackBot

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
