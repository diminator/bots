from chatbots.slack.render import render_topic, render_choice

EXAMPLE_COMMAND = "info"


def handle_command(command, event, bot):
    """
        Executes bot command if the command is known
    """
    print('slack::cmd::{}'.format(command))

    success, response = True, None

    cmd_list = command.split(' ')
    cmd = cmd_list[0].lower()
    args = cmd_list[1:] if len(cmd_list) else 0

    if cmd == 'help':
        response, success = handle_command_help()

    if cmd == 'get':
        response, success = handle_command_get(command, event, bot)

    if cmd == 'list':
        response, success = handle_command_list(args, bot)

    if cmd == 'accounts':
        response, success = handle_command_accounts(bot)

    if cmd == 'pull':
        response, success = handle_command_pull(args, bot)

    if cmd == 'signal':
        response, success = handle_command_signal(command, event, bot)

    if cmd == 'propose':
        response, success = handle_command_propose(command, args, event, bot)

    print('slack::cmd::{}::success::{}'.format(command, success))
    return success, response


def handle_command_help():
    return """
Hi there, I'm a curation agent 
    
Here's what I can do:

\t*info*: this screen
\t*accounts*: list account balances
\t*list*: list topics
\t*get* _topic_: activate topic
\t*pull* _query_: pull topics with query
\t*signal*: signal a new topic
\t*propose* _deposit_: propose the active topic
\t(challenge): challenge the active proposal
\t(vote) *{true|false}* _deposit_: vote on the active challenge

\t(under construction)

Not sure? try *pull*, *get* or *signal*
    """, True


def handle_command_accounts(bot):
    text = "\n".join(['{}: {}'.format(bot.store['users'][k]['profile']['display_name'], v) for k, v in bot.balance().items()])
    return {
            'text': text,
            'attachments': []
        }, True


def handle_command_get(command, event, bot):
    text, attachments = "", []

    args = command.split(' ')
    index = int(args[1]) if len(args) > 1 else bot.store['active']
    bot.store['active'] = index

    if len(bot.store['topics']) == 0:
        bot.pull()

    try:
        active_topic = bot.active_topic
        active_topic.load(bot.connections['bdb'])
        attachments = [
            render_topic(topic_event, bot) for topic_event in active_topic.history
        ]

        text = "Active topic is now {}".format(index)
    except TypeError as e:
        text = str(e)
    except IndexError as e:
        text = str(e)

    return {
            'text': text,
            'attachments': attachments
        }, True

def handle_command_list(args, bot, limit=3):
    topics = bot.sorted_topics

    text = """
    {} topics loaded, use *get* _index_ for activating a topic. 
    Negative indices are allowed and count backwards    

    Here are the newest {}:
            """.format(len(topics), limit)

    attachments = [
        render_topic(topic, bot)
        for topic in topics[::-1][:limit]
    ]

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_pull(args, bot, limit=3):
    query = " ".join(args) if len(args) > 0 else None
    bot.pull(query)
    return handle_command_list(args, bot, limit)


def handle_command_signal(command, event, bot):
    bot.put(command, event)
    bot.pull()
    bot.store['active'] = -1
    attachments = [
        render_topic(bot.active_topic, bot),
        render_choice(['propose'], bot)
    ]

    text = "Signal appended to the ledger"

    return {
            'text': text,
            'attachments': attachments
        }, True


def handle_command_propose(command, args, event, bot):
    if bot.active_topic is None \
            or 'tx' not in bot.active_topic.recent\
            or len(args) == 0:
        return 'Try *get* first or adding a deposit', False

    if not args[0].isdigit() or args[0] == '0':
        return 'Try valid positive integer deposit: 1, 3, 10, ...', False

    if bot.active_topic.recent['data']['message'].split(' ')[0] != 'signal':
        return 'Already proposed', False

    bot.put(command, event, bot.active_topic.recent['tx'])

    attachments = [
        render_topic(bot.active_topic, bot),
        render_choice(['withdraw', 'challenge'], bot)
    ]

    text = "Signal proposed to the registry"

    return {
            'text': text,
            'attachments': attachments
        }, True
