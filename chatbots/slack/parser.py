import re

MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


def parse_bot_commands(slack_events, bot_id):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    commands, events = [], []
    for event in slack_events:
        print('slack::event::', event)

        direct_mention = parse_direct_mention(event, bot_id)
        if direct_mention:
            events.append(event)
            commands.append(direct_mention)

        reaction = parse_reaction(event)
        if reaction:
            print(reaction)

        self_message = parse_self_message(event, bot_id)
        if self_message:
            events.append(event)
            commands.append(self_message)

    return commands, events


def parse_direct_mention(event, user_id):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    if event["type"] == "message" and "subtype" not in event:
        message_text = event['text']
        matches = re.search(MENTION_REGEX, message_text)

        # the first group contains the username, the second group contains the remaining message
        if matches:
            user_match_id = matches.group(1)
            message = matches.group(2).strip()

            if user_id == user_match_id:
                return message
    return None


def parse_reaction(event):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    if 'type' in event and event['type'].startswith('reaction_'):
        return '{} {}'.format(event['type'], event['reaction'], event['user'])

    return None


def parse_self_message(event, user_id):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    if event["type"] == "message" and "subtype" in event:
        return "self"
    return None
