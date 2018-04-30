from chatbots.backends.bdb import backend


class Topic:
    def __init__(self, topic=None):
        self.topic = topic
        self.history = []

    @property
    def recent(self):
        if len(self.history) > 0:
            return self.history[-1]
        return self.topic

    def load(self, connection):
        self.history = backend.history(asset_id=self.topic['id'], connection=connection)

    def balance(self):
        accounts = {}

        for event in self.history:
            args = event['data']['message'].split(' ')
            user = event['data']['event']['user']

            if user not in accounts:
                accounts[user] = 0

            if args[0] in ['propose'] and len(args) > 1 and args[1].isdigit():
                accounts[user] -= int(args[1])

        return accounts

