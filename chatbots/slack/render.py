from chatbots.slack.topic import Topic


def render_choice(choices, bot):
    return {
        "text": "What do you want to do?",
        "fallback": "You are unable to choose",
        "callback_id": "wopr_game",
        "color": "#3AA3E3",
        "attachment_type": "default",
        "actions": [
            {
                "name": "choice",
                "text": choice,
                "type": "button",
                "value": choice.lower(),
                "confirm": {
                    "title": choice,
                    "text": "Yeah... just type *@{} {}*".format(bot.name, choice),
                    "ok_text": "Yes",
                    "dismiss_text": "No"
                }
            }
            for choice in choices]
    }


def render_topic(topic, bot):
    asset = topic.recent if isinstance(topic, Topic) else topic
    tx_id = asset['tx']['id'] if 'tx' in asset else asset['id']
    user_id = asset['data']['event']['user']
    user_name = bot.store['users'][user_id]['profile']['display_name']
    return {
        "fallback": "Signal claim",
        "color": "#eeeeee",
        "pretext": None,
        "author_name": "{}.{}".format(asset['data']['namespace'], tx_id[:8]),
        "author_link": "{}api/v1/transactions/{}".format(bot.options['bdb']['uri'], tx_id),
        "author_icon": None,
        "title": None,
        "title_link": None,
        "text": "\n",
        "fields": [
            {
                "title": asset['data']['namespace'].split('.')[-1],
                "value": asset['data']['message'].lstrip(asset['data']['namespace'].split('.')[-1]),
                "short": False
            }
        ],
        "image_url": None,
        "thumb_url": None,
        "footer": "#{} @{}".format(asset['data']['event']['channel'], user_name),
        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
        "ts": asset['data']['event']['ts']
    }


def render_response(response, channel, connection):
    # Default response is help text for the user
    response = response or "Not sure what you mean. Try *help*."
    attachments = []

    if isinstance(response, dict):
        text = response['text'] if 'text' in response else response
        attachments = response['attachments'] if 'attachments' in response else attachments
    elif isinstance(response, str):
        text = response
    else:
        text = "wrong instance of type {}".format(type(response))

    print('slack::response::\n{}\n{}\n{}'.format('*'*10, text, '*'*10))
    # Sends the response back to the channel
    connection.api_call(
        "chat.postMessage",
        channel=channel,
        text=text,
        attachments=attachments
    )
