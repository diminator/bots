from .render import (
    render_choice,
)

from ..models.model import get_track

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

    if cmd == 'genres':
        response, success = handle_command_genres(args, event, bot)

    if cmd == 'songs':
        response, success = handle_command_songs(args, event, bot)

    if cmd == 'map':
        response, success = handle_command_map(args, event, bot)

    if cmd == 'self':
        response, success = handle_command_self(args, event, bot)

    if 'reaction_' in cmd:
        response, success = handle_command_reaction(args, event, bot)

    print('slack::cmd::{}::success::{}'.format(command, success))
    return success, response


def handle_command_help():
    return """
Hi there, I'm a curation agent 
    
Here's what I can do:

\t*info*: this screen
\t*accounts*: list account balances
\t*genres*: list genres
\t*genres* add <#genre>: add #genre to the list of genres
\t*songs*: list songs
\t*songs* add _<spotifyURI>_: add song to the list of songs by _<spotifyURI>_
\t*songs* get _<spotifyURI>_: get song with _<spotifyURI>_
\t*map* _<spotifyURI>_ <#genre>: map a song to a genre

Not sure? try *songs* or *genres*
    """, True


def handle_command_genres(args, event, bot, limit=3):
    if len(args) == 0:
        return handle_command_list_genres(args, bot, limit)
    elif args[0] == 'add':
        return handle_command_add_genre(args, event, bot)
    return None, False


def handle_command_list_genres(args, bot, limit=3):
    genres = bot.sorted_genres

    text = """
    {} genres loaded, here are the latest {}:
            """.format(len(genres), limit)

    attachments = [
        genre.render(bot)
        for genre in genres[::-1][:limit]
    ]

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_add_genre(args, event, bot):
    tx = bot.put('genre', event)
    bot.pull(tx_id=tx['id'])
    bot.store['active']['genre'] = -1
    attachments = [
        bot.active_genre.render(bot),
        render_choice(['propose'], bot)
    ]

    text = "Genre {} added".format(bot.active_genre.value)

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_songs(args, event, bot, limit=3):
    if len(args) == 0:
        return handle_command_list_songs(args, bot, limit)
    elif args[0] == 'add':
        return handle_command_add_song(args, event, bot)
    elif args[0] == 'get':
        return handle_command_get_song(args, event, bot)
    return None, False


def handle_command_list_songs(args, bot, limit=3):
    songs = bot.sorted_songs

    text = """
    {} songs loaded, here are the latest {}:
            """.format(len(songs), limit)

    attachments = [
        song.render(bot)
        for song in songs[::-1][:limit]
    ]

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_add_song(args, event, bot):
    track_uri = args[-1][1:-1]
    try:
        event['metadata'] = get_track(bot.connections['spotify'], track_uri)
    except Exception as e:
        event['metadata'] = {}
        print(e)
    event['metadata']['uri'] = track_uri
    tx = bot.put('song', event)
    bot.pull(tx_id=tx['id'])
    bot.store['active']['song'] = -1
    attachments = [
        bot.active_song.render(bot),
        # render_choice(['propose'], bot)
    ]

    text = "Song {} added".format(bot.active_song.title)

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_get_song(args, event, bot):
    song = None
    song_id = args[1]
    if 'spotify:track' in song_id:
        song = get_song_by_uri(bot, song_id[1:-1])
    else:
        try:
            song = bot.store['songs'][song_id]
        except Exception as e:
            print(e)
    if not song:
        handle_command_add_song([song_id], event, bot)
        song = get_song_by_uri(bot, song_id[1:-1])

    bot.pull(tx_id=song.id)
    song = get_song_by_uri(bot, song.uri)

    attachments = [
        song.render(bot),
        # render_choice(['withdraw', 'challenge'], bot)
    ]

    text = "Song *{} - {}*".format(song.artist, song.title)

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_map(args, event, bot):
    handle_command_get_song(['get', *args], event, bot)
    song = get_song_by_uri(bot, args[0][1:-1])

    genre = get_genre_by_name(bot, args[1])
    if not genre:
        handle_command_add_genre([], event, bot)
        genre = get_genre_by_name(bot, args[1])

    event['map'] = genre.value

    bot.pull(tx_id=song.id)
    bot.put('map', event, song.recent)
    bot.pull(tx_id=song.id)

    attachments = [
        bot.active_song.render(bot),
        # render_choice(['withdraw', 'challenge'], bot)
    ]

    text = "Song *{} - {}* mapped to genre *{}*".format(song.artist, song.title, genre.value)

    return {
               'text': text,
               'attachments': attachments
           }, True


def handle_command_self(args, event, bot):
    if 'attachments' in event \
            and len(event['attachments']) == 1 \
            and event['text'][:4] == 'Song':
        bot.connections['slack'].api_call(
            "reactions.add",
            channel=event['channel'],
            name="thumbsup",
            timestamp=event['ts']
        )
        bot.connections['slack'].api_call(
            "reactions.add",
            channel=event['channel'],
            name="thumbsdown",
            timestamp=event['ts']
        )
        bot.store['messages'][event['ts']] = event
    return None, True


def handle_command_reaction(args, event, bot):
    msg = bot.store['messages'].get(event['item']['ts'])
    if msg:
        song = get_song_by_uri(bot, msg['attachments'][0]['author_name'])
        bot.pull(tx_id=song.id)
        event['reaction'] = args[0]
        bot.put('reaction', event, song.recent)
        bot.pull(tx_id=song.id)
        text = "Reaction *{}* added to song *{} - {}*".format(args[0], song.artist, song.title)

        return {
                   'text': text,
                   'attachments': []
               }, True

    return None, True


def get_song_by_uri(bot, uri):
    song = [s for s in bot.store['songs'].values() if uri in s.uri]
    if len(song) > 0:
        return song[0]
    return None


def get_genre_by_name(bot, genre):
    genres = [g for g in bot.store['genres'].values() if genre == g.value]
    if len(genres) > 0:
        return genres[0]
    return None
