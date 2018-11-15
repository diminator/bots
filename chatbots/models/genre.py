from ..slack.render import generate_default_response
from .model import Model


class Genre(Model):
    def __init__(self, connection, _id):
        Model.__init__(self, connection, _id)
        self.value = self.raw['event']['text'].split(" ")[-1]

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
