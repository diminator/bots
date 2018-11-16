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


def generate_default_response(
        tx_id, tx_uri,
        title=None,
        title_link=None,
        field_title=None,
        field_value=None,
        thumb_url=None,
        footer=None,
        ts=None):
    return {
        "fallback": "Could not render",
        "color": "#cc99ff",
        "pretext": None,
        "author_name": "{}".format(tx_id),
        "author_link": tx_uri,
        "author_icon": None,
        "title": title,
        "title_link": title_link,
        "text": "\n",
        "fields": [
            {
                "title": field_title,
                "value": field_value,
                "short": False
            }
        ],
        "image_url": None,
        "thumb_url": thumb_url,
        "footer": footer,
        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
        "ts": ts
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
