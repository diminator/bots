from ocean_cli.api.assets import list_assets, publish

EXAMPLE_COMMAND = "info"


def handle_command(command, event, bot):
    """
        Executes bot command if the command is known
    """
    print('slack::cmd::{}'.format(command))

    cmd_list = command.split(' ')
    cmd = cmd_list[0].lower()
    args = cmd_list[1:] if len(cmd_list) else 0

    if cmd == 'help':
        response, success = handle_command_help()

    elif cmd == 'accounts':
        response, success = handle_command_accounts(args, event, bot)

    elif cmd == 'assets':
        response, success = handle_command_assets(args, event, bot)

    elif cmd == 'publish':
        response, success = handle_command_publish(args, event, bot)

    elif cmd == 'self':
        response, success = handle_command_self(args, event, bot)

    elif 'reaction_' in cmd:
        response, success = handle_command_reaction(args, event, bot)
    else:
        response, success = handle_command_help()

    print('slack::cmd::{}::success::{}'.format(command, success))
    return success, response


def handle_command_help():
    return """
Hi there, I hold your OCEAN
    
Here's what I can do:

\t*info*: this screen
\t*accounts*: list account balances
\t*assets*: list assets
\t*publish* _url_: encrypt and publish url on ocean

Not sure? try 
    @oceanbot publish https://i.giphy.com/media/8URvsoY7JWbvO/giphy.webp
    """, True


def handle_command_accounts(args, event, bot):
    if len(args) == 0:
        return handle_command_balance(args, bot)
    return None, False


def handle_command_balance(args, bot):
    balance = bot.ocean.accounts.balance(bot.account)

    return {
        'text': f"{balance}",
        'attachments': []
    }, True


def handle_command_assets(args, event, bot, limit=5):
    if len(args) == 0:
        return handle_command_list_assets(args, bot, limit)
    return None, False


def handle_command_publish(args, event, bot):
    did = publish(bot.ocean, bot.account,
                  name=f'url:{event["ts"]}',
                  secret=args[0][1:-1],
                  price=0)

    return {
        'text': did,
        'attachments': [render(did, bot)]
    }, True


def handle_command_list_assets(args, bot, limit=3):
    assets = list_assets(bot.ocean, bot.account, None)
    text = """
    {} assets loaded, here are the latest {}:
    """.format(len(assets), limit)

    attachments = [
        render(did, bot)
        for did in assets[::-1][:limit]
    ]

    return {
        'text': text,
        'attachments': attachments
    }, True


def handle_command_self(args, event, bot):
    if 'attachments' in event \
            and len(event['attachments']) == 1 \
            and event['text'][:3] == 'did':
        bot.connections['slack'].api_call(
            "reactions.add",
            channel=event['channel'],
            name="taco",
            timestamp=event['ts']
        )
        bot.connections['slack'].api_call(
            "reactions.add",
            channel=event['channel'],
            name="hankey",
            timestamp=event['ts']
        )
    return None, True


def handle_command_reaction(args, event, bot):
    print(args, event, bot)
    reaction = args[0]
    if reaction == 'taco' and event['type'] == 'reaction_added':
        print('TACOOO')
    text = f'Reaction *{reaction}*'
    return {
       'text': text,
       'attachments': []
    }, True


def render(did, bot):
    from ocean_cli.api.notebook import snippet_header, snippet_object
    ddo = bot.ocean.assets.resolve(did)
    return {
        "fallback": "Could not render",
        "color": "#cc99ff",
        "pretext": None,
        "author_name": ddo.metadata['base']['author'],
        "author_link": None,
        "author_icon": None,
        "title": ddo.metadata['base']['name'],
        "title_link": ddo.get_service('Metadata')._service_endpoint,
        "text": f'```{snippet_header() + snippet_object(did)}```',
        "fields": [],
        "image_url": None,
        "thumb_url": None,
        "footer": did,
        "footer_icon": None,
        "ts": None
    }