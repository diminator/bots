from ..slack.render import (
    generate_default_response,
    generate_small_response
)


class Model:
    def factory(tx_data):
        if not isinstance(tx_data, list):
            data = [tx_data]
        else:
            data = tx_data
        _type = data[0]['metadata']['type']
        if _type == 'song': 
            return Song(data)
        if _type == 'genre':
            return Genre(data)

    def __init__(self, tx_data):
        self.id = tx_data[0]['id']
        self.tx_data = tx_data
    
    @property
    def data(self):
        return self.tx_data[0]['metadata']
    
    @property
    def namespace(self):
        return self.data['namespace']

    @property
    def recent(self):
        return self.tx_data[-1]


class Genre(Model):
    def __init__(self, tx_data):
        Model.__init__(self, tx_data)
        self.value = self.data['event']['text'].split(" ")[-1]

    def render(self, bot):
        user_id = self.recent['metadata']['event']['user']
        user_name = bot.store['users'][user_id]['profile']['display_name']
        return generate_default_response(
            tx_id=self.id,
            tx_uri="{}api/v1/transactions/{}".format(bot.options['bdb']['uri'], self.id),
            field_title=self.value,
            field_value='musicmap::{}'.format(self.namespace.split('.')[-1]),
            footer="#{} @{}".format(self.recent['metadata']['event']['channel'], user_name),
            ts=self.recent['metadata']['event']['ts']
        )


class Song(Model):
    def __init__(self, tx_data):
        Model.__init__(self, tx_data)
        self.artist = None
        self.title = None
        self.uri = None
        try:
            self.uri = self.data['event']['metadata']['uri']
            self.artist = self.data['event']['metadata']['artists'][0]['name']
            self.title = self.data['event']['metadata']['name']
        except Exception as e:
            pass

    @property
    def genres(self):
        genres = []
        if len(self.tx_data) > 1:
            for event in self.tx_data[1:]:
                event_type = event['metadata']['type']
                if event_type == "map":
                    genres.append(event['metadata']['event']['map'])
        return genres

    @property
    def reactions(self):
        reactions = []
        if len(self.tx_data) > 1:
            for event in self.tx_data[1:]:
                event_type = event['metadata']['type']
                if event_type == "reaction":
                    reactions.append(event['metadata']['event']['reaction'])
        return reactions

    def render(self, bot, size='normal'):
        user_id = self.recent['metadata']['event']['user']
        user_name = bot.store['users'][user_id]['profile']['display_name']
        try:
            title_link = self.data['event']['metadata'].get('external_urls').get('spotify')
        except (AttributeError, KeyError):
            title_link = self.uri
        try:
            thumb_url = self.data['event']['metadata']['album']['images'][2]['url']
        except (AttributeError, KeyError):
            thumb_url = None

        if 'inputs' in self.tx_data[0]:
            genres = 'genres: {} / reactions:{}'.format(", ".join(self.genres), ", ".join(self.reactions))
        else:
            genres = 'load genres with "songs get {}"'.format(self.uri)

        try:
            footer = "#{} @{}".format(self.recent['metadata']['event']['channel'], user_name)
        except (AttributeError, KeyError):
            footer = None

        render = generate_default_response
        if size == 'small':
            render = generate_small_response

        return render(
            tx_id=self.uri,
            tx_uri="{}api/v1/transactions/{}".format(bot.options['bdb']['uri'], self.id),
            title='{} - {}'.format(self.artist, self.title),
            title_link=title_link,
            field_title=genres,
            field_value='musicmap::{}'.format(self.namespace.split('.')[-1]),
            thumb_url=thumb_url,
            footer=footer,
            ts=self.recent['metadata']['event']['ts']
        )


def get_track(spotify, uri):
    return spotify.track(uri)
