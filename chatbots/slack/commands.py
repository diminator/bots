from .render import (
    render_choice,
)

from ..models.song import get_track

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
\t*songs* add <spotifyURI>: add song to the list of songs by spotifyURI
\t*map* <spotifyURI> <#genre>: map a song to a genre

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
    bot.put('genre', event)
    bot.pull()
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
    bot.put('song', event)
    bot.pull()
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


def handle_command_map(args, event, bot):
    if 'spotify:track' in args[0]:
        song = get_song_by_uri(bot, args[0][1:-1])
        if not song:
            handle_command_add_song([args[0]], event, bot)
            song = get_song_by_uri(bot, args[0][1:-1])
    else:
        song = bot.store['songs'][args[0]]

    genre = get_genre_by_name(bot, args[1])
    if not genre:
        handle_command_add_genre([], event, bot)
        genre = get_genre_by_name(bot, args[1])

    event['map'] = genre.value

    bot.put('map', event, song.recent)
    bot.pull()

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
