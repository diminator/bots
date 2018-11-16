import os
import datetime

from slackclient import SlackClient
import spotipy.util

from bigchaindb_driver import BigchainDB

from .parser import parse_bot_commands
from .commands import handle_command
from .render import render_response

from ..backends.bdb.utils import generate_key_pair
from ..backends.bdb import backend

from ..models.model import Model, Genre, Song


class SlackBot:

    version = 'v0.0.2.0'

    def __init__(self, name=None, store=None, options=None):
        self.name = name if name else os.environ.get('SLACK_BOT_NAME', 'alice')
        secret = os.environ.get('SLACK_BOT_TOKEN_{}'.format(self.name), '')
        self.store = store if store else {
            'active': {
                'genre': -1,
                'song': -1
            },
            'genres': {},
            'songs': {},
            'users': {}
        }
        self.options = options if options else \
            {
                'slack': {
                    'token': secret,
                    # bot's user ID in Slack: value is assigned after the bot starts up
                    'user_id': None,
                    # 1 second delay between reading from RTM
                    'rtm_read_delay': 1,
                },
                'bdb': {
                    'uri': 'https://test.bigchaindb.com/',
                    'key_pair': generate_key_pair(secret),
                    'token': {
                        'app_id': os.environ.get('BDB_APP_ID', ''),
                        'app_key': os.environ.get('BDB_APP_KEY', '')
                    }
                }
            }

        self.connections = {
            'spotify': spotipy.Spotify(
                auth=spotipy.util.prompt_for_user_token(
                    os.environ.get('SPOTIFY_USER', ''),
                    'user-library-read',
                    client_id=os.environ.get('SPOTIFY_CLIENT_ID', ''),
                    client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET', ''),
                    redirect_uri="http://localhost:3000/callback/")
                ),
            'slack': SlackClient(self.options['slack']['token']),
            'bdb': BigchainDB(
                self.options['bdb']['uri'],
                headers=self.options['bdb']['token']
            )
        }

    @property
    def namespace(self):
        return 'agents.musicmap.bots.slack.{}.{}'.format(self.version, self.name)

    @property
    def active_genre(self):
        return self._get_active(self.sorted_genres, 'genre')

    @property
    def active_song(self):
        return self._get_active(self.sorted_songs, 'song')

    def _get_active(self, active_list, active_type):
        if len(active_list) > 0:
            return active_list[self.store['active'][active_type]]
        return None

    @property
    def sorted_genres(self):
        return self._get_sorted_from_store('genres')

    @property
    def sorted_songs(self):
        return self._get_sorted_from_store('songs')

    def _get_sorted_from_store(self, value):
        return sorted(self.store[value].values(), key=lambda k: k.recent['metadata']['event']['ts'])

    def connect(self):
        is_connected = self.connections['slack'].rtm_connect(with_team_state=False)
        if is_connected:
            self.options['slack']['user_id'] = self.connections['slack'].api_call("auth.test")["user_id"]
            users = {}
            for member in self.connections['slack'].api_call('users.list')['members']:
                users[member['id']] = member
            self.store['users'] = users
            self.pull()
        return is_connected

    def pull(self, query=None, tx_id=None):
        if tx_id:
            tx_data = backend.history(tx_id, connection=self.connections['bdb'])
            item = Model.factory(tx_data)
            if isinstance(item, Genre):
                self.store['genres'][item.id] = item
            elif isinstance(item, Song):
                self.store['songs'][item.id] = item
        else:
            assets, metadata = backend.get(query=self.namespace + (query or ""),
                                           connection=self.connections['bdb'])
            genres = {}
            songs = {}
            for asset in assets:
                if 'type' in asset['data']:
                    metadatum = [metadatum
                                 for metadatum in metadata
                                 if metadatum['id'] == asset['id']][0]
                    item = Model.factory(metadatum)
                    if isinstance(item, Genre):
                        genres[item.id] = item
                    elif isinstance(item, Song):
                        songs[item.id] = item
            self.store.update({
                'genres': genres,
                'songs': songs
            })
            return genres

    def put(self, data_type, data, unspent=None):
        if unspent and 'operation' not in unspent:
            print(unspent)
            pass
        return backend.put(
            asset={
                'namespace': '{}.{}'.format(self.namespace, data_type),
                'type': data_type,
            },
            metadata={
                'namespace': '{}.{}'.format(self.namespace, data_type),
                'timestamp': str(datetime.datetime.now()),
                'type': data_type,
                'event': data,
            },
            connection=self.connections['bdb'],
            key_pair=self.options['bdb']['key_pair'],
            unspent=unspent
        )

    def listen(self):
        slack_events = self.connections['slack'].rtm_read()
        return parse_bot_commands(slack_events=slack_events,
                                  bot_id=self.options['slack']['user_id'])

    def handle(self, command, event):
        success, response = handle_command(command=command, event=event, bot=self)
        channel = event['channel'] if 'channel' in event \
            else event['item']['channel'] if 'item' in event \
            else None
        return success, response, channel

    def respond(self, response, channel):
        if response:
            return render_response(response=response,
                                   channel=channel,
                                   connection=self.connections['slack'])
