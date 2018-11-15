from .model import Model
from ..slack.render import generate_default_response


class Song(Model):
    def __init__(self, connection, _id):
        Model.__init__(self, connection, _id)
        self.artist = None
        self.title = None
        self.uri = None
        try:
            self.uri = self.raw['event']['metadata']['uri']
            self.artist = self.raw['event']['metadata']['artists'][0]['name']
            self.title = self.raw['event']['metadata']['name']
        except Exception as e:
            pass

    @property
    def genres(self):
        genres = []
        if len(self.history) > 1:
            for event in self.history[1:]:
                event_type = event['metadata']['type']
                if event_type == "map":
                    genres.append(event['metadata']['event']['map'])
        return genres

    def render(self, bot):
        user_id = self.recent['metadata']['event']['user']
        user_name = bot.store['users'][user_id]['profile']['display_name']
        return generate_default_response(
            tx_id=self.uri,
            tx_uri="{}api/v1/transactions/{}".format(bot.options['bdb']['uri'], self.id),
            title='{} - {}'.format(self.artist, self.title),
            title_link=self.raw['event']['metadata'].get('external_urls').get('spotify'),
            field_title='genres: {}'.format(", ".join(self.genres)),
            field_value='musicmap::{}'.format(self.namespace.split('.')[-1]),
            thumb_url=self.raw['event']['metadata']['album']['images'][2]['url'],
            footer="#{} @{}".format(self.recent['metadata']['event']['channel'], user_name),
            ts=self.recent['metadata']['event']['ts']
        )


def get_track(spotify, uri):
    return spotify.track(uri)
